#!/usr/bin/env python3
"""Build the Full-Duplex-Bench v2 data audit and benchmark preview."""

from datetime import datetime
import hashlib
import html
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT.parent
DATA = PROJECT_ROOT / "data/benchmarks/full_duplex_bench_v2"
INTEGRITY_SOURCE = PROJECT_ROOT / "reports/full_duplex_bench_v2_integrity.json"
RESEARCH = ROOT / "research/full-duplex-bench-v2"
PAGE = ROOT / "full-duplex-bench-v2.html"

from site_navigation import project_tabs, review_tabs
from benchmark_scope import render_scope_section


REPOSITORY = "https://github.com/DanielLin94144/Full-Duplex-Bench"
REVISION = "3e799c45a045256f47d5f1c9cda90157e2d2ec9e"
PAPER = "https://aclanthology.org/2026.acl-short.4/"
AUTHOR_DEMO = "https://ericsunkuan.github.io/full-duplex-bench-v2-demo/"
DEMO_AUDIO_MANIFEST = RESEARCH / "audio-samples.json"
LICENSE_URL = "https://creativecommons.org/licenses/by-nc/4.0/"
FAMILY_DESCRIPTIONS = {
    "Daily": "Routine requests such as ordering, scheduling, planning, reservations, and troubleshooting.",
    "Correction": "Mid-turn and cross-turn repairs where a speaker revises an earlier detail or intent.",
    "EntityTracking": "Reference resolution and keeping entity attributes consistent across turns.",
    "Safety": "Eleven safety classes that test boundary setting, refusal, and safe redirection.",
}
PAPER_RESULTS = [
    {"system": "Freeze-Omni", "pacing": "Fast", "correction": 2.74, "entity_tracking": 2.62, "safety": 3.94},
    {"system": "Moshi", "pacing": "Fast", "correction": 2.88, "entity_tracking": 2.76, "safety": 3.67},
    {"system": "GPT-Realtime", "pacing": "Fast", "correction": 4.02, "entity_tracking": 4.51, "safety": 4.44},
    {"system": "Freeze-Omni", "pacing": "Slow", "correction": 3.50, "entity_tracking": 2.86, "safety": 4.27},
    {"system": "Moshi", "pacing": "Slow", "correction": 3.46, "entity_tracking": 3.84, "safety": 3.51},
    {"system": "GPT-Realtime", "pacing": "Slow", "correction": 3.94, "entity_tracking": 4.12, "safety": 4.53},
]
SAMPLES = ["Daily", "Correction", "EntityTracking", "Safety"]


def e(value):
    return html.escape(str(value), quote=True)


