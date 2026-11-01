"""Build paired, explicitly edited evidence clips and original-history inputs."""
import hashlib,json,math
from pathlib import Path
import numpy as np,soundfile as sf
from prepare_question_audio_completion import read_source,HEADERS
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'research/answering_study_20261101';A=ROOT/'exp/answering_study_assets';SR=16000
def read(p):return json.loads(Path(p).read_text())
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 assert not (D/'pilot-audio.json').exists(),'Preserve paired audio; use a new version for changes.'
 bank=read(D/'bank.json');qs={q['id']:q for q in bank['questions']};voices={c['catalog_id']:c for c in read(ROOT/'site/research/question-acoustic-bank/review.json')['cases'] if c['primary']}
 authored={q['distinct_question_id']:q for q in read(ROOT/'site/research/question-pilot/distinct-questions.json')['questions']};windows={w['id']:w for w in read(ROOT/'research/question_pilot/windows.json')}
 first={q['id']:q for q in read(ROOT/'research/ami_questions/accepted.json')};old={q['id']:q for q in read(ROOT/'research/question_study/cases-private.json')['cases']};A.mkdir(parents=True,exist_ok=True);rows=[];reviews=[];fulls={}
 for id in bank['pilot_ids']:
  q=qs[id];m=q['meeting']
  if m not in fulls:
   end=max(qs[i]['at'] for i in bank['pilot_ids'] if qs[i]['meeting']==m)
   if m=='TS3006c':
    x,sr=sf.read(ROOT/'exp/s1_meeting_pilot/assets/TS3006c-original-prefix.wav',dtype='int16');assert sr==SR;x=x[:round(end*SR)]
   else:assert m+'-Mix-Headset' in HEADERS;x=read_source(m,'Mix-Headset',0,end)
   fulls[m]=x
  if id.startswith('pilot:'):
   meta=authored[id.split(':',1)[1]];source={s['id']:s for s in windows[meta['window_id']]['prefix']};evidence=[source[i] for i in meta['evidence_ids']];answer=meta['reference_answer']
  elif id.startswith('first:'):meta=first[id.split(':',1)[1]];evidence=meta['evidence'];answer=meta['answer']
  else:meta=old[id];evidence=meta['evidence'];answer='C reported putting the files in the shared folder; D initially saw only their own presentation. The discussion identifies a components-design PowerPoint but does not verify live access for everyone or an outage.'
  assert evidence and all(e['end']+.5<=q['at'] for e in evidence)
  c=voices[id];injected,sr=sf.read(ROOT/'site/research/question-acoustic-bank'/c['injected_audio'],dtype='int16');assert sr==SR
  insertion=injected[round(c['inserted_interval_start_seconds']*SR):round(c['inserted_interval_end_seconds']*SR)];lead=c['synthetic_speech_playback_start_seconds']-c['inserted_interval_start_seconds'];assert len(insertion)>SR
  intervals=[]
  for e in sorted(evidence,key=lambda x:x['start']):
   a=max(0,e['start']-.4);b=min(q['at'],e['end']+.6)
   if intervals and a<=intervals[-1][1]+.5:intervals[-1][1]=max(intervals[-1][1],b)
   else:intervals.append([a,b])
  support=np.concatenate([fulls[m][round(a*SR):round(b*SR)] for a,b in intervals]);prefix=fulls[m][:round(q['at']*SR)]
  # Initial padding aligns native packet phase; no gap is added at the request.
  native_frame=round(.48*SR);pad=(len(prefix)-len(support))%native_frame;support=np.pad(support,(pad,0))
  assert len(support)%native_frame==len(prefix)%native_frame
  number=len(reviews)+1
  for variant,context in [('support',support),('full',prefix)]:
   path=A/f'M{number:02d}-{variant}.wav';audio=np.concatenate([context,insertion]);sf.write(path,audio,SR,subtype='PCM_16');actual,rate=sf.read(path,dtype='int16');assert np.array_equal(actual[len(context):],insertion)
   rows.append(dict(id=f'M{number:02d}-{variant}',question_id=id,variant=variant,meeting=m,question=q['question'],requester=q['requester'],input_audio=str(path.relative_to(ROOT)),input_sha256=sha(path),source_cutoff_seconds=len(context)/SR,request_start_seconds=len(context)/SR+lead,request_end_seconds=len(context)/SR+lead+c['question_length_seconds'],input_seconds=len(audio)/SR,insertion_pcm_sha256=hashlib.sha256(insertion.tobytes()).hexdigest(),edited_diagnostic=variant=='support',source_intervals=intervals if variant=='support' else [[0,q['at']]],initial_zero_padding_seconds=pad/SR if variant=='support' else 0,original_recording_question_time=q['at'],reference_answer=answer,source_evidence=evidence,question_audio_gain_db=0))
  reviews.append(dict(question_id=id,reference_answer=answer,source_evidence=evidence,review_status='existing_source_review_reused_with_new_audio_bindings',speaker_label_note='AMI A-D labels are oracle transcript labels, not spoken names; do not require the model to invent an unavailable personal name or speak a label as a name.'))
  print(id,'support',round(len(support)/SR,2),'full',round(len(prefix)/SR,2),'reference:',answer,flush=True)
  for e in evidence:print(' ',e['speaker'],e['start'],e['end'],e['text'],flush=True)
 assert len(rows)==12 and all(len({r['insertion_pcm_sha256'] for r in rows if r['question_id']==i})==1 for i in bank['pilot_ids'])
 save(D/'pilot-audio.json',dict(status='prepared_CPU_boundaries_checked',cases=rows,control_audio='data/benchmarks/natural_dailytalk_outlet/outlet_request.wav',speech_waveform_unchanged_between_paired_conditions=True,no_future_meeting_audio=True,no_enrollment_audio_in_history=True,maximum_response_silence_seconds=60,model_inputs_exclude_references_and_evidence_selection_labels=True))
 save(D/'pilot-reference-source-review.json',dict(reviewer='Codex; existing reviewed references and exact supporting speech inspected again before launch',cases=reviews,independent_human_rating=False))
if __name__=='__main__':main()
