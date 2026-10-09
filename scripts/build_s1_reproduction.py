"""Render the S1 harness comparison, verbatim source listings and run appendix.

Run from the migrated project checkout. Inference sources are checked against
the successful run's frozen manifest before any report is written.
"""
from html import escape
import hashlib
import json
import os
from pathlib import Path

from build_current_experiments import ROOT, table, version_assets
from site_navigation import project_tabs, experiment_subtabs

PROJECT = ROOT.parent
OUTPUT = ROOT / 'research/s1-reproduction'
PAGE = ROOT / 'experiments/s1-reproduction.html'
LAUNCH = '.migration/updates/2026-10-08-natural-interruption/launch-04'
UPSTREAM = '33bfba1a821b09c5aa66790944f9098584979d34'
SOURCES = {
    'loop': 'scripts/native_interaction.py',
    'control': 'scripts/controlled_runtime.py',
    'runner': 'scripts/smoke_duplexomni.py',
    'server': 'scripts/duplex_server_smoke.py',
    'gpu': 'scripts/with_gpu_runtime.py',
    'decoder': 'scripts/streaming_code2wav.py',
    'parser': 'scripts/s1_response_parser.py',
    'shim': 'scripts/runtime_shims/sitecustomize.py',
    'audio-shim': 'scripts/runtime_shims/audio_only_thinker.py',
    'author-caller': 'scripts/run_s1_author_reference.py',
    'inputs': 'scripts/prepare_natural_dailytalk.py',
    'audit': 'scripts/audit_natural_interruption.py',
    'cluster': 'scripts/cluster_runtime.sh',
    'batch': 'jobs/duplexomni_natural_interruption.sbatch',
    'smoke-batch': 'jobs/duplexomni_smoke.sbatch',
    'config': LAUNCH + '/config.json',
    'legacy-config': 'configs/duplexomni_controlled_3h100.json',
    'author-config': '.migration/updates/2026-10-08-s1-single/executed-reference-config.json',
    'native-controller': 'external/duplexomni/inference_framework/realtime_serving/omni_realtime_server.py',
    'author-loop': 'external/duplexomni/inference_framework/realtime_serving/simulate_v8.py',
}
DESCRIPTIONS = {
    'loop': '480 ms input, raw history, native controller, concurrent synthesis/playback',
    'control': 'S2-off policy, epoch-tagged PCM queue and runtime gates',
    'runner': 'Starts only configured services, assigns GPU roles, saves run summary',
    'server': 'Audio-only serving bounds and Thinker CUDA graphs',
    'gpu': 'Allocation-scoped GPU selection and MPS when required',
    'decoder': 'Bounded 25-frame streaming Code2Wav decoder',
    'parser': 'Audited recovery of known S1 field keys; speech values preserved',
    'shim': 'Runtime/NVML compatibility for allocation-scoped devices',
    'audio-shim': 'Audio-only model/runtime compatibility',
    'author-caller': 'Calls the actual author OfflineSimulator with explicit overrides',
    'inputs': 'Deterministic original-human crops and resampling',
    'audit': 'CPU Whisper transcript, PCM overlap and obsolete-epoch audit',
    'cluster': 'Cluster CUDA library environment',
    'batch': 'Successful one-GPU launcher and frozen-hash guard',
    'smoke-batch': 'Offline caches, runtime wrapper and inference entry point',
    'config': 'Exact executed N2a/N2b configuration',
    'legacy-config': 'Earlier three-GPU custom-prompt E1/E2 configuration',
    'author-config': 'Executed 1034130 source-harness controls',
    'native-controller': 'Author native STOP / THINK handler',
    'author-loop': 'Author raw-history offline simulation loop',
}
STYLE = '''<style>
.reproduction{max-width:1080px;margin:auto}.reproduction .section{scroll-margin-top:80px}
.reproduction pre,.source-scroll{overflow-x:auto;max-width:100%;padding:18px;background:var(--surface-2,#f4f5f7);border:1px solid var(--border,#d6dce4);border-radius:8px;font-size:13px;line-height:1.6}
.reproduction pre code{white-space:pre;overflow-wrap:normal;word-break:normal}
.study-table-scroll{max-width:100%;overflow-x:auto}.study-table-scroll table{min-width:720px}
.listing{margin:24px 0}.listing-caption,.source-note{font-size:14px;color:var(--muted,#586477)}
.reproduction code,.reproduction a,.reproduction h1{overflow-wrap:anywhere}.toc{display:flex;flex-wrap:wrap;gap:8px 20px;margin:24px 0}
.source-line{display:block;width:max-content;min-width:100%;scroll-margin-top:30px}.source-line:target{background:rgba(234,179,8,.18)}
.source-line a{display:inline-block;width:4em;margin-right:1em;text-align:right;text-decoration:none;color:var(--muted,#586477)}
</style>'''


