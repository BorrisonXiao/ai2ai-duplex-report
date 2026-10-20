#!/usr/bin/env python3
"""Build a local integrity and coverage preview for MultiTalkBench test data."""

from __future__ import annotations

import hashlib
from html import escape
import json
from pathlib import Path

from benchmark_scope import render_scope_section
from site_navigation import project_tabs, review_tabs
from multitalk_protocol import render_protocol


ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "research/multitalk-bench/validation.json"
PREVIEW_PATH = ROOT / "research/multitalk-bench/preview.json"


def e(value):
    return escape(str(value), quote=True)


def build() -> Path:
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    preview = json.loads(PREVIEW_PATH.read_text(encoding="utf-8"))
    if audit.get("validation", {}).get("status") != "passed":
        raise ValueError("The test data validation audit has not passed")
    if audit.get("revision") != preview.get("revision"):
        raise ValueError("Preview audio and dataset audit refer to different snapshots")

    css_digest = hashlib.sha256((ROOT / "assets/site.css").read_bytes()).hexdigest()[:12]
    cards = []
    for item in preview["examples"]:
        audio_path = ROOT / item["site_audio"]
        if hashlib.sha256(audio_path.read_bytes()).hexdigest() != item["site_audio_sha256"]:
            raise ValueError(f"Published excerpt hash mismatch: {item['site_audio']}")
        if item["excerpt_duration_seconds"] != 15.0 or item["sample_rate_hz"] != 16000 or item["channels"] != 2:
            raise ValueError(f"Unexpected preview format or duration: {item['sample_id']}")
        language = "English" if item["language"] == "en" else "Chinese"
        audio_url = e(item["site_audio"] + "?v=" + item["site_audio_sha256"][:12])
        cards.append(
            '<article class="card mtb-example"><span class="tag">'
            + e(language) + " · " + e(item["meeting_id"]) + "</span><h3>Target participant "
            + "<code>" + e(item["target_speaker"]) + "</code></h3>"
            + '<p class="meta">15-second source crop at '
            + f'{item["excerpt_start_seconds"]:.2f}–{item["excerpt_end_seconds"]:.2f} s · 16 kHz stereo PCM16</p>'
            + '<audio controls preload="none" aria-label="Play the ' + e(language)
            + ' MultiTalkBench excerpt"><source src="' + audio_url + '" type="audio/flac">'
            + 'Audio playback is unavailable. <a href="' + audio_url + '">Download the FLAC excerpt</a>.</audio>'
            + '<p class="mtb-transcript"><strong>Aligned target-speaker utterance ('
            + f'{item["transcript_start_seconds"]:.2f}–{item["transcript_end_seconds"]:.2f} s):</strong> '
            + e(item["transcript_text"]) + "</p>"
            + '<p class="meta">Source: <code>' + e(item["source_audio"])
            + "</code>; transcript: <code>" + e(item["source_alignment"]) + "</code>.</p></article>"
        )

    summary = audit["summary"]
    validation = audit["validation"]
    language_rows = [
        ("English", summary["languages"]["en"], "60 of 104 samples"),
        ("Chinese", summary["languages"]["zh"], "44 of 104 samples"),
        ("All samples", summary["examples"], f'{summary["audio_hours"]:.2f} hours across {summary["meetings"]} meetings'),
    ]
    language_table = "".join(
        "<tr><th scope=\"row\">" + e(language) + "</th><td>" + e(count) + "</td><td>" + e(note) + "</td></tr>"
        for language, count, note in language_rows
    )
    audit_items = [
        ("Release inventory", f'{validation["release_files_present"]} of {validation["release_files_expected"]} files present; all file sizes match the pinned Hub tree.'),
        ("Local hashes", f'SHA-256 recorded for all {validation["release_files_present"]} release files.'),
        ("Tabular split", f'{validation["metadata_rows"]} JSONL, {validation["csv_rows"]} CSV, and {validation["parquet_rows"]} Parquet rows agree, including all audio paths.'),
        ("Audio decode", f'{validation["audio_format_counts"][0]["files"]} of {summary["examples"]} recordings fully decoded as 16 kHz stereo FLAC PCM16.'),
        ("Aligned text", f'{validation["alignment_entries"]["sentence_alignments"]:,} sentence spans and {validation["alignment_entries"]["word_alignments"]:,} word spans fall within recording durations.'),
        ("Referenced assets", "Every audio, alignment, persona, meeting profile, and transcript-context path exists; profile IDs match sample meeting IDs."),
    ]
    audit_html = "".join(
        '<article class="mtb-audit-item"><h3>' + e(label) + "</h3><p>" + e(detail) + "</p></article>"
        for label, detail in audit_items
    )
    scope = render_scope_section(["multitalk"], number=1)
    revision = audit["revision"]
    release_bytes = validation["release_total_bytes"]
    protocol = render_protocol()

    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="MultiTalkBench evaluation protocol, exact Gemma judge prompt examples, scoring rules, two audio excerpts and a complete test-data audit.">
