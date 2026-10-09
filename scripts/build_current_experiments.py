"""Generate the current E1/E2 pages and keep historical runs in the archive."""
from html import escape
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path(os.environ.get('HTML_REPORT_SKILL_DIR',Path.home()/'.codex/skills/html-report'))))
import htmlkit as hk
from site_navigation import project_tabs


def table(headers,rows):
    return '<div class="study-table-scroll"><table><thead><tr>'+''.join('<th>'+escape(h)+'</th>' for h in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+escape(str(v))+'</td>' for v in row)+'</tr>' for row in rows)+'</tbody></table></div>'


def version_assets(page):
    for asset in ['assets/site.css','assets/trajectory/viewer.css','assets/trajectory/viewer.js']:
        digest=hashlib.sha256((ROOT/asset).read_bytes()).hexdigest()[:12]
        page=page.replace('"../'+asset+'"','"../'+asset+'?v='+digest+'"')
    return page


def viewer(group,filename,title,description):
    bundle=json.loads((ROOT/f'research/current-{group}.json').read_text())
    study=bundle['study'];rows=[r for r in study['conditions'] if r['experiment_group']==group]
    initial=rows[0]['initial_request']
    intro='<section class="section" aria-labelledby="input-title"><h2 id="input-title">The user request</h2><blockquote class="example-answer">'+escape(initial)+'</blockquote>'
    if group=='handoff':
        intro+='<p>Exactly one complete user request is supplied in both conditions. E1a disables S2. E1b invokes S2 once after the request, while S1 continues processing. This is a controlled handoff test.</p>'
    else:
        intro+='<p>Both conditions use one initial request with S2 disabled. E2b adds one correction while S1 is speaking: <strong>'+escape(rows[1]['correction'])+'</strong> E2a provides the matched uninterrupted control.</p>'
    verdicts=' '.join(r['id']+': '+r['finding'] for r in rows if r.get('finding'))
    message=verdicts or 'Input previews are available now. Audited model playback appears when available.'
    intro+='<div class="callout amber"><strong>Current attempt · '+escape(study['status'].replace('_',' '))+'</strong><p>GPU job '+study['gpu_job_id']+' · CPU audit '+study['cpu_followup_job_id']+'. '+escape(message)+' <a href="controlled-study.html">See execution status and pass criteria</a>.</p></div></section>'
    replacements={'TITLE':title,'DESCRIPTION':description,'NAV':project_tabs('experiments','../'),
       'EXAMPLE_INTRO':intro,'EXAMPLE':json.dumps(bundle,ensure_ascii=False).replace('<','\\u003c'),
       'DATA_URL':f'../research/current-{group}.json',
       'OTHER_EXPERIMENT':'<a href="interruption.html">E2 · S1 interruption</a>' if group=='handoff' else '<a href="handoff.html">E1 · Single-request handoff</a>'}
    page=(ROOT/'scripts/templates/current_trajectory.html.in').read_text()
    for key,value in replacements.items():page=page.replace('{{'+key+'}}',value)
    if (ROOT/'research/current-s1.json').exists():
        page=page.replace('Current controlled study ·','Earlier controlled study ·').replace('Current attempt ·','Earlier attempt ·')
    assert '{{' not in page
    (ROOT/'experiments'/filename).write_text(version_assets(page))


