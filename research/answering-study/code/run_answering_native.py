"""Unpaced native Moshi/MiniCPM accuracy pilot with complete packet/response loops."""
import argparse,hashlib,json,math,os,time
from pathlib import Path
import numpy as np,torch
try:import soundfile as sf
except ModuleNotFoundError:import mpbench_audio as sf
from run_mpbench_native import Moshi,MiniCPM
ROOT=Path(__file__).resolve().parents[1]
MEETING='You are a separate meeting assistant. Listen to the discussion and answer when addressed as Assistant, using only what was said earlier. Distinguish proposals from agreed decisions and completed work. If the discussion does not establish an answer, say so. You have no external lookup tools; do not claim to have performed an action.'
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);temp=p.with_suffix('.tmp');temp.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n');temp.replace(p)
def run(model,row,base):
 folder=base/row['id'];folder.mkdir(parents=True,exist_ok=False);audio,sr=sf.read(ROOT/row['input_audio'],dtype='float32')
 if sr!=model.rate:
  if isinstance(model,MiniCPM):
   import librosa
   audio=librosa.resample(audio,orig_sr=sr,target_sr=model.rate)
  else:
   import sphn
   audio,_=sphn.read(str(ROOT/row['input_audio']),sample_rate=model.rate)
 audio=audio.reshape(-1).astype('float32');frame=round(model.step*model.rate);n=math.ceil((len(audio)/model.rate+60)/model.step);audio=np.pad(audio,(0,n*frame-len(audio)))
 if isinstance(model,MiniCPM) and row['variant']!='control':
  model.model.prepare(prefix_system_prompt='<|im_start|>system\n'+MEETING+'\n<|audio_start|>',suffix_system_prompt='<|audio_end|><|im_end|>',ref_audio=model.ref_audio,prompt_wav_path=str(model.ref))
 else:model.reset()
 started=time.monotonic();parts=[];background=[];ticks=[];generated=[];record=dict(id=row['id'],question_id=row['question_id'],variant=row['variant'],status='running',native_frame_seconds=model.step,expected_frames=n,processed_frames=0,input_sha256=row['input_sha256'],gpus=1,history_policy='Native checkpoint/cache behavior; no explicit application-level trimming.',request_recognition_ASR='not exposed by this model; generated text is the response, not input ASR',output_scope='Actual generated waveform in call order; no paced-playback latency claim.')
 save(folder/'run.json',record)
 try:
  for i in range(n):
   before=time.monotonic();wave,decision=model.step_audio(audio[i*frame:(i+1)*frame]);end=(i+1)*model.step;capture=end>row['request_start_seconds'];piece=None
   if wave is not None:
    piece=np.asarray(wave,dtype='float32').reshape(-1);assert np.isfinite(piece).all()
    (parts if capture else background).append(piece)
   if capture:generated.append(decision.get('text') or '')
   tick=dict(index=i,input_end_seconds=end,phase='request_or_response' if capture else 'history',decision=decision,wall_seconds=time.monotonic()-before,output_samples=len(piece) if piece is not None else 0)
   ticks.append(tick)
   with (folder/'ticks.jsonl').open('a') as f:f.write(json.dumps(tick,ensure_ascii=False,default=str)+'\n')
   if i%16==0 or i==n-1:
    record.update(processed_frames=i+1,phase=tick['phase'],wall_seconds=time.monotonic()-started,generated_text=''.join(generated));save(folder/'run.json',record);save(base/'heartbeat.json',dict(case=row['id'],phase=tick['phase'],processed_frames=i+1,expected_frames=n,updated_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())))
  record.update(status='completed_content_review_required',complete_input=True)
 except Exception as exc:record.update(status='failed',complete_input=False,error=type(exc).__name__+': '+str(exc))
 finally:
  y=np.concatenate(parts) if parts else np.zeros(1,dtype='float32');sf.write(folder/'response.wav',y,24000,subtype='PCM_16')
  bg=np.concatenate(background) if background else np.zeros(1,dtype='float32');sf.write(folder/'background-generated.wav',bg,24000,subtype='PCM_16')
  record.update(processed_frames=len(ticks),generated_text=''.join(generated),wall_seconds=time.monotonic()-started,audio_sha256=hashlib.sha256((folder/'response.wav').read_bytes()).hexdigest(),native_text_in_last_packet=bool(ticks and ticks[-1]['decision'].get('text')),response_native_end_of_turn_observed=any(t['phase']=='request_or_response' and t['decision'].get('end_of_turn') for t in ticks));save(folder/'run.json',record)
 return record
def main():
 p=argparse.ArgumentParser();p.add_argument('--model',choices=['moshi','minicpm'],required=True);a=p.parse_args();snap=ROOT/os.environ['ANSWERING_SNAPSHOT']
 for name,h in json.loads((snap/'hashes.json').read_text()).items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h,name
 manifest=json.loads((ROOT/'research/answering_study_20261101/pilot-audio.json').read_text());job=os.environ['SLURM_JOB_ID'];base=ROOT/'exp/answering_native'/job;base.mkdir(parents=True,exist_ok=True);start=time.monotonic();torch.manual_seed(23);np.random.seed(23)
 with torch.inference_mode():
  model=Moshi() if a.model=='moshi' else MiniCPM();model.reset();startup=dict(model=a.model,load_seconds=time.monotonic()-start,roles='All native LM/codec/speech components share GPU 0; no S2.',gpu=torch.cuda.get_device_name(0),native_meeting_prompt=MEETING if a.model=='minicpm' else 'Moshi has no text system-prompt interface; native conditioning retained.')
  if a.model=='moshi':startup['sampling']={k:getattr(model.state.lm_gen,k,None) for k in ['use_sampling','temp','temp_text','top_k','top_k_text']}
  save(base/'startup.json',startup)
  control=ROOT/manifest['control_audio'];x,rate=sf.read(control,dtype='float32');seconds=len(x)/rate;rows=[dict(id='native-control',question_id='control:DailyTalk-outlet',variant='control',input_audio=manifest['control_audio'],input_sha256=hashlib.sha256(control.read_bytes()).hexdigest(),request_start_seconds=0.,request_end_seconds=seconds)]+sorted(manifest['cases'],key=lambda r:(r['variant']=='full',r['id']))
  results=[]
  for row in rows:
   assert hashlib.sha256((ROOT/row['input_audio']).read_bytes()).hexdigest()==row['input_sha256'];results.append(run(model,row,base));save(base/'summary.json',dict(model=a.model,status='running',cases=results,wall_seconds=time.monotonic()-start));print(a.model,row['id'],results[-1]['status'],flush=True)
  save(base/'summary.json',dict(model=a.model,status='completed_content_review_required',cases=results,wall_seconds=time.monotonic()-start,GPUs=1,peak_GPU_bytes=torch.cuda.max_memory_allocated(),no_real_time_latency_claim=True))
if __name__=='__main__':main()
