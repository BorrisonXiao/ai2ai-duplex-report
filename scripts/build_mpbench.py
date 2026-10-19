#!/usr/bin/env python3
"""Build the MP-Bench literature-review preview from its pinned local manifest."""
import hashlib
import html
import json
from pathlib import Path

from site_navigation import project_tabs, review_tabs
from benchmark_scope import render_scope_section

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
    structure = DATA['task_structure']
    hours = DATA['audio_total_seconds'] / 3600
    examples = '<div class="context-example mpbench-examples">' + ''.join(cards) + '</div>'
    reference = DATA['text_reference']
    result_rows = [
        ('Understanding accuracy (all questions)', 'understanding_overall_accuracy', 'All 543 understanding tasks'),
        ('Speaker-name accuracy (subset)', 'speaker_name_accuracy', '33.3% random baseline: three possible speakers'),
        ('Discussion turn-taking accuracy', 'discussion_turn_taking_accuracy', 'All Discussion behavior tasks expect a response'),
        ('Discussion appropriateness accuracy', 'discussion_appropriateness_accuracy', 'Logical consistency; factual correctness is not required'),
        ('Turn-based turn-taking accuracy', 'turnbased_turn_taking_accuracy', '50% random baseline: speak/stay-silent labels are balanced'),
        ('Turn-based appropriateness accuracy', 'turnbased_appropriateness_accuracy', 'Requires the correct turn and a game-rule-compliant reply'),
    ]
    result_rows_html = ''.join(
        '<tr><th scope="row">' + e(label) + '</th>'
        + '<td>' + f'{reference["results_percent"][key]["asr_only"]:.2f}%' + '</td>'
        + '<td>' + f'{reference["results_percent"][key]["spkd_asr"]:.2f}%' + '</td>'
        + '<td>' + e(note) + '</td></tr>'
        for label, key, note in result_rows
    )
    reference_table = (
        '<div class="mpbench-results-scroll" role="region" aria-label="Text-only Gemini reference results" tabindex="0">'
        '<table class="mpbench-results"><caption>Table 2. Text-only reference scores from paper Table 3 (accuracy %)</caption>'
        '<thead><tr><th scope="col">Metric</th><th scope="col">ASR-only</th>'
        '<th scope="col">SpkD-ASR</th><th scope="col">Baseline or scoring note</th></tr></thead>'
        '<tbody>' + result_rows_html + '</tbody></table></div>'
    )
    return '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Listen to three attributed MP-Bench multiparty voice task samples, read their upstream ASR transcripts, and inspect the task mix and paper-reported text-only LLM references.">
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
.mpbench-results-scroll { overflow-x:auto; margin:20px 0; border:1px solid var(--border); border-radius:12px; background:var(--surface); }
.mpbench-results { width:100%; min-width:720px; border-collapse:collapse; }
.mpbench-results caption { padding:16px; color:var(--muted); font-weight:700; text-align:left; }
.mpbench-results th, .mpbench-results td { padding:13px 16px; border-top:1px solid var(--border); text-align:left; vertical-align:top; }
.mpbench-results th[scope="row"] { min-width:210px; }
.mpbench-results td:nth-child(2), .mpbench-results td:nth-child(3) { white-space:nowrap; font-variant-numeric:tabular-nums; }
</style>
</head>
<body>
<a class="skip-link" href="#main">Skip to benchmark preview</a>
<header class="site-nav"><div class="nav-inner"><a class="brand" href="./">AI2AI Duplex</a>''' + project_tabs('literature') + '''</div></header>
<main id="main"><div class="container">''' + review_tabs('mpbench') + '''
<header class="hero" id="mpbench-review"><p class="eyebrow">Literature review · Dataset preview</p>
<h1>MP-Bench: listening for the right moment to participate</h1>
<p class="lede">Three complete task clips let you hear the benchmark’s discussion, speaker-identification, and turn-taking settings. Each player is paired with its upstream input transcript and the task’s label.</p>
<p class="meta">16 October 2026 · Original benchmark audio · Published paper references are identified separately from local model evaluation</p>
<div class="button-row"><a class="button primary" href="#previews">Listen to the examples</a><a class="button" href="#task-design">What the benchmark measures</a><a class="button" href="''' + e(DATA['repository']) + '''">Official repository</a></div></header>
<nav class="jump-links" aria-label="MP-Bench sections"><a href="#benchmark-scope">Tests and limits</a><a href="#overview">At a glance</a><a href="#task-design">Task design</a><a href="#previews">Audio and transcripts</a><a href="#scoring">Scoring protocol</a><a href="#text-reference">Text-only references</a><a href="#attribution">Attribution and license</a></nav>
''' + render_scope_section(['mp']) + '''
<section class="section" id="overview"><h2>At a glance</h2>
<p class="section-intro">MP-Bench evaluates a voice agent as a participant in a four-person spoken conversation: three simulated humans and the agent. The official task set has two scenarios and 927 tasks.</p>
<div class="stat-grid"><div class="stat"><strong>''' + str(counts['tasks']) + '''</strong><span>audio tasks</span></div>
<div class="stat"><strong>''' + f'{hours:.2f}' + ''' h</strong><span>total input audio across ''' + str(counts['tasks']) + ''' files</span></div>
<div class="stat"><strong>''' + str(counts['speaker_name_understanding']) + ''' / ''' + str(counts['understanding']) + '''</strong><span>understanding tasks ask for speaker identity</span></div>
<div class="stat"><strong>''' + str(counts['turnbased_should_speak']) + ''' / ''' + str(counts['turnbased_should_stay_silent']) + '''</strong><span>turn-based tasks labeled speak / stay silent</span></div></div>
<p>Audio files in the downloaded release are mono 16 kHz PCM. The task manifest records scenario family, whether the agent should speak, and—in speaker-name cases—the expected name. The full benchmark and its checksums remain in the project workspace; the published page contains only these three preview clips.</p>
</section>
<section class="section" id="task-design"><h2>Two scenarios, three evaluation groups</h2>
<p class="section-intro">A task is one complete multiparty recording, not one independent test per speaker turn. The paper reports a mean recording length of ''' + f'{structure["mean_duration_seconds"]:.1f} ± {structure["duration_standard_deviation_seconds"]:.1f}' + ''' seconds and ''' + f'{structure["mean_conversation_turns"]:.1f} ± {structure["turn_standard_deviation"]:.1f}' + ''' conversation turns (<a href="''' + e(structure['source']) + '''">paper task statistics</a>).</p>
<div class="card-grid">
<article class="card"><span class="tag">Understanding · ''' + str(counts['understanding']) + ''' tasks</span><h3>Follow who said what</h3><p>Discussion clips end with a comprehension question about the conversation. A speaker-name subset asks which participant made a statement; there are ''' + str(counts['speaker_name_understanding']) + ''' such labels in this release.</p></article>
<article class="card"><span class="tag blue">Discussion behavior · ''' + str(counts['discussion_behavior']) + ''' tasks</span><h3>Answer when invited</h3><p>Participants debate a question and directly invite the agent to answer or settle the disagreement. These tasks test whether the agent gives an appropriate response.</p></article>
<article class="card"><span class="tag amber">Turn-based behavior · ''' + str(counts['turnbased_behavior']) + ''' tasks</span><h3>Speak on the correct turn</h3><p>Word-chain and number games assign the agent a follower role. The last game speaker and team roles determine whether the agent should answer after the clip or stay silent. Half of these tasks call for a response and half for silence, so turn-taking accuracy has a 50% chance baseline.</p></article>
</div>
<div class="callout"><h3>No fixed-size chunking is described</h3><p>The paper says it streams each full input recording to real-time audio agents, but does not give a fixed audio chunk size or score every internal speaker change as a separate decision. For each task, the expected action is one binary label at the end of the full clip: speak or stay silent. The official reproduction instructions append 30 seconds of silence after the clip so a response can be captured.</p></div>
</section>
<section class="section" id="previews"><h2>Listen and read three examples</h2>
<p class="section-intro">Each player contains the complete task input WAV. Open a transcript beneath it to follow the corresponding upstream ASR text; task labels are shown separately from transcript text.</p>
<div class="callout amber"><h3>Transcript note</h3><p>The text below is copied from the repository’s example <code>all_stitched.json</code> files. It is ASR output and has not been manually corrected or presented as ground-truth wording.</p></div>''' + examples + '''
</section>
<section class="section" id="scoring"><h2>Protocol and interpretation</h2>
<div class="card-grid">
<article class="card"><span class="tag">Turn-taking accuracy</span><h3>Did it take the expected action?</h3><p>For audio output, Parakeet streaming ASR supplies word timestamps. If any generated word starts after the final input word, the task is marked “spoke”; otherwise it is “silent.” That binary action is compared with the task’s <code>should_speak</code> label, and accuracy is the percentage of task labels matched. The 128 Discussion behavior tasks all expect a reply, so 100% there is not a demanding test. The 256 game tasks are balanced 128/128, giving a 50% chance baseline.</p></article>
<article class="card"><span class="tag blue">Appropriateness accuracy</span><h3>Was the action and reply suitable?</h3><p>A task counts as appropriate only when the agent takes the right turn and its response fits. For Discussion, the judge checks logical consistency with the debate—not factual truth. For a game, it checks the assigned rules; silence is the right action on a negative turn.</p></article>
<article class="card"><span class="tag amber">Understanding accuracy</span><h3>Did the answer match the reference?</h3><p>Each of the 543 understanding questions gets a correct/incorrect verdict against its reference answer. The paper describes GPT-5 as its LLM judge; for its text baseline it says the generated text is compared directly to the reference answer. The speaker-name score is a 396-question subset with one of three human speakers as the answer; 33.3% is random guessing. This is answer accuracy, not word error rate. The pinned repository supplies answer and name-judging prompts.</p></article>
</div>
<div class="prose"><p>Latency is separate from accuracy: for a real-time audio agent it is the mean delay from the final input word to the first generated word, over non-silent responses. It is not reported for text-only references. See the paper’s <a href="https://arxiv.org/pdf/2609.13076#page=3">evaluation definitions (§3.3)</a>. The official scorer and prompts are linked in the repository’s <a href="''' + e(DATA['scoring_sources']['timestamps']) + '''">timestamp detector</a>, <a href="''' + e(DATA['scoring_sources']['metrics']) + '''">metric code</a>, <a href="''' + e(DATA['scoring_sources']['understanding_judge']) + '''">understanding judge</a>, and <a href="''' + e(DATA['scoring_sources']['turnbased_judge']) + '''">turn-based judge</a>.</p>
<p>The three clips illustrate task formats. Paper reference results below were not rerun locally and do not measure DuplexOmni.</p></div>
</section>
<section class="section" id="text-reference"><h2>Text-only LLM reference: transcript versus speaker labels</h2>
<p class="section-intro">The paper uses Gemini-3.1-Pro as a text baseline. It gets the task transcript as text rather than streaming audio; no fixed-size audio chunks or incremental transcript updates are described, and no response latency is reported. In <strong>ASR-only</strong>, the input is the paper’s ground-truth ASR transcript without per-turn speaker labels. In <strong>SpkD-ASR</strong>, the same transcript also includes the ground-truth anonymized speaker ID on every turn, approximating a cascaded system with perfect diarization.</p>
<div class="card-grid">
<article class="card"><span class="tag">ASR-only</span><h3>Transcript, no diarization</h3><p>Tests what a strong LLM can answer when the transcript is available but who-spoke-which-turn labels are not supplied.</p></article>
<article class="card"><span class="tag blue">SpkD-ASR</span><h3>Transcript plus oracle speaker IDs</h3><p>Adds the correct anonymized speaker label for each turn. This is an upper-bound reference for the diarization component, not the output of a practical diarization system.</p></article>
</div>
''' + reference_table + '''
<div class="callout"><h3>What the comparison suggests</h3><p>Adding oracle speaker IDs raises speaker-name accuracy from 27.27%—below the 33.3% three-speaker chance baseline—to 93.94%. Turn-based turn-taking rises from 49.22%, essentially the 50% balanced-label baseline, to 98.44%. This supports the authors’ diagnosis that speaker attribution is a major bottleneck for this model on these tasks; it does not show that a real ASR-plus-diarization pipeline will attain the oracle score.</p>
<p>Table 3’s overall understanding accuracy moves from 4.79% to 87.48% (+82.69 percentage points). The paper’s separate 66.67-point comparison (93.94 minus 27.27) is for the speaker-name subset. Discussion turn-taking is 100% in both text settings because every Discussion behavior item explicitly requires a reply. Discussion appropriateness is 75.00% versus 89.06%, but its rubric checks logical consistency with the debate, not factual truth; that score alone is not evidence of robust speaker-aware comprehension.</p></div>
<div class="callout amber"><h3>Caveat for text-only turn-taking scores</h3><p>The paper reports 49.22% and 98.44% turn-taking accuracy for its two text-only Gemini conditions, but it does not specify how generated text is mapped to the binary “spoke / stayed silent” label. Its word-timestamp rule is defined for audio output. We retain the reported values, but they are not documented as chunk-by-chunk turn decisions and cannot be reproduced from the text-baseline description alone.</p></div>
<p class="meta">These are the authors’ Table 3 results, not local experiments. The text-only reference is Gemini-3.1-Pro; it is distinct from the LLM judge used to score outputs and from the separately evaluated GPT-Realtime audio model. See <a href="''' + e(reference['source']) + '''">paper Table 3 and Sections 5.1–5.2</a> and the repository’s <a href="''' + e(DATA['readme']) + '''">scoring instructions</a>.</p>
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