def overview(study):
    status=study['status']
    lede={'queued':'The corrected run is queued; model results are pending.',
          'running':'The corrected run is executing; audited results are pending.',
          'failed':'The current attempt failed; inspect the attempt record before interpreting behavior.',
          'blocked':'Runtime qualification blocked the behavioral cases.',
          'completed':'The run completed; inspect the audit and played audio before declaring a behavioral pass.',
          'completed_with_behavior_failures':'The three-GPU layout passed runtime qualification. All four cases ran, but no task-level behavioral pass was demonstrated.'}[status]
    body=hk.hero('Earlier study · 8 October 2026','E1 handoff and E2 interruption',lede)
    body+=hk.section('1 · Current status',body='<p><a href="index.html">All experiments</a> · <a href="trajectory.html">E1 · Single-request handoff</a> · <a href="interruption.html">E2 · S1 interruption</a> · <a href="archive.html">Historical archive</a></p><p>Current GPU job <b>'+study['gpu_job_id']+'</b>, CPU follow-up <b>'+study['cpu_followup_job_id']+'</b>. '+escape(study['primary_layout'])+'. The job selects the smallest qualifying layout before running the behavioral cases. A measured contention failure permits the sequential three-H100 layout, with S2 on GPU 2; maximum three GPUs and no GPU overlap.</p>')
    rows=[]
    for c in study['conditions']:
        metric=c.get('metrics') or {}
        finding=('S2 requests: '+str(metric['s2_requests'])+'; guidance delivered: '+str(metric['complete_guidance_deliveries'])+'; content review required') if metric else 'Model results pending'
        finding=c.get('finding',finding)
        rows.append((c['id'],c['name'],c.get('verdict',c['status']),finding))
    body+=hk.section('2 · Conditions and results',body=hk.labeled_asset(table(['ID','Condition','Execution state','Observed result'],rows),'Table',1,'E1a/E1b share one bread request. E2a/E2b share one pet request; E2b adds an explicit user correction. Job identifiers name attempts rather than experiments.'))
    q=study['qualification'];criteria=study['qualification_criteria']
    if q:
        qr=[('Without S2 load',f"{q['baseline']['p95_s1_seconds']:.3f}",f"{q['baseline']['p95_talker_seconds']:.3f}",q['baseline_pass']),
            ('With S2 load',f"{q['with_s2_load']['p95_s1_seconds']:.3f}",f"{q['with_s2_load']['p95_talker_seconds']:.3f}",q['loaded_absolute_pass'])]
        note='Qualification verdict: '+q['status']+'. S2 load coverage '+f"{q['s2_load_interval_fraction']:.1%}"+'.'
    else:
        qr=[('Without S2 load','Pending','Pending','Pending'),('With S2 load','Pending','Pending','Pending')]
        note='Runtime qualification is pending. Behavioral interpretation waits for a qualified layout.'
    body+=hk.section('3 · Runtime qualification',body=hk.labeled_asset(table(['Matched condition','S1 p95 (s)','Talker p95 (s)','Absolute gates pass'],qr),'Table',2,note)+'<p>Required: p95 S1 and Talker latency at most 0.384 seconds; input/speech queues at most 0.480 seconds; added p95 latency at most the larger of 30 ms or 25% of the baseline. At least 20 samples and 80% S2 request coverage are required. Warmup, CUDA graphs, bounded decoding and CPU thread limits are fixed across the controls.</p>')
    if study.get('shared_gpu_qualification'):
        shared=study['shared_gpu_qualification']
        body+=hk.section('Why the third GPU was needed',body='<p>On two H100s, S2 shared the speech GPU. Talker p95 rose from '+f"{shared['baseline']['p95_talker_seconds']:.3f}"+' to '+f"{shared['with_s2_load']['p95_talker_seconds']:.3f}"+' seconds under sustained S2 load, with a '+f"{shared['with_s2_load']['max_speech_queue_delay_seconds']:.3f}"+'-second speech queue. Those cases were blocked before behavior was interpreted. Moving S2 to GPU 2 kept Talker p95 near 0.256 seconds and its queue below 10 ms in the loaded calibration.</p>')
    attempts=[(a['job_id'],a['status'],a['stage'],a['finding'],'Pending' if a['allocated_gpu_hours'] is None else f"{a['allocated_gpu_hours']:.4f}") for a in study['attempts']]
    body+=hk.section('4 · Attempt history',body=hk.labeled_asset(table(['Job','State','Stage','Finding','GPU hours'],attempts),'Table',3,'Failed or superseded attempts are retained once here. They are not selectable current examples or successful experiment results.'))
    body+=hk.section('5 · Validation and source',body='<p>The observed malformed S1 field key now has a narrow, audited recovery path. Twenty-five parser checks preserve speech/control values and reject incomplete or unsafe repairs; the paced CPU regression also checks handoff, THINK history retention, STOP invalidation and provider failures.</p><p>The authored input uses the same Flite synthetic voice in all conditions, with complete prompts and fixed margins. Independent CPU transcription verifies each request. The input contains no reference assistant reply. <a href="../research/flite/COPYING">Flite attribution</a> · <a href="../research/current-study.json">Exact study record</a>.</p><p>Software PCM replay and client request timing do not establish physical microphone/loudspeaker latency. Forced S2 tests handoff rather than autonomous delegation. Correct answers and graceful interruption require review of actual played speech.</p>')
    style='<style>.study-table-scroll{max-width:100%;overflow-x:auto}.study-table-scroll table{min-width:650px}.study-table-scroll th,.study-table-scroll td{text-align:left!important}</style>'
    full,_=hk.document('Current controlled duplex study',body,head_html=style)
    (ROOT/'experiments/controlled-study.html').write_text(full)


