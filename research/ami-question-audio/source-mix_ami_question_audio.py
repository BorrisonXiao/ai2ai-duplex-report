"""Match bounded recording characteristics and splice questions into a paused source.

Original prefix/suffix PCM samples are copied exactly. New audio is clearly
marked synthetic, with source-clock and playback-clock intervals in the manifest.
"""
import hashlib
import json
import math
from pathlib import Path
import numpy as np
import soundfile as sf
from scipy.ndimage import gaussian_filter1d
from scipy.signal import firwin2, fftconvolve, resample_poly, welch

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'exp/ami_question_audio'
OUT=BASE/'review'
SR=16000

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def frames(y):
 n=len(y)//320
 return y[:n*320].reshape(n,320)

def active_rms(y):
 r=np.sqrt(np.mean(frames(y)**2,axis=1)+1e-15);keep=r>max(np.max(r)*.12,np.quantile(r,.2)*2)
 return float(np.sqrt(np.mean(r[keep]**2))) if keep.any() else float(np.sqrt(np.mean(y*y)))

def floor_rms(y):return float(np.quantile(np.sqrt(np.mean(frames(y)**2,axis=1)+1e-15),.1))

def db(x):return float(20*np.log10(max(x,1e-10)))

def tone_before(words,mix,t):
 # Only annotated non-speech gaps in the preceding 90 s; never use future audio.
 intervals=sorted((max(t-90,w['start']),min(t,w['end'])) for w in words if not w['punctuation'] and w['end']>t-90 and w['start']<t)
 cursor=t-90;gaps=[]
 for start,end in intervals:
  if start-cursor>=.7:gaps.append((cursor+.08,start-.08))
  cursor=max(cursor,end)
 if t-cursor>=.7:gaps.append((cursor+.08,t-.04))
 choices=[]
 for start,end in gaps:
  if end-start<.4:continue
  end=min(end,start+2);y=mix[round(start*SR):round(end*SR)].astype('float64')/32768
  rms=np.sqrt(np.mean(y*y));peak=np.max(abs(y));choices.append((peak/(rms+1e-10),start,end,y))
 if not choices:raise ValueError('No past-only room-tone gap')
 # Prefer stationary gaps; reject isolated chair taps and other high-crest events.
 _,start,end,y=min(choices,key=lambda a:a[0])
 return y,dict(source_start_seconds=start,source_end_seconds=end,rms_dbfs=db(np.sqrt(np.mean(y*y))),peak_dbfs=db(np.max(abs(y))))

