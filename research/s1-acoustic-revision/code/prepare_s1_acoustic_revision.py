"""Make input-only acoustic revisions from past paired speech and room tone."""
import copy,hashlib,json
from pathlib import Path
import numpy as np
import soundfile as sf
from scipy import signal
from scipy.ndimage import gaussian_filter1d
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'research/s1_acoustic_revision';A=ROOT/'exp/s1_acoustic_revision/assets';SR=16000
LABELS={'headset_mix':'Headset mix','distant_01':'One distant microphone','beamformed_mdm8':'Eight-microphone beamformed audio'}
def read(p):return json.loads(p.read_text())
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def db(x):return float(20*np.log10(max(float(x),1e-12)))
def active(y):
 n=len(y)//320;r=np.sqrt(np.mean(y[:n*320].reshape(n,320)**2,axis=1)+1e-18);use=r>max(np.quantile(r,.2)*2,r.max()*.12)
 return float(np.sqrt(np.mean(r[use]**2))) if use.any() else float(np.sqrt(np.mean(y*y)))
def spectral_distance(x,y):
 f,p=signal.welch(x,SR,nperseg=1024);_,q=signal.welch(y,SR,nperseg=1024);mask=(f>=150)&(f<=6000)
 a=gaussian_filter1d(10*np.log10(p+1e-14),5)[mask];b=gaussian_filter1d(10*np.log10(q+1e-14),5)[mask];a-=np.mean(a);b-=np.mean(b)
 return float(np.sqrt(np.mean((a-b)**2)))
def fit_filter(pairs):
 xx=xy=yy=None
 for x,y in pairs:
  _,_,X=signal.stft(x,SR,nperseg=4096,noverlap=3072,boundary=None,padded=False);_,_,Y=signal.stft(y,SR,nperseg=4096,noverlap=3072,boundary=None,padded=False)
  energy=np.mean(abs(X)**2,axis=0);keep=energy>np.quantile(energy,.25)
  X=X[:,keep];Y=Y[:,keep]
  u=np.sum(abs(X)**2,axis=1);v=np.sum(X.conj()*Y,axis=1);w=np.sum(abs(Y)**2,axis=1)
  xx=u if xx is None else xx+u;xy=v if xy is None else xy+v;yy=w if yy is None else yy+w
 freq=np.fft.rfftfreq(4096,1/SR)
 delta=gaussian_filter1d(10*np.log10((yy+1e-16)/(xx+1e-16)),20)
 band=(freq>=150)&(freq<=6000);delta-=np.median(delta[band]);delta=np.clip(delta,-9,9)
 delta[freq<80]=delta[np.searchsorted(freq,80)];delta[freq>7000]=delta[np.searchsorted(freq,7000)]
 ir=signal.firwin2(513,freq/(SR/2),10**(delta/20))
 assert np.isfinite(ir).all() and np.max(abs(ir))>0
 return ir,dict(taps=len(ir),duration_seconds=len(ir)/SR,eq_limit_db=9,group_delay_removed_samples=256,method='Smoothed paired-speech spectral EQ, bounded to 9 dB; no room impulse response or added reverb',frequencies_hz=[float(v) for v in freq[::64]],gains_db=[float(v) for v in delta[::64]])

def noise_gaps(words,cut):
 spans=sorted((max(120.,w['start']),min(cut,w['end'])) for w in words if not w['punctuation'] and w['end']>120 and w['start']<cut);cursor=120.;out=[]
 for start,end in spans:
  if start-cursor>=.35:
   a=cursor+.06;b=start-.06
   for s in np.arange(a,b-.18,.35):
    e=min(s+.7,b)
    if e-s>=.2:out.append((float(s),float(e)))
  cursor=max(cursor,end)
 return out

