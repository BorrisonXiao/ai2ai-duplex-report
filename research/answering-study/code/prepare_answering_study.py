"""Freeze the full question bank and causal transcript inputs for answering studies."""
import argparse,hashlib,json,re,zipfile
from pathlib import Path
from prepare_question_audio_completion import words_for
ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'research/answering_study_20261101'
PILOT_IDS=['pilot:P-EN-notes','pilot:P-EN-audio','pilot:P-ES-slogan','pilot:P-TS-time','first:authored-W1-2','scale:TS3006c-S05-Q3']
def read(p):return json.loads(Path(p).read_text())
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def segments(words,meeting):
 out=[]
 for speaker in sorted({w['speaker'] for w in words}):
  cur=[]
  def flush(reason):
   nonlocal cur
   if not cur:return
   text=re.sub(r'\s+([,.;:!?])',r'\1',' '.join(w['text'] for w in cur)).strip()
   if text:out.append(dict(speaker=speaker,start=min(w['start'] for w in cur),end=max(w['end'] for w in cur),text=text,boundary=reason))
   cur=[]
  for w in sorted((w for w in words if w['speaker']==speaker),key=lambda w:(w['start'],w['end'])):
   if cur and w['start']-max(t['end'] for t in cur)>1.2:flush('speaker_gap')
   cur.append(w)
   if w.get('punctuation') and w['text'] in ['.','?','!']:flush('sentence_end')
   elif max(t['end'] for t in cur)-min(t['start'] for t in cur)>=12:flush('12s_cap')
  flush('speaker_end')
 out.sort(key=lambda s:(s['end'],s['start'],s['speaker']))
 for i,s in enumerate(out):s.update(id=f'{meeting}-U{i:05d}',available=s['end']+.5)
 return out
def main():
 D.mkdir(parents=True,exist_ok=True)
 assert not (D/'bank.json').exists(),'Preserve frozen bank; use a new study directory for a changed input.'
 cat=read(ROOT/'site/research/question-catalog/questions.json')['questions'];idx=read(ROOT/'site/research/question-acoustic-bank/current-input-index.json')['primary']
 split=read(ROOT/'research/question_audio_completion/evaluation-subset.json');meetings={};rows=[]
 with zipfile.ZipFile(ROOT/'data/prethinking_pilot/ami_EN2003a/annotations.zip') as z:
  for m in sorted({q['meeting'] for q in cat}):
   ws=words_for(m,z);assert ws and all(w['end']>=w['start'] for w in ws)
   meetings[m]=segments(ws,m)
 for q in cat:
  audio=idx[q['id']];cut=audio['source_time_seconds'];prefix=[s for s in meetings[q['meeting']] if s['available']<=cut]
  assert prefix and audio['question'].startswith('Assistant,')
  rows.append(dict(id=q['id'],meeting=q['meeting'],dataset=q['dataset'],requester=q['requester'],at=cut,question=audio['question'],draft_reference=q['versions'][0]['reference_answer'],prefix=prefix,split='development' if q['meeting'] in split['development_meetings'] else 'previously_inspected_diagnostic' if q['meeting']=='TS3006c' else 'evaluation',audio_record=audio,pilot=q['id'] in PILOT_IDS))
 assert len(rows)==105 and len({q['id'] for q in rows})==105
 save(D/'bank.json',dict(version='answering-2026-11-01-v1',questions=rows,meeting_count=len(meetings),question_count=105,pilot_ids=PILOT_IDS,scope='References are draft until source review; reader inputs omit draft references, evidence selections and scoring labels.',source_timing='AMI manual word times; Earnings21 published estimated word times; transcript segments released 0.5 s after end.'))
 save(D/'meeting-transcripts.json',dict(meetings=meetings))
 save(D/'protocol.json',dict(status='prepared_not_launched',primary_questions=105,pilot_questions=len(PILOT_IDS),native_models=['moshi','minicpm','duplexomni'],text_models=['Qwen3-30B-A3B-Instruct-2507','Qwen3-30B-A3B-Thinking-2507'],reference_status='proposal_and_check_then_Codex_source_review',pilot_conditions=['supporting_audio_then_question','original_full_history_then_question'],response_capture='60 s maximum input-clock silence; retain 19.2 s checkpoint and final-frame speech flags; native termination metadata is recorded, never assumed.',text_conditions=['reactive','amortized_summary','amortized_structured_notes'],chunking=dict(min_seconds=10,target_seconds=25,max_seconds=40,rule='Use the first observed sentence boundary at or after 25 s; otherwise close at 40 s. Do not query on empty chunks; do not close on tiny filler turns.'),evaluation_gate='Pilot and held-out scoring checks precede full-bank inference; model failures remain legitimate outcomes after caller qualification.',maximum_active_GPUs=4,reference_inputs='Past speaker-attributed transcript; draft answer hidden from first proposer.',amortized_inputs='Past transcript, previous saved results and fixed goal only; no future user question.',primary_metric='Source-supported complete answer correctness; three ordinal judge dimensions remain diagnostics.',thinking_tokens='Only native request-time thinking tokens; Instruct unexposed thinking is N/A, ordinary output separate.',history='Retain all available history; record capacity failures and any explicit fallback, never silently trim.',S2_notes_budget='1200 output tokens per earlier update; save all raw results and source-citation validity.',frozen_inputs={p:sha(ROOT/p) for p in ['site/research/question-catalog/questions.json','site/research/question-acoustic-bank/current-input-index.json','data/prethinking_pilot/ami_EN2003a/annotations.zip','research/question_audio_completion/evaluation-subset.json']}))
 print(json.dumps(dict(questions=len(rows),meetings=len(meetings),pilot=PILOT_IDS,maximum_prefix_segments=max(len(q['prefix']) for q in rows))))
if __name__=='__main__':main()
