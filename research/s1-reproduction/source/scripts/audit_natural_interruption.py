"""Audit real-human request/clarification timing and actual model PCM on CPU."""
import argparse
import json
from pathlib import Path
import statistics
import time

import librosa
import numpy as np
import soundfile as sf
import torch
from transformers import WhisperForConditionalGeneration,WhisperProcessor
from controlled_runtime import percentile

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--job',required=True);args=parser.parse_args()
run=ROOT/f'exp/inference/duplexomni/native_loop_{args.job}'
summary=json.loads((run/'summary.json').read_text())
runtime=json.loads((ROOT/f'exp/diagnostics/gpu_runtime_{args.job}/runtime.json').read_text())
torch.set_num_threads(4);started=time.monotonic()
proc=WhisperProcessor.from_pretrained(ROOT/'models/validation/whisper-base',local_files_only=True)
model=WhisperForConditionalGeneration.from_pretrained(ROOT/'models/validation/whisper-base',local_files_only=True).float().cpu().eval()
def transcript(wave,sr):
    if not len(wave):return ''
    x=librosa.resample(wave,orig_sr=sr,target_sr=16000) if sr!=16000 else wave
    inputs=proc(x,sampling_rate=16000,return_tensors='pt',return_attention_mask=True)
    with torch.inference_mode():ids=model.generate(inputs.input_features,attention_mask=inputs.attention_mask,language='english',task='transcribe',max_new_tokens=256)
    return proc.batch_decode(ids,skip_special_tokens=True)[0].strip()
def levels(wave,sr):
    step=round(.02*sr)
    return np.array([np.sqrt(np.mean(wave[i:i+step]**2)) for i in range(0,len(wave),step)])
def window(wave,sr,start=0):
    energy=levels(wave,sr);active=np.flatnonzero((energy>1e-3)&(np.arange(len(energy))*.02>=start))
    if not len(active):return None
    left=max(0,round((active[0]*.02-.15)*sr));right=min(len(wave),round(((active[-1]+1)*.02+.15)*sr))
    return left,right
review={'job_id':args.job,'depth':'standard','status':summary['status'],'gpus':summary['gpus'],
    'gpu_type':runtime['selected_gpus'][0]['name'],'layout':summary['layout'],'s2_loaded':False,
    'startup_seconds':summary['startup_seconds'],'driver_seconds':summary['wall_seconds'],
    'runtime_qualification':summary.get('runtime_qualification'),'cases':[],
    'scope':'Human-recorded scripted DailyTalk utterances, with adapted clarification timing. Per-case actual PCM and all returned fields inspected; no physical device or benchmark-score claim.'}
for config in summary['config']['native_loop']['cases']:
    folder=run/config['name'];path=folder/'native_summary.json'
    if not path.exists():continue
    data=json.loads(path.read_text());assert not data['s2_requests'] and not data['s2_loaded']
    pcm,sr=sf.read(folder/'conversation_replay.wav',dtype='float32');user,played=pcm[:,0],pcm[:,1]
    origin=data['turns'][0]['input_submitted_seconds']
    record={'name':config['name'],'id':config['id'],'temperature':config.get('temperature',0),
        'status':data['status'],'generated_asr':data['generated_asr'],'generated_tts':data['generated_tts'],
        's2_requests':0,'model_think_count':sum('[THINK]' in t['fields'].get('system2_control','') for t in data['turns']),
        'model_stop_count':sum('[STOP]' in t['fields'].get('tts_control','') for t in data['turns']),
        'p95_s1_seconds':percentile([t['end_seconds']-t['start_seconds'] for t in data['turns']],.95),
        'max_input_queue_delay_seconds':max(t['start_seconds']-t['input_submitted_seconds'] for t in data['turns']),
        'played_transcript':'','actual_nonquiet_seconds':float(np.sum(levels(played,sr)>1e-3)*.02),
        'source_user_requests':1,'source_user_interruptions':1 if config.get('interrupt_audio') else 0,
        'evidence_artifact':str(path.relative_to(ROOT))}
    bounds=window(played,sr)
    if bounds:
        left,right=bounds;sf.write(folder/'response_window.wav',played[left:right],sr,subtype='PCM_16')
        record.update(response_window_start_seconds=left/sr,response_window_seconds=(right-left)/sr,
            played_transcript=transcript(played[left:right],sr))
    if data.get('interruption'):
        interruption=data['interruption'];start=interruption.get('start_seconds')
        detail={'status':interruption['status'],'expected_packets':interruption['expected_packets'],
            'processed_packets':interruption['processed_packets'],'actual_user_model_overlap_seconds':0,
            'stop_delay_from_packet_seconds':None,'old_epoch_nonquiet_packets_after_stop':None,
            'post_clarification_tts':'','post_clarification_audio_transcript':''}
        if start is not None:
            onset=start-origin;duration=interruption['expected_packets']*.48
            user_energy,model_energy=levels(user,sr),levels(played,sr);size=min(len(user_energy),len(model_energy))
            time_axis=np.arange(size)*.02;span=(time_axis>=onset)&(time_axis<onset+duration)
            user_active=(user_energy[:size]>.003)&span
            active=np.flatnonzero(user_active)
            detail.update(first_correction_packet_seconds=onset,
                actual_user_model_overlap_seconds=float(np.sum(user_active&(model_energy[:size]>1e-3))*.02),
                post_clarification_tts=''.join(t['fields'].get('tts','') for t in data['turns'] if t['start_seconds']>=start))
            if len(active):detail['first_nonquiet_user_correction_seconds']=active[0]*.02
            stops=[s for s in data['stop_events'] if s['at']>=start]
            if stops:
                stop=stops[0];old=interruption['epoch_before_input'];detail.update(stop_delay_from_packet_seconds=stop['at']-start,
                    old_epoch_nonquiet_packets_after_stop=sum(p['at']>=stop['at'] and p['rms']>1e-3 and any(t['epoch']==old for t in p['tags']) for p in data['playback_packets']),
                    stop_chunk=stop['chunk'],cleared_buffer_bytes=stop['dropped_bytes'])
                after=stop['at']-origin
            else:after=onset+duration
            new_bounds=window(played,sr,after)
            if new_bounds:
                left,right=new_bounds;sf.write(folder/'post_clarification_window.wav',played[left:right],sr,subtype='PCM_16')
                detail['post_clarification_audio_transcript']=transcript(played[left:right],sr)
            detail['genuine_barge_in']=detail['actual_user_model_overlap_seconds']>0
        record['interruption']=detail
    (folder/'speech_audit.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
    review['cases'].append(record);print(json.dumps(record,ensure_ascii=False),flush=True)
review['limitations']=['One human-recorded scripted dialogue; original barge-in timing is adapted, not naturally occurring.',
    'Only original user channel is supplied; source counterpart responses are excluded.',
    'All waiting gaps and queued-audio decisions remain in full PCM replay. ASR uses one contiguous audible window; no concatenation or time compression.',
    'STOP timing is from the first correction packet; actual nonquiet user onset is reported separately and is not acoustic word alignment.',
    'S2 is absent. A model THINK request is logged separately from an actual S2 dispatch.',
    'Forty-tick capture avoids the identified late rolling-history cache issue; longer streams remain unqualified.',
    'Automatic speech transcripts and lexical flags require semantic content review; no robust benchmark success rate is implied.']
review['audit_seconds']=time.monotonic()-started
(ROOT/f'reports/natural_interruption_{args.job}_review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n')
