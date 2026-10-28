"""Matched short requests and independent native replays of nested P01 suffixes."""
import argparse,base64,copy,hashlib,io,json,math,os,time,wave
from pathlib import Path
import librosa,numpy as np,requests,soundfile as sf,torch
from run_s1_listening_native import PROMPT,prompt_bound,save,sha
from s1_listening_rules import saved_listening_response
from s1_listening_prefix import fields_from_prefix,STOP_BEFORE_TTS
from s1_response_parser import parse_s1_with_audit
ROOT=Path(__file__).resolve().parents[1]
FRAME=11520
def normalize(text):
    import re
    return re.findall(r'[a-z0-9]+',text.lower().replace("'",'').replace('’',''))
def recognition(text,reference):
    a,b=normalize(reference),normalize(text);previous=list(range(len(b)+1))
    for i,x in enumerate(a,1):
        current=[i]
        for j,y in enumerate(b,1):current.append(min(current[-1]+1,previous[j]+1,previous[j-1]+(x!=y)))
        previous=current
    wer=previous[-1]/max(1,len(a));terms=set(b)
    keys=all(w in terms for w in ['assistant','shared','folder','conceptual','design'])
    return {'WER':wer,'key_terms_present':keys,'recognized':wer<=.25 and keys,'recognized_text':text}