def loop_tone(tone,n):
 # Overlap-add with a cosine ramp prevents a repeated discontinuity.
 k=min(round(.08*SR),len(tone)//4);out=tone.copy();fade=np.linspace(0,1,k)
 while len(out)<n:
  out=np.concatenate([out[:-k],out[-k:]*(1-fade)+tone[:k]*fade,tone[k:]])
 return out[:n]

def process(y,ref,tone,eq_limit_db=0):
 original_duration=len(y)/SR
 # Trim only outer silence; keep 80 ms before and 140 ms after detected activity.
 env=np.sqrt(np.mean(frames(y)**2,axis=1)+1e-15);idx=np.flatnonzero(env>max(env.max()*.045,.00001))
 if not len(idx):raise ValueError('No question speech')
 a=max(0,(idx[0]*320)-1280);b=min(len(y),(idx[-1]+1)*320+2240);y=y[a:b]
 f,p=welch(y,SR,nperseg=1024);_,r=welch(ref,SR,nperseg=1024)
 delta=gaussian_filter1d(10*np.log10((r+1e-13)/(p+1e-13)),12)
 band=(f>=150)&(f<=6000);delta-=np.median(delta[band]);delta=np.clip(delta,-eq_limit_db,eq_limit_db)
 delta[f<80]=delta[np.searchsorted(f,80)];delta[f>7000]=delta[np.searchsorted(f,7000)]
 taps=firwin2(129,f/(SR/2),10**(delta/20))
 colored=fftconvolve(y,taps,mode='same') if eq_limit_db else y.copy()
 gain=np.clip(active_rms(ref)/(active_rms(colored)+1e-12),.25,4)
 colored*=gain
 # Add only the missing noise power; an already noisy clone gets no extra noise.
 real_noise=np.sqrt(np.mean(tone*tone));existing=floor_rms(colored)
 scale=np.sqrt(max(0,real_noise**2-existing**2))/(real_noise+1e-12)
 result=colored+loop_tone(tone,len(colored))*scale
 peak=np.max(abs(result));limiter=min(1,.96/(peak+1e-12));result*=limiter
 fade=min(80,len(result)//4);result[:fade]*=np.linspace(0,1,fade);result[-fade:]*=np.linspace(1,0,fade)
 return result,dict(trim_start_seconds=a/SR,trim_end_seconds=(round(original_duration*SR)-b)/SR,gain_db=db(gain),eq_limit_db=eq_limit_db,eq_frequencies_hz=[float(v) for v in f[::16]],eq_gain_db=[float(v) for v in delta[::16]],room_tone_scale=float(scale),peak_attenuation_db=db(limiter),reference_active_rms_dbfs=db(active_rms(ref)),raw_active_rms_dbfs=db(active_rms(y)),matched_active_rms_dbfs=db(active_rms(result)),raw_noise_floor_proxy_dbfs=db(existing),room_tone_rms_dbfs=db(real_noise),new_room_impulse_response=False)

def main():
 OUT.mkdir(parents=True,exist_ok=True)
 protocol=json.loads((ROOT/'research/ami_question_audio/protocol.json').read_text());words=[w for c in json.loads((ROOT/'exp/prethinking_pilot/data/chunks.json').read_text()) for w in c['words']]
 mix,sr=sf.read(ROOT/'data/prethinking_pilot/ami_EN2003a/EN2003a.Mix-Headset.wav',dtype='int16');assert sr==SR and mix.ndim==1
 asr={r['path']:r for r in json.loads((BASE/'evaluation/asr.json').read_text())};speaker={r['path']:r for r in json.loads((BASE/'evaluation/speaker.json').read_text())}
 journal=json.loads((ROOT/'.migration/updates/2026-10-20-ami-tts/submission.json').read_text());final_jobs={r['model']:r['job_id'] for r in journal['jobs']}
 candidates=[];excluded=[]
 for file in BASE.glob('*_*/generations.json'):
  for r in json.loads(file.read_text()):
   if not r.get('path') or r['path'] not in asr or r['path'] not in speaker:continue
   r['asr']=asr[r['path']];r['speaker_check']=speaker[r['path']]
   if str(r['job'])!=str(final_jobs[r['model']]):
    excluded.append(r);continue
   r['eligible']=r['asr']['wer']==0 and r['speaker_check']['target_minus_other']>0 and r['clipped_fraction']==0
   candidates.append(r)
 clips=[]
 for q in protocol['questions']:
  tone,tone_info=tone_before(words,mix,q['source_time_seconds'])
  for model in sorted({r['model'] for r in candidates}):
   group=[r for r in candidates if r['short_id']==q['short_id'] and r['model']==model]
   if not group:continue
   # Content first; choose strongest held-out voice match among equally accurate outputs.
   r=min(group,key=lambda r:(not r['eligible'],r['asr']['wer'],-r['speaker_check']['target_cosine']))
   ref,ref_sr=sf.read(ROOT/next(x for x in protocol['references'] if x['id']==q['requester']+'-primary')['mix'],dtype='float64');assert ref_sr==SR
   y,ysr=sf.read(ROOT/r['path'],dtype='float64')
   if ysr!=SR:y=resample_poly(y,SR//math.gcd(SR,ysr),ysr//math.gcd(SR,ysr))
   matched,acoustics=process(y,ref,tone)
   stem=q['short_id']+'--'+model;matched_path=OUT/(stem+'--matched.wav');sf.write(matched_path,matched,SR,subtype='PCM_16')
   start={'poster-capacity':1055.27,'outreach':1564.60,'deadlines':2118.85}[q['short_id']];t=q['source_time_seconds'];end=t+5
   pre=mix[round(start*SR):round(t*SR)];post=mix[round(t*SR):round(end*SR)]
   lead=round(.18*SR);tail=round(.25*SR)
   inserted=loop_tone(tone,lead+len(matched)+tail);inserted[lead:lead+len(matched)]=matched
   # Five-ms ramps affect inserted audio only; all original samples stay unchanged.
   n=80;fade=np.linspace(0,1,n);inserted[:n]=float(pre[-1])/32768*(1-fade)+inserted[:n]*fade;inserted[-n:]=inserted[-n:]*(1-fade)+float(post[0])/32768*fade
   pcm=np.round(np.clip(inserted,-1,32767/32768)*32768).astype('int16')
   joined=np.concatenate([pre,pcm,post]);injected=OUT/(stem+'--injected.wav');sf.write(injected,joined,SR,subtype='PCM_16')
   restored,_=sf.read(injected,dtype='int16');assert np.array_equal(restored[:len(pre)],pre) and np.array_equal(restored[-len(post):],post)
   clips.append(dict(id=stem,model=model,short_id=q['short_id'],question=q['question'],question_id=q['id'],requester=q['requester'],setting=r['setting'],source_time_seconds=t,context_start_seconds=start,context_end_seconds=end,synthetic_speech_playback_start_seconds=len(pre)/SR+.18,synthetic_speech_playback_end_seconds=(len(pre)+lead+len(matched))/SR,inserted_interval_start_seconds=len(pre)/SR,inserted_interval_end_seconds=(len(pre)+len(pcm))/SR,source_clock_shift_seconds=len(pcm)/SR,pause_policy='pause_insert_question_resume',original_prefix_pcm_sha256=hashlib.sha256(pre.tobytes()).hexdigest(),original_suffix_pcm_sha256=hashlib.sha256(post.tobytes()).hexdigest(),prefix_suffix_exact=True,raw_path=r['path'],matched_path=str(matched_path.relative_to(ROOT)),injected_path=str(injected.relative_to(ROOT)),matched_sha256=sha(matched_path),injected_sha256=sha(injected),asr=r['asr'],speaker_check=r['speaker_check'],acoustics=acoustics,room_tone=tone_info,eligible=r['eligible'],job=r['job']))
 data=dict(status='automated_checks_complete_listening_review_requested',clips=clips,candidates=candidates,excluded_attempt_outputs=excluded,protocol=protocol,answer_generation='deferred',speech_is_synthetic=True,voice_similarity_is_not_perceptual_validation=True,acoustic_method='Past-only AMI reference conditioning; active-level match, actual past room tone, 16 kHz resampling; zero additional EQ and no invented reverb',gpus_for_mixing=0)
 (OUT/'manifest.json').write_text(json.dumps(data,indent=2)+'\n')
 print(json.dumps([dict(id=c['id'],wer=c['asr']['wer'],speaker=c['speaker_check']['target_cosine'],setting=c['setting']['id'],eligible=c['eligible']) for c in clips],indent=2))

if __name__=='__main__':main()
