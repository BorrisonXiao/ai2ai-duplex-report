#!/usr/bin/env python3
"""Build the MP-Bench literature-review preview from its pinned local manifest."""
import hashlib
import html
import json
from pathlib import Path

from site_navigation import project_tabs, review_tabs

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / 'research/mpbench/preview.json').read_text(encoding='utf-8'))


def e(value):
    return html.escape(str(value), quote=True)


def build():
    css = hashlib.sha256((ROOT / 'assets/site.css').read_bytes()).hexdigest()[:12]
    cards = []
    for item in DATA['examples']:
        audio = ROOT / item['audio_file']
        digest = hashlib.sha256(audio.read_bytes()).hexdigest()
        if digest != item['audio_sha256']:
            raise ValueError('Preview audio SHA-256 mismatch: ' + item['audio_file'])
        audio_url = e(item['audio_file'] + '?v=' + digest[:12])
        question = ''
        if item['question_text']:
            question = '<p><strong>Question:</strong> ' + e(item['question_text']) + '</p>'
        cards.append(
            f'<article class="card mpbench-card"><span class="tag">{e(item["category"])}</span>'
            f'<h3>{e(item["title"])}</h3><p>{e(item["summary"])}</p>{question}'
            f'<p class="meta">Task ID: <code>{e(item["task_dir"])}</code> · '
            f'{item["audio_duration_seconds"]:.1f} seconds of input audio</p>'
            f'<p class="mpbench-label"><strong>{e(item["label"])}</strong></p>'
            f'<audio controls preload="none" aria-label="Play MP-Bench task: {e(item["title"])}">'
            f'<source src="{audio_url}" type="audio/wav">'
            f'Audio playback is unavailable. <a href="{audio_url}">Download the WAV</a>.'
            f'</audio><details><summary>Read the upstream input ASR transcript</summary>'
            f'<p class="mpbench-transcript">{e(item["transcript"])}</p></details>'
            f'<p class="mpbench-source">Transcript source: <code>{e(item["transcript_source"])}'
            '</code>. The transcript is an upstream ASR example, not a human-verified reference.</p></article>'
        )

    counts = DATA['counts']
    hours = DATA['audio_total_seconds'] / 3600
    examples = '<div class="context-example mpbench-examples">' + ''.join(cards) + '</div>'
    return '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Listen to three attributed MP-Bench multiparty voice task samples and read their upstream ASR transcripts; see the task mix and evaluation labels.">
