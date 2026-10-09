"""CPU audit of real S2 reasoning, delivery and the actually played S1 answer."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import time

import librosa
import numpy as np
import soundfile as sf
import torch
from transformers import WhisperForConditionalGeneration,WhisperProcessor
from controlled_runtime import percentile

ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--job',required=True);args=p.parse_args()
folder=ROOT/f'exp/inference/duplexomni/native_loop_{args.job}'
summary=json.loads((folder/'summary.json').read_text())
runtime=json.loads((ROOT/f'exp/diagnostics/gpu_runtime_{args.job}/runtime.json').read_text())
started=time.monotonic();torch.set_num_threads(4)
processor=WhisperProcessor.from_pretrained(ROOT/'models/validation/whisper-base',local_files_only=True)
model=WhisperForConditionalGeneration.from_pretrained(ROOT/'models/validation/whisper-base',local_files_only=True).float().cpu().eval()
def transcribe(wave,sr):
    if not len(wave):return ''
    wave=librosa.resample(wave,orig_sr=sr,target_sr=16000) if sr!=16000 else wave
    inputs=processor(wave,sampling_rate=16000,return_tensors='pt',return_attention_mask=True)
    with torch.inference_mode():ids=model.generate(inputs.input_features,attention_mask=inputs.attention_mask,language='english',task='transcribe',max_new_tokens=256)
    return processor.batch_decode(ids,skip_special_tokens=True)[0].strip()
def audible_window(wave,sr,after=0):
    size=round(sr*.02)
    active=[i for i in range(0,len(wave),size) if i/sr>=after and np.sqrt(np.mean(wave[i:i+size]**2))>1e-3]
    if not active:return None
    return max(0,active[0]-round(.15*sr)),min(len(wave),active[-1]+size+round(.15*sr))
def result_391(text):
    normal=re.sub(r'[^a-z0-9]+',' ',text.lower())
    return bool(re.search(r'\b391\b|three hundred (and )?ninety one',normal))
review={'job_id':args.job,'depth':'standard','status':summary['status'],'gpus':summary['gpus'],
        'gpu_types':[g['name'] for g in runtime['selected_gpus']],'layout':summary['layout'],
        's2_backend':summary['config']['system2']['repo'],'runtime_qualification':summary.get('runtime_qualification'),
        'initial_response_gate':summary.get('initial_response_gate'),'execution_error':summary.get('error'),'cases':[],
        'scope':'Matched one-request cases; S2 is forced explicitly, not autonomous. Review uses actual PCM and native field/delivery records.'}
for config in summary['config']['native_loop']['calibration_cases']+summary['config']['native_loop']['cases']:
    case_folder=folder/config['name'];path=case_folder/'native_summary.json'
    if not path.exists():continue
    data=json.loads(path.read_text());wave,sr=sf.read(case_folder/'playback.wav',dtype='float32')
    row={'id':config['id'],'name':config['name'],'policy':config['s2_policy'],'status':data['status'],
         'is_calibration':'calibration' in config['name'],'source_user_requests':1,'source_user_interruptions':0,
         'generated_asr':data['generated_asr'],'generated_tts':data['generated_tts'],
         'played_transcript':'','s2_loaded':data['s2_loaded'],'s2_request_count':len(data['s2_requests']),
         'model_think_count':sum('[THINK]' in t['fields'].get('system2_control','') for t in data['turns']),
         'forced_history_interventions':[t['chunk'] for t in data['turns'] if t.get('history_intervention')],
         's2_requests':data['s2_requests'],'guidance_deliveries':data['deliveries'],
         'p95_s1_seconds':percentile([t['end_seconds']-t['start_seconds'] for t in data['turns']],.95),
         'max_input_queue_delay_seconds':max(t['start_seconds']-t['input_submitted_seconds'] for t in data['turns']),
         'actual_nonquiet_seconds':sum(np.sqrt(np.mean(wave[i:i+round(.02*sr)]**2))>1e-3 for i in range(0,len(wave),round(.02*sr)))*.02}
    bounds=audible_window(wave,sr)
    if bounds:
        left,right=bounds;sf.write(case_folder/'audible_answer.wav',wave[left:right],sr,subtype='PCM_16')
        row['played_transcript']=transcribe(wave[left:right],sr)
    if data['deliveries']:
        origin=data['turns'][0]['input_submitted_seconds'];delivery=data['deliveries'][0]['at']
        bounds=audible_window(wave,sr,delivery-origin)
        row['post_guidance_generated_tts']=''.join(t['fields'].get('tts','') for t in data['turns'] if t['start_seconds']>=delivery)
        row['post_guidance_audio_transcript']=''
        if bounds:
            left,right=bounds;sf.write(case_folder/'post_guidance_answer.wav',wave[left:right],sr,subtype='PCM_16')
            row['post_guidance_audio_transcript']=transcribe(wave[left:right],sr)
    if config['s2_policy']!='off':
        row['reasoning_observed']=any(r['reasoning_characters']>0 for r in data['s2_requests'])
        row['complete_s2_guidance']=any(r['commands'] for r in data['s2_requests'])
        row['guidance_reached_s1']=bool(data['deliveries'])
        row['post_guidance_requested_speech']=bool(row.get('post_guidance_generated_tts','').strip())
        row['post_guidance_audible_speech']=bool(row.get('post_guidance_audio_transcript','').strip())
        row['transport_handoff_observed']=row['reasoning_observed'] and row['complete_s2_guidance'] and row['guidance_reached_s1']
    if 'arithmetic' in config['name']:
        row['correct_arithmetic_in_played_transcript']=result_391(row['played_transcript'])
        if row.get('guidance_deliveries'):row['correct_arithmetic_after_guidance']=result_391(row.get('post_guidance_audio_transcript',''))
    (case_folder/'s2_single_audit.json').write_text(json.dumps(row,ensure_ascii=False,indent=2)+'\n')
    review['cases'].append(row);print(json.dumps({k:v for k,v in row.items() if k!='s2_requests'},ensure_ascii=False),flush=True)
comparisons=[]
configured=summary['config']['native_loop']['cases']
for active in configured:
    if active['s2_policy']=='off':continue
    baseline=next((c for c in configured if c['s2_policy']=='off' and c['audio']==active['audio']),None)
    if baseline:comparisons.append((baseline['name'],active['name']))
for left,right in comparisons:
    a,b=folder/left/'native_summary.json',folder/right/'native_summary.json'
    if a.exists() and b.exists():
        x,y=json.loads(a.read_text()),json.loads(b.read_text())
        boundary=next((t['chunk'] for t in y['turns'] if t['effective_control_fields'].get('system2_control')=='[THINK]'),0)
        review.setdefault('paired_prefixes',[]).append({'baseline':left,'forced':right,'ticks_compared':boundary,
            'returned_fields_identical':all(x['turns'][i]['fields']==y['turns'][i]['fields'] for i in range(boundary))})
try:
    lines=subprocess.check_output(['sacct','-j',args.job,'-X','-n','-P','--format=JobIDRaw,State,ElapsedRaw,AllocTRES'],text=True).splitlines()
    line=next(s for s in lines if s.split('|')[0]==args.job);parts=line.split('|')
    review.update(slurm_state=parts[1],allocation_seconds=int(parts[2]),allocation_gpu_hours=int(parts[2])*summary['gpus']/3600)
except (OSError,subprocess.CalledProcessError,StopIteration):pass
review['audit_seconds']=time.monotonic()-started
review['limitations']=['Forced THINK is a declared intervention. Only cases with policy=model test model-triggered delegation.',
    'The local 4B Thinking model substitutes for the paper’s Gemini backend.',
    'The outlet request is human-recorded; the arithmetic request is authored Flite synthetic speech.',
    'S2 remains loaded on its dedicated GPU even in dispatch-off conditions.',
    'Speech already synthesized before a guidance delivery may play afterwards; post-delivery PCM timing alone cannot establish causal use of guidance.',
    'Semantic review of actual speech is required; successful execution or transport is not a task-level pass.',
    'Forty-step captures avoid the known later history-trimming path; long streams are unqualified.']
(ROOT/f'reports/s2_single_{args.job}_review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n')
