"""Generate a small, fully logged voice-conditioning/inference sweep; no answers."""
import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import random
import time
import traceback
import numpy as np
import soundfile as sf

ROOT=Path(__file__).resolve().parents[1]
PROTOCOL=ROOT/'research/ami_question_audio/protocol.json'

def write_json(path,value):path.write_text(json.dumps(value,indent=2)+'\n')

def seed_all(seed):
 import torch
 random.seed(seed);np.random.seed(seed);torch.manual_seed(seed);torch.cuda.manual_seed_all(seed)

def main():
 p=argparse.ArgumentParser();p.add_argument('--model',choices=['qwen','chatterbox','f5'],required=True);args=p.parse_args()
 import torch
 protocol=json.loads(PROTOCOL.read_text());job=os.environ['SLURM_JOB_ID'];out=ROOT/f'exp/ami_question_audio/{args.model}_{job}';out.mkdir(parents=True,exist_ok=True)
 started=time.monotonic();records=[]
 settings={
  'qwen':[dict(id='primary-icl',ref='primary',channel='headset',temperature=.9,xvec=False),dict(id='alternate-icl',ref='alternate',channel='headset',temperature=.9,xvec=False),dict(id='primary-calm',ref='primary',channel='headset',temperature=.65,xvec=False),dict(id='primary-mix',ref='primary',channel='mix',temperature=.9,xvec=False)],
  'chatterbox':[dict(id='primary-default',ref='primary',channel='headset',exaggeration=.5,cfg_weight=.5,temperature=.8),dict(id='primary-calm',ref='primary',channel='headset',exaggeration=.25,cfg_weight=.3,temperature=.7),dict(id='alternate-calm',ref='alternate',channel='headset',exaggeration=.25,cfg_weight=.3,temperature=.7),dict(id='primary-mix',ref='primary',channel='mix',exaggeration=.25,cfg_weight=.3,temperature=.7)],
  'f5':[dict(id='primary-default',ref='primary',channel='headset',nfe_step=32,cfg_strength=2,speed=1.0),dict(id='primary-calm',ref='primary',channel='headset',nfe_step=48,cfg_strength=1.5,speed=.9),dict(id='alternate-calm',ref='alternate',channel='headset',nfe_step=48,cfg_strength=1.5,speed=.9),dict(id='primary-mix',ref='primary',channel='mix',nfe_step=48,cfg_strength=1.5,speed=.9)]
 }[args.model]
 write_json(out/'config.json',dict(model=args.model,settings=settings,seed=17,gpus=1,gpu_role='all TTS components share GPU 0; no answer or duplex model',protocol_sha256=hashlib.sha256(PROTOCOL.read_bytes()).hexdigest(),job=job))
 if args.model=='chatterbox':
  from chatterbox.tts import ChatterboxTTS
  model=ChatterboxTTS.from_local(ROOT/'models/ami-chatterbox','cuda')
 elif args.model=='f5':
  from f5_tts.api import F5TTS
  model=F5TTS(ckpt_file=str(ROOT/'models/ami-f5-tts/F5TTS_v1_Base/model_1250000.safetensors'),vocab_file=str(ROOT/'models/ami-f5-tts/F5TTS_v1_Base/vocab.txt'),vocoder_local_path=str(ROOT/'models/ami-vocos'),device='cuda')
 else:
  from vllm_omni import Omni
  path=ROOT/'external/ami_tts/vllm-omni/examples/offline_inference/qwen3_tts/end2end.py'
  spec=importlib.util.spec_from_file_location('official_qwen_example',path);example=importlib.util.module_from_spec(spec);spec.loader.exec_module(example)
  model_path=str(ROOT/'models/ami-qwen3-tts')
  model=Omni(model=model_path,stage_configs_path=str(ROOT/'configs/ami_qwen_tts_stages.yaml'),stage_init_timeout=300,log_stats=False)
 load_seconds=time.monotonic()-started
 for setting in settings:
  for q in protocol['questions']:
   ref=next(r for r in protocol['references'] if r['id']==q['requester']+'-'+setting['ref']);seed_all(17)
   refpath=str(ROOT/ref[setting['channel']]);path=out/f"{q['short_id']}--{setting['id']}.wav";t=time.monotonic();torch.cuda.reset_peak_memory_stats()
   row=dict(question_id=q['id'],short_id=q['short_id'],requester=q['requester'],text=q['question'],model=args.model,job=job,setting=setting,seed=17,reference_id=ref['id'],reference_path=refpath,reference_text=ref['text'],reference_end_seconds=ref['source_end_seconds'],source_time_seconds=q['source_time_seconds'])
   try:
    if args.model=='chatterbox':
     wav=model.generate(q['question'],audio_prompt_path=refpath,**{k:setting[k] for k in ['exaggeration','cfg_weight','temperature']});y=wav.detach().cpu().numpy().flatten();sr=model.sr
    elif args.model=='f5':
     y,sr,_=model.infer(ref_file=refpath,ref_text=ref['text'],gen_text=q['question'],seed=17,**{k:setting[k] for k in ['nfe_step','cfg_strength','speed']})
    else:
     info={'task_type':['Base'],'ref_audio':[refpath],'ref_text':[ref['text']],'text':[q['question']],'language':['English'],'x_vector_only_mode':[False],'max_new_tokens':[512]}
     request={'prompt_token_ids':[0]*example._estimate_prompt_len(info,model_path),'additional_information':info}
     params=copy.deepcopy(model.default_sampling_params_list);params[0].temperature=setting['temperature'];params[0].max_tokens=512;params[0].seed=17
     pieces=[];sr=24000
     for stage_output in model.generate([request],sampling_params_list=params):
      for output in stage_output.request_output:
       mm=output.outputs[0].multimodal_output
       if mm and 'audio' in mm:
        a=mm['audio'];a=torch.cat(a,dim=-1) if isinstance(a,list) else a;pieces.append(a.float().cpu().numpy().flatten())
        value=mm.get('sr',24000);value=value[-1] if isinstance(value,list) else value;sr=int(value)
     if not pieces:raise ValueError('No final audio output')
     y=np.concatenate(pieces)
    y=np.asarray(y).flatten();assert y.size and np.isfinite(y).all()
    sf.write(path,y,sr,subtype='PCM_16');elapsed=time.monotonic()-t
    row.update(status='generated_content_review_required',path=str(path.relative_to(ROOT)),duration_seconds=len(y)/sr,sample_rate=sr,wall_seconds=elapsed,rtf=elapsed/(len(y)/sr),peak_abs=float(abs(y).max()),clipped_fraction=float(np.mean(abs(y)>=1)),peak_torch_gib=torch.cuda.max_memory_allocated()/2**30,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
   except Exception as exc:
    row.update(status='failed',error=str(exc),traceback=traceback.format_exc());print(row['traceback'],flush=True)
   records.append(row);write_json(out/'generations.json',records);print(json.dumps(row),flush=True)
 summary=dict(model=args.model,job=job,load_seconds=load_seconds,wall_seconds=time.monotonic()-started,count=len(records),generated=sum(r['status']!='failed' for r in records),gpus=1,gpu_name=torch.cuda.get_device_name(0))
 write_json(out/'summary.json',summary);print(json.dumps(summary),flush=True)
 if args.model=='qwen':model.close()
 if not summary['generated']:raise RuntimeError('All generations failed')

if __name__=='__main__':main()