def texture(signal_source,gaps,length):
 candidates=[]
 for a,b in gaps:
  y=signal_source[round(a*SR):round(b*SR)];r=np.sqrt(np.mean(y*y));crest=np.max(abs(y))/(r+1e-12)
  if r>1e-7:candidates.append((r,crest,a,b,y))
 # Low-energy, bounded-crest gaps avoid foreground taps and annotated words.
 pool=[]
 for c in sorted(candidates,key=lambda c:c[2],reverse=True):
  if c[1]>=10 or any(c[2]<v[3] and c[3]>v[2] for v in pool):continue
  pool.append(c)
  if len(pool)==8:break
 assert len(pool)>=3,(len(pool),len(candidates))
 rng=np.random.default_rng(17);k=320;out=pool[0][4].copy();fade=np.linspace(0,1,k)
 while len(out)<length:
  y=pool[int(rng.integers(len(pool)))][4];out=np.concatenate([out[:-k],out[-k:]*(1-fade)+y[:k]*fade,y[k:]])
 out=out[:length];target=float(np.sqrt(np.mean(np.concatenate([c[4] for c in pool])**2)));out*=target/(np.sqrt(np.mean(out*out))+1e-12)
 return out,dict(source_gaps=[dict(start_seconds=c[2],end_seconds=c[3]) for c in pool],rms_dbfs=db(target),source='Actual earlier annotation-gap audio, shuffled with 20 ms overlap-add; no future audio')
