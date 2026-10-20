"""Independent content and speaker checks; scores are proxies for listening review."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
import time
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'exp/ami_question_audio/evaluation'

def read16(path):
 y,sr=sf.read(path,dtype='float32');assert y.ndim==1
 if sr!=16000:y=resample_poly(y,16000//math.gcd(sr,16000),sr//math.gcd(sr,16000))
 return y.astype('float32')

def get_files():
 rows=[]
 for path in sorted((ROOT/'exp/ami_question_audio').glob('*_*/generations.json')):
  rows += [r for r in json.loads(path.read_text()) if r.get('path')]
 protocol=json.loads((ROOT/'research/ami_question_audio/protocol.json').read_text())
 for ref in protocol['references']:
  for channel in ['headset','mix']:
   rows.append(dict(path=ref[channel],text=ref['text'],requester=ref['speaker'],reference_id=ref['id'],is_reference=True))
 tone=ROOT/'research/ami_question_audio/room-tone.json'
 if tone.exists():rows+=json.loads(tone.read_text())
 matched=ROOT/'exp/ami_question_audio/review/manifest.json'
 if matched.exists():
  for c in json.loads(matched.read_text())['clips']:
   rows.append(dict(path=c['matched_path'],text=c['question'],requester=c['requester'],is_processed=True))
 unique={r['path']:r for r in rows}
 vc=ROOT/'exp/ami_question_audio/vc/generations.json'
 if vc.exists():
  for r in json.loads(vc.read_text()):unique[r['path']]=r
 return list(unique.values())

def norm(text):
 text=text.lower().replace('’',"'")
 text=re.sub(r"\bwho's\b",'who is',text)
 text=re.sub(r'\btwo\b','2',text)
 return re.sub(r'[^a-z0-9 ]','',text).split()

def wer(ref,hyp):
 a,b=norm(ref),norm(hyp);d=list(range(len(b)+1))
 for i,x in enumerate(a,1):
  n=[i]
  for j,y in enumerate(b,1):n.append(min(n[-1]+1,d[j]+1,d[j-1]+(x!=y)))
  d=n
 return d[-1]/max(1,len(a))

def main():
 p=argparse.ArgumentParser();p.add_argument('--stage',choices=['asr','speaker'],required=True);args=p.parse_args()
 OUT.mkdir(parents=True,exist_ok=True);rows=get_files();started=time.monotonic()
 if args.stage=='asr':
  import torch
  import nemo.collections.asr as nemo_asr
  sys.path.insert(0,str(ROOT/'external/mp-bench/scripts'))
  from transcribe import transcribe_paths
  model=nemo_asr.models.ASRModel.restore_from(str(next((ROOT/'models/mpbench-parakeet').glob('*.nemo'))),map_location=torch.device('cuda')).eval()
  result=[]
  for i,row in enumerate(rows):
   key=hashlib.sha256((ROOT/row['path']).read_bytes()).hexdigest();path=OUT/f'asr-{key[:20]}.json'
   if path.exists():r=json.loads(path.read_text())
   else:
    audio=OUT/'asr-input.wav';sf.write(audio,read16(ROOT/row['path']),16000,subtype='PCM_16')
    r=transcribe_paths(model,[str(audio)],batch_size=1)[0];r['audio_sha256']=key;path.write_text(json.dumps(r,indent=2)+'\n')
   result.append(dict(path=row['path'],expected=row['text'],**r,wer=wer(row['text'],r['text']),is_reference=row.get('is_reference',False),is_room_tone=row.get('is_room_tone',False)))
   print(i,row['path'],r['text'],flush=True)
  (OUT/'asr.json').write_text(json.dumps(result,indent=2)+'\n')
 else:
  rows=[r for r in rows if not r.get('is_room_tone')]
  import torch
  # SpeechBrain 1.0.3 predates torchaudio's backend-list removal.
  import torchaudio
  if not hasattr(torchaudio,'list_audio_backends'):torchaudio.list_audio_backends=lambda:['soundfile']
  from speechbrain.inference.speaker import EncoderClassifier
  source=str(ROOT/'models/ami-ecapa')
  model=EncoderClassifier.from_hparams(source=source,savedir=str(OUT/'ecapa-loaded'),overrides={'pretrained_path':source},run_opts={'device':'cuda'})
  embeds={}
  for row in rows:
   signal=torch.from_numpy(read16(ROOT/row['path'])).unsqueeze(0).cuda()
   with torch.inference_mode():v=model.encode_batch(signal).flatten().cpu().numpy()
   embeds[row['path']]=v/max(1e-10,np.linalg.norm(v))
  protocol=json.loads((ROOT/'research/ami_question_audio/protocol.json').read_text());held={r['speaker']:r['headset'] for r in protocol['references'] if r['role']=='heldout'}
  result=[]
  for row in rows:
   v=embeds[row['path']];scores={s:float(np.dot(v,embeds[path])) for s,path in held.items()}
   other='C' if row['requester']=='B' else 'B';target=scores[row['requester']]
   result.append(dict(path=row['path'],requester=row['requester'],cosine_to_heldout=scores,target_cosine=target,target_minus_other=target-scores[other],is_reference=row.get('is_reference',False)))
  (OUT/'speaker.json').write_text(json.dumps(result,indent=2)+'\n')
  print(json.dumps(result,indent=2),flush=True)
 (OUT/(args.stage+'-runtime.json')).write_text(json.dumps(dict(job=os.environ.get('SLURM_JOB_ID'),gpus=1,stage=args.stage,seconds=time.monotonic()-started,files=len(rows)),indent=2)+'\n')

if __name__=='__main__':main()
