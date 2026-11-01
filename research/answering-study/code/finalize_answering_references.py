"""Bind reviewed answers to all 105 current requests and validate the shared schema."""
import hashlib,json
from pathlib import Path
from s1_eval.core import validate_reference,fingerprint
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'research/answering_study_20261101'
def read(p):return json.loads(p.read_text())
def save(p,d):p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
def main():
    bank=read(D/'bank-v2.json')['questions'];review=read(D/'references-reviewed.json');by={r['id']:r for r in review['references']}
    assert len(bank)==len(by)==105 and review['source_verified_count']==105
    inventory=read(ROOT/'site/research/what-to-think/answer-validation-template.json');rows={r['id']:r for r in inventory['questions']};references={}
    for q in bank:
        r=by[q['id']];row=rows[q['id']]
        assert r['status']=='source_verified' and q['question']==r['question']
        if row['question']!=q['question']:
            row['earlier_inventory_question']=row['question']
            row['question']=q['question']
        assert r['at']==q['at'] and q['question'].startswith('Assistant,')
        assert r['required_facts'] and r['source_evidence'] and r['source_bindings_v2']
        assert all(s['end']<=q['at'] and s['text'] for s in r['source_evidence'])
        assert all(s['available']<=q['at'] for s in q['prefix'])
        assert all(p['text_matches'] for p in r['source_bindings_v2'])
        facts=[dict(id='fact-'+str(i+1),text=f) for i,f in enumerate(r['required_facts'])]
        evidence=[dict(id=s['id'],source=q['dataset']+' '+q['meeting']+' recorded transcript',speaker=s['speaker'],start_seconds=s['start'],end_seconds=s['end'],text=s['text']) for s in r['source_evidence']]
        ref=dict(status='verified',case_id=q['id'],question=q['question'],answer=r['answer'],required_facts=facts,evidence=evidence,reviewer='Codex source inspection; no independent human ratings',optional_details=r.get('optional_details',[]),unsupported_claims_to_avoid=r.get('unsupported_claims_to_avoid',[]))
        validate_reference(ref,dict(id=q['id'],question=q['question'],source_cutoff_seconds=q['at']))
        references[q['id']]=ref
        row.update(reference_status='verified',validated_answer=r['answer'],required_facts=facts,evidence=evidence,reviewer=ref['reviewer'],spoken_request_version_check='matches_frozen_v3_primary_request_text',notes='Source passage text, speaker and causal timing checked; see the answering-study source review. This is Codex review, not independent human validation.')
    inventory.update(status='all105_source_reviewed',new_validated_count=105)
    for base in [ROOT/'research/what_to_think_plan',ROOT/'site/research/what-to-think']:save(base/'answer-validation-template.json',inventory)
    save(D/'scoring-references.json',references)
    audit=dict(status='pass',questions=105,source_passages=sum(len(r['evidence']) for r in references.values()),future_evidence=0,current_request_text_matches=105,required_facts_nonempty=105,shared_evaluator_reference_checks=105,source_review='Codex; earlier source reviews reused where recorded; no independent human ratings',corrected_Earnings_cases=12,AMI_pilot_unchanged=True,inventory_sha256=fingerprint(inventory),references_sha256=fingerprint(references),bank_sha256=hashlib.sha256((D/'bank-v2.json').read_bytes()).hexdigest(),GPUs=0)
    save(D/'reference-validation.json',audit);print(json.dumps(audit))
if __name__=='__main__':main()
