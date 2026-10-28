"""Compare native decode-and-clear with constrained listening; no oracle content."""
import argparse,base64,copy,hashlib,io,json,math,os,time
from pathlib import Path
import librosa, numpy as np, requests, soundfile as sf, torch
from s1_response_parser import parse_s1_with_audit
from s1_listening_rules import saved_listening_response
from s1_listening_prefix import fields_from_prefix,STOP_BEFORE_TTS

ROOT=Path(__file__).resolve().parents[1]
PROMPT='你是有用的助手\n你的助手风格是：耐心。\n你的开场方式要求：短句清晰。'
ANSWER_CUE=''

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,d):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n');tmp.replace(p)
def user(wave):
    b=io.BytesIO();sf.write(b,wave,24000,format='WAV',subtype='PCM_16')
    return {'role':'user','content':[{'type':'text','text':"{'audio_input': '"},{'type':'input_audio','input_audio':{'data':base64.b64encode(b.getvalue()).decode(),'format':'wav'}},{'type':'text','text':"', 'from_s2': ''}"}]}

def prompt_bound(processor,messages):
    normalized=[];audio_items=0
    for message in messages:
        content=message['content']
        if isinstance(content,list):
            audio_items+=sum(p['type']=='input_audio' for p in content)
            content=''.join(p['text'] if p['type']=='text' else '<|audio_start|><|audio_pad|><|audio_end|>' for p in content)
        normalized.append({'role':message['role'],'content':content})
    shell=processor.apply_chat_template(normalized,tokenize=False,add_generation_prompt=True)
    return len(processor.tokenizer.encode(shell,add_special_tokens=False))+7*audio_items

