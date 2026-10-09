"""One-GPU, real Thinking-backend controls for the captured arithmetic failure.

Only private reasoning lengths/hashes are retained. Complete final content is
saved separately; no S1 or speech model is loaded in this diagnostic.
"""
import asyncio
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import time

from openai import AsyncOpenAI
import requests

ROOT=Path(__file__).resolve().parents[1]
job=os.environ['SLURM_JOB_ID'];out=ROOT/f'exp/diagnostics/s2_provider_{job}';out.mkdir(parents=True,exist_ok=True)
captured=json.loads((ROOT/'exp/inference/duplexomni/native_loop_1036322/arithmetic_s2_forced/native_summary.json').read_text())
request=captured['s2_requests'][0];system=request['input_messages'][0]
plain=[dict(system),{'role':'user','content':captured['generated_asr']}]
conditions=[('captured_context_2048',request['input_messages'],2048,1.0),
            ('captured_context_4096',request['input_messages'],4096,1.0),
            ('user_only_4096',plain,4096,1.0),
            ('user_only_top_p_095_4096',plain,4096,.95)]
cfg=json.loads((ROOT/'configs/duplexomni_s2_single_2h100.json').read_text())['system2']
command=[str(ROOT/'envs/duplexomni/bin/vllm'),'serve',str(ROOT/cfg['model']),
         '--served-model-name',cfg['served_model_name'],'--host','127.0.0.1','--port','22193',
         '--dtype','bfloat16','--tensor-parallel-size','1','--gpu-memory-utilization','.3',
         '--max-model-len','8192','--max-num-seqs','1','--max-num-batched-tokens','1024',
         '--kv-cache-memory-bytes',str(1610612736),'--reasoning-parser','deepseek_r1']
(out/'command.json').write_text(json.dumps(command,indent=2)+'\n')
summary={'job_id':job,'gpus':1,'gpu_type':'H100 SXM 80 GB','roles':'Thinking S2 only on GPU 0; S1/Talker absent',
         'scope':'Seeded provider controls, not an audio-handoff or latency qualification result.','cases':[]}
start=time.monotonic();handle=(out/'server.log').open('w')
proc=subprocess.Popen(command,cwd=ROOT,env=os.environ.copy(),stdout=handle,stderr=subprocess.STDOUT,start_new_session=True)
try:
    deadline=time.monotonic()+180
    while True:
        if proc.poll() is not None:raise RuntimeError(f'S2 server exited {proc.returncode}')
        try:
            if requests.get('http://127.0.0.1:22193/health',timeout=2).ok:break
        except requests.RequestException:pass
        if time.monotonic()>deadline:raise TimeoutError('S2 provider startup')
        time.sleep(1)
    summary['startup_seconds']=time.monotonic()-start
    async def run():
        client=AsyncOpenAI(base_url='http://127.0.0.1:22193/v1',api_key='EMPTY');private_prefixes=[]
        try:
            for name,messages,budget,top_p in conditions:
                before=time.monotonic();thought='';final='';usage=None;finish=None
                stream=await client.chat.completions.create(model=cfg['served_model_name'],messages=messages,
                    stream=True,stream_options={'include_usage':True},temperature=.6,top_p=top_p,seed=17,
                    max_tokens=budget,extra_body={'top_k':20})
                try:
                    async for chunk in stream:
                        if chunk.usage:usage=chunk.usage.model_dump()
                        if not chunk.choices:continue
                        delta=chunk.choices[0].delta.model_dump()
                        thought+=delta.get('reasoning') or delta.get('reasoning_content') or ''
                        final+=chunk.choices[0].delta.content or ''
                        finish=chunk.choices[0].finish_reason or finish
                finally:await stream.close()
                row={'name':name,'max_tokens':budget,'top_p':top_p,'temperature':.6,'top_k':20,'seed':17,
                     'input_messages':messages,'wall_seconds':time.monotonic()-before,
                     'reasoning_characters':len(thought),'reasoning_sha256':hashlib.sha256(thought.encode()).hexdigest(),
                     'final_content':final,'complete_guidance':re.findall(r'【([^【】]+)】',final),'finish_reason':finish,'usage':usage,
                     'correct_391_in_final':bool(re.search(r'\b391\b|three hundred (and )?ninety.one',final.lower()))}
                if name=='captured_context_2048':private_prefixes.append(thought)
                if name=='captured_context_4096':row['same_reasoning_prefix_as_2048']=thought.startswith(private_prefixes[0])
                # Private thought is discarded after the hash/length/prefix check.
                summary['cases'].append(row);print(json.dumps(row,ensure_ascii=False),flush=True)
                (out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
        finally:await client.close()
    asyncio.run(run());summary['status']='completed_provider_controls_review_required'
except BaseException as exc:
    summary.update(status='failed',error=f'{type(exc).__name__}: {exc}');raise
finally:
    summary['wall_seconds']=time.monotonic()-start
    (out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    if proc.poll() is None:
        os.killpg(proc.pid,signal.SIGTERM)
        try:proc.wait(timeout=30)
        except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL)
    handle.close()
