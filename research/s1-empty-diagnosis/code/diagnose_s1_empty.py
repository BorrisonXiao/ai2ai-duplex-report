"""Controlled S1 Thinker diagnostics; no S2, supplied answers, or speech service."""
import argparse,asyncio,base64,copy,hashlib,io,json,os,subprocess,sys,time
from pathlib import Path
import numpy as np,soundfile as sf
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'research/s1_empty_diagnosis'
sys.path.insert(0,str(ROOT/'external/duplexomni/inference_framework/realtime_serving/serving_core'))
os.environ['VLLM_ROOT']=str(ROOT/'envs/duplexomni/lib/python3.11/site-packages')
NATIVE='你是有用的助手\n你的助手风格是：耐心。\n你的开场方式要求：短句清晰。'
FORMAT="\nFor every response, return only the native four-field object: {'tts_control': '', 'system2_control': '', 'asr': '', 'tts': ''}. Put the words to speak in tts, and recognized recent user speech in asr. Do not return plain text outside the object."
TASK="\nThe audio contains a meeting followed by a question addressed to you. Answer the last question using the earlier speech. Give the supported answer directly, without a greeting or an offer to check. If the meeting does not establish a claimed result, say that."
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):
 p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix('.tmp');q.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n');q.replace(p)
def user(wave,rate):
 b=io.BytesIO();sf.write(b,wave,rate,format='WAV',subtype='PCM_16')
 return {'role':'user','content':[{'type':'text','text':"{'audio_input': '"},{'type':'input_audio','input_audio':{'data':base64.b64encode(b.getvalue()).decode(),'format':'wav'}},{'type':'text','text':"', 'from_s2': ''}"}]}
def prepare():
 import librosa
 rows=json.loads((ROOT/'research/s1_meeting_pilot/inputs.json').read_text())['cases'];cases=[];assets=D/'audio';assets.mkdir(exist_ok=True)
 for r in rows:
  original=ROOT/r['input_audio'];assert sha(original)==r['input_sha256'];x,rate=sf.read(original,dtype='float32');cut=round(r['source_cutoff_seconds']*rate);q=x[cut:]
  gain=min(.05/float(np.sqrt(np.mean(q.astype('float64')**2))),.95/max(float(abs(q).max()),1e-9))
  for level,g in [('original',1.),('rms_adjusted',gain)]:
   path=assets/(r['id']+'-'+level+'-request.wav');sf.write(path,q*g,rate,subtype='PCM_16')
   q24=librosa.resample(q*g,orig_sr=rate,target_sr=24000)
   frames=[np.pad(q24[i:i+11520],(0,max(0,11520-len(q24[i:i+11520])))) for i in range(0,len(q24),11520)]
   cases.append({'id':r['id']+'-request-only-'+level,'pilot_id':r['id'],'question_id':r['question_id'],'question':r['question'],'mode':'native_packets','level':level,'gain':g,'system_prompt':NATIVE,'audio_path':str(path.relative_to(ROOT)),'audio_sha256':sha(path),'history':'none; recognition diagnostic only','turns':[(f,24000) for f in frames]+[(np.zeros(11520),24000)]*12})
  for promptname,prompt in [('native',NATIVE),('format',NATIVE+FORMAT),('task',NATIVE+TASK),('format_task',NATIVE+FORMAT+TASK)]:
   cases.append({'id':r['id']+'-full-'+promptname,'pilot_id':r['id'],'question_id':r['question_id'],'question':r['question'],'mode':'buffered','level':'original','gain':1.,'system_prompt':prompt,'audio_path':r['input_audio'],'audio_sha256':sha(original),'history':'full','turns':[(x,rate)]+[(np.zeros(7680),16000)]*8})
  boosted=x.copy();boosted[cut:]*=gain;path=assets/(r['id']+'-full-request-adjusted.wav');sf.write(path,boosted,rate,subtype='PCM_16')
  cases.append({'id':r['id']+'-full-native-request-adjusted','pilot_id':r['id'],'question_id':r['question_id'],'question':r['question'],'mode':'buffered','level':'request_rms_adjusted','gain':gain,'system_prompt':NATIVE,'audio_path':str(path.relative_to(ROOT)),'audio_sha256':sha(path),'history':'full','turns':[(boosted,rate)]+[(np.zeros(7680),16000)]*8})
 sky=ROOT/'data/benchmarks/authored_controls/sky_question.wav';x,rate=sf.read(sky,dtype='float32');assert rate==24000
 frames=[np.pad(x[i:i+11520],(0,max(0,11520-len(x[i:i+11520])))) for i in range(0,len(x),11520)]
 cases.insert(0,{'id':'sky-native-control','pilot_id':'sky','mode':'native_packets','level':'original','gain':1.,'system_prompt':NATIVE,'audio_path':str(sky.relative_to(ROOT)),'audio_sha256':sha(sky),'history':'none','turns':[(f,rate) for f in frames]+[(np.zeros(11520),rate)]*24})
 return cases
