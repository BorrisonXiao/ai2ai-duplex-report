"""Record Codex source decisions for the 48 actual development-pilot text answers."""
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'research/answering_study_20261101'
# Condition order: selected source, reactive, summary, structured notes.
# C: complete supported answer; P: useful but incomplete or materially unsupported;
# I: central fact wrong. These decisions follow the policy frozen before outputs.
DECISIONS={
 'instruct':{
  'pilot:P-EN-notes':('CCCC',['Identifies D, the earlier volunteer.']*4),
  'pilot:P-EN-audio':('CCCC',['Gives at least one recorded reason for dropping the audio work.']*4),
  'pilot:P-ES-slogan':('CCCC',['Preserves the unresolved distinction between literal slogan and design idea.']*4),
  'pilot:P-TS-time':('CCCC',['Correct allowance of about seven minutes per presentation.']*4),
  'first:authored-W1-2':('CIII',['Correct sender, today/tomorrow timing and Psychology rationale.','Returns end of week instead of the main-call commitment of today/tomorrow.','Saved summaries do not prevent the wrong end-of-week timing.','Structured notes do not prevent the wrong end-of-week timing.']),
  'scale:TS3006c-S05-Q3':('CPPC',['Distinguishes C\'s placement report from D\'s inability to see the files; the PowerPoint description is not required.','Recovers placement and visibility but invents a literal file name from a disfluent PowerPoint description.','Adds an unsupported literal file name and broad failed-transfer/access claims.','Preserves the placement report and unresolved visibility/copy issue.'])},
 'thinking':{
  'pilot:P-EN-notes':('CCCC',['Identifies D, the earlier volunteer; citation or quotation issues are checked separately.']*4),
  'pilot:P-EN-audio':('CCCC',['Gives a recorded reason for dropping the work.']*4),
  'pilot:P-ES-slogan':('CCCC',['Recovers that the literal-slogan versus design-idea choice remained unresolved.']*4),
  'pilot:P-TS-time':('CCCC',['Correct allowance of seven minutes per presentation.']*4),
  'first:authored-W1-2':('CCPC',['Correct sender, today/tomorrow timing and Psychology rationale.','Correct main-call timing and tailoring rationale; the attendance concern is also present in the surrounding discussion.','Presents end of week/Thursday as an alternative to today/tomorrow, leaving the requested timing ambiguous.','Correct sender, today/tomorrow timing and Psychology rationale.']),
  'scale:TS3006c-S05-Q3':('CCPC',['Preserves C\'s placement report and D\'s visibility limit.','Recovers the placement report, visibility problem and subsequent proposal without claiming a completed live check.','Reports placement without the uncertainty or visibility limit required for the current-status question.','Preserves the report and unresolved visibility status.'])}}
def main():
 refs={r['id']:r for r in json.loads((D/'references-reviewed.json').read_text())['references']};policy=json.loads((D/'pilot-scoring-policy.json').read_text());bank={q['id']:q for q in json.loads((D/'bank-v2.json').read_text())['questions']};rows=[];summaries=[]
 conditions=['source_excerpt_diagnostic','reactive','amortized_summary','amortized_structured_notes']
 for model,job in [('instruct','1413130'),('thinking','1413131')]:
  answers=json.loads((ROOT/'exp/answering_text'/job/'answers.json').read_text())
  for a in answers:
   qid,condition=a['id'].rsplit('|',1);codes,reasons=DECISIONS[model][qid];index=conditions.index(condition);grade={'C':'complete','P':'partial','I':'incorrect'}[codes[index]]
   assert a['parsed'] and a['finish_reason']=='stop'
   ids={s['id'] for s in bank[qid]['prefix']}
   row=dict(id=a['id'],question_id=qid,model=model,job=job,grade=grade,complete=grade=='complete',reason=reasons[index],answer=a['parsed']['answer'],answer_sha256=hashlib.sha256(a['parsed']['answer'].encode()).hexdigest(),raw_output_sha256=hashlib.sha256(a['raw_output'].encode()).hexdigest(),reference_answer=refs[qid]['answer'],required_facts=policy['rules'][qid]['required'],source_evidence=refs[qid]['source_evidence'],unavailable_citation_ids=[i for i in a['parsed'].get('evidence_ids',[]) if condition!='source_excerpt_diagnostic' and i not in ids],native_thinking_tokens=a['native_thinking_tokens'],ordinary_output_tokens=a['ordinary_output_tokens'],reviewer='Codex source inspection',independent_human_review=False)
   rows.append(row)
  for condition in conditions:
   group=[r for r in rows if r['model']==model and r['id'].endswith('|'+condition)]
   assert len(group)==6
   summaries.append(dict(model=model,condition=condition,questions=6,complete=sum(r['complete'] for r in group),mean_request_thinking_tokens=statistics.mean(r['native_thinking_tokens'] for r in group) if model=='thinking' else None,mean_request_ordinary_output_tokens=statistics.mean(r['ordinary_output_tokens'] for r in group)))
 result=dict(status='Codex_source_review_complete_development_only',outputs=48,policy_sha256=hashlib.sha256((D/'pilot-scoring-policy.json').read_bytes()).hexdigest(),rows=rows,summaries=summaries,limits=['Six deliberately selected development/diagnostic questions; no held-out accuracy or statistical improvement claim.','Speaker labels are oracle information in text inputs; unavailable personal names are not required.','Citation availability is checked separately from factual correctness.','Earlier notes have format/source-ID checks, not complete semantic review.'])
 (D/'text-source-review.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n');print(json.dumps(summaries))
if __name__=='__main__':main()