<meta name="color-scheme" content="light dark">
<title>MP-Bench Preview — AI2AI Duplex</title>
<link rel="stylesheet" href="assets/site.css?v=''' + css + '''">
<script src="assets/site.js" defer></script>
<style>
.mpbench-card { display:flex; flex-direction:column; }
.mpbench-card audio { width:100%; margin:12px 0 16px; }
.mpbench-card .mpbench-label { color:var(--text); }
.mpbench-card .mpbench-transcript { color:var(--text); overflow-wrap:anywhere; }
.mpbench-card .mpbench-source { margin-top:auto; padding-top:14px; font-size:12px; }
.mpbench-license { overflow-wrap:anywhere; }
</style>
</head>
<body>
<a class="skip-link" href="#main">Skip to benchmark preview</a>
<header class="site-nav"><div class="nav-inner"><a class="brand" href="./">AI2AI Duplex</a>''' + project_tabs('literature') + '''</div></header>
<main id="main"><div class="container">''' + review_tabs('mpbench') + '''
<header class="hero" id="mpbench-review"><p class="eyebrow">Literature review · Dataset preview</p>
<h1>MP-Bench: listening for the right moment to participate</h1>
<p class="lede">Three complete task clips let you hear the benchmark’s discussion, speaker-identification, and turn-taking settings. Each player is paired with its upstream input transcript and the task’s label.</p>
<p class="meta">14 October 2026 · Original benchmark audio · No model evaluation was run for this preview</p>
<div class="button-row"><a class="button primary" href="#previews">Listen to the examples</a><a class="button" href="#task-design">What the benchmark measures</a><a class="button" href="''' + e(DATA['repository']) + '''">Official repository</a></div></header>
<nav class="jump-links" aria-label="MP-Bench sections"><a href="#overview">At a glance</a><a href="#task-design">Task design</a><a href="#previews">Audio and transcripts</a><a href="#scoring">Scoring protocol</a><a href="#attribution">Attribution and license</a></nav>
<section class="section" id="overview"><h2>At a glance</h2>
<p class="section-intro">MP-Bench evaluates a voice agent as a participant in a four-person spoken conversation: three simulated humans and the agent. The official task set has two scenarios and 927 tasks.</p>
<div class="stat-grid"><div class="stat"><strong>''' + str(counts['tasks']) + '''</strong><span>audio tasks</span></div>
<div class="stat"><strong>''' + f'{hours:.2f}' + ''' h</strong><span>total input audio across ''' + str(counts['tasks']) + ''' files</span></div>
<div class="stat"><strong>''' + str(counts['speaker_name_understanding']) + ''' / ''' + str(counts['understanding']) + '''</strong><span>understanding tasks ask for speaker identity</span></div>
<div class="stat"><strong>''' + str(counts['turnbased_should_speak']) + ''' / ''' + str(counts['turnbased_should_stay_silent']) + '''</strong><span>turn-based tasks labeled speak / stay silent</span></div></div>
<p>Audio files in the downloaded release are mono 16 kHz PCM. The task manifest records scenario family, whether the agent should speak, and—in speaker-name cases—the expected name. The full benchmark and its checksums remain in the project workspace; the published page contains only these three preview clips.</p>
</section>
<section class="section" id="task-design"><h2>Two scenarios, three evaluation groups</h2>
<div class="card-grid">
<article class="card"><span class="tag">Understanding · ''' + str(counts['understanding']) + ''' tasks</span><h3>Follow who said what</h3><p>Discussion clips end with a comprehension question about the conversation. A speaker-name subset asks which participant made a statement; there are ''' + str(counts['speaker_name_understanding']) + ''' such labels in this release.</p></article>
<article class="card"><span class="tag blue">Discussion behavior · ''' + str(counts['discussion_behavior']) + ''' tasks</span><h3>Answer when invited</h3><p>Participants debate a question and directly invite the agent to answer or settle the disagreement. These tasks test whether the agent gives an appropriate response.</p></article>
<article class="card"><span class="tag amber">Turn-based behavior · ''' + str(counts['turnbased_behavior']) + ''' tasks</span><h3>Speak on the correct turn</h3><p>Word-chain and number games assign the agent a follower role. Half of these tasks call for a response and half call for silence, so turn-taking accuracy has a 50% chance baseline.</p></article>
</div>
<div class="callout"><h3>What the scores separate</h3><p>Understanding and speaker-name accuracy assess the spoken answer. Turn-taking accuracy uses word timestamps to determine whether the agent speaks after the final input word. Appropriateness combines the turn decision with whether the reply fits the discussion or game rule. Latency measures the delay from the final input word to the agent’s first word.</p></div>
</section>
<section class="section" id="previews"><h2>Listen and read three examples</h2>
<p class="section-intro">Each player contains the complete task input WAV. Open a transcript beneath it to follow the corresponding upstream ASR text; task labels are shown separately from transcript text.</p>
<div class="callout amber"><h3>Transcript note</h3><p>The text below is copied from the repository’s example <code>all_stitched.json</code> files. It is ASR output and has not been manually corrected or presented as ground-truth wording.</p></div>''' + examples + '''
</section>
<section class="section" id="scoring"><h2>Protocol and interpretation</h2>
<div class="prose"><p>The authors’ protocol appends 30 seconds of silence after each task’s input audio and records through that tail so the system can respond. Their transcription script uses Parakeet TDT; the README recommends a batch size of one because larger batches changed transcripts in the reported check.</p>
<p>These samples illustrate task formats, not system performance. They do not measure DuplexOmni or any other model. The task labels, sample clips, and scoring definitions follow the upstream release.</p></div>
</section>
<section class="section" id="attribution"><h2>Attribution and license</h2>
<p class="mpbench-license"><strong>MP-Bench</strong> by Yi-Jen Shih, Shih-Yun Shan Kuan, Guan-Ting Lin, Kai-Wei Chang, Siddhant Arora, Shu-wen Yang, Abdelrahman Mohamed, Shinji Watanabe, Hung-yi Lee, and David Harwath (2026), “MP-Bench: Evaluating Voice Agents as a Multiparty Conversation Participant,” <a href="''' + e(DATA['paper']) + '''">arXiv:2609.13076</a>. Source repository: <a href="''' + e(DATA['readme']) + '''">atosystem/MP-Bench at the pinned commit</a>; audio: <a href="''' + e(DATA['audio_source']) + '''">official task audio archive</a>. Licensed under <a href="''' + e(DATA['license_url']) + '''">CC BY-NC 4.0</a>.</p>
<p>The three audio files are reproduced unchanged. Transcript text is copied verbatim from the upstream examples and paired with task descriptions for this preview. The authors state that MP-Bench is for evaluation only; do not use the tasks or audio to train models. See the <a href="research/mpbench/ATTRIBUTION.md">full local attribution record</a> and <a href="research/mpbench/preview.json">preview manifest with source hashes</a>.</p>
</section>
<footer class="site-footer"><p>MP-Bench dataset preview · <a href="index.html#literature-review">Return to the duplex landscape</a> · <a href="''' + e(DATA['repository']) + '''">Official benchmark repository</a></p></footer>
</div></main>
</body>
</html>
'''


def main():
    target = ROOT / 'mpbench.html'
    target.write_text(build(), encoding='utf-8')
    print('Built mpbench.html with 3 hash-checked task audio previews and upstream transcripts.')


if __name__ == '__main__':
    main()
