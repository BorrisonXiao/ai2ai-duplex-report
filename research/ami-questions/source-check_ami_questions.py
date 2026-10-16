"""CPU invariants that matter for causal question evaluation and label isolation."""
import copy
import json
from pathlib import Path
import ami_question_pilot as p
from ami_question_refinement import inclusive_reader_messages

def main():
    p.check_inputs()
    windows=json.loads((p.SNAP/'windows.json').read_text())
    authored=json.loads((p.ROOT/'research/ami_questions/authored.json').read_text())
    by={w['id']:w for w in windows}
    for w in windows:
        assert all(c['end']<=c['available']<=w['at'] for c in w['prefix'])
        assert all(c['speaker'] in ['A','B','C'] for c in w['prefix'])
        assert w['source_silence_remaining_seconds']>0
        assert 'formal_metadata' in w['role_status']
        assert set(w['role_evidence'])<={c['id'] for c in w['prefix']}
    for q in authored:
        w=by[q['window_id']]
        assert not p.validate(q,w)
        bad=copy.deepcopy(q);bad['evidence_ids'].append('future-injected-chunk')
        assert 'unknown_or_future_evidence' in p.validate(bad,w)
        sentinel='HIDDEN_REFERENCE_SHOULD_NEVER_APPEAR_9ac41'
        poisoned=dict(q,answer=sentinel,claims=sentinel,evidence=sentinel,review=sentinel,role_reason=sentinel)
        for condition in ['full_prefix','recent_60s','question_only','evidence_removed']:
            messages=p.reader_messages(poisoned,w,condition)
            assert sentinel not in json.dumps(messages)
            assert sentinel not in json.dumps(inclusive_reader_messages(poisoned,w,condition))
        full=p.reader_messages(q,w,'full_prefix')[1]['content']
        removed=p.reader_messages(q,w,'evidence_removed')[1]['content']
        for id_ in q['evidence_ids']:
            assert id_ in full and id_ not in removed
        recent=p.reader_messages(q,w,'recent_60s')[1]['content']
        for c in w['prefix']:
            assert (c['id'] in recent)==(c['start']>=w['at']-60)
        recent_inclusive=inclusive_reader_messages(q,w,'recent_60s')[1]['content']
        for c in w['prefix']:
            assert (c['id'] in recent_inclusive)==(c['end']>=w['at']-60)
    assert p.parse_final('<think>private {"x":1}',True)==(None,'')
    assert p.parse_final('private</think>{"questions":[]}',True)[0]=={'questions':[]}
    assert p.parse_final('```json\n{"answer":"ok"}\n```')[0]=={'answer':'ok'}
    print(json.dumps(dict(status='pass',gpus=0,cutoffs=4,authored=8,
         checks=['prefix availability','role provenance','nonword injection gaps','future citation rejection','hidden-label sentinel isolation in four reader conditions','exact ablation contexts','private reasoning exclusion'])))

if __name__=='__main__':main()
