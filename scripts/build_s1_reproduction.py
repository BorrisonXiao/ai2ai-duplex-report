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
    'loop': 'Runs the conversation: feeds audio, keeps model history, and coordinates speech generation and playback.',
    'control': 'Disables S2 for these tests, cancels outdated audio, and checks whether requests keep up with incoming speech.',
    'runner': 'Starts the required services, assigns them to GPUs, and saves the experiment summary.',
    'server': 'Configures the audio-only servers and enables CUDA graphs for the S1 Thinker.',
    'gpu': 'Selects only the allocated GPUs and enables CUDA MPS when the device’s compute mode requires it.',
    'decoder': 'Converts generated speech codes to audio using a bounded 25-frame context.',
    'parser': 'Recovers narrowly defined formatting errors in the model’s response without changing its speech text.',
    'shim': 'Applies compatibility fixes for GPU discovery in the pinned serving environment.',
    'audio-shim': 'Adapts model startup to the audio-only experiment.',
    'author-caller': 'Runs the authors’ actual OfflineSimulator and records the prompt and sampling settings used.',
    'inputs': 'Extracts and resamples the original human recordings with reproducible sample boundaries.',
    'audit': 'Transcribes played speech on CPU and checks voice overlap and cancellation of old audio.',
    'cluster': 'Selects the cluster’s CUDA toolkit and library environment.',
    'batch': 'Submits the one-GPU experiment and checks that its files match the saved successful setup.',
    'smoke-batch': 'Sets local cache paths and starts inference through the GPU runtime wrapper.',
    'config': 'Contains the exact settings used for the successful uninterrupted and interrupted runs.',
    'legacy-config': 'Contains the settings used in the earlier failed three-GPU E1/E2 study.',
    'author-config': 'Contains the author-harness controls executed in job 1034130.',
    'native-controller': 'Contains the authors’ handling of the model’s STOP and THINK commands.',
    'author-loop': 'Contains the authors’ simulation loop, including how it preserves model replies in history.',
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
LOOP_STYLE = '''<style>
.loop-diagram-scroll{max-width:100%;overflow-x:auto}.loop-diagram{display:block;width:100%;min-width:800px;height:auto;color:var(--text)}
.loop-diagram rect{fill:var(--surface);stroke:var(--border);stroke-width:2}.loop-diagram text{fill:currentColor;font-size:15px;font-family:inherit}
.loop-diagram .loop-name{font-size:18px;font-weight:700}.loop-diagram .loop-arrow{fill:none;stroke:var(--muted);stroke-width:2}.loop-diagram .loop-label{font-size:13px;fill:var(--muted)}
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
        return '<div class="listing" id="listing-'+str(n)+'"><p class="listing-caption">Listing '+str(n)+'. '+escape(title)+' Source: '+link_source(self.sources,key,index+1)+'.</p><pre><code>'+escape(snippet)+'</code></pre></div>'


def section(anchor, title, body):
    return '<section class="section" id="'+anchor+'"><h2>'+title+'</h2>'+body+'</section>'


def labeled_table(number, headers, rows, caption):
    return '<div class="asset-block">'+table(headers,rows)+'<p class="cap source-note"><span class="asset-label">Table '+str(number)+'.</span> '+caption+'</p></div>'


def command(text):
    return '<pre class="manual-command"><code>'+escape(text.strip())+'</code></pre>'


def paragraphs(*texts):
    """Keep paragraphs separate in the source without forcing visual line breaks."""
    return ''.join('<p>'+text+'</p>' for text in texts)


def inference_diagram():
    return '''<figure><div class="loop-diagram-scroll"><svg class="loop-diagram" viewBox="0 0 1000 405" role="img" aria-labelledby="loop-diagram-title loop-diagram-desc"><title id="loop-diagram-title">How the input, model and playback tasks communicate</title><desc id="loop-diagram-desc">The feeder puts packets on an input queue. The S1 loop sends audio and history to Thinker and receives fields and tensors. A speech queue sends work to Talker. Its audio enters a buffer read by the playback loop. STOP clears and invalidates old audio.</desc><defs><marker id="loop-arrowhead" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0 L8 4 L0 8 Z" fill="var(--muted)"></path></marker></defs>
