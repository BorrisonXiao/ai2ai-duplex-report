"""Question-free causal chunks and separate request-time inputs for the text pilot."""
import json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'research/answering_study_20261101'
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
def main():
 assert not (D/'amortized-inputs.json').exists(),'Preserve the frozen notes inputs.'
 bank=json.loads((D/'bank.json').read_text());by={q['id']:q for q in bank['questions']};transcripts=json.loads((D/'meeting-transcripts.json').read_text())['meetings'];pilot=[by[i] for i in bank['pilot_ids']];meetings=[]
 for m in sorted({q['meeting'] for q in pilot}):
  end=max(q['at'] for q in pilot if q['meeting']==m);segments=transcripts[m];clock=0.;chunks=[];previous=0
  for tick in range(1,math.floor(end*2)+1):
   t=tick/2;released=[s for s in segments if t-.5<s['available']<=t]
   sentence=any(s['boundary']=='sentence_end' and len(s['text'].split())>=4 for s in released)
   if t-clock>=40 or (t-clock>=25 and sentence):
    prefix=[s for s in segments if s['available']<=t];new=[s for s in prefix if s['available']>clock];words=sum(len(s['text'].split()) for s in new)
    assert 10<=t-clock<=40 and all(s['available']<=t for s in prefix)
    chunks.append(dict(id=f'{m}-C{len(chunks):03d}',start=clock,end=t,new_segment_ids=[s['id'] for s in new],new_word_count=words,query_model=words>=8));clock=t;previous=len(prefix)
  meetings.append(dict(meeting=m,segments=[s for s in segments if s['available']<=end],chunks=chunks))
 # This file contains no evaluation questions, references, requester IDs or evidence choices.
 save(D/'amortized-inputs.json',dict(meetings=meetings,chunk_rule='On the causal 0.5 s clock: first meaningful observed sentence end at/after 25 s, or the 40 s cap; no calls on fewer than eight new words.',future_user_question_present=False,minimum_seconds=10,target_seconds=25,maximum_seconds=40))
 refs={c['question_id']:c for c in json.loads((D/'pilot-reference-source-review.json').read_text())['cases']};support={c['question_id']:c for c in json.loads((D/'pilot-audio.json').read_text())['cases'] if c['variant']=='support'};cases=[]
 for q in pilot:
  cases.append({k:q[k] for k in ['id','meeting','requester','at','question','prefix','split']})
  cases[-1].update(source_excerpt_diagnostic=sorted(support[q['id']]['source_evidence'],key=lambda s:(s['start'],s['end'])),reference=refs[q['id']]['reference_answer'])
 save(D/'text-pilot-requests.json',dict(cases=cases,scope='Six development/diagnostic questions, not full-bank scores. Source-excerpt reader control has oracle selection and is separate from the full-history reader. References are evaluator-only and excluded from model inputs.'))
 save(D/'text-pilot-preflight.json',dict(status='pass',questions=len(cases),meetings=len(meetings),total_chunks=sum(len(m['chunks']) for m in meetings),queries_per_goal=sum(c['query_model'] for m in meetings for c in m['chunks']),minimum_chunk_seconds=min(c['end']-c['start'] for m in meetings for c in m['chunks']),maximum_chunk_seconds=max(c['end']-c['start'] for m in meetings for c in m['chunks']),question_blind_file_separated=True,GT_past_only=True,GPUs=0))
 print(json.loads((D/'text-pilot-preflight.json').read_text()))
if __name__=='__main__':main()
