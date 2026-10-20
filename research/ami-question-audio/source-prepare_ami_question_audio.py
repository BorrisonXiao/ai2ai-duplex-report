"""Prepare past-only AMI voice prompts, independent voice references and pause points."""
import hashlib
import json
from pathlib import Path
import re
import numpy as np
import soundfile as sf

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/prethinking_pilot/ami_EN2003a'
OUT=ROOT/'research/ami_question_audio'
ASSETS=ROOT/'exp/ami_question_audio/assets'

def join(words):
 text=' '.join(w['text'] for w in words)
 return re.sub(r'\s+([.,?!;:])',r'\1',text).lstrip('.,?!;: ')

def main():
 ASSETS.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
 chunks=json.loads((ROOT/'exp/prethinking_pilot/data/chunks.json').read_text())
 words=[w for c in chunks for w in c['words']]
 requests=[json.loads(x) for x in (ROOT/'research/ami_questions/requests.jsonl').read_text().splitlines()]
 selected=[]
 for qid,label in [('authored-W2-1','poster-capacity'),('authored-W3-1','outreach'),('curated-instruct-packets-W4-deadlines','deadlines')]:
  q=next(q for q in requests if q['id']==qid).copy();q.update(short_id=label,mode='pause_insert_question_resume',answer_generated=False)
  t=q['source_time_seconds']
  assert not [w for w in words if not w['punctuation'] and w['start']<t<w['end']],f'Word cut at {t}'
  q['context_start_seconds']=t-(19 if label=='deadlines' else 20)
  q['context_end_seconds']=t+5
  q['context_transcript']=[{k:c[k] for k in ['speaker','start','end','text']} for c in chunks if c['end']>q['context_start_seconds'] and c['start']<t+5]
  selected.append(q)
 refs=[]
 for speaker,channel,ranges in [('B',1,[(984.53,993.02,'primary'),(442.29,449.89,'alternate'),(714.61,721.75,'heldout')]),('C',3,[(999.66,1008.34,'primary'),(731.51,741.09,'alternate'),(1740.0,1756.0,'heldout')])]:
  path=DATA/f'EN2003a.Headset-{channel}.wav';y,sr=sf.read(path,dtype='float32');mix,mix_sr=sf.read(DATA/'EN2003a.Mix-Headset.wav',dtype='float32');assert sr==mix_sr==16000
  for start,end,kind in ranges:
   if kind=='heldout' and speaker=='C':
    candidates=[c for c in chunks if c['speaker']=='C' and c['start']>1700 and c['end']-c['start']>6]
    c=candidates[0];start,end=c['start'],c['end']
   selected_words=[w for w in words if w['speaker']==speaker and w['start']>=start-.001 and w['end']<=end+.001]
   transcript=join(selected_words);name=f'{speaker}-{kind}'
   for suffix,signal in [('headset',y),('mix',mix)]:
    crop=signal[round((start-.08)*sr):round((end+.12)*sr)]
    sf.write(ASSETS/f'{name}-{suffix}.wav',crop,sr,subtype='PCM_16')
   refs.append(dict(id=name,speaker=speaker,channel=channel,source_start_seconds=start-.08,source_end_seconds=end+.12,text=transcript,headset=str((ASSETS/f'{name}-headset.wav').relative_to(ROOT)),mix=str((ASSETS/f'{name}-mix.wav').relative_to(ROOT)),role=kind))
 for q in selected:
  assert all(r['source_end_seconds']<q['source_time_seconds'] for r in refs if r['speaker']==q['requester'] and r['role']!='heldout')
 manifest=dict(meeting='EN2003a',license='CC BY 4.0',questions=selected,references=refs,original_sample_rate=16000,speaker_mapping={'B':'Headset-1','C':'Headset-3'},speaker_mapping_note='meetings.xml explicitly corrects the Transcriber channel mismatch: C is audio channel 3, not channel 2.',max_gpus_authorized=4,answer_generation='deferred',pause_policy='source clock pauses for question only, then resumes; no assistant response')
 (OUT/'protocol.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print(json.dumps({'questions':[(q['short_id'],q['requester'],q['source_time_seconds']) for q in selected],'references':[{k:r[k] for k in ['id','source_start_seconds','source_end_seconds','text']} for r in refs]},indent=2))

if __name__=='__main__':main()