<meta name="color-scheme" content="light dark">
<title>MultiTalkBench Evaluation and Test Data — AI2AI Duplex</title>
<link rel="stylesheet" href="assets/site.css?v={css_digest}">
<script src="assets/site.js" defer></script>
<script>window.MathJax = {{tex: {{inlineMath: [['\\\\(', '\\\\)']], displayMath: [['\\\\[', '\\\\]']]}}, svg: {{fontCache: 'global'}}}};</script>
<script id="MathJax-script" defer src="assets/vendor/mathjax/tex-svg.js"></script>
<style>
.mtb-preview-figure {{ margin:24px 0; }}
.mtb-example {{ display:flex; flex-direction:column; }}
.mtb-example audio {{ width:100%; margin:12px 0; }}
.mtb-example .meta {{ overflow-wrap:anywhere; }}
.mtb-transcript {{ color:var(--text)!important; overflow-wrap:anywhere; }}
.mtb-audit-grid {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:12px; margin:22px 0; }}
.mtb-audit-item {{ padding:18px; border:1px solid var(--border); border-radius:12px; background:var(--surface); }}
.mtb-audit-item h3 {{ font-size:16px; }}
.mtb-audit-item p {{ margin:0; color:var(--muted); font-size:14px; }}
.mtb-prompt {{ min-width:0; }}
.mtb-prompt summary {{ overflow-wrap:anywhere; }}
.hero h1 {{ overflow-wrap:anywhere; }}
.container pre {{ white-space:pre-wrap; overflow-wrap:anywhere; }}
.container code {{ overflow-wrap:anywhere; }}
.mtb-prompt pre, #illustrative-transcript pre {{ white-space:pre-wrap; overflow-wrap:anywhere; padding:16px; border-radius:8px; background:var(--surface-2); font-size:13px; line-height:1.6; max-height:600px; overflow:auto; }}
.mtb-workflow li {{ margin:12px 0; }}
.mtb-call-list {{ display:grid; gap:18px; margin:20px 0; }}
.mtb-call {{ padding:20px; border:1px solid var(--border); border-radius:12px; background:var(--surface); min-width:0; }}
.mtb-call h4 {{ font-size:20px; line-height:1.35; margin:8px 0 14px; }}
.mtb-call .meta {{ margin:0; }}
.mtb-teaching-case {{ padding:20px; margin:22px 0; border-radius:12px; background:var(--accent-soft); }}
.mtb-teaching-case li {{ margin:8px 0; }}
.equation {{ overflow-x:auto; margin:14px 0; padding:14px 16px; border-radius:9px; background:var(--surface-2); }}
.equation mjx-container[display="true"] {{ margin:0 !important; }}
mjx-container {{ max-width:100%; }}
@media (max-width:700px) {{ .mtb-audit-grid {{ grid-template-columns:minmax(0,1fr); }} }}
</style>
</head>
<body>
<a class="skip-link" href="#main">Skip to MultiTalkBench review</a>
<header class="site-nav"><div class="nav-inner"><a class="brand" href="./">AI2AI Duplex</a>{project_tabs("literature")}</div></header>
<main id="main"><div class="container">{review_tabs("multitalk")}
<header class="hero"><p class="eyebrow">Literature review · Evaluation protocol and dataset preview</p>
<h1>MultiTalkBench: long, multi-party speech in English and Chinese</h1>
<p class="lede">How a model replaces one participant in a long group conversation, how Gemma judges its contributions, and what those scores can establish.</p>
<p class="meta">MultiTalkBench test split · Checked 19 October 2026 · Hugging Face revision <code>{e(revision[:12])}</code> · Dataset license: CC BY-SA 4.0</p>
<div class="button-row"><a class="button primary" href="#evaluation-protocol">Read the evaluation protocol</a><a class="button" href="#judge-prompts">Inspect actual prompts</a><a class="button" href="#audio-examples">Listen to excerpts</a><a class="button" href="https://huggingface.co/datasets/MultiTalk/MultiTalkBench">Dataset card</a><a class="button" href="https://arxiv.org/abs/2609.36903">Paper</a></div></header>
<nav class="jump-links" aria-label="MultiTalkBench sections"><a href="#benchmark-scope">Tests and limits</a><a href="#overview">At a glance</a><a href="#evaluation-protocol">Protocol</a><a href="#judge-prompts">Judge prompts</a><a href="#scoring">Scoring</a><a href="#evaluation-limits">Interpretation</a><a href="#audio-examples">Audio examples</a><a href="#data-layout">Data layout</a><a href="#validation">Local validation</a><a href="#reproduce">Reproduce</a><a href="#provenance">Attribution</a></nav>
{scope}
<section class="section" id="overview"><h2>At a glance</h2>
<p class="section-intro">MultiTalkBench is a held-out, long-form speech-to-speech benchmark. Each row pairs a real meeting recording with a designated participant, that participant’s aligned speech, and persona/context material. The evaluated model takes the designated participant’s role while the other participants remain part of the conversation.</p>
<div class="stat-grid"><div class="stat"><strong>{summary["examples"]}</strong><span>test samples</span></div>
<div class="stat"><strong>{summary["meetings"]}</strong><span>distinct meetings</span></div>
<div class="stat"><strong>{summary["audio_hours"]:.2f} h</strong><span>sum of sample audio durations</span></div>
<div class="stat"><strong>EN 60 · ZH 44</strong><span>English and Chinese samples</span></div></div>
<div class="table-wrap"><table id="mtb-composition"><caption>Table 2. Test samples by language and recorded audio duration.</caption>
<thead><tr><th scope="col">Split</th><th scope="col">Samples</th><th scope="col">Coverage</th></tr></thead><tbody>{language_table}</tbody></table></div>
<p>The release describes tests of long conversations, multi-party participation, and bilingual ability. It includes explicit probes for long-range entity tracking and topic coherence alongside addressee selection and turn-taking. The scope table above distinguishes those content and participation judgments from direct interruption latency, acoustic fluency, and tool-use evaluation.</p>
</section>
{protocol}
<section class="section" id="audio-examples"><h2>Two source excerpts</h2>
<p class="section-intro">These short English and Chinese examples come from the held-out test release. Each player contains a 15-second crop from a stereo recording; the aligned utterance and exact source interval are shown below it.</p>
<figure class="mtb-preview-figure"><div class="card-grid">{''.join(cards)}</div>
<figcaption>Figure 1. Two lossless excerpts from distinct MultiTalkBench test meetings. The excerpt crops preserve the source sample rate and stereo channels; they are dataset examples, not model outputs.</figcaption></figure>
</section>
<section class="section" id="data-layout"><h2>What is in the release</h2>
<p>The pinned snapshot includes the official test Parquet shard, JSONL and CSV metadata, full meeting audio, word- and sentence-level alignments, target-speaker persona prompts, meeting profiles, and transcript context. The metadata and Parquet row counts agree. Each sample represents one meeting and target-participant pair; several participants from one meeting share meeting-level material.</p>
<div class="card-grid"><article class="card"><h3>Inputs and identity</h3><p><code>audio</code> identifies the stereo meeting recording. <code>target_speaker</code> and <code>persona</code> specify whose role the model fills. The alternative minimal prompt supports a persona-off condition.</p></article>
<article class="card"><h3>Reference and context</h3><p><code>alignment</code> provides sentence and word spans for the target participant. <code>meeting_profile</code> and <code>transcript_context</code> provide meeting-level material used by the benchmark pipeline.</p></article></div>
<div class="callout amber"><h3>Keep test data held out</h3><p>This is the MultiTalkBench <code>test</code> split. The separate MultiTalkFT release is a fine-tuning corpus, not this benchmark’s test set. The workspace already contains a 158 MB MultiTalkFT pilot with manifests, a 100-row preview, and three English audio examples; it is not a complete corpus. The benchmark data and the training pilot remain in separate directories.</p></div>
</section>
<section class="section" id="validation"><h2>Local release validation</h2>
<p class="section-intro">The complete local copy was checked against Hugging Face commit <code>{e(revision)}</code>. Validation covers the downloaded inventory and sizes, row agreement across the three tabular views, every referenced asset, full FLAC decoding, and alignment bounds.</p>
<div class="mtb-audit-grid">{audit_html}</div>
<p>The repository snapshot is {release_bytes:,} bytes (5.19 GB decimal; about 4.83 GiB). The Parquet shard stores an audio payload column, so its metadata and non-audio columns were read without loading the multi-gigabyte audio column into memory. The separate audio files were all decoded in bounded blocks.</p>
<div class="callout"><h3>No model evaluation is claimed here</h3><p>The local checks validate the released data and the prompt examples document the public evaluator. No local model inference, judge requests, benchmark scores or quality claim have been produced from this snapshot.</p></div>
</section>
<section class="section" id="reproduce"><h2>Reproduce the data checks</h2>
<p>From the project workspace, download the same pinned snapshot and run the validator and preview exporter:</p>
<pre><code>python scripts/download_assets.py multitalkbench
envs/data/bin/python scripts/validate_multitalk_bench.py
envs/data/bin/python scripts/export_multitalk_bench_preview.py
python site/scripts/build_multitalk_bench.py</code></pre>
<p>The site hosts only two short, attributed excerpts and the integrity record; it does not mirror the full 5.19 GB release into GitHub Pages.</p>
</section>
<section class="section" id="provenance"><h2>Source, attribution and license</h2>
<p>MultiTalkBench is released by Ke Wang, Houxing Ren, Zimu Lu, Yunqiao Yang, Zhuofan Zong, Mingjie Zhan, and Hongsheng Li. The dataset card identifies <a href="https://creativecommons.org/licenses/by-sa/4.0/">CC BY-SA 4.0</a>. The two preview excerpts are 15-second crops, with source sample rate and stereo channels retained; they are provided under the same license. Source hash, excerpt bounds, and webpage asset hash are recorded in the <a href="research/multitalk-bench/preview.json">preview manifest</a>.</p>
<p>Paper: <a href="https://arxiv.org/abs/2609.36903">MultiTalk: Scaling Full-Duplex Speech Models to Long, Multi-Party, Bilingual Conversation</a>. Data card and full download: <a href="https://huggingface.co/datasets/MultiTalk/MultiTalkBench">Hugging Face MultiTalkBench</a>. The local release’s <a href="research/multitalk-bench/validation.json">validation and SHA-256 inventory</a> records the exact snapshot and checked counts. Full upstream attribution details are in the <a href="research/multitalk-bench/ATTRIBUTION.md">attribution record</a>.</p>
</section>
<footer class="site-footer"><p>MultiTalkBench data preview · <a href="index.html#literature-review">Return to the duplex landscape</a> · <a href="context-assistance.html#benchmark-scope">Compare benchmark scope</a> · <a href="https://huggingface.co/datasets/MultiTalk/MultiTalkBench">Open the dataset card</a></p></footer>
</div></main>
</body>
</html>
"""
    target = ROOT / "multitalk-bench.html"
    target.write_text(page, encoding="utf-8")
    print(f"Built {target.name}: {summary['examples']} test samples, {validation['release_files_present']} audited release files.")
    return target


if __name__ == "__main__":
    build()
