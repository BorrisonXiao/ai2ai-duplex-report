"""Build the current S1-only baseline and its evidence-backed investigation."""
from html import escape
import json
from pathlib import Path

from build_current_experiments import ROOT, hk, project_tabs, table, version_assets

def main():
    bundle=json.loads((ROOT/'research/current-s1.json').read_text())
    review=json.loads((ROOT/'research/s1-single-review.json').read_text())
    intro='<section class="section"><h2>One request; S1 only</h2><blockquote id="current-request" class="example-answer">What color is the sky on a clear day?</blockquote><p>The default control contains one complete factual question. S1 answers it aloud with S2 entirely absent. The second control asks S1 to repeat one sentence. Both use the native training-style prompt and preserve raw model replies in history.</p><div class="callout"><strong>Spoken answers verified · job '+review['job_id']+'</strong><p>Independent transcription matches both generated answers. No self-introduction or S2 request appears. One A100 80 GB hosts Thinker, Talker, MTP and Code2Wav; p95 S1 time is 0.369 s for the factual control, below the 0.480 s packet tick. <a href="s1-investigation.html">Read the investigation, remaining bread failure and evidence limits</a>.</p></div></section>'
    replacements={'TITLE':'S1 · Single-request baseline','DESCRIPTION':'Verified speech for one factual question, with S2 entirely disabled.',
        'NAV':project_tabs('experiments','../'),'EXAMPLE_INTRO':intro,
        'EXAMPLE':json.dumps(bundle,ensure_ascii=False).replace('<','\\u003c'),'DATA_URL':'../research/current-s1.json',
        'OTHER_EXPERIMENT':'<a href="s1-investigation.html">S1 investigation</a>'}
    page=(ROOT/'scripts/templates/current_trajectory.html.in').read_text()
    for key,value in replacements.items():page=page.replace('{{'+key+'}}',value)
    page=page.replace('Current controlled study · 8 October 2026','S1-only baseline · 8 October 2026')
    page=page.replace('<a href="controlled-study.html">Study status and criteria</a>','<a href="s1-investigation.html">Investigation and validation</a>')
    page=page.replace('../research/current-study.json','../research/s1-single-review.json')
    page=page.replace('Input, S1, S2 and Talker events when the run has completed.','Captured S1 requests and actual model audio; S2 is absent.')
    page=page.replace('Input previews contain authored synthetic speech. Completed replays contain actual model playback;','Authored synthetic user speech and actual model playback;')
    assert '{{' not in page
    (ROOT/'experiments/trajectory.html').write_text(version_assets(page))
    body='<header class="site-nav"><div class="nav-inner"><a class="brand" href="../index.html">AI2AI Duplex</a>'+project_tabs('experiments','../')+'</div></header>'
    body+=hk.hero('Investigation · 8 October 2026','S1 answers basic single requests.','The earlier blanket failure claim was too broad. Two basic spoken controls now pass; the bread-recipe silence remains unresolved.')
    body+=hk.section('What went wrong',body='<p>The failed example was a 480 ms streaming test. Its custom English prompt caused a startup greeting on the first packet, while the user was asking the question. The greeting was actual model output. The controlled harness also rewrote assistant replies into JSON, unlike the author harness, which retains raw replies. Changing history serialization alone does not repair the bread failure.</p><p>The authors provide <a href="https://github.com/MuyeHuang/DuplexOmni/blob/main/inference_framework/realtime_serving/simulate_v8.py">an offline simulation harness</a> and <a href="https://github.com/MuyeHuang/DuplexOmni/blob/main/inference_framework/realtime_serving/omni_realtime_server.py">a realtime server</a>. Their current source is commit 33bfba1, matching our local checkout. We ran the actual simulation loop and orchestrator, with S2 dispatch disabled and the local audio-only runtime. Stock simulation settings still give silence on the bread and repeat requests. A native patience/short-clear prompt with temperature 0 gives responsive speech for the repeat and factual controls.</p><p>That configuration fixes the two basic controls. The audio comparison changes prompt and temperature together; it does not isolate every causal contribution. S1 cannot yet be described as robust, and recipe generation has not been fixed.</p>')
    rows=[]
    for c in review['cases']:
        label={'bread_author_reference':'Bread · stock simulation settings','repeat_author_reference':'Repeat · stock simulation settings','repeat_native_prompt':'Repeat · native baseline','sky_native_prompt':'Factual question · native baseline'}[c['case']]
        rows.append((label,'Spoken answer verified' if c['spoken_basic_answer_verified'] else 'Silent answer',c['generated_tts'] or 'No speech text; actual output quiet',f"{c['p95_s1_seconds']:.3f} s"))
    body+=hk.section('Observed results',body=hk.labeled_asset(table(['Control','Result','Generated answer','p95 S1 request'],rows),'Table',1,'Four completed author-harness controls. All use one user request, raw history and no S2. Positive answers are independently transcribed from actual generated audio.'))
    examples=''
    for name,title in [('sky_native_prompt','Factual question'),('repeat_native_prompt','Repeat instruction'),('bread_author_reference','Remaining failure')]:
        c=next(c for c in review['cases'] if c['case']==name)
        examples+='<article class="card"><h3>'+title+'</h3><p><b>S1 heard:</b> '+escape(c['asr'])+'</p><p><b>Generated speech text:</b> '+escape(c['generated_tts'] or '(empty)')+'</p><p><b>Independent spoken transcript:</b> '+escape(c['played_transcript'] or '(no nonquiet speech)')+'</p></article>'
    body+=hk.section('Qualitative evidence',body='<div class="card-grid">'+examples+'</div><p><a class="button" href="trajectory.html">Listen to full replay and model-only audio</a></p>')
    body+=hk.section('Why this is not a speed failure',body='<p>Job 1034130 completed on one A100 SXM 80 GB. Thinker, Talker, MTP and Code2Wav share GPU 0; S2 is absent. All four main cases have zero measured input-clock backlog, and their S1 request p95 values range from 0.349 to 0.369 s under the 0.480 s tick. The bread case recognizes the complete question and remains silent despite that timing headroom.</p><p>Startup took 145.1 s, followed by a separate silent warmup session. Allocation lasted 241 s (0.06694 GPU hours); sampled peak device memory was 68.24 GiB. Three preceding Thinker-only diagnostic jobs also ran sequentially. No experiment GPU remains active. This is the smallest tested S1 layout and it meets this input clock; it does not test S1/S2 contention.</p>')
    prompt='你是有用的助手\n你的助手风格是：耐心。\n你的开场方式要求：短句清晰。'
    body+=hk.section('Local correction and remaining work',body='<p>The local S1-only configuration removes the S2 service, uses the native prompt below, and keeps raw assistant replies in history. The controller suppresses S2 dispatch independently from the saved model history. CPU regressions cover disabled dispatch, raw history, STOP handling, guidance and provider failures. Do not add the previous greeting/wait instructions: the tested wait directive made even the repeat control silent.</p><pre>'+escape(prompt)+'</pre><p>The exact cause of the bread-specific silence remains open. It persists under native and task-opening prompts, startup silence, raw and canonical history, and a cache-disabled control. No native THINK request is produced. Complete-file controls also lose ASR; the released model expects 480 ms packets, so those controls are not a valid general whole-file success test.</p><p>S2 and interruption experiments remain outside this baseline. <a href="controlled-study.html">Earlier E1/E2 failures</a> · <a href="handoff.html">Earlier bread/S2 replay</a> · <a href="archive.html">Older diagnostics</a>.</p>')
    body+=hk.section('Evidence limits and exact records',body='<ul>'+''.join('<li>'+escape(s)+'</li>' for s in review['limitations'])+'</ul><p><a href="../research/s1-single-review.json">Download the evidence review</a> · <a href="../research/current-s1.json">Download the two audio traces</a> · <a href="index.html">All experiments</a>.</p>')
    full,_=hk.document('S1-only single-request investigation',body,head_html='<link rel="stylesheet" href="../assets/site.css"><style>.study-table-scroll{max-width:100%;overflow-x:auto}.study-table-scroll table{min-width:650px}</style>')
    (ROOT/'experiments/s1-investigation.html').write_text(full)
    cards=[('S1','Single-request baseline','One factual question and one repeat instruction. Actual S1 speech verified; S2 absent.','trajectory.html','Listen to S1'),
        ('Investigation','What failed and what works','Prompt controls, author-harness comparison, runtime evidence and unresolved bread silence.','s1-investigation.html','Read investigation'),
        ('Earlier study','S2 handoff and interruption','The earlier E1/E2 cases completed but failed behavior checks. Kept as evidence.','controlled-study.html','View earlier study'),
        ('Archive','Older diagnostics','Superseded multi-turn budget recordings, decoder comparisons and previous controls.','archive.html','Browse archive')]
    content=''.join('<article class="card"><span class="tag">'+tag+'</span><h3>'+title+'</h3><p>'+desc+'</p><p><a class="button" href="'+url+'">'+button+'</a></p></article>' for tag,title,desc,url,button in cards)
    collection='<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="description" content="Verified S1-only baseline, investigation and earlier duplex studies."><title>Experiments · AI2AI Duplex</title><link rel="stylesheet" href="../assets/site.css"></head><body><header class="site-nav"><div class="nav-inner"><a class="brand" href="../index.html">AI2AI Duplex</a>'+project_tabs('experiments','../')+'</div></header><main><div class="container"><header class="hero"><p class="eyebrow">Current focus · 8 October 2026</p><h1>S1-only, one request.</h1><p class="lede">Start with verified basic speech before returning to S2 or interruption tests. Earlier failures remain clearly labeled.</p></header><section class="section"><h2>Current baseline and evidence</h2><div class="card-grid">'+content+'</div></section></div></main></body></html>'
    (ROOT/'experiments/index.html').write_text(version_assets(collection))
    print('Built S1 baseline, investigation and experiment collection.')

if __name__=='__main__':main()