def main():
 assert not (D/'submission.json').exists(),'Do not change submitted audio'
 A.mkdir(parents=True,exist_ok=True)
 old=read(ROOT/'research/s1_context_pressure/protocol.json');q=old['question'];cut=round(q['source_cutoff_seconds']*SR);lead=round((q['request_start_seconds']-q['source_cutoff_seconds'])*SR)
 source,sr=sf.read(ROOT/q['input_audio'],dtype='float64');assert sr==SR
 clean,sr=sf.read(ROOT/'site/research/question-audio-complete/audio/scale--TS3006c-S05-Q3--question.wav',dtype='float64');assert sr==SR
 assert len(clean)==round((q['request_end_seconds']-q['request_start_seconds'])*SR)
 refs=[r for r in read(ROOT/'research/question_audio_completion/protocol.json')['references'] if r['voice']=='TS3006c-D'];train=[r for r in refs if r['role']!='heldout'];held=next(r for r in refs if r['role']=='heldout')
 assert all(r['source_end_seconds']<q['source_cutoff_seconds'] and r['annotated_other_speech_fraction']==0 for r in refs)
 contrast=read(ROOT/'research/s1_array_contrast/protocol.json');words=read(ROOT/'data/question_audio_completion/TS3006c/words.json');gaps=noise_gaps(words,q['source_cutoff_seconds']);rows=[]
 for c in contrast['cases']:
  name=c['id'];old_audio,sr=sf.read(ROOT/c['protocol']['question']['input_audio'],dtype='float64');old_audio=old_audio.copy();old_audio[cut:]*=10**(old['request_level_gain_db']/20)
  if name=='headset_mix':native=source[:cut].copy()
  else:native,sr=sf.read(ROOT/f'data/s1_array_contrast/{name}.wav',dtype='float64');native=native[:cut]*10**(c['gain_db']/20)
  assert sr==SR and len(native)==cut and np.max(abs(native))<1
  native=np.rint(native*32768).clip(-32768,32767).astype('int16').astype('float64')/32768
  pairs=[]
  for ref in train:
   x,sr=sf.read(ROOT/ref['headset'],dtype='float64');y=native[round(ref['source_start_seconds']*SR):round(ref['source_end_seconds']*SR)];assert len(x)==len(y);pairs.append((x,y))
  ir,filter_info=fit_filter(pairs);sf.write(A/(name+'-relative-filter.wav'),ir,SR,subtype='FLOAT')
  x,sr=sf.read(ROOT/held['headset'],dtype='float64');target=native[round(held['source_start_seconds']*SR):round(held['source_end_seconds']*SR)];pred=signal.fftconvolve(x,ir,mode='same');fit_info=dict(unfiltered_spectral_distance_db=spectral_distance(x,target),filtered_spectral_distance_db=spectral_distance(pred,target),heldout_source_start_seconds=held['source_start_seconds'],heldout_source_end_seconds=held['source_end_seconds'])
  target_level=float(np.median([active(y) for x,y in pairs]));noise,noise_info=texture(native,gaps,len(source)-cut)
  native_path=A/(name+'-real-voice-reference.wav');sf.write(native_path,target,SR,subtype='PCM_16')
  noise_path=A/(name+'-background-control.wav');sf.write(noise_path,noise,SR,subtype='PCM_16')
  for variant in ['tone','channel']:
   speech=clean.copy() if variant=='tone' else signal.fftconvolve(clean,ir,mode='same')
   speech*=target_level/(active(speech)+1e-12)
   insertion=noise.copy();n=min(len(speech),len(insertion)-lead);insertion[lead:lead+n]+=speech[:n]
   # Alter inserted samples only: retain every native source-prefix sample.
   bridge=80;fade=np.linspace(0,1,bridge);insertion[:bridge]=native[-1]*(1-fade)+insertion[:bridge]*fade
   assert np.max(abs(insertion))<.98,'Inspect clipping rather than silently limiting'
   joined=np.concatenate([native,insertion]);path=A/(name+'-'+variant+'-input.wav');sf.write(path,joined,SR,subtype='PCM_16')
   question=A/(name+'-'+variant+'-question.wav');sf.write(question,insertion[lead:],SR,subtype='PCM_16')
   preview=A/(name+'-'+variant+'-preview.wav');sf.write(preview,joined[round(291.03*SR):],SR,subtype='PCM_16')
   original=A/(name+'-original-preview.wav')
   if not original.exists():sf.write(original,old_audio[round(291.03*SR):],SR,subtype='PCM_16')
   restored,sr=sf.read(path,dtype='int16');assert np.array_equal(restored[:cut],np.rint(native*32768).clip(-32768,32767).astype('int16'))
   gap=slice(round(.03*SR),round(.15*SR));old_gap=old_audio[cut:][gap];new_gap=insertion[gap]
   rows.append(dict(id=name+'-'+variant,condition=name,label=LABELS[name],context_gain_db=c['gain_db'],variant=variant,input_audio=str(path.relative_to(ROOT)),question_audio=str(question.relative_to(ROOT)),preview_audio=str(preview.relative_to(ROOT)),old_preview_audio=str(original.relative_to(ROOT)),real_reference_audio=str(native_path.relative_to(ROOT)),background_control_audio=str(noise_path.relative_to(ROOT)),input_sha256=sha(path),prefix_pcm_exact=True,request_wording=q['question'],source_cutoff_seconds=q['source_cutoff_seconds'],request_start_seconds=q['request_start_seconds'],request_end_seconds=q['request_end_seconds'],request_gain_db=0.,question_active_rms_dbfs=db(active(insertion[lead:])),reference_target_active_rms_dbfs=db(target_level),old_transition_rms_dbfs=db(np.sqrt(np.mean(old_gap**2))),revised_transition_rms_dbfs=db(np.sqrt(np.mean(new_gap**2))),noise=noise_info,filter=filter_info if variant=='channel' else None,heldout_channel_check={**fit_info,'scope':'Disjoint development reference, not independent perceptual validation'},peak=float(np.max(abs(insertion)))))
 save(D/'protocol.json',dict(status='prepared_input_ASR_required',meeting='TS3006c',question=q['question'],cases=rows,filter_training_references=[{k:r[k] for k in ['role','source_start_seconds','source_end_seconds']} for r in train],heldout_reference={k:held[k] for k in ['role','source_start_seconds','source_end_seconds']},scope='Six revised input realizations, not new S1 responses; original Figures1–4 remain unchanged.',limitations=['Only bounded spectral EQ is applied; a fixed room impulse response could not be validated from the paired speech. No new reverberation is synthesized.','Only one speaker/meeting/question; acoustic naturalness needs listening review.','Noise, level and boundary changes are combined; no single-factor performance attribution.','No new S1 replay, voice training or question wording change.'],gpus_for_preparation=0))
 print(json.dumps([dict(id=r['id'],old_transition_dbfs=r['old_transition_rms_dbfs'],new_transition_dbfs=r['revised_transition_rms_dbfs'],heldout=r['heldout_channel_check'],active_level=r['question_active_rms_dbfs'],target=r['reference_target_active_rms_dbfs']) for r in rows],indent=2))
if __name__=='__main__':main()