def run_case(row,method,out,processor,config):
    folder=out/(row['id']+'-'+method);folder.mkdir(parents=True,exist_ok=True)
    source=ROOT/row['input_audio'];assert sha(source)==row['input_sha256']
    x,sr=sf.read(source,dtype='float32')
    # The established level control changes the request only; no future speech.
    cut=round(row['source_cutoff_seconds']*sr);q=x[cut:]
    gain=min(.05/max(float(np.sqrt(np.mean(q.astype('float64')**2))),1e-9),.95/max(float(abs(q).max()),1e-9))
    if row['id'].startswith('sky'):gain=1.
    x=x.copy();x[cut:]*=gain
    x=librosa.resample(x,orig_sr=sr,target_sr=24000)
    width=11520;end=math.ceil(row['request_end_seconds']/.48)
    frames=[np.pad(x[i*width:(i+1)*width],(0,max(0,width-len(x[i*width:(i+1)*width])))) for i in range(end)]
    frames += [np.zeros(width,dtype='float32')]*config['listening_trial']['answer_frames']
    session='listen_'+os.environ['SLURM_JOB_ID']+'_'+row['id']+'_'+method
    messages=[{'role':'system','content':PROMPT}];indices=[];turns=[];speech=[];question_asr=[];prefix_asr=[]
    start=time.monotonic();trimmed=0;max_prompt=0;max_history=0;removed=0;answer_text=[];first_answer_context=None
    result={'case':row['id'],'method':method,'question_id':row['question_id'],'question':row['question'],'status':'running',
            'gpus':1,'gpu_type_vram':torch.cuda.get_device_name(0)+' / '+format(torch.cuda.get_device_properties(0).total_memory/2**30,'.1f')+' GiB' if torch.cuda.is_available() else 'CPU fixture','S2_enabled':False,'input_sha256':row['input_sha256'],
            'input_level_gain_db':20*math.log10(gain),'request_end_seconds':row['request_end_seconds'],
            'answer_enabled_at_seconds':end*.48,'listening_frames':end,'answer_frames':config['listening_trial']['answer_frames'],
            'history_policy':'Retain all native pairs while they fit, up to 1250 pairs (600 s); discard 200 oldest pairs (96 s) per overflow event to preserve reusable vLLM prefixes between events. No summary or reference text.',
            'system_prompt':PROMPT,'answer_trigger':'Require a letter or digit in the first post-question tts fragment only; subsequent tts is free, no answer words supplied.','answer_trigger_text':ANSWER_CUE,'frames_completed':0,'trimmed_frames':0,'speech_text':'','question_asr':''}
    save(folder/'run.json',result)
    try:
        for tick,wave in enumerate(frames):
            listening=tick<end
            messages.append(user(wave));indices.append(tick)
            if tick==end and ANSWER_CUE:
                messages[-1]['content'].append({'type':'text','text':'\n'+ANSWER_CUE})
            # Both methods use the same compact response serialization and context rule.
            while True:
                # The real 480 ms processor expansion is 7 tokens/audio; verify against returned usage.
                bound=prompt_bound(processor,messages)
                if len(indices)<=1250 and bound+999+256<65536:break
                assert len(indices)>1
                drop=min(200,len(indices)-1)
                del messages[1:1+drop*2];del indices[:drop];trimmed+=drop
            if not listening and first_answer_context is None:
                first_answer_context={'oldest_retained_seconds':indices[0]*.48,'retained_audio_pairs':len(indices),'conservative_prompt_bound':bound,'trimmed_frames':trimmed,'messages_sha256':hashlib.sha256(json.dumps(messages,ensure_ascii=False,sort_keys=True).encode()).hexdigest()}
            mode=('native_format' if method=='decode_clear' else 'listening') if listening else 'answer_start' if tick==end and config['listening_trial'].get('force_answer_start',True) else 'answering'
            payload={'model':str(ROOT/'models/duplexomni'),'session_id':session,'messages':messages,'temperature':.8,'top_p':1.,'max_tokens':999,'seed':17,'listening_rule':mode}
            if listening and method=='decode_clear':payload['stop']=[STOP_BEFORE_TTS]
            before=time.monotonic()
            response=requests.post('http://127.0.0.1:'+str(config.get('thinker_port',21991))+'/internal/chat_turn',json=payload,timeout=1200);response.raise_for_status()
            internal=torch.load(io.BytesIO(response.content),map_location='cpu',weights_only=False)
            choice=internal['response']['choices'][0];raw=choice['message']['content']
            with (folder/'raw-turns.jsonl').open('a') as f:f.write(json.dumps({'frame':tick,'raw_text':raw,'finish_reason':choice['finish_reason']},ensure_ascii=False)+'\n')
            fields,parser=fields_from_prefix(raw) if listening and method=='decode_clear' else parse_s1_with_audit(raw)
            actual=internal['response']['usage']['prompt_tokens'];assert actual<=bound+256,(actual,bound)
            assert choice['finish_reason']!='length','Output limit reached; do not invent a complete response'
            stored=saved_listening_response(fields) if listening else repr(fields)
            if method=='constrained' and listening:
                assert not any(fields[k] for k in ['tts','tts_control','system2_control'])
            if not listening:assert fields['system2_control']=='','S2 is disabled by the answer grammar'
            removed+=int(listening and any(fields[k] for k in ['tts','tts_control','system2_control']))
            messages.append({'role':'assistant','content':stored})
            if tick*.48>=row.get('source_cutoff_seconds',0) and listening:question_asr.append(fields['asr'])
            elif listening:prefix_asr.append({'start_seconds':tick*.48,'text':fields['asr']})
            turn={'frame':tick,'start_seconds':tick*.48,'phase':'listening' if listening else 'answering','raw_text':raw,'saved_text':stored,'fields':fields,'finish_reason':choice['finish_reason'],'prompt_tokens':actual,'completion_tokens':internal['response']['usage']['completion_tokens'],'wall_seconds':time.monotonic()-before,'retained_start_seconds':indices[0]*.48,'parser':parser}
            if not listening:
                answer_text.append(fields['tts'])
                reply=requests.post('http://127.0.0.1:'+str(config.get('talker_port',21992))+'/internal/talker/turn/'+session,data=response.content,headers={'content-type':'application/octet-stream'},timeout=1200);reply.raise_for_status()
                if reply.content:
                    path=folder/f'answer-{tick-end:03d}.wav';path.write_bytes(reply.content)
                    part,rate=sf.read(path,dtype='float32');assert rate==24000
                    speech.append(part)
            with (folder/'turns.jsonl').open('a') as f:f.write(json.dumps(turn,ensure_ascii=False)+'\n')
            turns.append(turn);max_prompt=max(max_prompt,actual);max_history=max(max_history,len(indices))
            if tick%32==0 or not listening:
                result.update(frames_completed=tick+1,phase=turn['phase'],trimmed_frames=trimmed,removed_action_frames=removed,max_prompt_tokens=max_prompt,max_retained_frames=max_history,wall_seconds=time.monotonic()-start,speech_text=''.join(answer_text),question_asr=''.join(question_asr),answer_context=first_answer_context)
                save(folder/'run.json',result)
                save(ROOT/('research/s1_listening/progress-'+method+'.json'),{'status':'running','job':os.environ['SLURM_JOB_ID'],'current_case':row['id'],'method':method,'phase':turn['phase'],'frames_completed':tick+1,'frames_planned':len(frames),'updated_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'active_gpus':1})
                print(json.dumps({'case':row['id'],'method':method,'frame':tick+1,'total':len(frames),'phase':turn['phase'],'tts':fields['tts'] if not listening else ''}),flush=True)
        result['status']='completed_content_review_required'
    except Exception as exc:
        result.update(status='failed',error=type(exc).__name__+': '+str(exc));raise
    finally:
        # These are actually synthesized sequential response packets, not model text.
        output=np.concatenate(speech) if speech else np.zeros(1,dtype='float32')
        sf.write(folder/'response.wav',output,24000,subtype='PCM_16')
        result.update(wall_seconds=time.monotonic()-start,frames_completed=len(turns),trimmed_frames=trimmed,removed_action_frames=removed,max_prompt_tokens=max_prompt,max_retained_frames=max_history,speech_text=''.join(answer_text),question_asr=''.join(question_asr),answer_context=first_answer_context,audio_sha256=sha(folder/'response.wav'),response_seconds=len(output)/24000)
        save(folder/'prefix-asr.json',prefix_asr);save(folder/'run.json',result)
        requests.delete('http://127.0.0.1:'+str(config.get('talker_port',21992))+'/v1/talker/session/'+session,timeout=30).raise_for_status()
    return result

def run_trial(root,out,config,trace):
    from transformers import AutoProcessor
    snap=ROOT/os.environ['S1_LISTENING_SNAPSHOT']
    for name,h in json.loads((snap/'hashes.json').read_text()).items():assert sha(ROOT/name)==h,name
    target=ROOT/'exp/s1_listening'/os.environ['SLURM_JOB_ID'];target.mkdir(parents=True,exist_ok=True)
    processor=AutoProcessor.from_pretrained(ROOT/'models/duplexomni',trust_remote_code=True)
    rows=json.loads((ROOT/'research/s1_meeting_pilot/inputs.json').read_text())['cases']
    if config['listening_trial'].get('control_only'):rows=[]
    elif config['listening_trial'].get('cases'):rows=[row for row in rows if row['id'] in config['listening_trial']['cases']]
    sky=ROOT/'data/benchmarks/authored_controls/sky_question.wav';wave,sr=sf.read(sky)
    control={'id':'sky','question_id':'control:sky','question':'Short factual control','input_audio':str(sky.relative_to(ROOT)),'input_sha256':sha(sky),'source_cutoff_seconds':0.,'request_end_seconds':len(wave)/sr}
    results=[]
    for row in [control]+rows:
        for method in config['listening_trial'].get('methods',['decode_clear','constrained']):
            try:result=run_case(row,method,target,processor,config)
            except Exception:
                result=json.loads((target/(row['id']+'-'+method)/'run.json').read_text())
            results.append(result)
            save(target/'summary.json',{'status':'running','gpus':1,'maximum_active_gpus':1,'S2_enabled':False,'cases':results})
        if row['id']=='sky':
            checks=[]
            for r in results:
                recognized=r.get('question_asr','').lower()
                wave,rate=sf.read(target/('sky-'+r['method'])/'response.wav',dtype='float32')
                checks.append({'method':r['method'],'recognized_request':recognized,'speech_text':r.get('speech_text',''),'ASR_pass':('color' in recognized or 'colour' in recognized) and 'sky' in recognized,'speech_text_pass':'blue' in r.get('speech_text','').lower(),'nonquiet_audio':float(abs(wave).max())>.0001,'status':r['status']})
            qualified=all(c['ASR_pass'] and c['speech_text_pass'] and c['nonquiet_audio'] and c['status']=='completed_content_review_required' for c in checks)
            save(target/'runtime-qualification.json',{'qualified':qualified,'checks':checks,'independent_speech_transcription':'After all S1 exits; no factual speech pass claimed yet'})
            if not qualified:raise RuntimeError('Short native-prompt controls did not qualify; no long replays')
            if config['listening_trial'].get('activation_comparison'):
                alternate=copy.deepcopy(config);alternate['listening_trial']['force_answer_start']=False
                allow_row={**control,'id':'sky_allow_empty'}
                for method in config['listening_trial'].get('methods',['decode_clear','constrained']):
                    results.append(run_case(allow_row,method,target,processor,alternate))
                save(target/'summary.json',{'status':'running','gpus':1,'maximum_active_gpus':1,'S2_enabled':False,'cases':results})
    save(target/'summary.json',{'status':'completed_content_review_required','gpus':1,'maximum_active_gpus':1,'S2_enabled':False,'cases':results})
    return [{'name':r['case']+'-'+r['method'],'status':r['status'],'turns':[],'wall_seconds':r['wall_seconds']} for r in results]

def main():
    pre=argparse.ArgumentParser(add_help=False);pre.add_argument('--config',type=Path,required=True);args,_=pre.parse_known_args()
    cfg=json.loads(args.config.read_text())
    source=(ROOT/'scripts/smoke_duplexomni.py').read_text()
    source=source.replace('from native_interaction import run_native_interaction','from run_s1_listening_native import run_trial as run_native_interaction')
    source=source.replace('str(root / "scripts/duplex_server_smoke.py")','str(root / "scripts/s1_listening_server.py")')
    source=source.replace('21991',str(cfg.get('thinker_port',21991))).replace('21992',str(cfg.get('talker_port',21992)))
    exec(compile(source,str(ROOT/'scripts/smoke_duplexomni.py')+' [controlled listening]','exec'),{'__name__':'__main__','__file__':str(ROOT/'scripts/smoke_duplexomni.py')})

if __name__=='__main__':main()
