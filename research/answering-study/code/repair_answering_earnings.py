"""Preserve untimed Earnings21 words using the existing conservative chunk releases."""
import copy,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'research/answering_study_20261101'
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
def main():
 assert not (D/'bank-v2.json').exists(),'Preserve corrected input version.'
 bank=copy.deepcopy(json.loads((D/'bank.json').read_text()));changed=[]
 for q in bank['questions']:
  if not q['meeting'].startswith('EC'):continue
  source=ROOT/'data/question_expansion/earnings'/q['meeting'][2:]/'chunks.json';chunks=json.loads(source.read_text());q['prefix']=[{**s,'boundary':'sentence_end' if re.search(r'[.!?]$',s['text']) else '35_word_cap'} for s in chunks if s['available'] is not None and s['available']<=q['at']];q['transcript_source']=str(source.relative_to(ROOT));q['timing_status']='Corrected text with estimated alignment; untimed words are held until a later observed timing anchor, not dropped or given invented word times.';changed.append(q['id'])
 bank.update(version='answering-2026-11-01-v2-complete-earnings-text',corrected_question_ids=changed,previous_version_preserved='bank.json');assert len(changed)==12
 save(D/'bank-v2.json',bank);save(D/'earnings-reference-v2/bank.json',dict(questions=[q for q in bank['questions'] if q['id'] in changed]))
 packets=json.loads((D/'reference-source-packets.json').read_text())['questions'];by={q['id']:q for q in bank['questions']};norm=lambda s:re.sub('[^a-z0-9]','',s.lower());proof=[]
 for q in packets:
  for e in q['source_evidence']:
   near=sorted([s for s in by[q['id']]['prefix'] if s['speaker']==e['speaker'] and s['end']>e['start']-.02 and s['start']<e['end']+.02],key=lambda s:s['start']);match=norm(e['text']) in norm(' '.join(s['text'] for s in near));proof.append(dict(question_id=q['id'],original_source_id=e['id'],available_source_ids=[s['id'] for s in near],text_matches=match));assert match,(q['id'],e['id'])
 save(D/'reference-source-bindings-v2.json',dict(status='pass',matched=len(proof),total=len(proof),proofs=proof,scope='Source text/attribution/time integrity, not automatic semantic validation of the reference answer.'))
 p=D/'protocol.json';protocol=json.loads(p.read_text());protocol.update(main_bank_file='bank-v2.json',pilot_bank_file='bank.json',corrected_Earnings_questions=changed,reference_input_correction='The audio-enrollment word list omits untimed words and must not be used as a complete text oracle. Corrected Earnings21 chunks preserve all words with conservative release; all 382 cited source passages now match. AMI pilot inputs are unchanged.');save(p,protocol)
 print('Corrected',len(changed),'earnings questions; matched source passages',len(proof),'/',len(proof))
if __name__=='__main__':main()
