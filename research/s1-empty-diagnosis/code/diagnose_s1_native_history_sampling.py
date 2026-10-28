"""Unpaced native 480 ms history prefill, retaining actual S1 outputs; S2 off."""
import argparse,asyncio,copy,json,math,os,subprocess,time
from pathlib import Path
import numpy as np,soundfile as sf,librosa
from diagnose_s1_empty import ROOT,NATIVE,user,save,sha
from s1_response_parser import parse_s1_with_audit
async def main(out):
 import server_thinker as server
 from transformers import AutoProcessor
 snap=ROOT/os.environ['S1_NATIVE_HISTORY_SNAPSHOT']
 for name,h in json.loads((snap/'hashes.json').read_text()).items():assert sha(ROOT/name)==h,name
 out.mkdir(parents=True,exist_ok=True);row=json.loads((ROOT/'research/s1_meeting_pilot/inputs.json').read_text())['cases'][0]
 originals=[]
 for path in [ROOT/row['input_audio'],ROOT/'research/s1_empty_diagnosis/audio/P01-full-request-adjusted.wav']:
  x,sr=sf.read(path,dtype='float32');originals.append(librosa.resample(x,orig_sr=sr,target_sr=24000))
 width=11520;n=math.floor(row['source_cutoff_seconds']/.48);assert np.array_equal(originals[0][:n*width],originals[1][:n*width])
 summary={'status':'loading','job':os.environ['SLURM_JOB_ID'],'gpus':1,'gpu_type_vram':'H200 NVL 141 GB','roles':{'0':'Same S1 Thinker only via vLLM; native message-history diagnostic, no Talker/ASR/S2'},'maximum_active_gpus':1,'question_id':row['question_id'],'source_cutoff_seconds':row['source_cutoff_seconds'],'prefill_frames_planned':n,'prefill_frames_completed':0,'history_trim_events':0,'temperature':.8,'max_output_tokens_per_turn':999,'branches':[]};save(out/'summary.json',summary)
 proc=AutoProcessor.from_pretrained(ROOT/'models/duplexomni',trust_remote_code=True);engine=None;started=time.monotonic();messages=[{'role':'system','content':NATIVE}];asr=[];tts=[];max_tokens=0;total_calls=0
 async def step(messages,wave,rid):
  nonlocal max_tokens,total_calls
  messages.append(user(wave,24000));prompt=server.build_engine_prompt(proc,messages,conversation_id='native-history')
  # Bound before generation, without constructing a padded batch of all audios.
  text_tokens=len(proc.tokenizer.encode(prompt['prompt'],add_special_tokens=False));audio_items=sum(m['role']=='user' for m in messages);assert text_tokens+7*audio_items+999<65536
  sampling=server.build_sampling_params({'temperature':.8,'max_tokens':999});sampling.seed=17;final=None
  async for value in engine.generate(prompt,sampling,rid):final=value
  c=final.outputs[0];await engine.collective_rpc('extract_reply_tensors',args=(rid,list(c.token_ids)));messages.append({'role':'assistant','content':c.text});total_calls+=1;max_tokens=max(max_tokens,len(final.prompt_token_ids))
  try:fields,audit=parse_s1_with_audit(c.text);error=None
  except ValueError as exc:fields=None;error=str(exc)
  r={'id':rid,'raw_text':c.text,'fields':fields,'parse_error':error,'finish_reason':c.finish_reason,'prompt_tokens':len(final.prompt_token_ids),'output_tokens':len(c.token_ids)}
  with (out/'turns.jsonl').open('a') as f:f.write(json.dumps(r,ensure_ascii=False)+'\n')
  return r
 try:
  engine=server.AsyncLLM.from_engine_args(server.AsyncEngineArgs(model=str(ROOT/'models/duplexomni'),tensor_parallel_size=1,max_model_len=65536,enable_prefix_caching=True,limit_mm_per_prompt={'audio':{'count':750,'length':7680},'image':0,'video':0},worker_cls='server_thinker.TensorCapturingGPUWorker',dtype='bfloat16',kv_cache_memory_bytes=7*2**30,gpu_memory_utilization=.85,enforce_eager=False,max_num_seqs=1,max_num_batched_tokens=20480))
  for i in range(n):
   r=await step(messages,originals[0][i*width:(i+1)*width],f'prefix-{i}');f=r['fields'] or {};asr.append(f.get('asr',''));tts.append(f.get('tts',''));summary['prefill_frames_completed']=i+1
   if i%64==0:
    summary.update(status='native_history_prefill',max_prompt_tokens=max_tokens,total_model_calls=total_calls,wall_seconds=time.monotonic()-started);save(out/'summary.json',summary);print(json.dumps({'prefill_frames':i+1,'source_seconds':(i+1)*.48,'prompt_tokens':r['prompt_tokens']}),flush=True)
  save(out/'prefix-messages-private.json',messages);summary['prefix_asr']=''.join(asr);summary['prefix_tts']=''.join(tts);save(out/'summary.json',summary)
  for name,wave in zip(['original','request_adjusted'],originals):
   branch=copy.deepcopy(messages);speech=wave[n*width:];frames=[np.pad(speech[i:i+width],(0,max(0,width-len(speech[i:i+width])))) for i in range(0,len(speech),width)]+[np.zeros(width)]*40;turns=[]
   for i,w in enumerate(frames):turns.append(await step(branch,w,name+'-'+str(i)))
   summary['branches'].append({'id':name,'question':row['question'],'model_calls':len(turns),'native_text':''.join((r['fields'] or {}).get('tts','') for r in turns),'model_asr':''.join((r['fields'] or {}).get('asr','') for r in turns),'S2_requests':[(r['fields'] or {})['system2_control'] for r in turns if (r['fields'] or {}).get('system2_control')],'unstructured_text':[r['raw_text'] for r in turns if r['fields'] is None]});save(out/'summary.json',summary);print(json.dumps(summary['branches'][-1]),flush=True)
  summary['status']='completed_content_review_required'
 finally:
  if engine:engine.shutdown()
  summary.update(wall_seconds=time.monotonic()-started,max_prompt_tokens=max_tokens,total_model_calls=total_calls);save(out/'summary.json',summary)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);asyncio.run(main(p.parse_args().out))