def sha(data):
    return hashlib.sha256(data).hexdigest()


def rel(target, base):
    return os.path.relpath(target, base).replace(os.sep, '/')


def shell_display(text):
    # Public launcher views are documentation, not byte-identical runnable copies.
    return text.replace(str(PROJECT), '/path/to/duplex').replace(
        'lgarci27_omnienc', 'YOUR_SLURM_ACCOUNT')


def source_views(prepared):
    result = {}
    for key, name in SOURCES.items():
        original = (PROJECT / name).read_bytes()
        text = original.decode('utf-8')
        redacted = key in {'batch', 'smoke-batch'}
        displayed = shell_display(text) if redacted else text
        # Stable short paths for hidden launch snapshots; retain original in manifest.
        exported = ('configs/n2-greedy-executed.json' if key == 'config' else
                    'configs/s1-author-executed.json' if key == 'author-config' else name)
        raw = OUTPUT / 'source' / exported
        raw.parent.mkdir(parents=True, exist_ok=True)
        raw.write_bytes(displayed.encode('utf-8'))
        view = raw.with_name(raw.name + '.html')
        code = ''.join('<span class="source-line" id="L'+str(i)+'"><a href="#L'+str(i)+'">'+str(i)+'</a>'+escape(line)+'</span>'
                       for i, line in enumerate(displayed.splitlines(), 1))
        note = ('Public view substitutes the private workspace path and Slurm account; all other lines are preserved. Use the original local launcher for execution.'
                if redacted else 'Verbatim source snapshot. Line numbers refer to the original local file.')
        proof = 'Matches the successful launch’s frozen SHA-256.' if name in prepared['files'] else 'Reference snapshot; not covered by the N2 launch hash guard.'
        title = escape(name)
        source_header = '<header class="site-nav"><div class="nav-inner"><a class="brand" href="'+rel(ROOT/'index.html',view.parent)+'">AI2AI Duplex</a>'+project_tabs('experiments',rel(ROOT,view.parent)+'/')+'</div></header>'
        html = '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+title+' · S1 source</title><link rel="stylesheet" href="'+rel(ROOT/'assets/site.css',view.parent)+'">'+STYLE+'</head><body>'+source_header+'<main class="container reproduction"><header class="hero"><p class="eyebrow">S1 reproduction · source snapshot</p><h1>'+title+'</h1><p class="source-note">'+note+' '+proof+'</p><p><a href="'+rel(PAGE,view.parent)+'#source-map">Return to S1 reproduction report</a> · <a href="'+escape(raw.name)+'" download>Download source view</a></p><p class="source-note">Original SHA-256: <code>'+sha(original)+'</code></p></header><pre class="source-scroll"><code>'+code+'</code></pre></main></body></html>'
        view.write_text(html)
        result[key] = {'local_path': name, 'original_sha256': sha(original),
                       'published_sha256': sha(displayed.encode('utf-8')),
                       'redacted': redacted, 'matches_frozen_launch': name in prepared['files'],
                       'view': rel(view,ROOT), 'raw': rel(raw,ROOT), 'lines': displayed.splitlines()}
    return result


def link_source(sources, key, line=None):
    item = sources[key]
    href = '../' + item['view'] + ('#L'+str(line) if line else '')
    return '<a href="'+href+'">'+escape(item['local_path'])+(':'+str(line) if line else '')+'</a>'


