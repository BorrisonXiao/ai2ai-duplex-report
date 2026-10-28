"""Run saved-output checks, write immutable evidence and refresh progress snapshots."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import tempfile
import threading
import time
from .core import aggregate, evaluate, extract, fingerprint, judge_payload, validate_reference, token_summary, evidence_path

ROOT = Path(__file__).resolve().parents[1]


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n'
    fd, temporary = tempfile.mkstemp(prefix='.' + path.name + '.', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def immutable_json(path, value):
    """Atomically create evidence; repeat ingestion must have identical content."""
    path = Path(path)
    data = json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n'
    fd, temporary = tempfile.mkstemp(prefix='.evidence.', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError:
            if json.loads(path.read_text()) != value:
                raise ValueError('Refusing to overwrite changed evidence: ' + str(path))
    finally:
        os.unlink(temporary)


def load_manifest(path, root):
    manifest = json.loads(path.read_text())
    if manifest.get('schema_version') != 's1-eval-manifest/v1':
        raise ValueError('Unknown evaluation manifest version')
    cases = manifest['cases']
    ids = [case['id'] for case in cases]
    if not cases or len(ids) != len(set(ids)):
        raise ValueError('Evaluation questions must be nonempty and distinct')
    sets = {c['evaluation_set'] for c in cases}
    if len(sets) != 1 or sets != {manifest['evaluation_set']}:
        raise ValueError('Never mix historical checks, fixtures and main evaluation cases')
    if manifest['evaluation_set'] == 'main105' and len(cases) != 105:
        raise ValueError('The main evaluation requires all 105 distinct questions')
    references = json.loads(evidence_path(root, manifest['references']).read_text())
    if set(references) != set(ids):
        raise ValueError('Reference inventory must match every planned case')
    for case in cases:
        validate_reference(references[case['id']], case)
        source = (root / case['source']['path']).resolve()
        if not source.is_relative_to(root.resolve()):
            raise ValueError('Evidence must stay under the declared workspace')
    if manifest['evaluation_set'] == 'main105':
        if any(c['source']['format'] != 'run_record' for c in cases):
            raise ValueError('Main evaluation needs new run records, not historical published traces')
        if manifest.get('expected_model') not in {'Moshi', 'MiniCPM', 'DuplexOmni S1'}:
            raise ValueError('Main evaluation must name the S1 model for this condition')
        inventory = json.loads((root / 'site/research/what-to-think/answer-validation-template.json').read_text())
        if any(q.get('reference_status') != 'verified' or not q.get('validated_answer') for q in inventory['questions']):
            raise ValueError('All 105 reference answers must be validated before main evaluation')
        if manifest.get('frozen_inventory_sha256') != fingerprint(inventory):
            raise ValueError('Main manifest must bind the frozen validated question inventory')
        if any(c['question'] != next(q['question'] for q in inventory['questions'] if q['id'] == c['id']) for c in cases if c['id'] in {q['id'] for q in inventory['questions']}):
            raise ValueError('Main question text differs from the frozen request version')
        if set(ids) != {q['id'] for q in inventory['questions']}:
            raise ValueError('Main evaluation differs from the frozen question inventory')
        if manifest.get('frozen_references_sha256') != fingerprint(references):
            raise ValueError('Main manifest must bind the frozen scoring references')
        for q in inventory['questions']:
            reference = references[q['id']]
            if (reference['answer'] != q['validated_answer'] or
                    reference['required_facts'] != q.get('required_facts') or
                    reference['evidence'] != q.get('evidence')):
                raise ValueError('Scoring reference differs from the frozen answer/facts/evidence')
    return manifest, references


def project_snapshot(project, manifest, summary, state, timestamp):
    """Keep software checks separate from scores over the 105-question bank."""
    updated = dict(project)
    if manifest['evaluation_set'] == 'main105':
        conditions = dict(updated.get('conditions', {}))
        conditions[manifest['condition_id']] = {
            'attempted': summary['attempted'], 'completed': summary['completed_outputs'], 'reviewed': summary['scored'],
            'correct': summary['correct'], 'planned': summary['planned']}
        updated['conditions'] = conditions
        updated['attempted'] = sum(x['attempted'] for x in conditions.values())
        updated['completed_outputs'] = sum(x['completed'] for x in conditions.values())
        updated['reviewed_outputs'] = sum(x['reviewed'] for x in conditions.values())
        updated['correct_outputs'] = sum(x['correct'] for x in conditions.values())
        updated['status'] = state
    else:
        updated['software_checks'] = {
            'status': state, 'evaluation_set': manifest['evaluation_set'],
            'planned': summary['planned'], 'processed': summary['recorded_results'],
            'scored': summary['scored'], 'correct': summary['correct'],
            'scope': 'Earlier real outputs; excluded from the new 105-question evaluation.'}
    updated['last_worker_update'] = timestamp
    updated['updated_at'] = timestamp
    return updated


LIVE_HTML = '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>S1 evaluation progress</title><style>body{font:17px/1.6 system-ui;max-width:850px;margin:30px auto;padding:0 20px}pre{white-space:pre-wrap;overflow-wrap:anywhere}a{color:#087850}</style></head><body><h1>S1 evaluation progress</h1><p>Updates every five seconds from the worker’s saved progress file.</p><ul id="status"><li>Loading the latest update.</li></ul><div id="examples"></div><script>
async function refresh(){try{const r=await fetch('progress.json?t='+Date.now(),{cache:'no-store'});if(!r.ok)throw Error('HTTP '+r.status);const d=await r.json();const age=(Date.now()-Date.parse(d.updated_at))/1000;const lines=['Evaluation set: '+({historical_pipeline_check:'Earlier real outputs (software checks)',main105:'105-question evaluation',script_fixture:'Script checks'}[d.evaluation_set]||d.evaluation_set),'Worker: '+({running:'Evaluating saved outputs',completed:'Finished',failed:'Stopped after an error'}[d.state]||d.state)+((d.state==='running'&&age>60)?' (last update is stale)':''),'Last update: '+d.updated_at,'Processed: '+d.summary.recorded_results+' / '+d.summary.planned,'Scored: '+d.summary.scored+'; correct: '+d.summary.correct,'The scoring worker runs on CPU; model inference is a separate stage.'];const ul=document.getElementById('status');ul.replaceChildren(...lines.map(t=>{const li=document.createElement('li');li.textContent=t;return li}));const el=document.getElementById('examples');el.replaceChildren(...d.examples.map(x=>{const p=document.createElement('p');p.textContent=x.case_id+': '+(x.score===1?'Complete answer':x.score===0?'Does not satisfy the request':'Waiting for a score')+' — '+x.reason;return p}));}catch(e){document.getElementById('status').textContent='Progress unavailable: '+e.message;}}
refresh();setInterval(refresh,5000);
</script></body></html>'''


def run(manifest_path, output, *, root=ROOT, reviews_path=None, project_path=None,
        heartbeat_seconds=30., finalize=False):
    started = time.monotonic()
    manifest, references = load_manifest(manifest_path, root)
    reviews = json.loads(reviews_path.read_text()) if reviews_path else {}
    if set(reviews) - {c['id'] for c in manifest['cases']}:
        raise ValueError('Review contains an unplanned case')
    output.mkdir(parents=True, exist_ok=True)
    immutable_json(output / 'manifest.json', manifest)
    immutable_json(output / ('references-' + fingerprint(references)[:16] + '.json'), references)
    immutable_json(output / ('reviews-' + fingerprint(reviews)[:16] + '.json'), reviews)
    (output / 'live.html').write_text(LIVE_HTML)
    scores, examples, requests = {}, [], []
    lock, stop = threading.Lock(), threading.Event()
    state = 'running'
    journal = output / 'events.jsonl'
    old_events = {json.loads(line)['event_id'] for line in journal.read_text().splitlines()} if journal.exists() else set()

    def write_progress():
        summary = aggregate([c['id'] for c in manifest['cases']], scores, finalize=finalize and state == 'completed')
        stamp = now()
        snapshot = {'schema_version': 's1-eval-progress/v1', 'state': state,
                    'updated_at': stamp, 'evaluation_set': manifest['evaluation_set'],
                    'condition_id': manifest['condition_id'], 'summary': summary,
                    'examples': list(examples), 'gpus': 0, 'active_job': None}
        atomic_json(output / 'progress.json', snapshot)
        if project_path:
            project = json.loads(project_path.read_text())
            atomic_json(project_path, project_snapshot(project, manifest, summary, state, stamp))

    def heartbeat():
        while not stop.wait(heartbeat_seconds):
            with lock:
                write_progress()

    with lock:
        write_progress()
    thread = threading.Thread(target=heartbeat, daemon=True)
    thread.start()
    try:
        for case in manifest['cases']:
            key = case['id']
            folder = output / fingerprint(key)[:16]
            folder.mkdir(exist_ok=True)
            if not (root / case['source']['path']).is_file():
                score = {'case_id': key, 'score': 0 if finalize else None,
                         'state': 'missing' if finalize else 'not_run',
                         'reason': 'No run output exists for this planned question.', 'attempt_recorded': False,
                         'run_status': 'missing', 'complete_input': False}
            else:
                candidate = extract(root, case, folder)
                if manifest.get('expected_model') and candidate['model'] != manifest['expected_model']:
                    raise ValueError('Run model differs from the declared condition')
                immutable_json(folder / 'candidate.json', candidate)
                score = evaluate(candidate, references[key], reviews.get(key))
                name = 'score-' + fingerprint(score)[:16] + '.json'
                immutable_json(folder / name, score)
                request = {'case_id': key, 'candidate_sha256': candidate['candidate_sha256'],
                           'reference_sha256': fingerprint(references[key]),
                           'payload': judge_payload(candidate, references[key])}
                immutable_json(folder / 'judge-input.json', request)
                requests.append(request)
            with lock:
                scores[key] = score
                examples.append({k: score[k] for k in ['case_id', 'score', 'state', 'reason']})
                event = {'kind': 'case_evaluated', 'case_id': key,
                         'score_sha256': fingerprint(score), 'evaluation_set': case['evaluation_set']}
                event['event_id'] = fingerprint(event)
                if event['event_id'] not in old_events:
                    with journal.open('a') as stream:
                        stream.write(json.dumps(dict(event, recorded_at=now())) + '\n')
                        stream.flush()
                        os.fsync(stream.fileno())
                    old_events.add(event['event_id'])
                write_progress()
            print(json.dumps({'case': key, 'state': score['state'], 'score': score['score']}), flush=True)
        state = 'completed'
    except BaseException:
        state = 'failed'
        raise
    finally:
        stop.set()
        thread.join()
        with lock:
            write_progress()
        seconds = time.monotonic() - started
        summary = aggregate([c['id'] for c in manifest['cases']], scores, finalize=finalize and state == 'completed')
        atomic_json(output / 'summary.json', {
            'schema_version': 's1-eval-summary/v1', 'status': state,
            'evaluation_set': manifest['evaluation_set'], 'manifest_sha256': fingerprint(manifest),
            'references_sha256': fingerprint(references), 'reviews_sha256': fingerprint(reviews),
            'summary': summary, 'token_summary': token_summary(scores), 'results': scores, 'wall_seconds': seconds,
            'cases_per_second': len(scores) / seconds if seconds else None,
            'gpus': 0, 'maximum_active_gpus': 0, 'GPU_roles': {}, 'shared_components': [], 'dependencies': []})
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('evaluate')
    p.add_argument('--manifest', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--reviews', type=Path)
    p.add_argument('--root', type=Path, default=ROOT)
    p.add_argument('--project-progress', type=Path)
    p.add_argument('--finalize', action='store_true')
    p = sub.add_parser('serve')
    p.add_argument('--directory', type=Path, required=True)
    p.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    if args.command == 'evaluate':
        print(json.dumps(run(args.manifest, args.output, root=args.root, reviews_path=args.reviews,
                             project_path=args.project_progress, finalize=args.finalize), indent=2))
    else:
        print(f'Local progress: http://127.0.0.1:{args.port}/live.html', flush=True)
        ThreadingHTTPServer(('127.0.0.1', args.port),
                            partial(SimpleHTTPRequestHandler, directory=str(args.directory.resolve()))).serve_forever()


if __name__ == '__main__':
    main()
