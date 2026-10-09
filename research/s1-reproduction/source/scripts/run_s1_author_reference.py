"""Run the authors' actual OfflineSimulator.run with S2 dispatch disabled.

The source loop, sampling, history, websocket listener and audio stitching are
retained. An optional prompt override is explicitly recorded. Also save a replay
without the reference renderer's small-jitter corrections for independent audit.
"""
from __future__ import annotations
import asyncio
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from types import SimpleNamespace

import numpy as np
from openai import AsyncOpenAI
import requests
import soundfile as sf
from s1_response_parser import parse_s1_with_audit

def run_s1_author_reference(root, out, config, trace):
    source = root/'external/duplexomni/inference_framework/realtime_serving'
    sys.path.insert(0,str(source))
    import simulate_v8 as author
    author.S1_OMNI_BASE_URL = 'http://127.0.0.1:21990/v1'
    author.S1_AUDIO_WS_BASE = 'ws://127.0.0.1:21990/v1/audio/stream'
    author.S1_CLEAR_SESSION_BASE = 'http://127.0.0.1:21990/v1/session'
    author.S1_HEALTH_URL = 'http://127.0.0.1:21990/health'
    author.S1_MODEL_NAME = str(root/'models/duplexomni')
    env = os.environ.copy()
    env.update({'ORCH_PORT':'21990','ORCH_HOST':'127.0.0.1',
        'THINKER_INTERNAL_URL':'http://127.0.0.1:21991/internal/chat_turn',
        'TALKER_INTERNAL_URL_BASE':'http://127.0.0.1:21992/internal/talker/turn',
        'TALKER_DELETE_URL_BASE':'http://127.0.0.1:21992/v1/talker/session',
        'PYTHONPATH':str(source/'serving_core')+os.pathsep+env.get('PYTHONPATH','')})
    handle = (out/'orchestrator.log').open('w')
    process = subprocess.Popen([str(root/'envs/duplexomni/bin/python'),'-u',str(source/'serving_core/server_orchestrator.py')],
        cwd=root,env=env,stdout=handle,stderr=subprocess.STDOUT,start_new_session=True)
    results=[]
    try:
        deadline=time.monotonic()+90
        while True:
            assert process.poll() is None, 'Author orchestrator exited'
            try:
                if requests.get(author.S1_HEALTH_URL,timeout=2).ok:break
            except requests.RequestException:pass
            if time.monotonic()>deadline:raise TimeoutError('Orchestrator startup')
            time.sleep(.5)

        async def one_case(case):
            directory=out/case['name']; directory.mkdir(exist_ok=True)
            path=root/case['audio']; x,sr=sf.read(path,dtype='int16')
            assert sr==24000 and x.ndim==1
            steps=case.get('steps',40); assert len(x)<=steps*11520
            x=np.pad(x,(0,steps*11520-len(x))); sf.write(directory/'input.wav',x,sr,subtype='PCM_16')
            record={'name':case['name'],'gpus':config['gpus'],'gpu_type':config.get('gpu_type'),
                's2_loaded':False,'s2_requests':[],'blocked_s2_controls':[],'turns':[],
                'audio':case['audio'],'input_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                'source_user_requests':0 if case.get('is_warmup') else 1,'input_speech_file_seconds':sf.info(path).duration,
                'reference_source':'inference_framework/realtime_serving/simulate_v8.py',
                'reference_source_sha256':hashlib.sha256((source/'simulate_v8.py').read_bytes()).hexdigest(),
                'reference_commit':'33bfba1a821b09c5aa66790944f9098584979d34',
                'prompt_override':case.get('system_prompt'),'history':'raw model replies',
                'temperature':case.get('temperature',.3),'max_tokens':999,
                'scope':'Authors simulation loop and orchestrator; S2 disabled, CPU-recorded websocket audio. No physical microphone or speaker.'}
            class NoS2:
                is_thinking=False; thinking_task=None; client=None
                def add_context(self,*args):pass
                def get_new_commands(self,*args):return ''
                async def trigger_think(self):record['blocked_s2_controls'].append({'control':'[THINK]','at':time.monotonic()-begin})
                async def trigger_wait(self):record['blocked_s2_controls'].append({'control':'[WAIT]','at':time.monotonic()-begin})
            # Replace before construction, so no S2 API client is ever created.
            author.System2Agent=NoS2
            sim=author.OfflineSimulator(str(directory/'input.wav'))
            client=sim.s1_client
            async def create(**kwargs):
                if case.get('system_prompt'):
                    kwargs['messages'][0]['content']=case['system_prompt']
                if 'temperature' in case:
                    kwargs['temperature']=case['temperature']
                before=time.monotonic()
                response=await client.chat.completions.create(**kwargs)
                raw=next(c.message.content for c in response.choices if c.message.content)
                fields,audit=parse_s1_with_audit(raw)
                record['turns'].append({'chunk':len(record['turns']),'fields':fields,'raw_text':raw,
                    'parser':audit,'start_seconds':before-begin,'end_seconds':time.monotonic()-begin,
                    'usage':response.usage.model_dump() if response.usage else None,
                    'finish_reason':response.choices[0].finish_reason})
                (directory/'native_summary.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
                return response
            sim.s1_client=SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
            author.OUTPUT_FILENAME=str(directory/'reference_mix.wav')
            begin=time.monotonic()
            try:
                await sim.run()
            finally:
                await client.close()
            size=max(len(x),max((round(at*sr)+len(pcm)//2 for at,pcm in sim.agent_audio_events),default=0))
            played=np.zeros(size,dtype='int32'); events=[]
            for i,(at,pcm) in enumerate(sim.agent_audio_events):
                wave=np.frombuffer(pcm,dtype='<i2'); start=round(at*sr)
                played[start:start+len(wave)]+=wave.astype('int32')
                sf.write(directory/f'packet_{i:03}.wav',wave,sr,subtype='PCM_16')
                events.append({'index':i,'arrival_seconds':at,'duration_seconds':len(wave)/sr,
                    'rms':float(np.sqrt(np.mean((wave.astype('float32')/32768)**2)))})
            played=np.clip(played,-32768,32767).astype('int16')
            mix=played.astype('int32'); mix[:len(x)]+=x.astype('int32')
            sf.write(directory/'played.wav',played,sr,subtype='PCM_16')
            sf.write(directory/'actual_mix.wav',np.clip(mix,-32768,32767).astype('int16'),sr,subtype='PCM_16')
            record.update(status='completed_content_review_required',wall_seconds=time.monotonic()-begin,
                tts_joined=''.join(t['fields'].get('tts','') for t in record['turns']),
                asr_joined=''.join(t['fields'].get('asr','') for t in record['turns']),audio_events=events)
            assert len(record['turns'])==steps
            assert all(t['finish_reason']!='length' for t in record['turns'])
            (directory/'native_summary.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
            print(json.dumps({'case_complete':case['name'],'tts':record['tts_joined'],'asr':record['asr_joined']},ensure_ascii=False),flush=True)
            return record
        async def all_cases():
            for case in config['author_reference']['cases']:results.append(await one_case(case))
        asyncio.run(all_cases())
        return results
    finally:
        if process.poll() is None:os.killpg(process.pid,signal.SIGTERM)
        try:process.wait(timeout=20)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid,signal.SIGKILL);process.wait(timeout=10)
        handle.close()
