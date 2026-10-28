"""Same S1 checkpoint: ordinary audio QA, question-text oracle, transcript oracle.

These are text-output diagnostics, not native duplex speech baseline results.
"""
import argparse,asyncio,copy,json,os,subprocess,time
from pathlib import Path
import soundfile as sf
from diagnose_s1_empty import ROOT,user,save,sha
PROMPT='Answer the final request using only the supplied meeting. Give a short, complete English answer. If the meeting does not establish something, state that. This is an offline question-answering check: return ordinary answer text rather than streaming control fields. Do not invent facts or claim to use unavailable tools.'
async def main(out):
 import server_thinker as server
 from transformers import AutoProcessor
 p=AutoProcessor.from_pretrained(ROOT/'models/duplexomni',trust_remote_code=True);rows=json.loads((ROOT/'research/s1_meeting_pilot/inputs.json').read_text())['cases'];snap=ROOT/os.environ['S1_ORACLE_SNAPSHOT']
 for name,h in json.loads((snap/'hashes.json').read_text()).items():assert sha(ROOT/name)==h,name
 out.mkdir(parents=True,exist_ok=True);summary={'status':'loading','gpus':1,'gpu_type_vram':subprocess.check_output(['nvidia-smi','--query-gpu=name,memory.total','--format=csv,noheader'],text=True).strip(),'roles':{'0':'DuplexOmni S1 Thinker only, using vLLM; no speech/S2/ASR service'},'maximum_active_gpus':1,'scope':'Ordinary answer-text diagnostics, not native duplex speech scores. The question-text and transcript conditions explicitly supply oracle text.','cases':[]};save(out/'summary.json',summary);started=time.monotonic();engine=None
 try:
  engine=server.AsyncLLM.from_engine_args(server.AsyncEngineArgs(model=str(ROOT/'models/duplexomni'),tensor_parallel_size=1,max_model_len=49152,enable_prefix_caching=True,limit_mm_per_prompt={'audio':{'count':1,'length':7680},'image':0,'video':0},worker_cls='server_thinker.TensorCapturingGPUWorker',dtype='bfloat16',kv_cache_memory_bytes=5*2**30,gpu_memory_utilization=.85,enforce_eager=False,max_num_seqs=1,max_num_batched_tokens=20480))
  for row in rows:
   assert sha(ROOT/row['input_audio'])==row['input_sha256'];wave,rate=sf.read(ROOT/row['input_audio'],dtype='float32');audio=user(wave,rate)['content'][1]
   chunks=json.loads((ROOT/'data/question_scale'/row['meeting']/'chunks.json').read_text());chunks=sorted([c for c in chunks if c['end']<=row['source_cutoff_seconds']],key=lambda c:(c['start'],c['end']))
   transcript='\n'.join(f"{c['start']:.2f}–{c['end']:.2f} s, speaker {c['speaker']}: {c['text']}" for c in chunks)
   for mode,content in [('audio',[copy.deepcopy(audio),{'type':'text','text':'Answer the request spoken at the end of this recording.'}]),('audio_question_text',[copy.deepcopy(audio),{'type':'text','text':'Final request: '+row['question']}]),('transcript_question_text','Meeting transcript available before the request:\n'+transcript+'\nFinal request: '+row['question'])]:
    name=row['id']+'-'+mode;messages=[{'role':'system','content':PROMPT},{'role':'user','content':content}];prompt=server.build_engine_prompt(p,messages,conversation_id=name);sampling=server.build_sampling_params({'temperature':0,'max_tokens':1024});sampling.seed=17;final=None;before=time.monotonic()
    async for result in engine.generate(prompt,sampling,name):final=result
    result=final.outputs[0];await engine.collective_rpc('extract_reply_tensors',args=(name,list(result.token_ids)))
    r={'id':name,'question_id':row['question_id'],'question':row['question'],'mode':mode,'oracle_question_text':mode!='audio','oracle_history_text':mode=='transcript_question_text','answer_text':result.text,'finish_reason':result.finish_reason,'output_tokens':len(result.token_ids),'prompt_tokens':len(final.prompt_token_ids),'wall_seconds':time.monotonic()-before,'audio_input_sha256':row['input_sha256'] if mode!='transcript_question_text' else None,'source_cutoff_seconds':row['source_cutoff_seconds']};assert r['prompt_tokens']+1024<=49152;summary['cases'].append(r);save(out/'summary.json',summary);print(json.dumps(r),flush=True)
  summary['status']='completed_source_review_required'
 finally:
  if engine:engine.shutdown()
  summary['wall_seconds']=time.monotonic()-started;save(out/'summary.json',summary)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);asyncio.run(main(p.parse_args().out))