def user_packet(pcm):
    b=io.BytesIO()
    with wave.open(b,'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(24000);f.writeframes(pcm)
    return {'role':'user','content':[{'type':'text','text':"{'audio_input': '"},{'type':'input_audio','input_audio':{'data':base64.b64encode(b.getvalue()).decode(),'format':'wav'}},{'type':'text','text':"', 'from_s2': ''}"}]}
def pressure_packets(protocol,level):
    row=protocol['question'];x,sr=sf.read(ROOT/row['input_audio'],dtype='float32')
    assert sha(ROOT/row['input_audio'])==row['input_sha256']
    cut=round(row['source_cutoff_seconds']*sr);x=x.copy();x[cut:]*=10**(protocol['request_level_gain_db']/20)
    x=librosa.resample(x,orig_sr=sr,target_sr=24000)
    begin=math.floor(level['source_start_seconds']/.48);end=math.ceil(row['request_end_seconds']/.48)
    samples=np.pad(x,(0,max(0,end*FRAME-len(x))))
    frames=[]
    for tick in range(begin,end):
        frame=samples[tick*FRAME:(tick+1)*FRAME].copy()
        if tick==begin:frame[:round(level['source_start_seconds']*24000)-begin*FRAME]=0
        b=io.BytesIO();sf.write(b,frame,24000,format='WAV',subtype='PCM_16')
        with wave.open(io.BytesIO(b.getvalue()),'rb') as f:frames.append((tick,f.readframes(FRAME)))
    return frames,begin,end
def short_packets():
    import sys
    sys.path.insert(0,str(ROOT/'external/duplexomni/inference_framework/realtime_serving'))
    import omni_realtime_server as native
    x,sr=sf.read(ROOT/'data/benchmarks/natural_dailytalk_outlet/outlet_request.wav',dtype='float32');assert sr==24000
    frames=[]
    for tick,i in enumerate(range(0,len(x),FRAME)):
        f=np.pad(x[i:i+FRAME],(0,max(0,FRAME-len(x[i:i+FRAME]))))
        frames.append((tick,native.apply_noise_gate((np.clip(f,-1,1)*32767).astype('<i2').tobytes(),native.SILENCE_THRESHOLD)))
    return frames
def run_case(case,config,base,processor,heartbeat):
    folder=base/case['id'];folder.mkdir(parents=True,exist_ok=True)
    if case['kind']=='pressure':frames,begin,end=pressure_packets(case['protocol'],case['level'])
    else:frames=short_packets();begin=0;end=len(frames)
    listening=len(frames);answer_frames=case.get('answer_frames',40)
    frames=frames+[(end+i,bytes(FRAME*2)) for i in range(answer_frames)]
    session='pressure_'+os.environ['SLURM_JOB_ID']+'_'+case['id']
    messages=[{'role':'system','content':PROMPT}];turns=[];audio=[];texts=[];asr=[];first_context=None
    method=case['method'];started=time.monotonic()
    result={k:v for k,v in case.items() if k not in ['protocol']}
    result.update(status='running',listening_frames=listening,answer_frames=answer_frames,S2_enabled=False,temperature=case.get('temperature',0.),max_tokens=256,history_trimmed=False,frames_completed=0)
    save(folder/'run.json',result)
    try:
        for i,(tick,pcm) in enumerate(frames):
            during=i<listening
            packet=user_packet(pcm);messages.append(packet)
            bound=prompt_bound(processor,messages)
            if bound+256+256>config['max_model_len']:raise OverflowError('Selected history exceeds context; do not trim it')
            mode='unconstrained' if method=='native' else ('native_format' if method=='decode_clear' else 'listening') if during else 'answer_start' if i==listening else 'answering'
            payload={'model':str(ROOT/'models/duplexomni'),'session_id':session,'messages':messages,'temperature':case.get('temperature',0.),'top_p':1.,'max_tokens':256,'seed':17,'listening_rule':mode}
            if method=='decode_clear' and during:payload['stop']=[STOP_BEFORE_TTS]
            if i==listening:first_context={'prompt_bound':bound,'message_hash':hashlib.sha256(json.dumps(messages,sort_keys=True,ensure_ascii=False).encode()).hexdigest(),'retained_start_seconds':begin*.48}
            t=time.monotonic();response=requests.post('http://127.0.0.1:'+str(config.get('thinker_port',21991))+'/internal/chat_turn',json=payload,timeout=600);response.raise_for_status()
            internal=torch.load(io.BytesIO(response.content),map_location='cpu',weights_only=False)
            choice=internal['response']['choices'][0];raw=choice['message']['content'];usage=internal['response']['usage']
            raw_record={'index':i,'source_frame':tick,'raw_text':raw,'finish_reason':choice['finish_reason'],'prompt_tokens':usage['prompt_tokens'],'completion_tokens':usage['completion_tokens']}
            with (folder/'raw-turns.jsonl').open('a') as f:f.write(json.dumps(raw_record,ensure_ascii=False)+'\n')
            if choice['finish_reason']=='length':raise RuntimeError('Output truncated; not a recognition failure')
            fields,audit=fields_from_prefix(raw) if method=='decode_clear' and during else parse_s1_with_audit(raw)
            saved=raw if method=='native' else saved_listening_response(fields) if during else repr(fields)
            messages.append({'role':'assistant','content':saved})
            if not during or method=='native':
                reply=requests.post('http://127.0.0.1:'+str(config.get('talker_port',21992))+'/internal/talker/turn/'+session,data=response.content,headers={'content-type':'application/octet-stream'},timeout=600);reply.raise_for_status()
                if reply.content:
                    part,sr=sf.read(io.BytesIO(reply.content),dtype='float32');assert sr==24000
                    if not during or method=='native':audio.append(part)
                texts.append(fields['tts'])
            question_start=case.get('protocol',{}).get('question',{}).get('source_cutoff_seconds',0)
            if tick*.48+.48>question_start and i<listening+4:asr.append(fields['asr'])
            turn={**raw_record,'fields':fields,'saved_text':saved,'phase':'listening' if during else 'answering','wall_seconds':time.monotonic()-t,'packet_pcm_sha256':hashlib.sha256(pcm).hexdigest(),'parser':audit}
            turns.append(turn)
            with (folder/'turns.jsonl').open('a') as f:f.write(json.dumps(turn,ensure_ascii=False)+'\n')
            if i%32==0 or not during:
                result.update(frames_completed=i+1,phase=turn['phase'],speech_text=''.join(texts),question_asr=''.join(asr),wall_seconds=time.monotonic()-started)
                save(folder/'run.json',result);save(heartbeat,{'job':os.environ['SLURM_JOB_ID'],'case':case['id'],'index':case.get('level',{}).get('index'),'frames_completed':i+1,'frames_planned':len(frames),'phase':turn['phase'],'updated_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())})
        result['status']='completed_content_review_required'
    except Exception as exc:result.update(status='capacity_failure' if isinstance(exc,OverflowError) else 'failed',error=type(exc).__name__+': '+str(exc))
    finally:
        output=np.concatenate(audio) if audio else np.zeros(1,dtype='float32');sf.write(folder/'response.wav',output,24000,subtype='PCM_16')
        result.update(speech_text=''.join(texts),question_asr=''.join(asr),frames_completed=len(turns),wall_seconds=time.monotonic()-started,answer_context=first_context,audio_sha256=sha(folder/'response.wav'),max_prompt_tokens=max((t['prompt_tokens'] for t in turns),default=0),listening_field_violations=sum(any(__import__('ast').literal_eval(t['saved_text'])[k] for k in ['tts','tts_control','system2_control']) for t in turns if method!='native' and t['phase']=='listening'),ASR_text_changes=sum(__import__('ast').literal_eval(t['saved_text'])['asr']!=t['fields']['asr'] for t in turns if method!='native' and t['phase']=='listening'))
        if case['kind']=='pressure':result['recognition']=recognition(result['question_asr'],case['protocol']['question']['question'])
        save(folder/'run.json',result)
        requests.delete('http://127.0.0.1:'+str(config.get('talker_port',21992))+'/v1/talker/session/'+session,timeout=30).raise_for_status()
    return result
def run_trial(root,out,config,trace):
    from transformers import AutoProcessor
    snapshot=ROOT/os.environ['S1_PRESSURE_SNAPSHOT']
    for name,digest in json.loads((snapshot/'hashes.json').read_text()).items():assert sha(ROOT/name)==digest,name
    base=ROOT/'exp/s1_context_pressure'/os.environ['SLURM_JOB_ID'];base.mkdir(parents=True,exist_ok=True)
    protocol=json.loads((ROOT/'research/s1_context_pressure/protocol.json').read_text());phase=config['pressure']['phase']
    processor=AutoProcessor.from_pretrained(ROOT/'models/duplexomni',trust_remote_code=True);results=[]
    if phase=='matched':
        from native_interaction import run_native_interaction
        results_native=run_native_interaction(root,out,config,trace)
        save(base/'native-reference.json',results_native)
        import shutil
        reference=base/'M0-original-native';reference.mkdir(exist_ok=True)
        shutil.copyfile(out/'natural_outlet_control/playback.wav',reference/'response.wav')
        save(reference/'run.json',{'id':'M0-original-native','kind':'short','method':'native_reference','status':results_native[0]['status'],'speech_text':results_native[0].get('generated_tts',''),'question_asr':results_native[0].get('generated_asr',''),'temperature':0.,'audio_sha256':sha(reference/'response.wav'),'scope':'Original native_interaction.py helper with the earlier DailyTalk recipe; actual played waveform.'})
        for case in [{'id':'M1-new-native','kind':'short','method':'native','answer_frames':29},{'id':'M2-constrained-greedy','kind':'short','method':'constrained','answer_frames':29},{'id':'M3-clear-greedy','kind':'short','method':'decode_clear','answer_frames':29},{'id':'M4-constrained-sampled','kind':'short','method':'constrained','temperature':.8,'answer_frames':29}]:results.append(run_case(case,config,base,processor,base/'heartbeat.json'))
        level=protocol['levels'][0]
        results.append(run_case({'id':'P01-L00','kind':'pressure','method':'constrained','level':level,'protocol':protocol,'answer_frames':29},config,base,processor,base/'heartbeat.json'))
        native_asr=results_native[0].get('generated_asr','') if results_native else ''
        native_text=results_native[0].get('generated_tts','') if results_native else ''
        # Native helper returns result fields; waveform/source inspection remains separate.
        recognition_pass=results[-1].get('recognition',{}).get('recognized',False)
        save(base/'qualification.json',{'request_only_recognized':recognition_pass,'matched_cases_completed':sum(r['status']=='completed_content_review_required' for r in results),'pressure_may_start':recognition_pass,'scope':'Request-only recognition qualifies the suffix sweep; meaningful DailyTalk speech still requires independent ASR/source review.','native_reference_asr':native_asr,'native_reference_text':native_text})
    else:
        parent=ROOT/'exp/s1_context_pressure'/str(config['pressure']['matched_job'])/'qualification.json';assert json.loads(parent.read_text())['pressure_may_start'],'Matched request-only control failed'
        for index in config['pressure']['levels']:
            level=protocol['levels'][index]
            results.append(run_case({'id':level['id'],'kind':'pressure','method':'constrained','level':level,'protocol':protocol},config,base,processor,base/'heartbeat.json'))
            save(base/'summary.json',{'status':'running','cases':results,'gpus':1,'maximum_active_gpus':1})
    save(base/'summary.json',{'status':'completed_content_review_required','cases':results,'gpus':1,'maximum_active_gpus':1})
    return [{'name':r['id'],'status':r['status'],'turns':[],'wall_seconds':r['wall_seconds']} for r in results]
def main():
    pre=argparse.ArgumentParser(add_help=False);pre.add_argument('--config',type=Path,required=True);args,_=pre.parse_known_args();config=json.loads(args.config.read_text())
    source=(ROOT/'scripts/smoke_duplexomni.py').read_text()
    source=source.replace('from native_interaction import run_native_interaction','from run_s1_context_pressure import run_trial as run_native_interaction')
    source=source.replace('str(root / "scripts/duplex_server_smoke.py")','str(root / "scripts/s1_listening_server.py")')
    source=source.replace('21991',str(config.get('thinker_port',21991))).replace('21992',str(config.get('talker_port',21992)))
    exec(compile(source,str(ROOT/'scripts/smoke_duplexomni.py')+' [context pressure]','exec'),{'__name__':'__main__','__file__':str(ROOT/'scripts/smoke_duplexomni.py')})
if __name__=='__main__':main()
