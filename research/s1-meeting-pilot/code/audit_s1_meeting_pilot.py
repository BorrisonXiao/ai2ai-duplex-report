"""Record Codex's source/ASR review without replacing original model verdicts."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from s1_eval.core import evaluate,fingerprint,validate_review
from s1_eval import VERSION
D=ROOT/'research/s1_meeting_pilot'
def read(p):return json.loads(p.read_text())
def save(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
def main():
 audit=[];judge_errors=[]
 for experiment,job,label in [('s1_meeting_pilot','1317667','buffered'),('s1_native_packet_pilot','1317837','native_stock_gate'),('s1_native_packet_ungated_pilot','1317930','native_no_gate')]:
  base=ROOT/'exp'/experiment/job;refs=read(D/'references.json') if label=='buffered' else read(base/'references.json')
  for row in read(D/'inputs.json')['cases']:
   name=row['id'] if label=='buffered' else row['id']+'-full-history';f=base/name;c=read(f/'evaluation/candidate.json');ref=refs[c['case_id']];original=read(f/'evaluation/score.json');old=original.get('review')
   facts={x['id']:'missing' for x in ref['required_facts']}
   reason=('No complete answer can be established from this quiet recording: native speech text and independent ASR are empty; retain the pending listening check.' if label=='buffered' and row['id']=='P01' else
    'The complete input was processed and raw S1 text gives the supported choose-one answer, but it is outside the four-field speech format; no usable spoken answer was produced.' if label=='buffered' and row['id']=='P02' else
    'The reply offers to check the folder but gives neither the earlier shared-folder statement nor the identified PowerPoint; no lookup tool was called.' if row['id']=='P01' else
    'The reply contains a greeting or an unrelated offer of help and does not supply the required answer facts.')
   review={'complete_answer':False,'fact_verdicts':facts,'unsupported_claims':[],'reason':reason,'candidate_sha256':c['candidate_sha256'],'reference_sha256':fingerprint(ref),'reviewer':'Codex source-passage, raw-output and independent-ASR review; no independent human listening rating','version':'pilot-source-audit-v1'}
   score=evaluate(c,ref,review);save(f/'evaluation/codex-review.json',review);save(f/'evaluation/score-audited.json',score)
   try:
    if old:validate_review(old,c,ref)
   except ValueError as error:judge_errors.append({'job':job,'case':row['id'],'finding':str(error)})
   if old and old.get('fact_verdicts')!=facts:judge_errors.append({'job':job,'case':row['id'],'finding':'The automatic fact verdicts mark an absent answer fact as supported.','automatic_verdicts':old['fact_verdicts'],'source_checked_verdicts':facts})
   audit.append({'job':job,'case':row['id'],'condition':label,'score':score['score'],'state':score['state'],'explanation':reason,'reference_sha256':fingerprint(ref),'candidate_sha256':c['candidate_sha256'],'automatic_review_preserved':True})
 result={'reviewer':'Codex','evaluator_version':VERSION,'distinct_questions':3,'full_bank_run':False,'overall_protocol_status':'not_validated','completed_native_no_gate_questions':3,'complete_native_no_gate_answers':0,'interpretation':'These runs do not establish a usable long-history S1 baseline. The requests remain intelligible to independent ASR, while S1 fails to transcribe two requests in the native-packet check; input format, request recognition and answer generation still need to be separated before drawing conclusions about history retention.','judge_finding':'The automatic judge sometimes marked absent facts as supported, and once marked an empty spoken answer complete; Codex checked every pilot judgment against the source passages and response transcripts. New script checks reject these inconsistent verdicts, while the original verdicts are retained.','audit_scope':'Source evidence, raw S1 fields, independent Parakeet transcripts and waveform measurements; quiet audio still needs listening, and no human listening rating is claimed.','thinking_tokens':'not applicable: no separate native thinking channel','request_output_tokens':'Engine totals are available for the buffered condition (408, 50, 425), including transcription/control text; channel-specific token IDs were not exposed.','amortized_thinking':'not run','full_history_cases':audit,'automatic_judge_findings':judge_errors,'software_checks':46,'software_code_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['s1_eval/core.py','s1_eval/__init__.py','scripts/check_s1_evaluation.py']}}
 save(D/'content-audit.json',result);print(json.dumps({'audited_cases':len(audit),'judge_findings':len(judge_errors),'native_complete_answers':0,'pending_quiet_audio':1}))
if __name__=='__main__':main()
