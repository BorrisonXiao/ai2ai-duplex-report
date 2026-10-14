"""Audited S2 experiment extension of the frozen, working S1 harness.

The original S1 files remain unchanged. Exact, checked substitutions add an
explicit GPU-role map and a recorded forced-THINK history intervention. The
complete resulting sources and diffs are saved before each real launch.
"""
import difflib
import hashlib
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FROZEN = ROOT/'.migration/updates/2026-10-08-natural-interruption/launch-04/prepared.json'


def open_private_reasoning_trace(root, case_name, request_index, model):
    """Open a mode-restricted local file for raw streamed S2 reasoning."""
    job_id = os.environ.get('SLURM_JOB_ID', f'local-{os.getpid()}')
    private_root = Path(root)/'exp'/'private_s2_reasoning'
    private_root.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(private_root, 0o700)
    run_dir = private_root/job_id
    run_dir.mkdir(exist_ok=True, mode=0o700)
    os.chmod(run_dir, 0o700)
    case_dir = run_dir/case_name
    case_dir.mkdir(exist_ok=True, mode=0o700)
    os.chmod(case_dir, 0o700)
    path = case_dir/f'request-{request_index:02d}.jsonl'
    fd = os.open(path, os.O_WRONLY|os.O_CREAT|os.O_EXCL, 0o600)
    os.fchmod(fd, 0o600)
    stream = os.fdopen(fd, 'w', encoding='utf-8')
    stream.write(json.dumps({'type':'request','job_id':job_id,'case':case_name,
        'request_index':request_index,'model':model},ensure_ascii=False)+'\n')
    stream.flush()
    return {'path':path,'stream':stream,'chunk_index':0}


def write_private_reasoning_chunk(trace, text, monotonic_seconds):
    """Persist a raw reasoning delta without echoing it to logs or stdout."""
    if trace is None:
        return
    trace['stream'].write(json.dumps({'type':'reasoning_chunk','index':trace['chunk_index'],
        'monotonic_seconds':monotonic_seconds,'text':text},ensure_ascii=False)+'\n')
    trace['stream'].flush()
    trace['chunk_index'] += 1


def close_private_reasoning_trace(trace, status, character_count, finish_reason):
    if trace is None:
        return
    stream = trace['stream']
    stream.write(json.dumps({'type':'end','stream_status':status,
        'finish_reason':finish_reason,'reasoning_characters':character_count,
        'reasoning_chunks':trace['chunk_index'],'complete':status in {
            'completed_with_guidance','completed_without_guidance','no_guidance_token_limit'}},ensure_ascii=False)+'\n')
    stream.flush()
    os.fsync(stream.fileno())
    stream.close()


def forced_history(raw, fields, effective, policy, index, final_input, serialization):
    """Change only the forced THINK value; retain the original model record."""
    default = raw if serialization == 'raw' else json.dumps(effective,ensure_ascii=False)
    if policy != 'force_once_after_input' or index != final_input or serialization != 'raw':
        return default,None
    if '[THINK]' in fields.get('system2_control',''):
        return raw,None
    pattern = re.compile(r'''(["']system2_control["']\s*:\s*)("(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')''')
    matches = list(pattern.finditer(raw))
    if len(matches)!=1:
        raise ValueError('Cannot safely insert the forced THINK history cue')
    match = matches[0];quote=match.group(2)[0]
    modified = raw[:match.start(2)]+quote+'[THINK]'+quote+raw[match.end(2):]
    parsed,_ = parse_s1_with_audit(modified)
    assert parsed == fields | {'system2_control':'[THINK]'}
    return modified,{'type':'forced_THINK_history_value','model_control':fields.get('system2_control',''),
                     'history_control':'[THINK]','original_model_response':raw,'history_response':modified,
                     'scope':'Explicit experimental intervention, not a model-produced delegation.'}


def calibration_speech_gate(results,out):
    observations=[]
    for case in results[:2]:
        audible=any(p['requested_speech'] and p['rms']>1e-3 for p in case['playback_packets'])
        observations.append({'case':case['name'],'audible':audible,'blue_in_generated_tts':'blue' in case['generated_tts'].lower()})
    gate={'qualified':all(c['audible'] and c['blue_in_generated_tts'] for c in observations),
          'status':'known_sky_calibration_spoken' if all(c['audible'] and c['blue_in_generated_tts'] for c in observations) else 'known_s1_calibration_response_missing',
          'observations':observations,'scope':'Known single-question calibration; independent PCM transcription still required.'}
    (out/'initial_response_gate.json').write_text(json.dumps(gate,indent=2)+'\n')
    return gate['qualified']


def s2_messages(history,turns,policy):
    """A declared context control for one-request experiments, using real ASR."""
    if policy=='native':return [dict(m) for m in history]
    if policy!='user_only':raise ValueError('Unknown S2 context policy: '+policy)
    user=''.join(t['fields'].get('asr','') for t in turns).strip()
    if not user:raise ValueError('S2 user-only context requires actual S1 ASR')
    return [dict(history[0]),{'role':'user','content':user}]


