"""Replay the exact captured native prompt in a fresh Thinker; no speech/S2."""
import argparse,copy,hashlib,io,json,os,signal,subprocess,time
from pathlib import Path
import requests,torch
from run_s1_context_pressure import pressure_packets,user_packet,PROMPT,FRAME
from s1_response_parser import parse_s1_with_audit
ROOT=Path(__file__).resolve().parents[1]
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
def digest(messages):return hashlib.sha256(json.dumps(messages,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
def reconstruct():
    protocol=json.loads((ROOT/'research/s1_context_pressure/protocol.json').read_text());level=protocol['levels'][40]
    base=ROOT/'exp/s1_context_pressure/1355163/P01-L40';record=json.loads((base/'run.json').read_text());turns=[json.loads(s) for s in (base/'turns.jsonl').read_text().splitlines()]
    frames,begin,end=pressure_packets(protocol,level);messages=[{'role':'system','content':PROMPT}]
    for i,(tick,pcm) in enumerate(frames):
        assert turns[i]['source_frame']==tick and turns[i]['packet_pcm_sha256']==hashlib.sha256(pcm).hexdigest()
        messages.extend([user_packet(pcm),{'role':'assistant','content':turns[i]['saved_text']}])
    messages.append(user_packet(bytes(FRAME*2)))
    assert digest(messages)==record['answer_context']['message_hash'],'Captured native prompt is not identical'
    return messages,turns[len(frames):],record
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--preflight',action='store_true');a=parser.parse_args()
    original,recorded,source=reconstruct()
    if a.preflight:
        result={'status':'pass','gpus':0,'captured_message_hash_matches':True,'messages':len(original),'audio_packets':sum(isinstance(m['content'],list) for m in original),'retains_all_native_audio_response_turns':True,'source_job':'1355163','scope':'A replay of native packet history, not a single-WAV shortcut.'}
        save(ROOT/'research/s1_context_pressure/frozen-replay-preflight.json',result);print(json.dumps(result));return
    job=os.environ['SLURM_JOB_ID'];out=ROOT/'exp/s1_context_replay'/job;out.mkdir(parents=True,exist_ok=True)
    snapshot=ROOT/os.environ['S1_FROZEN_SNAPSHOT']
    for name,value in json.loads((snapshot/'hashes.json').read_text()).items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==value,name
    port=33000+int(job)%1000
    env=os.environ.copy();core=ROOT/'external/duplexomni/inference_framework/realtime_serving/serving_core'
    env.update(PYTHONPATH=str(core)+os.pathsep+str(ROOT/'scripts/runtime_shims')+os.pathsep+str(ROOT/'scripts'),VLLM_ROOT=str(ROOT/'envs/duplexomni/lib/python3.11/site-packages'),THINKER_MODEL=str(ROOT/'models/duplexomni'),THINKER_HOST='127.0.0.1',THINKER_PORT=str(port),THINKER_TP='1',THINKER_MAX_MODEL_LEN='49152',THINKER_GPU_MEM_UTIL='.8',DUPLEX_SMOKE_AUDIO_LIMIT='1250',DUPLEX_SMOKE_MAX_MODEL_LEN='49152',DUPLEX_SMOKE_MAX_BATCHED_TOKENS='20480',DUPLEX_SMOKE_THINKER_KV_CACHE_BYTES=str(6*1024**3),DUPLEX_THINKER_CUDA_GRAPHS='1',THINKER_HIDDEN_STORE_DIR='0')
    started=time.monotonic();results=[]
    with (out/'thinker.log').open('w') as log:
        process=subprocess.Popen([str(ROOT/'envs/duplexomni/bin/python'),'-u','scripts/s1_listening_server.py','thinker'],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        try:
            while True:
                assert process.poll() is None,'Thinker startup failed'
                try:
                    if requests.get(f'http://127.0.0.1:{port}/health',timeout=2).ok:break
                except requests.RequestException:pass
                if time.monotonic()-started>300:raise TimeoutError('Thinker startup')
                time.sleep(1)
            for name in ['unchanged_fresh_1','unchanged_fresh_2','earlier_ASR_cleared']:
                messages=copy.deepcopy(original)
                if name=='earlier_ASR_cleared':
                    for m in messages:
                        if m['role']=='assistant':
                            fields=parse_s1_with_audit(m['content'])[0];fields['asr']='';m['content']=repr(fields)
                initial_hash=digest(messages);turns=[]
                for tick in range(16):
                    if tick:messages.append(user_packet(bytes(FRAME*2)))
                    response=requests.post(f'http://127.0.0.1:{port}/internal/chat_turn',json={'model':str(ROOT/'models/duplexomni'),'session_id':'frozen_'+job+'_'+name,'messages':messages,'temperature':0.,'top_p':1.,'max_tokens':256,'seed':17,'listening_rule':'answer_start' if tick==0 else 'answering'},timeout=600);response.raise_for_status()
                    internal=torch.load(io.BytesIO(response.content),map_location='cpu',weights_only=False);choice=internal['response']['choices'][0];assert choice['finish_reason']!='length'
                    fields,audit=parse_s1_with_audit(choice['message']['content']);turns.append({'index':tick,'fields':fields,'raw_text':choice['message']['content'],'usage':internal['response']['usage']});messages.append({'role':'assistant','content':repr(fields)})
                row={'condition':name,'initial_message_hash':initial_hash,'native_text':''.join(t['fields']['tts'] for t in turns),'ASR':''.join(t['fields']['asr'] for t in turns),'identical_recorded_field_turns':sum(t['fields']==r['fields'] for t,r in zip(turns,recorded[:16])),'turns':turns}
                results.append(row);save(out/'summary.json',{'status':'running','gpus':1,'gpu_type_vram':'H100 SXM 80 GB','roles':{'0':'Thinker only; no Talker/MTP/Code2Wav/ASR/S2'},'cases':results});print(json.dumps({k:v for k,v in row.items() if k!='turns'}),flush=True)
        finally:
            if process.poll() is None:os.killpg(process.pid,signal.SIGTERM)
            try:process.wait(timeout=30)
            except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait(timeout=10)
    save(out/'summary.json',{'status':'completed_text_diagnostic_not_spoken_accuracy','gpus':1,'gpu_type_vram':'H100 SXM 80 GB','roles':{'0':'Thinker only; no Talker/MTP/Code2Wav/ASR/S2'},'maximum_active_gpus':1,'source_native_prompt_hash':source['answer_context']['message_hash'],'cases':results,'wall_seconds':time.monotonic()-started,'scope':'Fresh sessions replay the exact native prompt, then 16 silence ticks; altered-ASR input is a diagnostic, not an S1 baseline or extra pressure level.'})
if __name__=='__main__':main()