def collection():
    cards=[('E1','Single-request handoff','One bread question. Compare S2 disabled with S2 forced once.','trajectory.html','Open E1'),
           ('E2','S1 interruption','One pet request plus an explicit correction during speech. S2 is disabled.','interruption.html','Open E2'),
           ('Study record','Status and qualification','Current attempts, readable condition IDs, latency gates and audit results.','controlled-study.html','View study status'),
           ('Archive','Historical diagnostics','The earlier multi-turn budget recordings, decoder variants and text-only diagnostics.','archive.html','Browse archive')]
    rows=''.join('<article class="card"><span class="tag">'+a+'</span><h3>'+b+'</h3><p>'+c+'</p><p><a class="button" href="'+d+'">'+e+'</a></p></article>' for a,b,c,d,e in cards)
    page='<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="description" content="Current controlled duplex experiments, results and historical archive."><title>Experiments · AI2AI Duplex</title><link rel="stylesheet" href="../assets/site.css"></head><body><header class="site-nav"><div class="nav-inner"><a class="brand" href="../index.html">AI2AI Duplex</a>'+project_tabs('experiments','../')+'</div></header><main><div class="container"><header class="hero"><p class="eyebrow">Experiments · 8 October 2026</p><h1>Two controlled experiments.</h1><p class="lede">E1 isolates S1/S2 handoff with a single request. E2 isolates S1 interruption handling. Choose an experiment, then compare its matched conditions.</p></header><section class="section"><h2>Current study and archive</h2><div class="card-grid">'+rows+'</div></section></div></main></body></html>'
    (ROOT/'experiments/index.html').write_text(version_assets(page))
    archive='<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="description" content="Superseded duplex diagnostics retained for provenance."><title>Historical experiment archive · AI2AI Duplex</title><link rel="stylesheet" href="../assets/site.css"></head><body><header class="site-nav"><div class="nav-inner"><a class="brand" href="../index.html">AI2AI Duplex</a>'+project_tabs('experiments','../')+'</div></header><main><div class="container"><header class="hero"><p class="eyebrow">Historical archive</p><h1>Superseded diagnostics.</h1><p class="lede">These runs explain earlier fixes and failure modes. The current examples are E1 and E2.</p><p><a href="index.html">All current experiments</a></p></header><section class="section"><h2>Earlier evidence</h2><div class="card-grid"><article class="card"><h3>Multi-turn timing and decoding</h3><p>Earlier budget conversation, A100/H100 comparisons and S2 continuation diagnostics. Archived condition labels A01–A06 retain their original job IDs.</p><p><a class="button" href="archive-budget.html">Open archived replay</a></p></article><article class="card"><h3>Timing and decoder audit</h3><p>The earlier evidence audit remains available with its original measurements and limitations.</p><p><a class="button" href="interaction-review.html">Read archived audit</a></p></article></div></section></div></main></body></html>'
    (ROOT/'experiments/archive.html').write_text(version_assets(archive))


def main():
    study=json.loads((ROOT/'research/current-study.json').read_text())
    viewer('handoff','handoff.html','E1 · Earlier single-request handoff','One complete bread question, with S2 disabled or forced once; earlier failed study.')
    viewer('interruption','archive-interruption.html' if (ROOT/'research/current-natural.json').exists() else 'interruption.html','E2 · Earlier S1 interruption','One pet request and a correction during speech; earlier failed study, S2 disabled.')
    overview(study);collection()
    if (ROOT/'research/current-s1.json').exists():
        from build_s1_baseline import main as build_s1
        build_s1()
        page=ROOT/'experiments/controlled-study.html'
        page.write_text(page.read_text().replace('href="trajectory.html">E1','href="handoff.html">E1').replace('Current GPU job','Earlier GPU job'))
        archive=ROOT/'experiments/archive.html'
        text=archive.read_text().replace('The current examples are E1 and E2.','The current S1-only baseline is separate. Earlier E1/E2 controls and the budget diagnostics remain here as historical evidence.')
        text=text.replace('<h2>Earlier evidence</h2>','<h2>Earlier evidence</h2><p><a href="handoff.html">E1 · Earlier bread/S2 replay</a> · <a href="interruption.html">E2 · Earlier interruption replay</a> · <a href="controlled-study.html">Earlier E1/E2 review</a></p>')
        archive.write_text(text)
    if (ROOT/'research/current-natural.json').exists():
        basic=ROOT/'experiments/single-request.html'
        basic.write_text((ROOT/'experiments/trajectory.html').read_text())
        for name in ['handoff.html','controlled-study.html','archive.html','s1-investigation.html']:
            page=ROOT/'experiments'/name
            page.write_text(page.read_text().replace('href="interruption.html"','href="archive-interruption.html"'))
        page=ROOT/'experiments/s1-investigation.html'
        page.write_text(page.read_text().replace('href="trajectory.html"','href="single-request.html"'))
        from build_natural_interruption import main as build_natural
        build_natural()
    print('Built current E1/E2 viewers, study status, collection and archive.')


if __name__=='__main__':main()
