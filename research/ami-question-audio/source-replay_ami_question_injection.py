"""Create a full local paused replay and a 480-ms packet/timeline manifest.

Questions are precomputed. This implements audio injection, not live TTS or an
answering model. The published review page exports only short context clips.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import soundfile as sf

ROOT=Path(__file__).resolve().parents[1]

def main():
 p=argparse.ArgumentParser();p.add_argument('--block-ms',type=int,default=480);args=p.parse_args()
 base=ROOT/'exp/ami_question_audio/review';data=json.loads((base/'manifest.json').read_text())
 source=ROOT/'data/prethinking_pilot/ami_EN2003a/EN2003a.Mix-Headset.wav';y,sr=sf.read(source,dtype='int16');assert sr==16000
 events=[];parts=[];cursor=0;playback=0;preferred=[]
 for q in sorted(data['protocol']['questions'],key=lambda q:q['source_time_seconds']):
  group=[c for c in data['clips'] if c['question_id']==q['id'] and c['eligible'] and c['asr']['wer']==0]
  if not group:raise ValueError('No exact-transcript voice-qualified question: '+q['id'])
  c=max(group,key=lambda c:c['speaker_check']['target_cosine']);preferred.append(c['id'])
  n=round(c['source_time_seconds']*sr);part=y[cursor:n];parts.append(part);playback+=len(part)
  clip,_=sf.read(ROOT/c['injected_path'],dtype='int16');a=round(c['inserted_interval_start_seconds']*sr);b=round(c['inserted_interval_end_seconds']*sr);inserted=clip[a:b]
  events.append(dict(clip_id=c['id'],question_id=q['id'],question=q['question'],requester=q['requester'],source_time_seconds=n/sr,playback_start_seconds=playback/sr,playback_end_seconds=(playback+len(inserted))/sr,source_sample=n,playback_start_sample=playback,playback_end_sample=playback+len(inserted),source_clock='paused',answer_generated=False))
  parts.append(inserted);playback+=len(inserted);cursor=n
 parts.append(y[cursor:]);full=np.concatenate(parts);path=base/'EN2003a.questions-injected.wav';sf.write(path,full,sr,subtype='PCM_16')
 # Removing injected intervals must recover every original PCM sample exactly.
 recovered=[];cursor=0
 for event in events:
  recovered.append(full[cursor:event['playback_start_sample']]);cursor=event['playback_end_sample']
 recovered.append(full[cursor:]);assert np.array_equal(np.concatenate(recovered),y)
 block=round(args.block_ms*sr/1000);packets=[]
 for a in range(0,len(full),block):
  b=min(a+block,len(full));overlap=[ev['clip_id'] for ev in events if a<ev['playback_end_sample'] and b>ev['playback_start_sample']]
  paused_before=sum(max(0,min(a,ev['playback_end_sample'])-ev['playback_start_sample']) for ev in events)
  paused_through=sum(max(0,min(b,ev['playback_end_sample'])-ev['playback_start_sample']) for ev in events)
  packets.append(dict(index=len(packets),playback_start_sample=a,playback_end_sample=b,source_start_sample=a-paused_before,source_end_sample=b-paused_through,synthetic_intersections=overlap))
 replay=dict(status='offline_audio_injection_verified',audio=str(path.relative_to(ROOT)),audio_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),source=str(source.relative_to(ROOT)),sample_rate=sr,packet_ms=args.block_ms,packets=packets,events=events,preferred_clip_ids=preferred,source_samples=len(y),replay_samples=len(full),source_pcm_exact_after_removing_insertions=True,new_gpus=0,answer_generation='deferred',live_paced_model_inference=False)
 (base/'replay.json').write_text(json.dumps(replay,indent=2)+'\n');print(json.dumps({k:v for k,v in replay.items() if k!='packets'},indent=2))

if __name__=='__main__':main()