<a href="#inference-feeder"><rect x="15" y="40" width="180" height="100" rx="10"></rect><text x="30" y="69" class="loop-name">Input feeder</text><text x="30" y="97">while running</text><text x="30" y="121">480 ms input clock</text></a>
<rect x="235" y="40" width="130" height="100" rx="10"></rect><text x="250" y="82">Input queue</text><text x="250" y="108">FIFO packets</text>
<a href="#inference-model"><rect x="405" y="40" width="220" height="100" rx="10"></rect><text x="420" y="69" class="loop-name">S1 request loop</text><text x="420" y="97">for range(max_turns)</text><text x="420" y="121">History and controls</text></a>
<a href="#inference-model"><rect x="710" y="40" width="260" height="100" rx="10"></rect><text x="725" y="69" class="loop-name">Thinker model</text><text x="725" y="97">Text and control fields</text><text x="725" y="121">GPU 0</text></a>
<a href="#inference-playback"><rect x="15" y="225" width="180" height="100" rx="10"></rect><text x="30" y="254" class="loop-name">Playback loop</text><text x="30" y="282">while running</text><text x="30" y="306">Record 20 ms blocks</text></a>
<rect x="235" y="225" width="130" height="100" rx="10"></rect><text x="250" y="266">Audio buffer</text><text x="250" y="293">Version tags</text>
<rect x="405" y="225" width="140" height="100" rx="10"></rect><text x="420" y="265">Speech queue</text><text x="420" y="293">FIFO requests</text>
<a href="#inference-playback"><rect x="625" y="225" width="345" height="100" rx="10"></rect><text x="640" y="254" class="loop-name">Speech worker → Talker</text><text x="640" y="282">while True · requests stay in order</text><text x="640" y="306">Talker, MTP and Code2Wav on GPU 0</text></a>
<path class="loop-arrow" d="M195 90 H232" marker-end="url(#loop-arrowhead)"></path><path class="loop-arrow" d="M365 90 H402" marker-end="url(#loop-arrowhead)"></path>
<path class="loop-arrow" d="M625 72 H707" marker-end="url(#loop-arrowhead)"></path><text class="loop-label" x="642" y="57">Request</text><path class="loop-arrow" d="M710 114 H628" marker-end="url(#loop-arrowhead)"></path><text class="loop-label" x="648" y="134">Reply</text>
<path class="loop-arrow" d="M515 140 V182 H475 V222" marker-end="url(#loop-arrowhead)"></path><text class="loop-label" x="531" y="182">Queue speech work</text>
<path class="loop-arrow" d="M430 140 V185 H300 V222" stroke-dasharray="5 4" marker-end="url(#loop-arrowhead)"></path><text class="loop-label" x="184" y="175">STOP cancels old audio</text>
<path class="loop-arrow" d="M545 275 H622" marker-end="url(#loop-arrowhead)"></path><path class="loop-arrow" d="M798 325 V375 H300 V328" marker-end="url(#loop-arrowhead)"></path><text class="loop-label" x="485" y="365">Accepted PCM after synthesis</text><path class="loop-arrow" d="M235 275 H198" marker-end="url(#loop-arrowhead)"></path>
</svg></div><figcaption class="source-note"><span class="asset-label">Figure 1.</span> The logical tasks in the current harness. Thinker and speech generation share one GPU, while software queues separate input, model calls and playback. Arrows show data flow; the dashed arrow is the STOP action. Click a task to jump to its explanation. On a phone, scroll the diagram sideways.</figcaption></figure>'''


def inference_appendix(sources, q):
    def line(key, marker):
        matches = [i for i,text in enumerate(sources[key]['lines'],1) if marker in text]
        assert len(matches)==1,(key,marker,matches)
        return link_source(sources,key,matches[0])

    body = paragraphs(
        'The core loop repeatedly gives S1 a short piece of incoming audio, together with the conversation so far. S1 returns its current transcription, speech text and control commands. A separate worker turns that response into audio while the input and playback tasks continue running. Figure 1 shows how those tasks connect.',
        'There are two different kinds of streaming to keep in mind. At the application level, audio arrives in packets and produces a sequence of model calls. Inside each call, the model generates its response tokens. This harness waits for the complete response to that packet before sending the next S1 request; it does not insert new audio samples into a model call that is already running.',
        'The walkthrough below describes the local harness used for N2a and N2b. It replays a saved WAV rather than reading a physical microphone. All S1 components share one H100 SXM GPU with 80 GB of memory, and S2 is absent. Explaining this loop does not require a new GPU run.')
    body += inference_diagram()
    body += '<h3 id="inference-input">1 · Load the recording and prepare audio packets</h3>'+paragraphs(
        'The WAV is read into memory before the conversation starts. The harness checks that it is mono, resamples it to 24 kHz if needed, and divides it into 11,520-sample pieces. At 24,000 samples per second, each piece represents 480 milliseconds. The last piece is padded with zeros if it is shorter.',
        'Each piece is then converted to signed 16-bit PCM bytes and passed through the authors’ noise gate, which zeros samples below its threshold. A packet therefore contains 23,040 bytes: 11,520 samples with two bytes per sample. Listing 16 is the actual preparation code. The gradual behavior comes from releasing these prepared packets on a clock, not from repeatedly reopening or extending the file.')
    body += q.quote('loop',"x, sr = sf.read(root / case['audio']",7,'Read the WAV once, normalize its sample rate, and prepare the fixed-size audio packets.')
    body += '<h3 id="inference-feeder">2 · The while loop releases one packet at a time</h3>'+paragraphs(
        'The input feeder starts with packet index <code>i = 0</code>. As long as <code>running</code> is true, it chooses the next packet from the recording. Once those packets are exhausted, it supplies a packet of zero-valued samples. It continues sending silence because S1 may still be speaking, listening for a clarification, or deciding what to do next.',
        'In the interrupted condition, the feeder can replace those silent packets with the clarification recording. That happens only after the initial request has been supplied and while model speech is actually playing, using the checks shown in <a href="#listing-10">Listing 10</a>. It is the same input queue and the same S1 conversation; the clarification does not start a new model session.')
    body += q.quote('loop','async def feeder():',7,'Choose the next initial-audio packet, or silence after the initial recording ends.')
    body += paragraphs(
        'The feeder puts four items on the queue: the packet number, its audio bytes, the time it was supplied, and a label saying whether it belongs to the initial request, silence or the interruption. The queue keeps them in the order they arrived. After enqueueing a packet, the feeder advances <code>i</code> and waits for the next scheduled boundary.',
        'The timing expression in Listing 18 is based on the original start time. Packet 0 is due near time 0, packet 1 near 0.48 seconds, packet 2 near 0.96 seconds, and so on. It does not add another 480-millisecond delay after an S1 request finishes. If the feeder itself is late, the remaining wait becomes zero and it catches up with the clock.')
    body += q.quote('loop','await queue.put((i,packet',3,'Enqueue the packet and sleep only until the next boundary on the input clock.')
    body += paragraphs('Both <code>await queue.get()</code> and <code>await asyncio.sleep(...)</code> let other tasks run while this task is waiting. They are not busy-waiting loops. The input queue here is unbounded, so it does not discard packets when S1 is slow; instead, a backlog can grow. That is why the experiment measures how long each packet waits before inference.')
    body += '<h3 id="inference-model">3 · The S1 loop takes a packet and builds the next model request</h3>'+paragraphs(
        'The model-request loop is separate from the feeder. In this short experiment it is a <code>for</code> loop limited to 40 steps, rather than an indefinite <code>while</code> loop. At each step it waits for the next queued packet at '+line('loop','packet_index,packet,submitted,part = await queue.get()')+'. If a packet is already waiting, it can proceed immediately; otherwise, it yields until the feeder supplies one.',
        'It then appends a new user message to the conversation history. Listing 19 shows the exact message format. The PCM packet is wrapped in a WAV header and base64-encoded for transport as <code>input_audio</code>. The surrounding text gives it the released <code>audio_input</code> and <code>from_s2</code> structure. In this S1-only run, <code>from_s2</code> is empty because the disabled reasoner returns no guidance.',
        'The model receives audio directly. There is no Whisper transcription step in front of S1; Whisper is used later to audit the experiment. On the model server, the request’s audio is decoded and prepared as multimodal input rather than treated as a base64 text string.')
    body += q.quote('loop',"messages.append({'role':'user','content':[",4,'Add the current audio packet and any available S2 guidance as the next user message.')
    body += paragraphs(
        'The request contains the whole retained <code>messages</code> list: the system prompt, earlier audio packets, the original assistant replies to those packets, and the new audio packet. S1 is therefore not answering each 480-millisecond piece as an unrelated conversation. It can use the preceding words and its own earlier responses.',
        'Listing 20 sends that history to the local Thinker server on port 21991. The same <code>session_id</code> is used throughout the case. Temperature is 0 and <code>max_new_tokens</code> is 256 in the saved configuration. That token limit is an upper bound on the response to one packet; it is not an audio duration or an instruction to finish the entire conversation.')
    body += q.quote('loop',"response = await asyncio.to_thread(requests.post,'http://127.0.0.1:21991/internal/chat_turn'",4,'Call the resident S1 Thinker with the accumulated history and the selected generation settings.')
    backend = 'https://github.com/MuyeHuang/DuplexOmni/blob/'+UPSTREAM+'/inference_framework/realtime_serving/serving_core/server_thinker.py'
    body += paragraphs(
        'The Thinker model is loaded when its server starts, not reloaded for each packet. In the authors’ <a href="'+backend+'#L931">_run_chat_turn</a>, the server converts the messages to the model’s chat template and audio inputs, then asks the existing vLLM engine to generate a response. The engine has prefix caching enabled, and the session ID is used as a cache salt. Caching can reuse earlier computation, but the application still explicitly sends its retained history on every request; a session ID alone does not supply that history.',
        'This local endpoint returns the response text together with tensors used by Talker, serialized as a binary payload. Listing 21 decodes that payload and parses the model’s fields. A single response may contain a few recognized words, a piece of speech, a control command, or empty speech text. The harness does not require a complete user sentence before it starts making model calls.')
    body += q.quote('loop','internal = await asyncio.to_thread(torch.load,',4,'Decode the binary Thinker response and extract the current transcription, speech and control fields.')
    body += paragraphs(
        'The original response is appended to assistant history using <a href="#listing-4">Listing 4</a>. The controller acts on a separate copy of its fields. A <code>[STOP]</code> clears and invalidates old queued speech; an S2 request remains visible in the raw trace but is suppressed by the S1-only policy. The original binary payload is placed on the speech queue with its current audio version, as shown in <a href="#listing-15">Listing 15</a>. The S1 loop can then take the next input packet without waiting for that speech to finish playing.',
        'S1 calls are sequential within this loop: the current Thinker response is awaited before the next Thinker call begins. However, <code>asyncio.to_thread</code> keeps the blocking HTTP request out of the event loop. During that wait, the feeder can supply new input and the playback task can continue emitting old response audio. If inference takes longer than the 480-millisecond input interval repeatedly, the input queue grows and the model’s view of the user becomes delayed.')
    body += '<h3 id="inference-playback">4 · Speech generation and playback continue alongside S1</h3>'+paragraphs(
        'The speech worker has its own <code>while True</code> loop. It waits for work on the speech queue and sends the original Thinker payload to Talker on port 21992. Requests stay in order. Talker, MTP and Code2Wav produce the waveform, which is accepted only if its version has not been canceled by STOP.',
        'Every processed S1 step queues this handoff, even if the returned <code>tts</code> text is empty. Queuing a Talker request therefore does not prove that the model said anything useful. The report’s response checks use audible playback and the returned speech text as evidence.')
    body += q.quote('loop',"response = await asyncio.to_thread(requests.post,f'http://127.0.0.1:21992/internal/talker/turn/",2,'Ask Talker to synthesize the next response using the Thinker’s unchanged internal payload.')
    body += paragraphs(
        'The returned WAV is converted to PCM and normalized by the released <code>stretch_pcm_to_chunk</code> helper into a 480-millisecond block before it enters the tagged audio buffer. That helper trims a longer block and interpolates a shorter one to the target length. This is a transport step in the current harness, separate from the bounded Code2Wav decoder. Its implementation is at '+line('native-controller','def stretch_pcm_to_chunk(')+'.',
        'Playback has another <code>while running</code> loop, shown at '+line('loop','async def playback():')+'. It takes 20 milliseconds of PCM from the buffer at a time and records the result. If there is no queued audio, the buffer supplies zeros. Playback therefore continues on its own clock while Thinker and Talker are working, and recorded silence remains part of the replay.',
        'This is how the test can accept a user interruption while an earlier reply is playing: the input feeder and S1 loop remain active during playback. Once S1 recognizes the interruption and emits STOP, the buffer version changes. Both queued and unfinished audio from the old version are rejected, as explained in the <a href="#code">main code discussion</a>.')
    body += '<h3>5 · The capture ends after the configured number of S1 steps</h3>'+paragraphs(
        'Reaching the end of the input WAV does not end the feeder. In this experiment, the S1 loop ends after 40 processed packets. That is roughly 19.2 seconds of packet time, with startup and the final audio drain taking additional wall time.',
        'After the last S1 step, the harness sends <code>None</code> to the speech queue. The speech worker treats that as its end marker, finishes previously queued work and returns. The main task then waits until the playback buffer is empty, so the recorded replay includes the remaining response rather than cutting it at the last input step. Listing 23 shows this shutdown order.')
    body += q.quote('loop','await speech_queue.put(None)',6,'Finish queued speech work and drain playback before marking the capture complete.')
    body += paragraphs(
        'Finally, the cleanup block sets <code>running = False</code> and cancels any tasks that are still waiting, at '+line('loop','running = False')+'. The feeder may have queued additional packets during the final drain, but those are not extra S1 steps: only packets consumed by the 40-step model loop are processed.',
        'The 40-step bound also keeps this case out of the longer-history trimming path discussed earlier. It is a deliberate limit on this capture, not a general repair for indefinitely long conversations.')
    rows = [
        ('Input feeder · while running','The next 480 ms boundary on the input clock','Chooses an initial, silent or clarification packet and puts it on the input queue.','The main task sets running to false or cancels it during cleanup.'),
        ('S1 request loop · for range(max_turns)','An input packet and then the current Thinker response','Appends audio to history, calls S1, records the reply, applies controls and queues the Talker payload.','Forty processed steps in this configuration, or an error.'),
        ('Speech worker · while True','The next speech-queue item and then its Talker response','Synthesizes in order and accepts only audio whose version is still current.','It reads the None marker after previously queued work.'),
        ('Playback · while running','The next 20 ms playback boundary','Reads tagged PCM or silence from the audio buffer and records what was emitted.','The main task drains the buffer, then ends or cancels the playback task.')]
    body += labeled_table(5,['Loop','What it waits for','What it does','How it ends'],rows,'Each row is a software task or loop. Waiting yields control to the other tasks; it does not mean that all GPU requests are running simultaneously.')
    body += '<h3>How this relates to the authors’ live while loop</h3>'+paragraphs(
        'The authors’ live websocket implementation uses a <code>while self.running</code> loop in '+line('native-controller','async def _process_loop(self):')+'. Its inner loop collects incoming PCM until it has one complete 480-millisecond chunk; if input does not arrive within its timeout, it fills the remainder with silence. It then appends that chunk to the same conversation history and calls S1. The model-facing structure is similar to the replay harness, but the source of bytes is a live input queue rather than a preloaded recording.',
        'The local replay makes that structure easier to inspect: one task controls when each recorded packet arrives, one task processes those packets with the model, and separate tasks handle speech synthesis and playback. That separation is what allows the system to keep listening while a response is audible.')
    return section('inference-loop','Appendix 2 · How the core inference loop works',body)


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
    body += '<header class="hero"><p class="eyebrow">Reproduction notes · 8 October 2026</p><h1>S1 reproduction report</h1><p class="lede">The current example answers a human question, stops when the speaker interrupts, and responds to the clarification. This report explains how we got there, what went wrong in earlier attempts, and how to run the experiment yourself.</p>'+paragraphs(
        'We now have a working example of DuplexOmni’s S1 speech system without the separate S2 reasoning backend. Getting it to work involved finding a prompt and sampling setup that produced useful replies, preserving the model’s original conversation history, and checking that canceled speech really stayed out of playback. Some other requests still leave the model silent, so the result should be read as a successful example rather than a general solution to S1 reliability.',
        'Here, <b>S1</b> means the system that listens and speaks as audio arrives. <b>S2</b> is the optional reasoning service that S1 can ask for help. The component named <b>Thinker</b> belongs to S1; it is not the separate S2 service. The test harness is the code that feeds recorded user speech into these components and records their responses.')+'<p><a class="button" href="interruption.html">Listen to the two conditions</a> · <a href="single-request.html">Listen to the earlier single-request checks</a> · <a href="index.html">All experiments</a></p></header>'
    body += '<nav class="toc" aria-label="Report sections">'+''.join('<a href="#'+a+'">'+b+'</a>' for a,b in [('working','Working result'),('comparison','Failed vs. working'),('code','Key code'),('source-map','Source files'),('limits','What remains open'),('appendix','Appendix · run manually'),('inference-loop','Appendix · inference loop')])+'</nav>'
    interrupted = next(c for c in review['cases'] if c['id']=='N2b')
    metric = interrupted['interruption']
    rows = [('N2a · no interruption', review['cases'][0]['played_transcript']),
            ('N2b · one interruption', interrupted['played_transcript']),
            ('The model’s stop command', 'STOP was recorded at processing step 13. It removed 13,440 queued bytes, equivalent to 0.28 seconds of mono audio.'),
            ('Time when both voices were audible', '0.40 seconds'),
            ('Delay before STOP', f"{metric['stop_delay_from_packet_seconds']:.3f} seconds after the first clarification packet; {metric['stop_delay_from_nonquiet_user_onset_seconds']:.3f} seconds after the human voice became audible."),
            ('Canceled speech played after STOP', 'No audible packets from the canceled reply were played afterwards.'),
            ('Clarification received by the model', 'All three audio packets were processed.'),
            ('Use of S2', 'No S2 model was loaded, and no S2 requests were made.'),
            ('Request latency in the uninterrupted condition', 'S1 p95 was 0.206 seconds; Talker p95 was 0.262 seconds. Both were within the 0.384-second limit.'),
            ('S1 request latency in the interrupted condition', f"The p95 was {interrupted['p95_s1_seconds']:.3f} seconds.")]
    working = paragraphs(
        'The user asks, <b>“Umm what’s the difference between an outlet and a regular store?”</b> In the uninterrupted condition, called <b>N2a</b>, the model gives a complete spoken explanation. In the interrupted condition, <b>N2b</b>, the same speaker asks <b>“Faulty products?”</b> while the model is speaking. The model stops its first explanation partway through and gives a new answer to that clarification.',
        'These are recordings of a real person from DailyTalk conversation 656, using the same speaker’s turns 2 and 4 on channel 1. DailyTalk dialogues are scripted. We extracted only this speaker’s audio and chose when to insert the clarification during the model’s reply; the original conversation partner’s answer was never supplied to the model. The voice is human-recorded, while the interruption timing is controlled for this experiment.',
        'Both conditions ran in job <b>1035079</b> on <b>one H100 SXM GPU with 80 GB of memory</b>. The S1 Thinker, Talker, MTP and Code2Wav components all shared GPU 0, and S2 was not loaded. The harness ran N2a first and checked that requests kept up with the incoming audio and that an answer was audible before starting N2b. The two conditions ran sequentially, with at most one GPU active. The allocation lasted 130 seconds, or 0.03611 GPU hours.',
        'The two runs used the same settings, and the fields returned by the model were identical for the first 12 processing steps before the clarification. This makes the comparison easier to interpret: the interrupted run begins with the same response, then receives the additional human utterance.',
        'Table 1 collects the spoken results and timing measurements. The <b>p95</b> latency is the time below which 95% of the measured requests fell. We use it to check whether the system can keep up with audio arriving in 480-millisecond packets; it does not tell us whether an answer is useful.')
    working += labeled_table(1,['What we checked','What we observed'],rows,'The two conditions use the same prompt, temperature-zero decoding and unedited model history. Audio timing is measured in software at 20-millisecond intervals; it does not measure physical microphone or loudspeaker delay.')
    working += paragraphs(
        'The transcripts in Table 1 come from audio that actually reached playback. That distinction matters here. The model generated the words “a store” as part of its first answer, but those words were still waiting in the audio queue when STOP arrived and were discarded. Playing every synthesized chunk back-to-back would hide that cancellation and give a misleading account of the interruption.',
        'You can inspect the <a href="../research/natural-interruption-review.json">full evidence review</a>, download <a href="../research/current-natural.json">both replay traces</a>, or check the <a href="../research/natural-dailytalk/manifest.json">original recordings and exact crop boundaries</a>.')
    body += section('working','1 · What happens in the current example',working)
    rows = [
        ('1030269 · earlier local harness','Three H100 SXM GPUs, 80 GB each. Thinker used GPU 0, speech generation GPU 1, and S2 GPU 2.','A custom English prompt described the response fields and desired behavior. Assistant history contained the JSON after our controller edits. S1 used temperature 0.','The system met its speed requirements, but dispatch-disabled bread and pet cases produced introductions instead of useful answers. The pet interruption produced no STOP. Forced S2 reasoning reached its 1,536-token limit without usable guidance.'),
        ('1034073, 1034085 and 1034117 · text diagnostics','One 80 GB GPU per job: an A100, then two H100 jobs. Only the S1 Thinker was loaded.','We compared prompt styles, original versus rewritten history, and how audio was divided into packets.','Preserving original history alone did not stop the custom-prompt greeting. The native-style prompt with greedy decoding answered factual and repeat requests in text, but the bread request remained silent.'),
        ('1034130 · authors’ simulation','One A100-SXM4 with 80 GB. All S1 components shared GPU 0; S2 was absent.','We called the actual OfflineSimulator.run and the standard orchestrator, with explicit prompt and temperature overrides.','The patient, short-clear prompt at temperature 0 produced complete sky and repeat answers in audio. Some default-prompt controls were silent, and the bread request was still unresolved.'),
        ('1034587 · human dinner request','One A100-SXM4 with 80 GB. All S1 components shared GPU 0; S2 was absent.','We supplied a real human dinner proposal using the native-style prompt and greedy decoding.','The request was transcribed completely, but the model stayed silent, so the interruption was withheld. Later history trimming coincided with slower requests, after the initial answering failure had already occurred.'),
        ('1035064 · human outlet controls','One H100 SXM with 80 GB. All S1 components shared GPU 0; S2 was absent.','We checked the local harness with a sky question and compared outlet responses at temperatures 0 and 0.8.','The greedy outlet baseline answered. The temperature-0.8 interruption emitted STOP, but also greeted the user and requested unavailable S2 help before stalling.'),
        ('1035079 · current two conditions','One H100 SXM with 80 GB. All S1 components shared GPU 0; S2 was absent.','Both runs used the patient, short-clear prompt, temperature 0, original model history and a 40-step capture.','The first answer, interruption, cancellation of old audio and new clarification answer were all verified in actual playback.')]
    comparison = '<h3>The first problem was answering, even when the system was fast enough</h3>'+paragraphs(
        'The earlier budget recording contained several questions, which made it difficult to tell whether a failure came from initial answering, interruption handling or S2. We therefore moved to smaller tests that isolated those behaviors. The budget recording remains in the <a href="archive-budget.html">archive</a>.',
        'In the later three-GPU study, job 1030269, the model heard the bread and pet requests but replied with a self-introduction. The pet correction did not produce a native STOP command or an answer to the revised request. This happened even after separating Thinker, speech generation and S2 onto their own H100 GPUs had brought request latency within the required limits. At that point, insufficient processing speed could no longer explain the whole failure.')
    comparison += '<h3>The authors’ harness showed that S1 can answer a single request</h3>'+paragraphs(
        'To check whether our local conversation loop was responsible, we ran the authors’ actual OfflineSimulator and standard orchestrator. With a patient, short-clear system prompt and temperature 0, job 1034130 gave complete spoken answers to a sky question and a repeat instruction, without the unwanted introduction. Independent transcription of the played audio confirmed those answers.',
        'That result ruled out a blanket claim that the checkpoint cannot answer a single request without S2. It also exposed a narrower problem: behavior depends strongly on the prompt and the request. Preserving the original response text in history was not sufficient by itself, and the bread request remained silent even in the authors’ harness. Because some audio controls changed the prompt and temperature together, they do not tell us the separate contribution of every setting.')
    comparison += '<h3>Human recordings exposed a separate failure after interruption</h3>'+paragraphs(
        'The first human-recorded dinner proposal was fully transcribed but received no answer. We then tested the outlet-store question, which produced a useful initial answer at temperature 0. At temperature 0.8, an interrupted outlet run did emit STOP, but it also introduced itself and asked S2 for help. S2 was deliberately absent, and no new useful reply followed. This showed that stopping old audio and answering the interruption are two separate requirements.',
        'The final run used temperature 0 in both outlet conditions. It began with the same response in both runs, then stopped and answered when the clarification was inserted. Table 2 provides the job identifiers, configurations and allocations behind this progression. All of these jobs ran sequentially. The earlier study used at most three GPUs at once; each S1 investigation used one GPU. Revising this report uses zero GPUs.')
    comparison += '<details><summary>Table 2 · Open the run-by-run comparison and GPU allocations</summary>'+labeled_table(2,['Run','GPU allocation','How it was tested','What happened'],rows,'The text-only diagnostics establish generated text behavior. The author-harness and natural-audio results also include a review of played speech. A completed job or a latency pass does not, by itself, establish a useful conversation.')+'</details>'
    comparison += paragraphs('The underlying reviews are available for the <a href="controlled-study.html">failed E1/E2 study</a>, the <a href="../research/s1-single-review.json">author-harness speech checks</a>, and the <a href="../research/natural-interruption-review.json">human-recorded interruption tests</a>.')
    body += section('comparison','2 · How the earlier failures led to this setup',comparison)
    code = paragraphs(
        'The code below shows both the settings that changed and the machinery needed to run a streaming conversation. Compared with failed job 1030269, the successful setup uses the authors’ prompt format, explicitly preserves original model replies in history, leaves the S2 service unloaded, and tests a simpler factual request. In the human outlet comparison, it also uses greedy decoding instead of the failing temperature-0.8 setup.',
        'Feeding audio on schedule, generating speech asynchronously and rejecting canceled audio were already part of the failed controlled harness. They are necessary for this experiment, but their presence did not make the model answer or emit STOP. We therefore describe them as working code paths that we verified, rather than new fixes that explain every earlier failure.')
    code += '<h3>Choose a prompt and sampling setting that produce an answer</h3>'+paragraphs(
        'The successful run uses a short Chinese system prompt whose meaning is: “You are a useful assistant. Your style is patient. Your opening should use short, clear sentences.” The user question and model answer are still in English. This prompt follows the three-line style used in the released inference code, with the patient and short-clear choices that worked in our controls.',
        'The earlier custom English prompt added instructions about JSON fields and conversational behavior. With that prompt, the model often introduced itself instead of answering. Our controls show that prompt choice matters, although they do not establish that the prompt’s language alone causes the difference.',
        'We also set <code>temperature</code> to 0, which selects the highest-scoring next token rather than randomly sampling one. This is called <b>greedy decoding</b>. It produced a useful clarification reply in the outlet test, whereas the temperature-0.8 run greeted the user and requested S2 help. Listings 1 and 2 show the exact successful settings.')
    code += q.quote('config','"history_turns":',8,'The saved configuration preserves original history, uses temperature 0, and plays audio in 20-millisecond blocks.')
    code += q.quote('config','"system_prompt":',4,'The patient, short-clear prompt used in N2a. N2b uses the same prompt and also disables S2.',occurrence=0)
    code += paragraphs('The independent single-request check used the authors’ own simulator. Listing 3 shows where we instantiate it and apply the recorded prompt and temperature overrides before calling its inference method.')
    code += q.quote('author-caller','sim=author.OfflineSimulator',9,'Construct the authors’ simulator and pass the selected prompt and sampling settings to its client.')
    run_line = next(i for i,line in enumerate(sources['author-caller']['lines'],1) if 'await sim.run()' in line)
    code += paragraphs('The call to <code>sim.run()</code> is at '+link_source(sources,'author-caller',run_line)+'. The simulator’s default prompt asks for a more controlling conversational style and uses temperature 0.3; our successful control explicitly replaces both settings. We kept the author source at commit <code>'+UPSTREAM+'</code> so the test can be repeated against the same code.')
    code += '<h3>Preserve what the model said in its conversation history</h3>'+paragraphs(
        'At each step, S1 returns recognized user words, speech text and optional control commands. Our harness may edit the S2 control field to enforce the experiment’s rule that S2 is off. That edited copy is used to decide which actions the controller can take.',
        'For the next model request, however, we keep the original reply exactly as it was returned. This is what the report means by <b>raw history</b>. It follows the authors’ loop and prevents our controller edits from becoming part of the model’s conversation context. The original internal response is also passed to Talker for speech generation. Listings 4 and 5 show the local and author implementations of history preservation.',
        'This change makes the interfaces consistent, but it is not sufficient to guarantee an answer. The bread request remained silent in controls that preserved original history.')
    code += q.quote('loop',"history_raw = raw if",2,'Keep the original model reply when raw history is selected. Older configurations can still use the rewritten JSON branch.')
    code += q.quote('author-loop','s1_messages.append({"role": "assistant"',1,'The authors’ simulator also appends the original response to assistant history.')
    code += paragraphs('Listings 6 and 7 show how S2 is disabled separately. We blank its control field in the controller’s copy and supply a replacement object that does not construct a reasoning client.')
    code += q.quote('control','effective = dict(fields)',3,'Apply the S2 policy to a copy of the returned fields, preserving the speech and other controls.')
    code += q.quote('loop',"controller.s2_agent = DisabledReasoner()",1,'Use the disabled reasoner when the case’s S2 policy is off.')
    code += paragraphs('The successful configuration also omits the <code>system2</code> service block, so '+link_source(sources,'runner')+' never starts an S2 model. If S1 nevertheless emits <code>[THINK]</code>, we retain that request in the original trace while preventing an actual S2 call. This distinction explains the temperature-0.8 failure: stopping the call to S2 did not make S1 produce its own useful answer.')
    code += '<h3>Keep audio moving while the model generates speech</h3>'+paragraphs(
        'The harness supplies 24 kHz mono audio in 480-millisecond packets, following the released streaming interface. It runs three tasks alongside the S1 request loop: one supplies user audio, one plays the available response audio in 20-millisecond blocks, and one sends speech-generation requests to Talker in order. Network requests run in worker threads so that waiting for a response does not freeze audio input or playback.',
        'Listings 8 and 9 show the input clock and the three tasks. Warmup runs use separate sessions, so their history cannot introduce a greeting into the user’s conversation.')
    code += q.quote('loop',"source_parts.append(part)",4,'Put each input packet on the queue, then wait until the next 480-millisecond boundary.')
    code += q.quote('loop','tasks = [asyncio.create_task(feeder())',1,'Start the input, playback and speech-generation tasks together.')
    code += paragraphs('For N2b, the harness first finishes supplying the initial question. It then waits until the model has actually played enough speech and is still speaking before inserting “Faulty products?”. Listing 10 also checks that enough steps remain to process the clarification and its response. The trigger is based on heard model speech, rather than an assumption that a submitted synthesis request is already audible.')
    code += q.quote('loop','can_finish_correction =',7,'Insert the clarification during recent model playback, allowing time for the rest of the interaction.')
    code += '<h3>Make STOP cancel both queued audio and unfinished synthesis</h3>'+paragraphs(
        'When the model emits <code>[STOP]</code>, the authors’ controller clears the audio that is waiting to play. Listing 11 shows that handler. There is another case to handle when synthesis runs asynchronously: an old speech request may still be computing when STOP arrives, and its audio may return after the model has started a new reply.',
        'A single “drop audio” flag is not enough to distinguish those replies, because new speech resets the flag. Our audio buffer therefore keeps a version number, called an <b>epoch</b>. Each synthesis request is tagged with the current version. STOP clears the queue and increases that number; audio tagged with an earlier version is rejected. In this way, unfinished work from the interrupted answer cannot reappear during the new answer.')
    code += q.quote('native-controller','if "[STOP]" in str(tts_ctrl)',6,'The authors’ handler clears queued audio at STOP and allows playback again when new speech arrives.')
    code += q.quote('control','async def clear(self):',14,'Increase the audio version when clearing the queue, and reject audio carrying an older version.')
    code += paragraphs('The speech worker checks this version in two places. Listing 13 skips canceled work before sending it to Talker. Listing 14 checks again after Talker returns, catching an old request that was already running when STOP happened. Listing 15 shows where the request receives its version tag.')
    code += q.quote('loop','chunk, blob, fields, queued_at, epoch = item',7,'Skip a queued request if its audio version has already been canceled.')
    code += q.quote('loop',"'epoch':epoch,'dropped_by_STOP':",1,'Discard a completed response if its version is old, even when the general drop flag has been reset.')
    code += q.quote('loop','await speech_queue.put((index,response.content',2,'Queue the original response payload together with the current audio version.')
    code += paragraphs('In job 1035079, STOP changed the version from 0 to 1 at step 13. No audible packets carrying version 0 were played afterwards. That verifies the cancellation path in this example. The model still has to decide to emit STOP and produce a useful new answer; the buffer code cannot make those decisions for it.')
    body += section('code','3 · How the code supports the conversation',code)
    rows = []
    for key,item in sources.items():
        rows.append((item['local_path'], DESCRIPTIONS[key],
                     'Matches the successful run’s saved checksum' if item['matches_frozen_launch'] else 'Included as a reference file',
                     'Workspace path and account name replaced' if item['redacted'] else 'Copied without edits'))
    source_table = labeled_table(3,['File in the project','What it does','How it was checked','Public copy'],rows,'Code excerpts are copied directly from these files. The public launchers replace the private workspace path and account name; the manifest records checksums for both the original and displayed copies.')
    links = '<ul>'+''.join('<li>'+link_source(sources,key)+' — '+escape(DESCRIPTIONS[key])+'</li>' for key in sources)+'</ul>'
    source_map = paragraphs(
        'To follow the main conversation loop, start with '+link_source(sources,'loop')+'. It shows how user audio reaches S1, how replies are saved in history, and how the controller and Talker are called. Then read '+link_source(sources,'control')+' for the cancellation buffer and the S2-off policy.',
        'For the independent check using the authors’ simulator, read '+link_source(sources,'author-caller')+'. The exact settings for the current experiment are in '+link_source(sources,'config')+', and the batch launcher is '+link_source(sources,'batch')+'. The complete inventory below includes the serving helpers and earlier configurations as well.',
        'All local paths are relative to <code>~/cxiao/duplex</code>. Clicking a file opens a copy with line numbers; clicking a citation next to a listing takes you directly to the quoted lines. The copies let you inspect the code from the public report. To run the model, you also need the full migrated project, environments, recordings and checkpoints described in the appendix.')
    source_map += '<details><summary>Table 3 · Open the complete source-file inventory</summary>'+source_table+links+'</details>'
    source_map += paragraphs('Before generating this report, we compared all files listed in the successful run’s saved manifest with their recorded SHA-256 checksums. A checksum is a fingerprint of a file’s contents, so a match confirms that the file has not changed. The <a href="../research/s1-reproduction/manifest.json">public manifest</a> records those fingerprints, quoted text and line ranges. The author source is accompanied by its <a href="../research/s1-reproduction/UPSTREAM-LICENSE">Apache 2.0 license</a>. Public copies of the shell launchers replace private paths and account names; use the original local files for the commands below.')
    body += section('source-map','4 · Where to find the source code',source_map)
    limits = paragraphs(
        'The current result is encouraging because we can hear both the initial answer and the clarification reply, and the trace confirms that canceled speech never resumes. It does not tell us how often the model will succeed on other questions or interruption types. Table 4 lists the failures and limits that remain.',
        'The dinner test is especially useful for separating response quality from speed. During its first 40 steps, S1 had a p95 request time of about 0.316 seconds and almost no input backlog, yet it gave no answer. The later slowdown appeared after that initial failure. We therefore cannot explain the dinner silence simply as a consequence of the late latency spikes.')
    limits += labeled_table(4,['What remains unresolved','What it means for the result'],[
        ('The bread request still receives no answer.','This happened in both local controls and the authors’ harness. We need broader testing across requests and prompts before claiming reliable single-request answering.'),
        ('The human dinner proposal also receives no answer.','The initial requests were processed quickly enough, and the user’s words were transcribed completely. The model’s silence is still unexplained.'),
        ('Longer conversations show a later slowdown.','Trimming old history around steps 40–45 coincided with S1 p95 increasing to about 0.570 seconds and input backlog reaching about 0.446 seconds. The current 40-step capture stops before this trimming path is reached; it does not repair the longer-stream problem.'),
        ('S1 can request S2 even when S2 is disabled.','At temperature 0.8, the outlet interruption requested THINK and then stalled. Preventing an S2 call does not guarantee that S1 will answer independently.'),
        ('The clarification reply oversimplifies outlet-store quality.','“Not faulty products” shows that the model responded to the clarification, but the answer is too categorical. Correct turn handling and factual accuracy need separate assessment.'),
        ('The current GPU setup is efficient for this short test.','All S1 components fit on one H100, avoiding transfers between GPUs and competition with S2. CUDA graphs, a bounded 25-frame decoder and four CPU threads keep this capture within its measured timing limits. We have not compared every layout or established a globally optimal setup.')], 'These issues remain open. Timing checks assess whether the system keeps up with audio; listening and content review assess whether it responds appropriately.')
    limits += paragraphs('Several compatibility fixes support the experiment without resolving these response failures. The parser in '+link_source(sources,'parser')+' can recover specific malformed quotation around known response keys and records each repair, but it does not create speech that the model omitted. GPU selection, audio-only startup and bounded decoding likewise help the serving stack run; a useful answer still has to come from the model.')
    body += section('limits','5 · What still needs investigation',limits)
    appendix = '<h3>A · Submit the two-condition experiment</h3>'+paragraphs(
        'On this cluster, the shortest way to reproduce the successful run is to submit the saved batch launcher from <code>~/cxiao/duplex</code>. It uses the existing migrated environments, checkpoints and recordings, so no reinstall or download is needed here.',
        'For reference, the setup uses <code>envs/duplexomni</code> for inference and <code>envs/data</code> for lightweight file checks. The checkpoint is at <code>models/duplexomni</code>, revision <code>b8a5ff6395ae51460d0402424fbd3359614a901a</code>. The author code is at commit <code>'+UPSTREAM+'</code>, and the installed vLLM version is <code>0.16.0+precompiled</code> with the project’s compatibility fixes. The two DailyTalk crops and the saved <code>launch-04</code> directory must also be present.',
        'The command below requests <b>one H100 SXM GPU with 80 GB of memory</b>. Thinker, Talker, MTP and Code2Wav share GPU 0; S2 is not loaded. The launcher runs the uninterrupted case first and only proceeds to the interrupted case if request timing and the initial audible response pass their checks. Both cases run sequentially, with at most one GPU active.',
        'Before inference begins, the launcher compares the source, configuration and input files with the checksums saved for the successful run. If a file has changed, it stops and names the mismatch. This helps you distinguish a repeat of the documented experiment from a run using different code or data.')
    appendix += command('''cd ~/cxiao/duplex