async def run(args):
 from transformers import AutoProcessor
 import server_thinker as server
 from vllm.config import ModelConfig
 from vllm.multimodal import MULTIMODAL_REGISTRY
 from s1_response_parser import parse_s1_with_audit
 cases=prepare();out=args.out;out.mkdir(parents=True,exist_ok=True)
 processor=AutoProcessor.from_pretrained(ROOT/'models/duplexomni',trust_remote_code=True)
 limit={'audio':{'count':49,'length':7680},'image':0,'video':0}
 config=ModelConfig(model=str(ROOT/'models/duplexomni'),max_model_len=49152,limit_mm_per_prompt=limit);mm=MULTIMODAL_REGISTRY.create_processor(config)
 if args.preflight:
  checked=[]
  for c in cases:
   longest=[{'role':'system','content':c['system_prompt']},user(*c['turns'][0])]
   p=server.build_engine_prompt(processor,longest,conversation_id=c['id']);processed=mm.apply(p['prompt'],mm.info.parse_mm_data(p['multi_modal_data']),{});n=len(processed['prompt_token_ids']);assert n+8192<49152
   checked.append({'id':c['id'],'initial_prompt_tokens':n,'maximum_audio_items':len(c['turns']),'gpus':0})
  save(out/'preflight.json',{'status':'pass','cases':checked,'gpus':0});return
 for name,h in json.loads((ROOT/os.environ['S1_EMPTY_SNAPSHOT']/'hashes.json').read_text()).items():assert sha(ROOT/name)==h,name
 monitor=subprocess.Popen(['nvidia-smi','--id',os.environ['CUDA_VISIBLE_DEVICES'],'--query-gpu=timestamp,uuid,name,memory.total,memory.used,utilization.gpu','--format=csv,nounits','-l','2','-f',str(out/'gpu.csv')])
 gpu_type=subprocess.check_output(['nvidia-smi','--id',os.environ['CUDA_VISIBLE_DEVICES'],'--query-gpu=name,memory.total','--format=csv,noheader'],text=True).strip()
 summary={'status':'loading','job':os.environ['SLURM_JOB_ID'],'gpus':1,'gpu_type_vram':gpu_type,'roles':{'0':'DuplexOmni S1 Thinker only; vLLM, audio encoder and language model together'},'S2_enabled':False,'speech_loaded':False,'maximum_active_gpus':1,'model':'MuyeHuang/DuplexOmni','revision':'b8a5ff6395ae51460d0402424fbd3359614a901a','cases':[]};save(out/'summary.json',summary);started=time.monotonic();engine=None
 try:
  engine=server.AsyncLLM.from_engine_args(server.AsyncEngineArgs(model=str(ROOT/'models/duplexomni'),tensor_parallel_size=1,max_model_len=49152,enable_prefix_caching=True,limit_mm_per_prompt=limit,worker_cls='server_thinker.TensorCapturingGPUWorker',dtype='bfloat16',kv_cache_memory_bytes=5*2**30,gpu_memory_utilization=.85,enforce_eager=False,max_num_seqs=1,max_num_batched_tokens=20480))
  summary['startup_seconds']=time.monotonic()-started
  for c in cases:
   r={k:v for k,v in c.items() if k!='turns'};r.update(turns=[],tts='',asr='',status='running');summary['cases'].append(r);messages=[{'role':'system','content':c['system_prompt']}]
   folder=out/c['id'];folder.mkdir(exist_ok=True);before=time.monotonic()
   for tick,w in enumerate(c['turns']):
    messages.append(user(*w));prompt=server.build_engine_prompt(processor,messages,conversation_id=c['id'])
    sampling=server.build_sampling_params({'max_tokens':1024 if tick==0 and c['mode']=='buffered' else 256,'temperature':0});sampling.seed=17;rid=c['id']+'-'+str(tick);final=None
    async for answer in engine.generate(prompt,sampling,rid):final=answer
    assert final is not None;completion=final.outputs[0]
    await engine.collective_rpc('extract_reply_tensors',args=(rid,list(completion.token_ids)))
    turn={'tick':tick,'raw_text':completion.text,'token_ids':list(completion.token_ids),'prompt_tokens':len(final.prompt_token_ids),'finish_reason':completion.finish_reason};r['turns'].append(turn)
    try:fields,audit=parse_s1_with_audit(completion.text)
    except ValueError as error:r.update(status='unstructured_response',error=str(error),raw_unstructured_text=completion.text);break
    turn['fields']=fields;turn['parser']=audit;r['tts']+=fields['tts'];r['asr']+=fields['asr'];messages.append({'role':'assistant','content':completion.text})
    if completion.finish_reason=='length':r['status']='truncated';break
   r.setdefault('wall_seconds',time.monotonic()-before)
   if r['status']=='running':r['status']='completed_content_review_required'
   save(folder/'result.json',r);summary.update(status='running',current_case=c['id'],wall_seconds=time.monotonic()-started);save(out/'summary.json',summary)
   save(D/'progress.json',{'job':os.environ['SLURM_JOB_ID'],'phase':'thinker_diagnostic','current_case':c['id'],'completed_conditions':len(summary['cases']),'total_conditions':len(cases),'gpus':1,'gpu_type_vram':gpu_type,'updated_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())})
   print(json.dumps({'id':c['id'],'status':r['status'],'asr':r['asr'],'tts':r['tts'],'unstructured':r.get('raw_unstructured_text')}),flush=True)
  summary['status']='completed_content_review_required'
 finally:
  if engine:engine.shutdown()
  monitor.terminate();monitor.wait(timeout=20);summary['wall_seconds']=time.monotonic()-started;save(out/'summary.json',summary)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--preflight',action='store_true');asyncio.run(run(p.parse_args()))
