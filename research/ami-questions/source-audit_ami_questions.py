"""Assemble evidence and explicit review decisions for the AMI text pilot.

No automatic correctness score is inferred from an LLM's answerability flag.
"""
from __future__ import annotations
import collections
import copy
import hashlib
import json
from pathlib import Path
import re
import sys
import ami_question_pilot as pilot

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'research/ami_questions'
JOBS=['1110768','1110785','1111068']

def read_lines(path):
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()] if path.exists() else []

def assemble():
    windows={w['id']:w for w in json.loads((pilot.SNAP/'windows.json').read_text())}
    authored=json.loads((OUT/'authored.json').read_text())
    candidates=[];calls=[];readbacks=[];completions=[]
    for job in JOBS:
        base=pilot.BASE/('job_'+job)
        for model in pilot.MODELS:
            path=base/(model+'_candidates.json')
            if path.exists():candidates+=json.loads(path.read_text())
        calls += [dict(r,job_id=job) for r in read_lines(base/'generation_calls.jsonl')]
        readbacks += [dict(r,job_id=job) for r in read_lines(base/'readback.jsonl')]
        if (base/'completion.json').exists():completions.append(json.loads((base/'completion.json').read_text()))
    candidates += authored
    assert len({q['id'] for q in candidates})==len(candidates)
    candidate_map={q['id']:q for q in candidates}
    for row in readbacks:
        q=candidate_map[row['question_id']];w=windows[q['window_id']];context=w['prefix']
        if row['condition']=='recent_60s':
            context=[c for c in context if (c['end'] if row.get('recent_window_semantics') else c['start'])>=w['at']-60]
        elif row['condition']=='question_only':context=[]
        elif row['condition']=='evidence_removed':context=[c for c in context if c['id'] not in q.get('evidence_ids',[])]
        visible={c['id'] for c in context};response=row.get('response');flags=[]
        if not isinstance(response,dict):flags.append('unparsed_reader_output')
        elif not isinstance(response.get('evidence_ids'),list):flags.append('invalid_evidence_ids_schema')
        elif any(id_ not in visible for id_ in response['evidence_ids']):flags.append('reader_citation_outside_visible_context')
        if row.get('finish_reason')=='length':flags.append('reader_token_limit')
        row['validation_errors']=flags
        row['answer_text_for_review']=response.get('answer','') if isinstance(response,dict) else ''
        row['answer_extraction']='parsed_object' if isinstance(response,dict) else 'unavailable'
        if not row['answer_text_for_review']:
            match=re.search(r'"answer"\s*:\s*',row.get('final_text',''))
            if match:
                try:
                    value,_=json.JSONDecoder().raw_decode(row['final_text'][match.end():])
                    if isinstance(value,str):
                        row['answer_text_for_review']=value
                        row['answer_extraction']='complete_json_string_field_from_incomplete_object'
                except json.JSONDecodeError:pass
    reviews=json.loads((OUT/'reviews.json').read_text()) if (OUT/'reviews.json').exists() else []
    by_review={r['id']:r for r in reviews}
    reader_review_path=OUT/'reader_content_reviews.json'
    reader_reviews={r['id']:r for r in json.loads(reader_review_path.read_text())['cases']} if reader_review_path.exists() else {}
    by_read=collections.defaultdict(dict)
    for r in readbacks:
        # Authored examples are repeated across jobs; retain both for audit.
        by_read[r['question_id']][r['job_id']+':'+r['condition']]=r
    all_records=[];accepted=[]
    for q in candidates:
        w=windows[q['window_id']]
        errors=pilot.validate(q,w)
        if q.get('validation_errors'):
            errors=sorted(set(errors+q['validation_errors']))
        evidence=[c for c in w['prefix'] if c['id'] in q.get('evidence_ids',[])]
        r=dict(q,validation_errors=errors,requester_perspective=w['perspective'],role_status=w['role_status'],
               evidence=evidence,review=by_review.get(q['id'],dict(decision='pending',note='No content verdict yet.')),
               readbacks=by_read[q['id']],source_meeting='EN2003a',injection_mode='pause_insert_question_answer_resume',
               reference_status='synthetic_assistant_reviewed_reference_not_original_AMI_gold')
        if q['id'] in reader_reviews:r['reader_content_review']=reader_reviews[q['id']]
        r['replay_source_time_seconds']=1578.92 if q['window_id']=='W3' else q['at']
        if q['window_id']=='W3':
            r['replay_timing_note']='Generation and reader probes use 1489.99 s, a word gap within an unfinished sentence. Planned replay moves to 1578.92 s after a complete sentence. Review of intervening speech finds no revision of the cited outreach facts; no speech replay has run.'
        all_records.append(r)
        if r['review']['decision']=='accept':
            assert not errors,(q['id'],errors)
            assert r['review'].get('history_essential') is True
            assert r['review'].get('reference_supported') is True
            accepted.append(r)
    grouped={}
    for key in sorted({(r.get('model','assistant_authored'),r.get('prompt_variant','authored')) for r in candidates}):
        rows=[r for r in all_records if (r.get('model','assistant_authored'),r.get('prompt_variant','authored'))==key]
        g_calls=[c for c in calls if (c['model'],c['variant'])==key]
        grouped[' / '.join(key)] = dict(candidates=len(rows),expected_candidates=2*len(g_calls) if g_calls else len(rows),
            generation_calls=len(g_calls),truncated_calls=sum(c['finish_reason']=='length' for c in g_calls),
            unparseable_calls=sum(not c['parse_ok'] for c in g_calls),schema_valid=sum(not r['validation_errors'] for r in rows),
            decisions=dict(collections.Counter(r['review']['decision'] for r in rows)),
            generation_tokens=sum(c['output_tokens'] for c in g_calls),generation_wall_seconds=sum(c['wall_seconds'] for c in g_calls))
    raw_accepted=len(accepted)
    edits=json.loads((OUT/'reference_edits.json').read_text()) if (OUT/'reference_edits.json').exists() else []
    raw_records={r['id']:r for r in all_records}
    for edit in edits:
        source=raw_records[edit['source_id']];r=copy.deepcopy(source);assert edit['question_unchanged'] is True
        r.update(id=edit['id'],source_candidate_id=source['id'],origin='local_model_with_assistant_reference_edit',
                 annotation_provenance='Question verbatim; reference and rationale edited by primary assistant.',
                 review=dict(decision='accept',reviewer='primary_assistant',history_essential=True,reference_supported=True,note=edit['review_note'],intent_group=edit.get('intent_group',edit['id'])))
        for key in ['answer','claims','evidence_ids','history_reason']:r[key]=edit[key]
        w=windows[r['window_id']];r['evidence']=[c for c in w['prefix'] if c['id'] in r['evidence_ids']]
        r['validation_errors']=pilot.validate(r,w);assert not r['validation_errors']
        assert r['question']==source['question']
        if r['id'] in reader_reviews:r['reader_content_review']=reader_reviews[r['id']]
        all_records.append(r);accepted.append(r)
    accounting=json.loads((OUT/'accounting.json').read_text()) if (OUT/'accounting.json').exists() else None
    audit=dict(date='2026-10-16',status='content_review_complete' if len(reviews)==len(candidates) and len(completions)==len(JOBS) else 'in_progress',
        scope='One meeting, four development prefixes; text synthesis and reader diagnostics, no speech-model evaluation or generalization claim.',
        candidates=len(all_records),raw_candidates=len(candidates),accepted=len(accepted),raw_accepted=raw_accepted,
        reference_edited=len(edits),reviews=len(reviews)+len(edits),raw_reviews=len(reviews),groups=grouped,
        reader_calls=len(readbacks),completed_jobs=[x['job_id'] for x in completions],resources=dict(gpus_per_job=1,
        gpu_type='H100 SXM 80 GB',gpu_0='Sequential 4B generation, 30B generation, 4B reading',
        shared='One text model at a time; no S1/ASR/TTS.',dependencies='1110785 afterok:1110768; 1111068 afterok:1110785; internal stages sequential',max_gpus_active=1,
        per_job={'1110768':'4B Instruct generator, 30B Thinking generator and 4B reader sequentially on GPU 0',
                 '1110785':'4B Instruct generator, 30B Thinking generator and 4B reader sequentially on GPU 0',
                 '1111068':'4B Instruct packet generator and reader reuse one GPU 0 vLLM engine sequentially; no 30B model'}),
        accounting=accounting,limitations=['Same-model reading of 4B questions is flagged; no LLM reader is an oracle.',
        'Assistant review is not independent human annotation.','Prompt refinement and selection share these development prefixes.',
        'EN2003a has no formal metadata roles.','Sentence-release timing conservatively withholds incomplete utterances.',
        'No TTS or live streaming behavior was evaluated.'])
    audit['reader_diagnostics']={job:dict(calls=sum(r['job_id']==job for r in readbacks),
        unparsed=sum(r['job_id']==job and r['response'] is None for r in readbacks),
        token_limited=sum(r['job_id']==job and r['finish_reason']=='length' for r in readbacks),
        invalid_citations=sum(r['job_id']==job and 'reader_citation_outside_visible_context' in r['validation_errors'] for r in readbacks)) for job in JOBS}
    if set(['1110768','1110785'])<={x['job_id'] for x in completions} and len(reviews)==len(candidates) and '1111068' not in {x['job_id'] for x in completions}:
        audit['status']='primary_complete_packet_trial_pending'
    audit['pending_optional_job']='1111068' if '1111068' not in {x['job_id'] for x in completions} else None
    audit['accepted_intent_groups']=len({r['review'].get('intent_group',r['id']) for r in accepted})
    audit['generation_throughput']={}
    for job in JOBS:
        for model in ['instruct','thinking']:
            rows=[c for c in calls if c['job_id']==job and c['model']==model]
            if rows:
                tokens=sum(c['output_tokens'] for c in rows);seconds=sum(c['wall_seconds'] for c in rows)
                audit['generation_throughput'][job+'/'+model]=dict(output_tokens=tokens,wall_seconds=seconds,tokens_per_second=tokens/seconds,
                    note='Measured generation calls, including prefill; Thinking token totals include private reasoning. Prompts/lengths/settings differ across jobs.')
    pilot.write(OUT/'audit.json',audit)
    pilot.write(OUT/'all_candidates.json',all_records)
    pilot.write(OUT/'accepted.json',accepted)
    # The model input export deliberately cannot contain answer/evidence/review.
    requests=[dict(id=r['id'],meeting='EN2003a',source_time_seconds=r['replay_source_time_seconds'],requester=r['requester'],recipient='meeting_assistant',
                   question=r['question'],mode='pause_insert_question_answer_resume',requester_identity_condition='explicit_oracle_label',
                   prefix_window_id=r['window_id'],question_tts=None) for r in accepted]
    refs=[dict(id=r['id'],answer=r['answer'],claims=r['claims'],evidence=r['evidence'],review=r['review'],reference_tts=None) for r in accepted]
    for name,rows in [('requests.jsonl',requests),('references.jsonl',refs)]:
        (OUT/name).write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
    for r in requests:
        assert not (set(r)&{'answer','claims','evidence','review','reference_tts'})
    chunks=json.loads((ROOT/'exp/prethinking_pilot/data/chunks.json').read_text())
    replay_windows=[]
    for w in windows.values():
        at=1578.92 if w['id']=='W3' else w['at']
        prefix=[{k:c[k] for k in ['id','speaker','start','end','available','text','boundary']} for c in chunks if c['available']<=at]
        assert all(c['end']<=c['available']<=at for c in prefix)
        assert not any(word['start']<at<word['end'] for c in chunks for word in c['words'] if not word.get('punctuation'))
        replay_windows.append(dict(id=w['id'],source_time_seconds=at,generation_source_time_seconds=w['at'],prefix=prefix,
            status='planned_text_replay_context_not_executed_audio',timing_note='W3 moved after a complete sentence; all original generation/readback traces preserve the earlier cutoff.' if w['id']=='W3' else 'Original generation cutoff retained.'))
    pilot.write(OUT/'replay_windows.json',replay_windows)
    pilot.write(OUT/'generation_calls.json',[{k:v for k,v in c.items() if k!='final_text'} for c in calls])
    print(json.dumps(dict(status=audit['status'],raw_candidates=len(candidates),display_records=len(all_records),accepted=len(accepted),readbacks=len(readbacks),raw_reviews=len(reviews),reference_edits=len(edits))))

if __name__=='__main__':assemble()