sbatch --partition=h100 --constraint=h100_sxm --gres=gpu:h100:1 \\
  --mem=128G --time=00:06:00 --job-name=duplex-natural-greedy \\
  jobs/duplexomni_natural_interruption.sbatch \\
  .migration/updates/2026-10-08-natural-interruption/launch-04''')
    appendix += paragraphs('Submit the command once and note the job number that Slurm returns. Substitute that number for <code>NEW_JOB_ID</code> in the commands below. The first shows whether the job is still queued or running, the second shows its recorded state and allocation, and the third displays the end of the output log. They do not submit another GPU job.')
    appendix += command('''squeue -j NEW_JOB_ID
sacct -j NEW_JOB_ID -X --format=JobID,State,ExitCode,Elapsed,AllocTRES
tail -n 60 logs/duplex-natural-greedy-NEW_JOB_ID.out''')
    appendix += '<h3>B · Listen to the result and check the saved evidence</h3>'+paragraphs(
        'Once the job finishes, look under <code>exp/inference/duplexomni/native_loop_NEW_JOB_ID/</code>. The uninterrupted and interrupted results are in <code>natural_outlet_control/</code> and <code>natural_outlet_interruption/</code>, respectively.',
        'Start by listening to <code>conversation_replay.wav</code> in each directory. The left channel contains the user recording; the right contains the model audio that actually reached playback. Use <code>playback.wav</code> to hear just the model. The summary status <code>completed_content_review_required</code> means the pipeline finished and the answer still needs review.',
        'The following commands print the overall summary and run the CPU audit of speech and interruption timing:')
    appendix += command('''envs/data/bin/python -m json.tool \\
  exp/inference/duplexomni/native_loop_NEW_JOB_ID/summary.json