def render_audio_card(item):
    label = f"{item['family']} · {item['pacing']} · {item['sample']} · {item['model']}"
    return (
        '<article class="card fdbv2-audio-card"><span class="tag">' + e(item["family"]) + " · " + e(item["pacing"]) + "</span>"
        + "<h3>" + e(item["model"]) + "</h3><p>" + e(item["sample"]) + "</p>"
        + '<audio controls preload="none" aria-label="' + e(label) + '" src="' + e(item["url"]) + '">'
        + 'Your browser does not support HTML audio. <a href="' + e(item["url"]) + '">Open the WAV</a>.'
        + "</audio><p class=\"meta\">" + f"{item['wave']['duration_seconds']:g} s · {item['wave']['sample_rate_hz']:,} Hz mono · "
        + '<a href="' + e(item["url"]) + '" target="_blank" rel="noopener noreferrer">Open source WAV</a></p></article>'
    )


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_preview(prompt_data, integrity, eval_prompts):
    split_rows = []
    examples = []
    for split, block in prompt_data["splits"].items():
        class_names = [item["name"] for item in block["classes"]]
        split_rows.append({
            "split": split,
            "task_count": len(block["tasks"]),
            "classes": class_names,
            "class_count": len(class_names),
            "description": FAMILY_DESCRIPTIONS[split],
        })
        task = block["tasks"][0]
        examples.append({
            "split": split,
            "id": task["id"],
            "class_name": task["class_name"],
            "scenario_title": task["scenario_title"],
            "skills_tested": task["skills_tested"],
        })
    prompt_record = next(item for item in integrity["files"] if item["source_path"] == "v2/prompts_staged_200.json")
    eval_record = next(item for item in integrity["files"] if item["source_path"] == "v2/eval/eval_prompts.json")
    daily_example = next(task for task in prompt_data["splits"]["Daily"]["tasks"] if task["id"] == "Daily.ordering.001")
    correction_rubric = next(item for item in eval_prompts["task_specific_prompts"] if item["id"] == "correction")
    audio_manifest = json.loads(DEMO_AUDIO_MANIFEST.read_text(encoding="utf-8"))
    preview = {
        "benchmark": "Full-Duplex-Bench v2",
        "paper": PAPER,
        "repository": REPOSITORY,
        "source_revision": REVISION,
        "checked_at_utc": integrity["checked_at_utc"],
        "license": "CC BY-NC 4.0",
        "prompt_file_version": prompt_data["version"],
        "task_count": sum(row["task_count"] for row in split_rows),
        "family_count": len(split_rows),
        "class_count": sum(row["class_count"] for row in split_rows),
        "split_counts": split_rows,
        "settings_declared_in_prompt_file": prompt_data["settings"],
        "source_note_consistency": integrity["validation"]["source_note_consistency"],
        "static_audio_recordings": integrity["dataset"]["static_audio_recordings"],
        "local_files": [
            {"name": "prompts_staged_200.json", "bytes": prompt_record["bytes"], "sha256": prompt_record["sha256"]},
            {"name": "eval_prompts.json", "bytes": eval_record["bytes"], "sha256": eval_record["sha256"]},
        ],
        "examples": examples,
        "prompt_examples": {
            "examiner": {
                "task_id": daily_example["id"],
                "scenario_title": daily_example["scenario_title"],
                "roleplay_excerpt": "Roleplay a customer ordering a breakfast set to-go.",
                "staged_goals": [
                    "Begin with a pickup order request.",
                    "Reveal the drink and bread preference when asked.",
                    "Give a pickup window and the order name.",
                    "Confirm the items, estimated price, and pickup time.",
                ],
                "system_summary": "The shared examiner instructions ask for concise, natural, cooperative spoken turns; details are revealed progressively and the exchange stays short.",
            },
            "judge": {
                "system_excerpt": "You are an impartial evaluator of Channel B.",
                "turn_taking_excerpt": "How natural and well-timed are Channel B’s responses during the conversation?",
                "scoring_summary": "The evaluator scores turn-taking fluency and instruction following per Examinee response event, then gives one task-specific score for correction, entity tracking, or safety.",
                "correction_rubric_summary": "For correction tasks, the rubric checks whether the Evaluatee notices a revised value, acknowledges the correction, and consistently uses the corrected value later.",
                "input_summary": "The pinned runner combines these rubrics with staged goals, channel transcript summaries, and timestamped Channel B segments before calling its configured Gemini evaluator.",
                "default_model": "gemini-2.5-flash-preview-09-2025",
                "output_summary": "JSON with time-bounded turn-taking and instruction-following scores plus a dialogue-level task-specific score.",
                "task_specific_rubric_title": correction_rubric["title"],
            },
        },
        "audio_samples": audio_manifest["samples"],
        "audio_demo_url": audio_manifest["source_demo"],
        "audio_demo_notice": audio_manifest["source_notice"],
        "author_reported_task_scores": PAPER_RESULTS,
    }
    RESEARCH.mkdir(parents=True, exist_ok=True)
    (RESEARCH / "preview.json").write_text(json.dumps(preview, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (RESEARCH / "integrity.json").write_text(json.dumps(integrity, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return preview


def render_page(preview):
    css_hash = hashlib.sha256((ROOT / "assets/site.css").read_bytes()).hexdigest()[:12]
    task_json = f"{REPOSITORY}/blob/{REVISION}/v2/prompts_staged_200.json"
    eval_json = f"{REPOSITORY}/blob/{REVISION}/v2/eval/eval_prompts.json"
    source_tree = f"{REPOSITORY}/tree/{REVISION}/v2"
    audit_url = "research/full-duplex-bench-v2/integrity.json"
    task_rows = []
    task_cards = []
    for row in preview["split_counts"]:
        task_rows.append(
            "<tr><th scope=\"row\">" + e(row["split"]) + "</th>"
            + "<td>" + str(row["task_count"]) + "</td>"
            + "<td>" + str(row["class_count"]) + "</td>"
            + "<td>" + e(", ".join(row["classes"])) + "</td>"
            + "<td>" + e(row["description"]) + "</td></tr>"
        )
    for item in preview["examples"]:
        task_cards.append(
            "<article class=\"card fdbv2-example\"><span class=\"tag\">" + e(item["split"]) + " · " + e(item["class_name"]) + "</span>"
            + "<h3>" + e(item["scenario_title"]) + "</h3><p class=\"meta\">Example task ID: <code>" + e(item["id"]) + "</code></p>"
            + "<p>Skill labels: " + e(", ".join(item["skills_tested"])) + "</p></article>"
        )
    result_rows = []
    for row in preview["author_reported_task_scores"]:
        result_rows.append(
            "<tr><th scope=\"row\">" + e(row["system"]) + "</th><td>" + e(row["pacing"]) + "</td>"
            + "<td>" + f"{row['correction']:.2f}" + "</td><td>" + f"{row['entity_tracking']:.2f}" + "</td>"
            + "<td>" + f"{row['safety']:.2f}" + "</td></tr>"
        )
    audit = preview["source_note_consistency"]
    status_label = "Validated with a source metadata caveat" if audit["mismatch"] else "Validated"
    file_rows = []
    for item in preview["local_files"]:
        file_rows.append(
            "<tr><th scope=\"row\">" + e(item["name"]) + "</th><td>" + f"{item['bytes']:,}" + "</td>"
            + "<td><code>" + e(item["sha256"]) + "</code></td></tr>"
        )
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="An integrity-checked preview of Full-Duplex-Bench v2: 200 staged prompts for real-time multi-turn audio evaluation, four task families, source hashes, scoring protocol and paper-reported reference scores.">
<meta name="color-scheme" content="light dark">
<title>Full-Duplex-Bench v2 Preview — AI2AI Duplex</title>
<link rel="stylesheet" href="assets/site.css?v={css_hash}">
<script src="assets/site.js" defer></script>
<style>
.fdbv2-table-scroll {{ overflow-x:auto; margin:20px 0; border:1px solid var(--border); border-radius:12px; background:var(--surface); }}
.fdbv2-table {{ width:100%; min-width:760px; border-collapse:collapse; }}
.fdbv2-table caption {{ padding:16px; color:var(--muted); font-weight:700; text-align:left; }}
.fdbv2-table th, .fdbv2-table td {{ padding:13px 16px; border-top:1px solid var(--border); text-align:left; vertical-align:top; }}
.fdbv2-table th[scope="row"] {{ min-width:135px; }}
.fdbv2-table td.numeric {{ white-space:nowrap; font-variant-numeric:tabular-nums; }}
.fdbv2-example {{ min-width:0; }}
.fdbv2-audio-card {{ min-width:0; }}
.fdbv2-audio-card audio {{ display:block; width:100%; min-height:44px; margin:12px 0; }}
.fdbv2-prompt-card {{ min-width:0; }}
.fdbv2-prompt-card ol {{ padding-left:22px; }}
.fdbv2-hash {{ overflow-wrap:anywhere; }}
.fdbv2-license {{ overflow-wrap:anywhere; }}
</style>
</head>
<body>
<a class="skip-link" href="#main">Skip to benchmark preview</a>
<header class="site-nav"><div class="nav-inner"><a class="brand" href="./">AI2AI Duplex</a>{project_tabs('literature')}</div></header>
<main id="main"><div class="container">{review_tabs('fdb2')}
<header class="hero" id="fdb-v2-review"><p class="eyebrow">Literature review · Dataset and protocol preview</p>
<h1>Full-Duplex-Bench v2: evaluating live multi-turn speech interaction</h1>
<p class="lede">The pinned v2 task set contains 200 staged role-play prompts across Daily, Correction, Entity Tracking, and Safety. It is designed for live Examiner–Evaluatee audio conversations; the release contains prompt JSON rather than a static recording corpus.</p>
<p class="meta">{datetime.now().astimezone().strftime('%d %B %Y')} · Source revision <code>{REVISION[:12]}</code> · {e(status_label)} · No local model inference or benchmark scoring</p>
<div class="button-row"><a class="button primary" href="#audio-examples">Listen to audio</a><a class="button" href="#prompt-examples">See prompt examples</a><a class="button" href="{e(task_json)}">Pinned task JSON</a><a class="button" href="{e(eval_json)}">Pinned judge prompts</a><a class="button" href="{e(PAPER)}">ACL 2026 paper</a></div></header>
<nav class="jump-links" aria-label="Full-Duplex-Bench v2 sections"><a href="#benchmark-scope">Tests and limits</a><a href="#overview">At a glance</a><a href="#task-design">Task design</a><a href="#response-flow">How responses start</a><a href="#audio-examples">Audio examples</a><a href="#examples">Example tasks</a><a href="#prompt-examples">Prompt examples</a><a href="#evaluation">Scoring</a><a href="#paper-results">Paper results</a><a href="#audit">Download audit</a><a href="#attribution">Attribution</a></nav>
{render_scope_section(['fdb-v2'], number=1)}
<section class="section" id="overview"><h2>At a glance</h2>
<p class="section-intro">FDB-v2 uses a spoken Examiner to guide the model under evaluation through a staged conversation. The task JSON and scoring prompts are checked against the official repository at one pinned revision.</p>
<div class="stat-grid"><div class="stat"><strong>{preview['task_count']}</strong><span>staged task prompts</span></div>
<div class="stat"><strong>{preview['family_count']}</strong><span>task families, 50 prompts each</span></div>
<div class="stat"><strong>{preview['class_count']}</strong><span>scenario classes</span></div>
<div class="stat"><strong>0</strong><span>audio files in the downloaded prompt package</span></div></div>
<p>The Examiner delivers synthesized speech and adjusts the next goal based on the Evaluatee’s response. The paper describes Fast and Slow pacing, a streaming WebRTC orchestrator, and a canonical 48 kHz mono PCM interface with 10 ms frames. The two roles are the Examiner and the Evaluatee; this is not a multi-party group-conversation benchmark.</p>
<div class="callout"><h3>What is in the local download</h3><p>The workspace stores the task set, evaluator prompt file, and upstream license under <code>data/benchmarks/full_duplex_bench_v2/</code>. The prompt release contains no WAVs, but the authors’ demo separately hosts recorded evaluation examples. Three demo clips are playable below and stream from the authors’ site.</p></div>
</section>
<section class="section" id="audio-examples"><h2>Listen to author-hosted audio examples</h2>
<p class="section-intro">These are actual recorded clips from the benchmark authors’ demo: one Daily-family, Sample 1, Fast-pacing set across three evaluated systems. They are not recordings packaged with our downloaded prompt JSON and are not local model outputs. The source demo labels its audio samples for research use.</p>
<div class="card-grid">{''.join(render_audio_card(item) for item in preview['audio_samples'])}</div>
<p class="meta">Audio is streamed directly from the <a href="{e(preview['audio_demo_url'])}" target="_blank" rel="noopener noreferrer">authors’ FDB-v2 demo</a>; this page does not rehost the WAVs. <a href="research/full-duplex-bench-v2/audio-samples.json">Clip URLs, WAV metadata, and SHA-256 audit</a>.</p>
</section>
<section class="section" id="task-design"><h2>Four prompt families</h2>
<p class="section-intro">Each task includes an examiner role, a staged semantic-goal prompt, skill labels, metric-focus labels, and a flag allowing examiner barge-in. The v6 prompt file declares a five-turn limit and a 60-second duration setting.</p>
<div class="fdbv2-table-scroll" role="region" aria-label="Full-Duplex-Bench v2 task family counts" tabindex="0"><table class="fdbv2-table"><caption>Table 2. Counts from the locally validated v6 prompt arrays; class names are copied from the prompt file.</caption>
<thead><tr><th scope="col">Family</th><th scope="col">Prompts</th><th scope="col">Classes</th><th scope="col">Class names</th><th scope="col">Focus</th></tr></thead><tbody>{''.join(task_rows)}</tbody></table></div>
<p>The paper describes Fast as more proactive, including stage-completion interruptions and backchannels, and Slow as waiting for an end of turn or long pause. These are interaction settings, not separate pre-recorded audio versions of each prompt. The pinned adapter’s actual response triggers and Fast/Slow interruption flags are explained below because they do not fully match that description.</p>
</section>
<section class="section" id="response-flow"><h2>What makes the Examiner speak?</h2>
<p class="section-intro">The Examiner is a live GPT-Realtime speech session. The orchestrator continuously forwards the Evaluatee’s audio to it; this is an audio path, not a requirement to first produce a transcript. The pinned adapter leaves optional input-audio transcription unset.</p>
<div class="card-grid">
<article class="card"><span class="tag">1 · Opening</span><h3>One explicit start request</h3><p>After the Examiner session is configured, the adapter’s Role A autostart sends a <code>response.create</code> event. This starts the opening response using the current session instructions and conversation context.</p></article>
<article class="card"><span class="tag blue">2 · Later turns</span><h3>VAD detects a pause</h3><p>For later turns, the adapter sets <code>server_vad</code> and <code>create_response: true</code>. The Realtime service watches incoming audio for speech and silence; when it reports that speech has stopped, it automatically starts a response. This is a response-generation trigger, not a guarantee of a useful or audible answer.</p></article>
<article class="card"><span class="tag amber">3 · What it hears</span><h3>Audio received so far</h3><p>The Examiner receives streaming audio as it arrives. If a short pause is mistaken for the end of a turn, the automatic response can start using only the utterance heard so far—even if the Evaluatee was about to continue. The source has no separate partial-ASR message that tells the Examiner when to speak.</p></article>
<article class="card"><span class="tag">4 · While it is speaking</span><h3>A VAD setting controls cancellation</h3><p><code>interrupt_response</code> means “cancel the Examiner’s current output when new incoming speech starts.” It does not mean “decide semantically that it is time to interrupt the other speaker.” If false, the existing response continues; if true, new speech can cancel it.</p></article>
</div>
<div class="callout"><h3>Why can the demo have awkward overlap?</h3><p>For example, the Evaluatee says “I can come Friday,” pauses briefly, then continues “morning after ten.” If VAD treats that pause as the end of speech, it starts the Examiner’s reply before the sentence is complete. If the Evaluatee resumes while that reply is playing, both audio streams may overlap; whether the Examiner’s output is canceled depends on <code>interrupt_response</code>. The orchestrator forwards both directions and does not assign the floor to one speaker, so overlap in a clip does not by itself show that the Examiner deliberately chose a semantic interruption.</p></div>
<div class="callout amber"><h3>The paper and this pinned adapter disagree</h3><p>The paper says Fast may speak at stage completion or give backchannels, while Slow waits for an end of turn or a long pause. Its Appendix C config examples set <code>interrupt_response</code> to true for Fast and false for Slow. In the inspected pinned adapter, the values are reversed: Fast sets it to false, Slow sets it to true. Both set <code>create_response: true</code>; the source does not show a separate event that starts an Examiner response when a semantic stage is complete. The Fast adapter also sets a 600 ms silence duration, while Slow leaves the service defaults unspecified. This mismatch means the pinned code alone cannot establish which settings produced the author-hosted demo clips.</p>
<p class="meta">Sources: <a href="{e(REPOSITORY)}/blob/{REVISION}/v2/adapters/gptRealtime_adapter.js">pinned Realtime adapter</a>; <a href="{e(REPOSITORY)}/blob/{REVISION}/v2/orchestrator.js">pinned audio orchestrator</a>; <a href="{e(PAPER)}">paper, §2 and Appendix C</a>; <a href="https://platform.openai.com/docs/api-reference/realtime-client-events/session?lang=node.js">Realtime API turn-detection documentation</a>.</p></div>
<div class="callout"><h3>Does <code>response.create</code> attach a <code>&lt;bos&gt;</code> token?</h3><p>The code sends a JSON event named <code>response.create</code>; the API describes that event as starting a new response and triggering model inference. The checked source contains no literal <code>&lt;bos&gt;</code> token or token IDs. The API hides its internal conversation serialization, so this source cannot confirm whether the service uses any internal beginning-of-sequence marker. The precise claim supported by the evidence is that the event starts response generation—not that it visibly inserts a BOS token.</p>
<p class="meta">Sources: <a href="{e(REPOSITORY)}/blob/{REVISION}/v2/adapters/gptRealtime_adapter.js">pinned adapter’s autostart</a> and <a href="https://platform.openai.com/docs/api-reference/realtime-client-events/session?lang=node.js">Realtime API <code>response.create</code> event</a>.</p></div>
</section>
<section class="section" id="examples"><h2>Four example scenarios</h2>
<p class="section-intro">These cards show the first task ID and short scenario title in each split. They identify the format without reproducing the complete public prompt set.</p>
<div class="card-grid">{''.join(task_cards)}</div>
</section>
<section class="section" id="prompt-examples"><h2>What prompts do the Examiner and judge use?</h2>
<p class="section-intro">The Examiner gets a task-specific role prompt and staged goals. The separate judge prompt file defines scoring dimensions and output format. The pinned runner sends the judge ASR transcript summaries and timestamps, not raw audio.</p>
<div class="card-grid">
<article class="card fdbv2-prompt-card"><span class="tag">Examiner · {e(preview['prompt_examples']['examiner']['task_id'])}</span><h3>{e(preview['prompt_examples']['examiner']['scenario_title'])}</h3>
<p><strong>Task-prompt excerpt:</strong> “{e(preview['prompt_examples']['examiner']['roleplay_excerpt'])}”</p>
<p>{e(preview['prompt_examples']['examiner']['system_summary'])}</p>
<p><strong>Staged goals, summarized:</strong></p><ol>{''.join('<li>' + e(goal) + '</li>' for goal in preview['prompt_examples']['examiner']['staged_goals'])}</ol>
<p class="meta">The runner passes the task’s Examiner system prompt and task prompt to Channel A; Channel B is the model being evaluated.</p></article>
<article class="card fdbv2-prompt-card"><span class="tag blue">LLM judge · {e(preview['prompt_examples']['judge']['default_model'])}</span><h3>{e(preview['prompt_examples']['judge']['task_specific_rubric_title'])} and event-level scoring</h3>
<p><strong>System-prompt excerpt:</strong> “{e(preview['prompt_examples']['judge']['system_excerpt'])}”</p>
<p><strong>Turn-taking rubric excerpt:</strong> “{e(preview['prompt_examples']['judge']['turn_taking_excerpt'])}”</p>
<p>{e(preview['prompt_examples']['judge']['correction_rubric_summary'])} {e(preview['prompt_examples']['judge']['scoring_summary'])}</p>
<p>{e(preview['prompt_examples']['judge']['input_summary'])}</p>
<details><summary>Illustrative output shape</summary><pre><code>{{
  "turn_events": [
    {{"start": 1.2, "end": 2.1, "turn_taking": 4, "instruction_following": 5}}
  ],
  "task_specific_score": 4
}}</code></pre><p class="meta">The pinned prompt requests a parseable JSON result with event time ranges and a global task-specific score; field names above are simplified for readability.</p></details>
<p class="meta">The source evaluator prompt includes separate rubrics for turn-taking fluency, multi-turn instruction following, and the task-specific family. <a href="{e(eval_json)}">Open the full pinned judge prompt JSON</a>.</p></article>
</div>
</section>
<section class="section" id="evaluation"><h2>How the live evaluation is scored</h2>
<div class="card-grid">
<article class="card"><span class="tag">Turn-taking fluency</span><h3>Coordination at each event</h3><p>The automated judge labels Evaluatee turn-taking events and scores response naturalness and timing on a 1–5 scale. The paper discusses overlaps and handoffs and reports scores over the dialogue timeline.</p></article>
<article class="card"><span class="tag blue">Instruction following</span><h3>Staged goals across turns</h3><p>A separate 1–5 event score measures whether the model understands and executes the Examiner’s current semantic goal while retaining earlier constraints.</p></article>
<article class="card"><span class="tag amber">Task-specific competence</span><h3>Dialogue-level outcome</h3><p>Correction Handling, Entity Tracking, and Safety receive one global 1–5 score per dialogue. Daily prompts are evaluated through the shared turn-taking and instruction-following dimensions.</p></article>
</div>
<p>The paper’s setup uses a synthesized-speech GPT-Realtime Examiner, Parakeet-TDT transcription, and a Gemini 2.5 Flash judge. Reproduction therefore depends on model/API versions and evaluator prompts in addition to the static task file. The authors report judge–human Krippendorff’s α values from 0.588 to 0.693 across metrics; these figures describe their validation study, not this local data audit.</p>
<div class="callout amber"><h3>Timing coverage is partial</h3><p>FDB-v2 scores perceived turn-taking fluency during live streaming and plots event scores over time. The paper does not report an absolute first-response or interruption-stop latency metric. A smoothness score should not be interpreted as a measured stop delay.</p></div>
</section>
<section class="section" id="paper-results"><h2>Author-reported task-specific scores</h2>
<p class="section-intro">These are the authors’ global task-specific scores from ACL 2026 Table 1, not local model runs. Scores range from 1 to 5; higher is better. Turn-taking fluency and instruction-following trajectory results are reported separately in the paper’s Figure 2.</p>
<div class="fdbv2-table-scroll" role="region" aria-label="Author-reported FDB-v2 task-specific scores" tabindex="0"><table class="fdbv2-table"><caption>Table 3. Paper-reported Correction, Entity Tracking, and Safety scores by system and Examiner pacing; 1–5 scale.</caption>
<thead><tr><th scope="col">System</th><th scope="col">Pacing</th><th scope="col">Correction</th><th scope="col">Entity Tracking</th><th scope="col">Safety</th></tr></thead><tbody>{''.join(result_rows)}</tbody></table></div>
<p>Fast and Slow are independent Examiner settings. The paper notes that slower pacing can help some systems recover instruction-following performance on memory-heavy tasks. The table is a context reference only and has not been recomputed from the downloaded prompts.</p>
</section>
<section class="section" id="audit"><h2>Download and integrity audit</h2>
<p class="section-intro">The task set was extracted byte-for-byte from the official repository at commit <a href="{e(REPOSITORY + '/commit/' + REVISION)}"><code>{REVISION}</code></a>. The scoring prompt and license were copied from that same commit. The audit checks hashes against Git blobs, parses all JSON, verifies every task ID and class reference, and checks the expected per-family counts.</p>
<div class="fdbv2-table-scroll" role="region" aria-label="Downloaded FDB-v2 file hashes" tabindex="0"><table class="fdbv2-table"><caption>Table 4. Locally downloaded files; SHA-256 values match the recorded import manifest and pinned Git blobs.</caption>
<thead><tr><th scope="col">File</th><th scope="col">Bytes</th><th scope="col">SHA-256</th></tr></thead><tbody>{''.join(file_rows)}</tbody></table></div>
<div class="callout amber"><h3>Upstream note does not match the data arrays</h3><p>The source JSON’s top-level note says it stages 150 tasks across Daily, Correction, and Entity Tracking. Its actual arrays contain 200 unique prompts: 50 in each of four splits, including Safety. All four arrays, task schemas, class references, and pinned-source hashes pass validation. The stale note remains unchanged in the downloaded file and is recorded as a metadata caveat in the <a href="{e(audit_url)}">full integrity report</a>.</p></div>
<p>The audit is for the prompt release, not audio quality. No audio files are packaged in the checked v2 task directory; the audio section links to author-hosted demo recordings instead. No benchmark model inference, transcription, judging, or GPU allocation was performed for this page.</p>
<p class="meta">Audit status: <strong>{e(status_label)}</strong> · {preview['task_count']} prompts · {preview['class_count']} classes · pinned source SHA-256 checks passed</p>
</section>
<section class="section" id="attribution"><h2>Attribution, license, and related versions</h2>
<p class="fdbv2-license"><strong>Full-Duplex-Bench v2</strong> by Guan-Ting Lin, Shih-Yun Shan Kuan, Jiatong Shi, Kai-Wei Chang, Siddhant Arora, Shinji Watanabe, and Hung-yi Lee. “Full-Duplex-Bench-v2: A Multi-Turn Evaluation Framework for Duplex Dialogue Systems with an Automated Examiner.” In <em>Proceedings of the 64th Annual Meeting of the Association for Computational Linguistics (Volume 2: Short Papers)</em>, pages 27–36, 2026. <a href="{e(PAPER)}">ACL Anthology</a>; DOI <a href="https://doi.org/10.18653/v1/2026.acl-short.4">10.18653/v1/2026.acl-short.4</a>.</p>
<p>Source repository: <a href="{e(source_tree)}">Full-Duplex-Bench v2 at the pinned revision</a>. The repository’s top-level dataset/code license is <a href="{e(LICENSE_URL)}">CC BY-NC 4.0</a>. Short prompt excerpts and the playable sample recordings are attributed in the <a href="{e(preview['audio_demo_url'])}">authors’ demo</a> and full <a href="research/full-duplex-bench-v2/ATTRIBUTION.md">attribution record</a>; the page does not imply endorsement by the authors.</p>
<p>Compare versions: <a href="full-duplex-bench.html">Full-Duplex-Bench v3</a> evaluates tool use with released human recordings; <a href="{e(REPOSITORY + '/tree/' + REVISION + '/v1_v1.5')}">v1/v1.5</a> cover earlier static turn-taking and overlap tests.</p>
<details><summary>Paper citation (BibTeX)</summary><pre><code>@inproceedings{{lin-etal-2026-full,
  title = {{Full-Duplex-{{B}}ench-v2: A Multi-Turn Evaluation Framework for Duplex Dialogue Systems with an Automated Examiner}},
  author = {{Lin, Guan-Ting and Kuan, Shih-Yun Shan and Shi, Jiatong and Chang, Kai-Wei and Arora, Siddhant and Watanabe, Shinji and Lee, Hung-yi}},
  booktitle = {{Proceedings of the 64th Annual Meeting of the Association for Computational Linguistics (Volume 2: Short Papers)}},
  pages = {{27--36}},
  year = {{2026}},
  doi = {{10.18653/v1/2026.acl-short.4}}
}}</code></pre></details>
</section>
<footer class="site-footer"><p>AI2AI Duplex · Literature review · <a href="index.html#literature-review">Back to duplex landscape</a> · <a href="{e(source_tree)}">Official source</a></p></footer>
</div></main>
</body></html>
'''


def main():
    prompt_data = json.loads((DATA / "prompts_staged_200.json").read_text(encoding="utf-8"))
    integrity = json.loads(INTEGRITY_SOURCE.read_text(encoding="utf-8"))
    eval_prompts = json.loads((DATA / "eval_prompts.json").read_text(encoding="utf-8"))
    preview = build_preview(prompt_data, integrity, eval_prompts)
    page = render_page(preview)
    PAGE.write_text(page, encoding="utf-8")
    print(f"Built {PAGE.relative_to(ROOT)} from {preview['task_count']} validated prompt entries")


if __name__ == "__main__":
    main()