class Listings:
    def __init__(self, sources):
        self.sources = sources
        self.items = []

    def quote(self, key, start, count, title, occurrence=None):
        lines = self.sources[key]['lines']
        matches = [i for i,line in enumerate(lines) if start in line]
        assert len(matches) == 1 or occurrence is not None, (key, start, matches)
        index = matches[0 if occurrence is None else occurrence]
        snippet = '\n'.join(lines[index:index+count])
        n = len(self.items)+1
        self.items.append({'listing':n,'source':key,'start_line':index+1,
                           'end_line':index+count,'text':snippet})
        return '<div class="listing"><p class="listing-caption">Listing '+str(n)+'. '+escape(title)+' Source: '+link_source(self.sources,key,index+1)+'.</p><pre><code>'+escape(snippet)+'</code></pre></div>'


def section(anchor, title, body):
    return '<section class="section" id="'+anchor+'"><h2>'+title+'</h2>'+body+'</section>'


def labeled_table(number, headers, rows, caption):
    return '<div class="asset-block">'+table(headers,rows)+'<p class="cap source-note"><span class="asset-label">Table '+str(number)+'.</span> '+caption+'</p></div>'


def command(text):
    return '<pre class="manual-command"><code>'+escape(text.strip())+'</code></pre>'


def main():
    prepared = json.loads((PROJECT/LAUNCH/'prepared.json').read_text())
    for name, digest in prepared['files'].items():
        assert sha((PROJECT/name).read_bytes()) == digest, 'Frozen launch changed: '+name
    assert (PROJECT/'configs/duplexomni_natural_outlet_greedy.json').read_bytes() == (PROJECT/LAUNCH/'config.json').read_bytes()
    review = json.loads((ROOT/'research/natural-interruption-review.json').read_text())
    assert review['job_id'] == '1035079' and review['paired_prefix_identical']
    sources = source_views(prepared)
    q = Listings(sources)
    top = '<header class="site-nav"><div class="nav-inner"><a class="brand" href="../index.html">AI2AI Duplex</a>'+project_tabs('experiments','../')+'</div></header>'
    body = experiment_subtabs('reproduction')
    body += '<header class="hero"><p class="eyebrow">Reproduction notes · 8 October 2026</p><h1>S1 reproduction report</h1><p class="lede">A working S1-only interaction, the failed controls that explain its configuration, and the exact code and commands needed to reproduce it.</p><p>Native-shaped prompting and greedy decoding recover meaningful speech on selected requests. Raw model history preserves the authors’ interface. Epoch-tagged playback makes native STOP cancel both buffered and unfinished old speech. These results establish a working example; they do not resolve every silent request.</p><p><a class="button" href="interruption.html">Listen to N2a / N2b</a> · <a href="single-request.html">Listen to the author-harness basic checks</a> · <a href="index.html">All experiments</a></p></header>'
    body += '<nav class="toc" aria-label="Report sections">'+''.join('<a href="#'+a+'">'+b+'</a>' for a,b in [('working','Working result'),('comparison','Failed vs. working'),('code','Key code'),('source-map','Source files'),('limits','What remains open'),('appendix','Appendix · run manually')])+'</nav>'
    interrupted = next(c for c in review['cases'] if c['id']=='N2b')
    metric = interrupted['interruption']
    rows = [('N2a · no interruption', review['cases'][0]['played_transcript']),
            ('N2b · one interruption', interrupted['played_transcript']),
            ('Native STOP', 'Tick 13; 13,440 queued bytes removed (0.28 s mono PCM)'),
            ('Actual nonquiet user / model overlap', '0.40 s'),
            ('STOP delay from correction packet / nonquiet human onset', f"{metric['stop_delay_from_packet_seconds']:.3f} s / {metric['stop_delay_from_nonquiet_user_onset_seconds']:.3f} s"),
            ('Old-epoch nonquiet playback after STOP', '0 packets'),
            ('Correction input / S2 calls', '3 of 3 packets processed / 0 calls; no S2 model loaded'),
            ('Baseline p95 S1 / Talker', '0.206 s / 0.262 s, within the 0.384 s gate'),
            ('N2b p95 S1', f"{interrupted['p95_s1_seconds']:.3f} s")]
    body += section('working','1 · What works now', '<p>Job <b>1035079</b> supplies one original human question, <b>“Umm what’s the difference between an outlet and a regular store?”</b>, and N2b adds the same speaker’s <b>“Faulty products?”</b> during actual playback. Both come from DailyTalk conversation 656, channel 1, turns 2 and 4. Only the user’s crops enter the model. The original dialogue is scripted, and interruption timing is adapted; this is a controlled human-recorded test.</p><p><b>One H100 SXM 80 GB</b>: Thinker, Talker, MTP and Code2Wav share GPU 0. S2 is absent. N2a qualifies runtime and audible initial response before N2b executes; both run sequentially, maximum one GPU active. Historical allocation: 130 seconds / 0.03611 GPU hours. Returned fields match for the first 12 ticks before the clarification.</p>'+labeled_table(1,['Evidence from actual playback / trace','Result'],rows,'N2a/N2b use the same greedy/native-prompt/raw-history setup. Timings are software PCM measurements on a 20 ms grid, not physical microphone latency or precise word alignment.')+'<p>Table 1 uses the PCM that reached playback. The generated continuation includes “a store”, but those words were queued and cut; concatenating all synthesized chunks would incorrectly make the old explanation sound as though it continued. <a href="../research/natural-interruption-review.json">Standard evidence review</a> · <a href="../research/current-natural.json">Both replay traces</a> · <a href="../research/natural-dailytalk/manifest.json">Input checksums and crop bounds</a>.</p>')
    rows = [
        ('1030269 · local E1/E2','3 H100 SXM 80 GB; Thinker 0, speech 1, S2 2','Custom English JSON-instruction prompt; effective JSON history; S1 temperature 0','Runtime qualified, but S1-only bread/pet replies are introductions. Corrected pet case has no native STOP or fulfilled answer. Forced S2 truncates at 1536 tokens.','Shows hardware speed alone does not fix task behavior.'),
        ('1034073 / 1034085 / 1034117 · text controls','1 × 80 GB per sequential job: A100, then H100, H100; Thinker only','Custom vs native-shaped prompts; raw vs normalized history; packet controls','Raw custom prompt still greets. Native/greedy factual and repeat text responds; bread remains silent.','Raw history alone is insufficient. Extra wait/no-greeting instructions can suppress speech.'),
        ('1034130 · author source harness','1 A100-SXM4 80 GB; all S1 on GPU 0; no S2','Actual OfflineSimulator.run and stock orchestrator; native patience/short-clear override; temperature 0','Complete independently transcribed sky/repeat audio with no introduction. Stock simulator prompt/temperature 0.3 controls leave some requests silent; bread is unresolved.','Verifies basic S1 speech without depending on the newer local loop. Prompt and sampling changes are not a full factorial audio ablation.'),
        ('1034587 · local human dinner case','1 A100-SXM4 80 GB; all S1 on GPU 0; no S2','Native/greedy; real dinner proposal; longer history','Request fully transcribed but silent; interruption withheld. Late history trimming coincides with latency spikes.','Silence starts before the late stall; do not blame that request’s failure on speed.'),
        ('1035064 · local human controls','1 H100 SXM 80 GB; all S1 on GPU 0; no S2','Same local caller; sky check plus outlet temperature 0 vs 0.8','Greedy outlet baseline answers. Temperature 0.8 interruption emits STOP but greets, requests disabled S2, then stalls.','STOP mechanics can pass while conversational recovery fails.'),
        ('1035079 · current matched pair','1 H100 SXM 80 GB; all S1 on GPU 0; no S2','Native patience/short-clear prompt, temperature 0, raw history, paced input, tagged PCM; 40 ticks','Initial answer, native STOP, old-audio invalidation and new clarification reply verified.','Demonstrates this pair; no general benchmark accuracy claim.')]
    body += section('comparison','2 · Which attempts failed, and what changed', '<p>The earlier budget conversation mixed several requests and could not isolate initial answering, interruption and S2. It remains in the <a href="archive-budget.html">historical archive</a>. Table 2 compares the later controlled attempts. “COMPLETED” and a latency pass mean execution succeeded; only audible content and control traces establish an interaction result.</p>'+labeled_table(2,['Attempt / harness','GPU count, type and roles','Relevant setup','Observed result','What this establishes'],rows,'Historical jobs ran sequentially; the earlier isolated S2 study reached three GPUs, while all S1 investigations used one GPU per job. Text-only controls do not establish audible behavior. No new GPU inference is launched for this report.')+'<p>Primary saved reviews: <a href="controlled-study.html">1030269 failed E1/E2 study</a>, <a href="../research/s1-single-review.json">1034130 author-harness review</a> and <a href="../research/natural-interruption-review.json">1034587 / 1035064 / 1035079 natural-audio review</a>. The source map below identifies the two local callers and their executed configurations.</p>')
    code = '<p>The changes relative to failed job 1030269 are the native-shaped prompt, explicit raw-history serialization, a genuinely unloaded S2 service, and the simpler factual input. Paced input, asynchronous synthesis and epoch invalidation were already present in that failed controlled harness; they are required wiring, not newly discovered explanations for its lack of a model-produced STOP. In the human outlet controls, greedy sampling replaces the failing 0.8 interruption recipe.</p><h3>Use the observed working prompt and sampling recipe</h3><p>The successful English response comes from an English audio request with this Chinese system prompt: “You are a useful assistant; assistant style: patient; opening requirement: short, clear sentences.” It follows the released prompt shape. The older English prompt added field-format and behavior instructions and produced introductions. The diagnostic controls support prompt sensitivity; they do not show that translating a prompt alone fixes every request. Temperature 0 avoids the greeting/delegation regression seen in the human 0.8 interruption control.</p>'
    code += q.quote('config','"history_turns":',8,'Successful history, sampling and playback settings, taken from the executed configuration.')
    code += q.quote('config','"system_prompt":',4,'Native patience / short-clear prompt and explicit S2-off policy in N2a (N2b uses the same prompt).',occurrence=0)
    code += '<p>The basic speech check really called the authors’ simulation, rather than reproducing only its outer interface:</p>'
    code += q.quote('author-caller','sim=author.OfflineSimulator',9,'Actual source-harness construction and the recorded prompt/temperature override.')
    run_line = next(i for i,line in enumerate(sources['author-caller']['lines'],1) if 'await sim.run()' in line)
    code += '<p>The run awaits <code>sim.run()</code> at '+link_source(sources,'author-caller',run_line)+'. The stock author loop uses its own control-style prompt and temperature 0.3; the successful author-harness control explicitly overrides both. Its source is pinned to <code>'+UPSTREAM+'</code>.</p>'
    code += '<h3>Keep model history distinct from controller interventions</h3><p>Dispatch policy modifies only the controller’s S2 field. The working case retains the original model reply in assistant history and sends the original serialized internal response to Talker. The legacy JSON history branch remains available for old configurations. Raw history matches the authors’ loop and avoids injecting our dispatch edits into model context; raw-history-only controls still failed on bread.</p>'
    code += q.quote('loop',"history_raw = raw if",2,'Select original model text for assistant history; the older default branch uses effective JSON.')
    code += q.quote('author-loop','s1_messages.append({"role": "assistant"',1,'The author simulator also keeps the original assistant response.')
    code += q.quote('control','effective = dict(fields)',3,'Explicit S2-off intervention preserves all other returned fields.')
    code += q.quote('loop',"controller.s2_agent = DisabledReasoner()",1,'No S2 client is constructed for an S1-only case.')
    code += '<p>The current configuration has no <code>system2</code> service block. '+link_source(sources,'runner')+' starts S2 only when that block exists. A model-produced <code>[THINK]</code> remains in the saved original fields, while actual S2 calls remain zero. Disabling dispatch cannot force the model to answer; the 0.8 control demonstrates that limitation.</p>'
    code += '<h3>Keep listening and playing while synthesis runs</h3><p>Input is 24 kHz mono PCM in the model’s 480 ms packets, not a whole-file audio request. Three asynchronous tasks feed input, play 20 ms PCM blocks and serialize Talker requests. HTTP work runs in a thread so it does not block the event loop. Separate warmup sessions do not seed user history with an introduction.</p>'
    code += q.quote('loop',"source_parts.append(part)",4,'Pace incoming packets by the original clock while the S1 loop consumes its queue.')
    code += q.quote('loop','tasks = [asyncio.create_task(feeder())',1,'Concurrent input, playback and speech workers.')
    code += '<p>The correction is scheduled only after the initial request’s packets and during recent actual requested-speech playback; it does not wait for the model’s entire answer to finish:</p>'
    code += q.quote('loop','can_finish_correction =',7,'Barge-in follows measured speech, with enough remaining ticks to process the correction.')
    code += '<h3>Honor the model’s native STOP and reject late obsolete speech</h3><p>The author controller already handles <code>[STOP]</code> by clearing buffered PCM. With asynchronous synthesis, clearing alone does not guard an old request that finishes later: a new <code>tts</code> can reset the boolean drop flag. Our buffer therefore advances an epoch at STOP, tags each synthesis request and rejects audio from prior epochs. This mechanism prevents old work from resuming after the new reply.</p>'
    code += q.quote('native-controller','if "[STOP]" in str(tts_ctrl)',6,'Author native STOP handling; new tts resets the boolean audio-drop flag.')
    code += q.quote('control','async def clear(self):',14,'Atomic queue clearing and epoch validation in TaggedAudioBuffer.')
    code += q.quote('loop','chunk, blob, fields, queued_at, epoch = item',7,'Skip obsolete queued synthesis work before making the Talker request.')
    code += q.quote('loop',"'epoch':epoch,'dropped_by_STOP':",1,'Also discard an old request that finishes after STOP, even if the drop flag has reset.')
    code += q.quote('loop','await speech_queue.put((index,response.content',2,'Pass the unchanged Talker payload and capture the current epoch when work is queued.')
    code += '<p>The 1035079 trace verifies STOP at tick 13, an epoch transition from 0 to 1 and no nonquiet old-epoch packets afterwards. This is a demonstrated code-path invariant, not an isolated performance gain. Native STOP emission and a meaningful new answer still depend on model behavior.</p>'
    body += section('code','3 · Key code that supports the working case',code)
    rows = []
    for key,item in sources.items():
        rows.append((item['local_path'], DESCRIPTIONS[key],
                     'Launch hash verified' if item['matches_frozen_launch'] else 'Reference snapshot',
                     'Private path/account substituted' if item['redacted'] else 'Verbatim'))
    source_table = labeled_table(3,['Original local file','Role','Provenance','Published view'],rows,'Every quoted listing is extracted from its source snapshot. Launcher views explicitly replace private paths/account names; their original and public hashes are both recorded.')
    links = '<ul>'+''.join('<li>'+link_source(sources,key)+' — '+escape(DESCRIPTIONS[key])+'</li>' for key in sources)+'</ul>'
    body += section('source-map','4 · Source files and provenance', '<p>Paths refer to the migrated project root (<code>~/cxiao/duplex</code>). The links open line-numbered source snapshots, so they remain usable from the public report. These snapshots are documentation of the executed environment; downloading the report repository does not install checkpoints, environments or the model.</p>'+source_table+links+'<p><a href="../research/s1-reproduction/manifest.json">SHA-256, line ranges and listing text</a>. All entries in the successful launch’s source/config/input manifest were rechecked before rendering. The pinned author source and <a href="../research/s1-reproduction/UPSTREAM-LICENSE">Apache 2.0 license</a> are included for attribution. Public launcher views require local path/account edits before reuse.</p>')
    limits = '<p>Table 4 separates response behavior from runtime plumbing. These are priorities and limits, not fixes silently folded into the successful run.</p>'
    limits += labeled_table(4,['Finding','Interpretation / remaining work'],[
        ('Bread recipe silent in author and local controls','The selected working question does not fix arbitrary single-request answering. Broader prompt/request coverage is still needed.'),
        ('Real dinner proposal silent before late slowdown','Early 40-tick S1 p95 0.316 s with negligible backlog. No-answer behavior predates history truncation; speed is not its established cause.'),
        ('History prefix trim around ticks 40–45','Later S1 p95 about 0.570 s and backlog about 0.446 s coincide with trimming. Current max_turns=history_turns=40 avoids that branch; long-stream cache behavior remains unresolved.'),
        ('Temperature 0.8 emits THINK while S2 is absent','Dispatch suppression prevents S2 execution but cannot guarantee independent S1 recovery. Keep the raw request visible in traces.'),
        ('Retail clarification answer is categorical','“Not faulty products” demonstrates uptake but oversimplifies outlet quality. Interaction success is separate from factual accuracy.'),
        ('Efficient configuration is qualified for this capture','One H100 avoids cross-GPU handoffs and S2 contention here. CUDA graphs, 25-frame bounded decoder, four CPU threads and measured queue gates qualify this setup; global throughput optimality was not benchmarked.')], 'Unresolved model behavior and longer-stream limits remain explicit. p95 gates assess infrastructure; they are not conversational pass criteria.')
    limits += '<p>Parser recovery in '+link_source(sources,'parser')+' repairs only malformed quotation around known string keys and logs it. It does not invent missing speech. GPU mapping, the audio-only shim and bounded decoding make the pinned serving stack run efficiently; they do not explain the semantic difference between a greeting and an answer.</p>'
    body += section('limits','5 · What the evidence does not yet resolve', limits)
    appendix = '<h3>A · Minimal batch reproduction on this migrated cluster</h3><p>Prerequisites already present here: the complete migrated project, <code>envs/duplexomni</code> and <code>envs/data</code>, the DuplexOmni checkpoint at <code>models/duplexomni</code> (revision <code>b8a5ff6395ae51460d0402424fbd3359614a901a</code>), author checkout at <code>'+UPSTREAM+'</code>, local CPU Whisper weights, the two DailyTalk crops and the frozen <code>launch-04</code> directory. The installed vLLM version is <code>0.16.0+precompiled</code> with the project’s runtime shims; reuse this pinned environment.</p><p>The following submits one new <b>H100 SXM 80 GB</b> job, all S1 components sharing GPU 0, no S2. It runs N2a then N2b, maximum one GPU active. N2b depends on N2a passing latency/queue and initial-audible-response gates. The original launcher checks frozen source/config/input hashes first; a mismatch aborts instead of silently changing the reproduction.</p>'
    appendix += command('''cd ~/cxiao/duplex
sbatch --partition=h100 --constraint=h100_sxm --gres=gpu:h100:1 \\
  --mem=128G --time=00:06:00 --job-name=duplex-natural-greedy \\
  jobs/duplexomni_natural_interruption.sbatch \\
  .migration/updates/2026-10-08-natural-interruption/launch-04''')
    appendix += '<p>Run this once and note the returned job number. Replace <code>NEW_JOB_ID</code> below with that number. These commands monitor the new job without launching another allocation:</p>'
    appendix += command('''squeue -j NEW_JOB_ID
sacct -j NEW_JOB_ID -X --format=JobID,State,ExitCode,Elapsed,AllocTRES
tail -n 60 logs/duplex-natural-greedy-NEW_JOB_ID.out''')
    appendix += '<h3>B · Inspect actual output and decide whether it passed</h3><p>Outputs are under <code>exp/inference/duplexomni/native_loop_NEW_JOB_ID/</code>, with case directories <code>natural_outlet_control/</code> and <code>natural_outlet_interruption/</code>. Read the summary and listen to <code>conversation_replay.wav</code> in each directory: left channel is the supplied user; right channel is PCM actually played. <code>playback.wav</code> isolates model speech. The run’s <code>completed_content_review_required</code> status is deliberately not a semantic pass.</p>'
    appendix += command('''envs/data/bin/python -m json.tool \\
  exp/inference/duplexomni/native_loop_NEW_JOB_ID/summary.json
envs/duplexomni/bin/python scripts/audit_natural_interruption.py --job NEW_JOB_ID''')
    appendix += '<p>The second command performs CPU-only Whisper/PCM review and writes <code>reports/natural_interruption_NEW_JOB_ID_review.json</code> plus per-case audit windows. Use the new job number: rerunning it for 1035079 would overwrite the saved manually annotated review. Automatic transcripts still require listening and semantic review. It uses zero GPUs and starts after inference artifacts exist; it submits no Slurm job.</p><p>Require a complete N2a answer, a real overlap in N2b, a model-produced <code>[STOP]</code>, all correction packets processed, zero old-epoch nonquiet playback after STOP, and a new answer to “Faulty products?”. Inspect returned <code>fields</code>, effective control fields and playback epoch tags in each <code>native_summary.json</code>. A Slurm success, nonempty greeting or generated-but-discarded Talker clip is insufficient.</p>'
    appendix += '<h3>C · Alternative: run inside an existing one-H100 allocation</h3><p>If a suitable allocation is already active, reuse it rather than submitting A as well. From a shell inside that allocation, with a valid <code>SLURM_JOB_ID</code> and allocation-scoped <code>CUDA_VISIBLE_DEVICES</code>:</p>'
    appendix += command('''cd ~/cxiao/duplex
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 NUMEXPR_NUM_THREADS=4
bash jobs/duplexomni_smoke.sbatch \\
  --config configs/duplexomni_natural_outlet_greedy.json''')
    appendix += '<p>This is the same inference entry point/configuration, but it bypasses the outer frozen-hash guard. Calling a <code>.sbatch</code> file with <code>bash</code> does not request its header resources; it uses your existing allocation. Do not run twice under the same job ID because output paths share that ID. The preferred exact reproduction is A.</p><h3>D · Earlier author-harness single-request check</h3><p>To reproduce the independent basic speech controls, in a separate existing <b>one-A100 80 GB</b> allocation with all S1 components on GPU 0 and no S2, use:</p>'
    appendix += command('''cd ~/cxiao/duplex
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 NUMEXPR_NUM_THREADS=4
bash jobs/duplexomni_smoke.sbatch \\
  --config .migration/updates/2026-10-08-s1-single/executed-reference-config.json''')
    appendix += '<p>The saved config includes separate stock-prompt and native-prompt controls. Each non-warmup case contains one request; factual/repeat success does not imply the bread case succeeds. Historical reference job 1034130 allocated 241 seconds / 0.06694 GPU hours; exact repeat wall time and numerical outputs can vary. Run this separately from A–C, maximum one GPU active in this reproduction sequence.</p>'
    body += section('appendix','Appendix · Run the experiment manually',appendix)
    body += '<footer class="site-footer"><p><a href="index.html">All experiments</a> · <a href="interruption.html">Current replay</a> · <a href="natural-study.html">Interaction evidence</a></p></footer>'
    page = '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="S1 working and failed harnesses, exact source code and manual reproduction commands."><title>S1 reproduction report · AI2AI Duplex</title><link rel="stylesheet" href="../assets/site.css">'+STYLE+'</head><body><a class="skip-link" href="#main">Skip to report</a>'+top+'<main id="main"><div class="container reproduction">'+body+'</div></main></body></html>'
    PAGE.write_text(version_assets(page))
    manifest = {'report':'experiments/s1-reproduction.html','evidence_job':'1035079',
                'author_commit':UPSTREAM,'frozen_launch':LAUNCH,
                'all_frozen_hashes_verified':True,'new_inference_gpus':0,
                'sources':{key:{k:v for k,v in item.items() if k!='lines'} for key,item in sources.items()},
                'listings':q.items}
    (OUTPUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    (OUTPUT/'UPSTREAM-LICENSE').write_bytes((PROJECT/'external/duplexomni/LICENSE').read_bytes())
    print(f'Built S1 reproduction report; {len(sources)} source views, {len(q.items)} verbatim listings; frozen launch hashes verified.')


if __name__ == '__main__':
    main()