envs/duplexomni/bin/python scripts/audit_natural_interruption.py --job NEW_JOB_ID''')
    appendix += paragraphs(
        'The audit uses Whisper on CPU to transcribe the played speech and examines the saved audio for overlap and cancellation. It writes <code>reports/natural_interruption_NEW_JOB_ID_review.json</code> and audio windows for each case. Run it after inference has created the files. It uses zero GPUs and does not submit a Slurm job.',
        'Use your new job number for this audit. Running it again for 1035079 would replace that job’s saved, manually annotated review. Automatic transcripts are useful evidence, but listen to the audio as well before deciding whether the response makes sense.',
        'A successful reproduction should give a complete answer in N2a. In N2b, you should hear the human clarification overlap the first answer, followed by a cut and a new reply to “Faulty products?”. The trace should show a model-produced <code>[STOP]</code>, all clarification packets processed, and no audible audio from the canceled version after STOP.',
        'For those trace checks, open each case’s <code>native_summary.json</code>. Its <code>fields</code> show what the model returned, the effective control fields show what the controller acted on, and the playback tags identify the audio version. A successful Slurm exit only tells you that the process finished; the audio and trace establish what happened in the conversation.')
    appendix += '<h3>C · If you already have a suitable GPU allocation</h3>'+paragraphs('You can also run inference from a shell inside an existing allocation of <b>one H100 SXM GPU with 80 GB</b>, instead of submitting another batch job. In that shell, <code>SLURM_JOB_ID</code> must identify the allocation and <code>CUDA_VISIBLE_DEVICES</code> must point to its assigned GPU. Then run:')
    appendix += command('''cd ~/cxiao/duplex
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 NUMEXPR_NUM_THREADS=4
bash jobs/duplexomni_smoke.sbatch \\
  --config configs/duplexomni_natural_outlet_greedy.json''')
    appendix += paragraphs(
        'This uses the same inference entry point and settings as the successful run, with all S1 components on GPU 0 and S2 absent. It skips the outer checksum check, so section A is the preferred route for reproducing the saved setup exactly.',
        'Running a <code>.sbatch</code> file with <code>bash</code> executes it inside your current allocation; its resource-request header is not submitted to Slurm. Each run writes to a path containing the job ID, so running it twice under the same ID would reuse the same output directory. Choose either A or C for a single reproduction.')
    appendix += '<h3>D · Repeat the independent check with the authors’ harness</h3>'+paragraphs('To check basic single-request speech through the authors’ simulator, use a separate existing allocation of <b>one A100 GPU with 80 GB</b>. The Thinker and all speech-generation components share GPU 0, and S2 is absent. From a shell inside that allocation, run:')
    appendix += command('''cd ~/cxiao/duplex
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 NUMEXPR_NUM_THREADS=4
bash jobs/duplexomni_smoke.sbatch \\
  --config .migration/updates/2026-10-08-s1-single/executed-reference-config.json''')
    appendix += paragraphs(
        'This saved configuration runs separate cases using the default author prompt and the patient, short-clear prompt. Each case after warmup contains one user request. The earlier run answered the factual and repeat requests, while the bread failure remained unresolved, so that same distinction should guide your review.',
        'Reference job 1034130 held one GPU for 241 seconds, or 0.06694 GPU hours. A repeat may have different wall time and numerical outputs. Run this check separately from the outlet experiment, keeping at most one GPU active throughout the reproduction sequence.')
    body += section('appendix','Appendix 1 · Run the experiment manually',appendix)
    body += inference_appendix(sources,q)
    body += '<footer class="site-footer"><p><a href="index.html">All experiments</a> · <a href="interruption.html">Current replay</a> · <a href="natural-study.html">Interaction evidence</a></p></footer>'
    page = '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="S1 working and failed harnesses, exact source code and manual reproduction commands."><title>S1 reproduction report · AI2AI Duplex</title><link rel="stylesheet" href="../assets/site.css">'+STYLE+LOOP_STYLE+'</head><body><a class="skip-link" href="#main">Skip to report</a>'+top+'<main id="main"><div class="container reproduction">'+body+'</div></main></body></html>'
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