def replace_once(source,old,new):
    assert source.count(old)==1,old
    return source.replace(old,new,1)


def sources():
    frozen=json.loads(FROZEN.read_text())['files']
    original={name:(ROOT/name).read_text() for name in ['scripts/native_interaction.py','scripts/smoke_duplexomni.py']}
    for name in original:
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==frozen[name],name
    native=original['scripts/native_interaction.py']
    native=replace_once(native,
        "history_raw = raw if config['native_loop'].get('history_serialization','json') == 'raw' else effective_raw",
        "history_raw, history_intervention = forced_history(raw,fields,effective,policy,index,len(gated)-1,config['native_loop'].get('history_serialization','json'))\n"
        "                if history_intervention:\n"
        "                    record['history_intervention'] = history_intervention\n"
        "                    capture.mark('control','forced_think_history','Preserve explicitly forced THINK in S1 history',history_intervention)")
    native=replace_once(native,
        "number = len(result['s2_requests'])",
        "number = len(result['s2_requests'])\n"
        "                context_policy = case.get('s2_context_policy',cfg.get('context_policy','native'))\n"
        "                reasoner_messages = s2_messages(self.history,result['turns'],context_policy)")
    native=replace_once(native,
        "result['s2_requests'].append(request)\n                span = f's2-{number}'",
        "result['s2_requests'].append(request)\n"
        "                private_trace = open_private_reasoning_trace(root,name,number,cfg['repo'])\n"
        "                span = f's2-{number}'")
    native=replace_once(native,
        "'reasoning_characters': 0, 'commands': [], 'final_text': '', 'model': cfg['repo']}",
        "'reasoning_characters': 0, 'commands': [], 'final_text': '', 'model': cfg['repo'], 'input_messages':reasoner_messages, 'context_policy':context_policy}")
    native=replace_once(native,
        "request['reasoning_characters'] += len(thought)",
        "write_private_reasoning_chunk(private_trace,thought,time.monotonic()-capture.origin)\n"
        "                            request['reasoning_characters'] += len(thought)")
    native=replace_once(native,'messages=self.history,','messages=reasoner_messages,')
    native=replace_once(native,"extra_body={'top_k':20}, max_tokens=cfg['max_tokens'])",
        "extra_body={'top_k':20}, top_p=cfg.get('top_p',1.0), seed=cfg.get('seed'), max_tokens=cfg['max_tokens'])")
    native=replace_once(native,
        "if not qualification['qualified']:\n                return results\n        for case",
        "if not qualification['qualified']:\n                return results\n            if not calibration_speech_gate(results,out):\n                return results\n        for case")
    native=replace_once(native,
        "request.update(final_text=full,end_seconds=time.monotonic()-capture.origin)",
        "close_private_reasoning_trace(private_trace,request.get('status','failed'),\n"
        "                        request['reasoning_characters'],request.get('finish_reason'))\n"
        "                    request.update(final_text=full,end_seconds=time.monotonic()-capture.origin)")
    smoke=original['scripts/smoke_duplexomni.py']
    smoke=replace_once(smoke,'speech_gpu = 0 if config["gpus"] == 1 else thinker_tp',
        'speech_gpu = int(config.get("speech_gpu",0 if config["gpus"] == 1 else thinker_tp))\nassert 0 <= speech_gpu < config["gpus"]')
    smoke=replace_once(smoke,'from native_interaction import run_native_interaction',
        'from s2_single_adapter import run_native_interaction')
    return original,{'scripts/native_interaction.py':native,'scripts/smoke_duplexomni.py':smoke}


def save_sources(directory):
    original,modified=sources();directory.mkdir(parents=True,exist_ok=True)
    records={}
    for name,source in modified.items():
        target=directory/Path(name).name;target.write_text(source)
        (directory/(target.name+'.diff')).write_text(''.join(difflib.unified_diff(original[name].splitlines(True),source.splitlines(True),fromfile=name,tofile='S2 variant of '+name)))
        records[name]={'base_sha256':hashlib.sha256(original[name].encode()).hexdigest(),
                       'variant_sha256':hashlib.sha256(source.encode()).hexdigest()}
    (directory/'sources.json').write_text(json.dumps(records,indent=2)+'\n')


# Make the variant a normal module so the existing paced CPU regression can
# replace transports and clients in its globals without replacing model code.
_original,_modified=sources()
exec(compile(_modified['scripts/native_interaction.py'],str(ROOT/'scripts/native_interaction.py')+' [S2 variant]','exec'),globals())


if __name__=='__main__':
    import os
    destination=ROOT/'.migration/updates/2026-10-09-s2-single'/('executed-source-'+os.environ.get('SLURM_JOB_ID','local'))
    save_sources(destination)
    namespace={'__name__':'__main__','__file__':str(ROOT/'scripts/smoke_duplexomni.py')}
    exec(compile(_modified['scripts/smoke_duplexomni.py'],str(ROOT/'scripts/smoke_duplexomni.py')+' [S2 variant]','exec'),namespace)
