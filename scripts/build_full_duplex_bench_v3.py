#!/usr/bin/env python3
"""Build the Full-Duplex-Bench v3 preview from the locally audited release."""

import audioop
from datetime import datetime
import hashlib
import html
import json
from pathlib import Path
import shutil
import sys
import wave


ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT.parent
DATA = PROJECT_ROOT / "data/benchmarks/full_duplex_bench_v3/fdb_v3_data_released"
INTEGRITY_SOURCE = PROJECT_ROOT / "reports/full_duplex_bench_v3_integrity.json"
RESEARCH = ROOT / "research/full-duplex-bench-v3"
ASSETS = ROOT / "assets/full-duplex-bench-v3"
PREVIEW = RESEARCH / "preview.json"
INTEGRITY = RESEARCH / "integrity.json"
PAGE = ROOT / "full-duplex-bench.html"

sys.path.insert(0, str(ROOT / "scripts"))
from site_navigation import project_tabs, review_tabs
from benchmark_scope import render_scope_section


EXAMPLES = [
    ("finance_18", "Three-tool chain without a disfluency label"),
    ("travel_19", "Mid-utterance correction and state rollback"),
    ("ecommerce_04", "A pause during an e-commerce request"),
]
DOMAIN_LABELS = {
    "ecommerce_support": "E-commerce support",
    "finance_billing": "Finance and billing",
    "housing_location": "Housing and location",
    "travel_identity": "Travel and identity",
}
DIFFICULTY_LABELS = {"easy": "Easy", "medium": "Medium", "hard": "Hard"}
FEATURE_LABELS = {
    "FILLER": "Filler",
    "PAUSE": "Pause",
    "HESITATION": "Hesitation",
    "FALSE_START": "False start",
    "SELF_CORRECTION": "Self-correction",
}
PAPER_RESULTS = [
    {"model": "GPT-Realtime", "tool_f1": 0.876, "argument_accuracy": 0.680, "response_quality": 0.792, "pass_at_1": 0.600, "turn_take": 96.0, "task_latency": 6.89, "interruption": 13.5},
    {"model": "Gemini Live 2.5", "tool_f1": 0.786, "argument_accuracy": 0.593, "response_quality": 0.554, "pass_at_1": 0.490, "turn_take": 92.0, "task_latency": 7.26, "interruption": 14.1},
    {"model": "Gemini Live 3.1", "tool_f1": 0.817, "argument_accuracy": 0.588, "response_quality": 0.718, "pass_at_1": 0.540, "turn_take": 78.0, "task_latency": 4.25, "interruption": 19.2},
    {"model": "Grok", "tool_f1": 0.797, "argument_accuracy": 0.542, "response_quality": 0.617, "pass_at_1": 0.430, "turn_take": 94.0, "task_latency": 6.65, "interruption": 25.5},
    {"model": "Ultravox", "tool_f1": 0.794, "argument_accuracy": 0.513, "response_quality": 0.510, "pass_at_1": 0.410, "turn_take": 96.0, "task_latency": 8.40, "interruption": 47.9},
    {"model": "Cascaded", "tool_f1": 0.803, "argument_accuracy": 0.562, "response_quality": 0.600, "pass_at_1": 0.450, "turn_take": 100.0, "task_latency": 10.12, "interruption": 33.0},
]


def e(value):
    return html.escape(str(value), quote=True)


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def preview_audio(source, destination):
    """Normalize a complete source clip to mono 24 kHz PCM16 for browser playback."""
    with wave.open(str(source), "rb") as reader:
        channels = reader.getnchannels()
        rate = reader.getframerate()
        width = reader.getsampwidth()
        frame_count = reader.getnframes()
        require(reader.getcomptype() == "NONE", f"Unsupported source WAV compression: {source}")
        pcm = reader.readframes(frame_count)
    if channels == 2:
        pcm = audioop.tomono(pcm, width, 0.5, 0.5)
    elif channels != 1:
        raise ValueError(f"Unexpected source channel count: {channels}")
    if rate != 24000:
        pcm, _ = audioop.ratecv(pcm, width, 1, rate, 24000, None)
    if width != 2:
        pcm = audioop.lin2lin(pcm, width, 2)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(destination), "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(24000)
        writer.writeframes(pcm)
    with wave.open(str(destination), "rb") as result:
        return {
            "channels": result.getnchannels(),
            "sample_rate_hz": result.getframerate(),
            "sample_width_bytes": result.getsampwidth(),
            "duration_seconds": result.getnframes() / result.getframerate(),
            "bytes": destination.stat().st_size,
        }


def require(condition, message):
    if not condition:
        raise ValueError(message)


def build_preview(integrity):
    require(integrity.get("status") == "validated_with_coverage_gaps", "Run the local dataset audit first")
    require(integrity["archive"]["sha256"] == "37545bd896f81718136598cf5be25d42ea9aa22efcd91f58370938d05d7d672f",
            "Unexpected FDB-v3 archive; review its provenance before publishing")
    manifest = {item["path"]: item for item in integrity["files"]}
    sample_rows = []
    source_seen = set()
    for scenario_id, role in EXAMPLES:
        matches = sorted(DATA.glob(f"{scenario_id}_*/metadata.json"))
        require(matches, f"Missing preview scenario in local release: {scenario_id}")
        metadata_path = matches[0]
        source_folder = metadata_path.parent
        source_audio = source_folder / "input.wav"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        source_path = str(source_audio.relative_to(PROJECT_ROOT))
        source_hash = manifest.get(source_path, {}).get("sha256")
        require(source_hash and sha256(source_audio) == source_hash, f"Source audio hash mismatch: {source_path}")
        require(source_path not in source_seen, f"Duplicate sample preview source: {source_path}")
        source_seen.add(source_path)
        slug = scenario_id.replace("_", "-")
        target = ASSETS / f"{slug}.wav"
        audio_info = preview_audio(source_audio, target)
        sample_rows.append({
            "id": scenario_id,
            "role": role,
            "title": metadata["title"],
            "domain": metadata["domain"],
            "difficulty": metadata["difficulty"],
            "disfluency_features": metadata["disfluency_features"],
            "expected_tool_calls": metadata["num_expected_calls"],
            "state_rollback_test": bool(metadata["state_rollback_test"]),
            "source_file": source_path,
            "source_sha256": source_hash,
            "preview_file": f"assets/full-duplex-bench-v3/{target.name}",
            "preview_sha256": sha256(target),
            "preview_audio": audio_info,
        })

    output = {
        "benchmark": integrity["benchmark"],
        "checked_on": "2026-10-19",
        "source_revision": integrity["source_revision"],
        "archive_sha256": integrity["archive"]["sha256"],
        "archive_bytes": integrity["archive"]["bytes"],
        "stats": integrity["dataset"],
        "catalogue_crosswalk": integrity["catalogue_crosswalk"],
        "license": integrity["license"],
        "examples": sample_rows,
        "source_report": "integrity.json",
    }
    RESEARCH.mkdir(parents=True, exist_ok=True)
    PREVIEW.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    shutil.copyfile(INTEGRITY_SOURCE, INTEGRITY)
    return output


def render_stats(stats):
    values = [
        (stats["recordings"], "recorded user clips"),
        (stats["unique_scenario_ids"], "unique audio scenario IDs"),
        (stats["anonymized_speaker_ids"], "speaker IDs in archive names"),
        (len(stats["domain_counts"]), "tool-use domains"),
    ]
    return '<div class="fdb-stat-grid">' + "".join(
        '<article class="fdb-stat"><strong>' + e(value) + '</strong><span>' + e(label) + '</span></article>'
        for value, label in values
    ) + "</div>"


def render_composition(stats, crosswalk):
    rows = []
    for category, counts, labels in (
        ("Task domain", stats["domain_counts"], DOMAIN_LABELS),
        ("Difficulty", stats["difficulty_counts"], DIFFICULTY_LABELS),
        ("Disfluency tag", stats["disfluency_recording_counts"], FEATURE_LABELS),
    ):
        for key, count in counts.items():
            rows.append(
                '<tr><th scope="row">' + e(category) + '</th><td>' + e(labels.get(key, key))
                + '</td><td>' + e(count) + '</td></tr>'
            )
    return (
        '<div class="fdb-table-scroll" role="region" aria-label="Dataset composition" tabindex="0">'
        '<table class="fdb-table"><caption>Table 2. Counts from the 100 audio-side metadata files. Disfluency labels can co-occur.</caption>'
        '<thead><tr><th scope="col">Label type</th><th scope="col">Value</th><th scope="col">Audio records</th></tr></thead>'
        '<tbody>' + "".join(rows) + '</tbody></table></div>'
        '<p>The clips total ' + e(f"{stats['audio_hours']:.3f}") + ' hours. The audio labels mark '
        + e(stats["metadata_state_rollback_recordings"]) + ' clips for state rollback; the separate code catalogue marks '
        + e(crosswalk["catalogue_rollback_scenarios"]) + ' scenario definitions. The audio set has '
        + e(crosswalk["catalogue_ids_without_audio"]) + ' catalogue IDs without an audio recording.</p>'
    )


def render_examples(examples):
    cards = []
    for item in examples:
        features = item["disfluency_features"] or ["No disfluency label"]
        tags = "".join('<span class="tag">' + e(FEATURE_LABELS.get(feature, feature)) + '</span>' for feature in features)
        url = e(item["preview_file"] + "?v=" + item["preview_sha256"][:12])
        facts = (
            e(DOMAIN_LABELS[item["domain"]]) + ' · ' + e(DIFFICULTY_LABELS[item["difficulty"]])
            + ' · ' + e(item["expected_tool_calls"]) + ' expected tool call'
            + ("s" if item["expected_tool_calls"] != 1 else "")
            + ' · ' + e(f"{item['preview_audio']['duration_seconds']:.1f}") + ' s'
        )
        cards.append(
            '<article class="card fdb-example"><p class="eyebrow">' + e(item["role"]) + '</p>'
            + '<h3>' + e(item["title"]) + '</h3><div class="fdb-tags">' + tags + '</div>'
            + '<p class="meta">' + facts + '</p><audio controls preload="none" aria-label="Play FDB-v3 input audio for '
            + e(item["id"]) + '"><source src="' + url + '" type="audio/wav">'
            + 'Audio playback is unavailable. <a href="' + url + '">Download this preview WAV</a>.</audio>'
            + '<p class="fdb-example-note">Complete source clip; converted to mono 24 kHz PCM16 for browser playback. '
            + 'The scenario title and labels come from the released metadata; this is human input audio, not an agent response.</p></article>'
        )
    return '<div class="fdb-examples">' + "".join(cards) + '</div>'


def render_results():
    rows = []
    for item in PAPER_RESULTS:
        rows.append(
            '<tr><th scope="row">' + e(item["model"]) + '</th>'
            + '<td>' + f"{item['tool_f1']:.3f}" + '</td><td>' + f"{item['argument_accuracy']:.3f}" + '</td>'
            + '<td>' + f"{item['response_quality']:.3f}" + '</td><td>' + f"{item['pass_at_1']:.3f}" + '</td>'
            + '<td>' + f"{item['turn_take']:.1f}%" + '</td><td>' + f"{item['task_latency']:.2f} s" + '</td>'
            + '<td>' + f"{item['interruption']:.1f}%" + '</td></tr>'
        )
    return (
        '<div class="fdb-table-scroll" role="region" aria-label="Paper-reported model results" tabindex="0">'
        '<table class="fdb-table fdb-results"><caption>Table 3. Overall results reported in the v3 paper, reproduced from its Table 2.</caption>'
        '<thead><tr><th scope="col">System</th><th scope="col">Tool selection F1</th><th scope="col">Argument accuracy</th>'
        '<th scope="col">Response quality</th><th scope="col">Pass@1</th><th scope="col">Turn-taking rate</th>'
        '<th scope="col">Task completion latency</th><th scope="col">Agent interruption rate</th></tr></thead>'
        '<tbody>' + "".join(rows) + '</tbody></table></div>'
        '<p>F1 and accuracy scores range from 0 to 1; turn-taking and interruption are percentages; latency is mean seconds. '
        'Higher scores are better. Lower latency and interruption rates are better. These are author-reported results, not local model runs.</p>'
    )


def build_page(data):
    stats = data["stats"]
    crosswalk = data["catalogue_crosswalk"]
    css_hash = sha256(ROOT / "assets/site.css")[:12]
    scope = render_scope_section(ids=["fdb-v3"], number=1)
    page = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Inspect the latest Full-Duplex-Bench v3 release: human-recorded speech, disfluency labels, tool-use scenarios, paper results and a local integrity audit.">
<meta name="color-scheme" content="light dark">
<title>Full-Duplex-Bench v3 Preview — AI2AI Duplex</title>
<link rel="stylesheet" href="assets/site.css?v={css_hash}">
<script src="assets/site.js" defer></script>
<style>
.fdb-jump-links {{ display:flex; flex-wrap:wrap; gap:8px; margin:18px 0 34px; }}
.fdb-jump-links a {{ color:var(--accent); border:1px solid var(--border); border-radius:999px; padding:7px 12px; text-decoration:none; font-size:13px; }}
.fdb-stat-grid {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:14px; margin:22px 0; }}
.fdb-stat {{ background:var(--surface); border:1px solid var(--border); border-radius:14px; padding:18px; }}
.fdb-stat strong {{ display:block; font-size:26px; font-variant-numeric:tabular-nums; }}
.fdb-stat span {{ color:var(--muted); font-size:13px; }}
.fdb-table-scroll {{ overflow-x:auto; margin:18px 0; border:1px solid var(--border); border-radius:12px; background:var(--surface); }}
.fdb-table {{ width:100%; min-width:620px; border-collapse:collapse; }}
.fdb-table caption {{ padding:15px 16px; color:var(--muted); text-align:left; font-weight:700; }}
.fdb-table th,.fdb-table td {{ padding:12px 14px; border-top:1px solid var(--border); text-align:left; vertical-align:top; }}
.fdb-table th[scope="row"] {{ min-width:170px; }}
.fdb-results {{ min-width:980px; }}
.fdb-results td {{ white-space:nowrap; font-variant-numeric:tabular-nums; }}
.fdb-examples {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:14px; margin:20px 0; }}
.fdb-example {{ min-width:0; }}
.fdb-example audio {{ display:block; width:100%; margin:12px 0; }}
.fdb-example h3 {{ min-height:3.1em; }}
.fdb-tags {{ display:flex; flex-wrap:wrap; gap:6px; }}
.fdb-example-note {{ color:var(--muted); font-size:13px; }}
.fdb-license,.fdb-integrity {{ overflow-wrap:anywhere; }}
.fdb-hash,.fdb-path {{ overflow-wrap:anywhere; word-break:break-all; }}
@media (max-width:760px) {{ .fdb-stat-grid {{ grid-template-columns:repeat(2,minmax(0,1fr)); }} .fdb-examples {{ grid-template-columns:1fr; }} .fdb-example h3 {{ min-height:0; }} }}
@media (max-width:420px) {{ .fdb-stat-grid {{ gap:8px; }} .fdb-stat {{ padding:13px; }} .fdb-stat strong {{ font-size:22px; }} }}
</style>
</head>
<body>
<a class="skip-link" href="#main">Skip to benchmark preview</a>
<header class="site-nav"><div class="nav-inner"><a class="brand" href="./">AI2AI Duplex</a>{project_tabs('literature')}</div></header>
<main id="main"><div class="container">{review_tabs('fdb')}
<header class="hero"><p class="eyebrow">Literature review · Dataset preview</p>
<h1>Full-Duplex-Bench v3: tool use under real speech disfluencies</h1>
<p class="lede">FDB-v3 pairs human-recorded spoken requests with multi-step mock-API tasks. This page previews the latest released audio set, checks it against the accompanying scenario catalogue, and separates those release facts from the paper’s model results.</p>
<p class="meta">Release source revision <code>{e(data['source_revision'])}</code> · Local archive checked 19 October 2026 · Dataset archive: {e(data['archive_bytes'] / (1024 * 1024))[:6]} MiB</p>
<div class="button-row"><a class="button primary" href="#audio-examples">Listen to input examples</a><a class="button" href="#results">Read paper results</a><a class="button" href="https://drive.google.com/file/d/1SO_4MTazWQ_jvCx0dtmpQ-t40bdd07yz/view?usp=sharing">Official dataset download</a><a class="button" href="https://github.com/DanielLin94144/Full-Duplex-Bench/tree/{e(data['source_revision'])}/v3">Upstream v3 code</a><a class="button" href="https://arxiv.org/abs/2604.04847">Paper</a></div></header>
<nav class="fdb-jump-links" aria-label="Full-Duplex-Bench v3 sections"><a href="#benchmark-scope">Tests and limits</a><a href="#overview">At a glance</a><a href="#composition">Data composition</a><a href="#audio-examples">Audio examples</a><a href="#scoring">Scoring</a><a href="#results">Paper results</a><a href="#validation">Integrity and limits</a><a href="#provenance">Attribution</a></nav>
{scope}
<section class="section" id="overview"><h2>What the release contains</h2>
<p class="section-intro">The v3 release is the newest dataset and code version listed by the upstream project as of this check. Its task catalog has 100 definitions; the audio archive has 100 recordings covering 79 unique scenario IDs, with repeated recordings for some scenarios.</p>
{render_stats(stats)}
<p>The paper describes real human speech from 12 speakers and annotations for fillers, pauses, hesitations, false starts and self-corrections. The four domains use deterministic mock APIs, so they test tool selection, argument passing and spoken completion without contacting real services.</p>
<p>Full-Duplex-Bench also has v1, v1.5 and v2 releases. They use different evaluation protocols; this page covers v3’s downloadable multi-step tool-use audio set.</p>
</section>
<section class="section" id="composition"><h2>Counts in the downloaded audio set</h2>
<p class="section-intro">The values below come from the 100 per-record metadata files in the downloaded archive. They describe the audio subset, not every scenario in the code catalogue.</p>
{render_composition(stats, crosswalk)}
</section>
<section class="section" id="audio-examples"><h2>Listen to three released input clips</h2>
<p class="section-intro">These examples cover a clean multi-call request, a corrected travel request and a pause-tagged e-commerce request. The players contain user input only; they are not benchmark model responses.</p>
{render_examples(data['examples'])}
<p>The site previews are complete source recordings converted to mono 24 kHz PCM16 for web playback. The source archive remains available from the upstream Drive link above.</p>
</section>
<section class="section" id="scoring"><h2>What the evaluation scores</h2>
<div class="callout"><h3>Task completion requires correct calls and arguments</h3><p>The benchmark reports tool-selection F1, semantic argument accuracy, response quality and strict Pass@1. Pass@1 requires the expected tool calls and correct arguments. GPT-4o judges semantic argument matches and whether the spoken transcript conveys the task result. Separate streaming measures include whether the agent takes a turn, latency to first speech/tool/factual completion, and the rate at which it begins speaking before the user finishes.</p><p>The APIs are deterministic local mocks with zero service latency. This isolates model and agent behavior from live-service variability; paper latency for hosted models still includes provider/network effects.</p></div>
</section>
<section class="section" id="results"><h2>Results reported in the v3 paper</h2>
<p class="section-intro">GPT-Realtime has the highest reported Pass@1 and response-quality score in this comparison. Gemini Live 3.1 has the shortest task-completion latency, alongside the lowest turn-taking rate. The table reproduces the paper’s overall configuration results.</p>
{render_results()}
<p>The paper reports that self-correction remains difficult: GPT-Realtime’s Pass@1 on that category is 0.588, and the other tested systems score lower. These are the authors’ published evaluation results, not measurements from this workspace.</p>
</section>
<section class="section" id="validation"><h2>Integrity audit and release gaps</h2>
<p>The downloaded archive is {e(f"{data['archive_bytes'] / (1024 * 1024):.1f}")} MiB compressed and expands to {e(f"{data['stats']['audio_hours']:.3f}")} audio hours. Its ZIP CRC passes; all 100 metadata files parse, and all 100 PCM WAVs decode. The archive’s SHA-256 is <code class="fdb-hash">{e(data['archive_sha256'])}</code>. The upstream archive did not include a checksum manifest, so this hash records the copy audited here rather than matching a publisher-provided digest.</p>
<p class="callout fdb-integrity"><strong>The audio set does not contain one recording for every catalogue ID.</strong> It covers {e(crosswalk['audio_scenario_ids'])} of {e(crosswalk['catalogue_scenario_ids'])} scenario IDs; {e(len(crosswalk['catalogue_ids_without_audio']))} catalogue IDs have no audio file. All non-dialogue task fields in the audio metadata match the pinned code catalogue for the overlapping IDs. The audio-side JSON stores one user turn, while the catalogue stores the scripted multi-turn exchange. The downloaded audio metadata marks {e(crosswalk['metadata_rollback_recordings'])} recordings for state rollback, compared with {e(crosswalk['catalogue_rollback_scenarios'])} rollback scenarios in the catalogue.</p>
<p>The paper describes the inputs as 48 kHz audio. The release contains three PCM layouts: 83 mono 48 kHz/32-bit WAVs, 10 stereo 48 kHz/32-bit WAVs and 7 mono 16 kHz/16-bit WAVs. Use each file’s actual header when preparing evaluation inputs.</p>
<p>At 100 clips and 12 speaker IDs, this remains a small single-user evaluation set. It has no group conversation, no real-service execution, no dedicated user-barge-in recovery test, and no acoustic speech-quality metric. Response quality is judged from transcription; it should not be read as a human-rated audio-quality score.</p>
<p><a href="research/full-duplex-bench-v3/integrity.json">Open the complete integrity report</a> · <a href="research/full-duplex-bench-v3/preview.json">Open the sample manifest</a>.</p>
</section>
<section class="section" id="provenance"><h2>Source, license and attribution</h2>
<p class="fdb-license"><strong>Benchmark:</strong> Full-Duplex-Bench v3 by Guan-Ting Lin, Chen Chen, Zhehuai Chen and Hung-yi Lee. The data and code are developed by National Taiwan University; the upstream project notes NVIDIA’s collaborative research contribution. See the <a href="https://arxiv.org/abs/2604.04847">paper</a>, <a href="https://github.com/DanielLin94144/Full-Duplex-Bench/tree/{e(data['source_revision'])}">pinned source revision</a>, and <a href="https://drive.google.com/file/d/1SO_4MTazWQ_jvCx0dtmpQ-t40bdd07yz/view?usp=sharing">official dataset archive</a>.</p>
<p>The upstream GitHub repository has a top-level <a href="https://github.com/DanielLin94144/Full-Duplex-Bench/blob/{e(data['source_revision'])}/LICENSE">CC BY-NC 4.0 license</a>. The audio was distributed separately through Google Drive, and its ZIP contains no license file or reuse statement; the repository license’s scope over that separate archive is unspecified. The three preview WAVs are converted from the released input recordings for playback, with no speech content edited. The source and preview hashes are in the <a href="research/full-duplex-bench-v3/integrity.json">integrity report</a>.</p>
<p><strong>Suggested citation:</strong> Lin, G.-T., Chen, C., Chen, Z., &amp; Lee, H.-y. (2026). <em>Full-Duplex-Bench-v3: Benchmarking Tool Use for Full-Duplex Voice Agents Under Real-World Disfluency.</em> arXiv:2604.04847.</p>
<p>Dataset files are kept locally under <code class="fdb-path">data/benchmarks/full_duplex_bench_v3/</code>. Only three converted previews and their source hashes are included on this site.</p>
</section>
<footer class="site-footer"><p>AI2AI Duplex · Literature review · <a href="index.html#literature-review">Duplex landscape</a> · <a href="research/full-duplex-bench-v3/ATTRIBUTION.md">Attribution record</a> · <a href="https://github.com/BorrisonXiao/ai2ai-duplex-report">Source repository</a></p></footer>
</div></main>
</body>
</html>'''
    PAGE.write_text(page, encoding="utf-8")


def main():
    require(INTEGRITY_SOURCE.is_file(), "Run scripts/validate_full_duplex_bench_v3.py from the workspace first")
    integrity = json.loads(INTEGRITY_SOURCE.read_text(encoding="utf-8"))
    data = build_preview(integrity)
    build_page(data)
    print(json.dumps({
        "page": str(PAGE.relative_to(ROOT)),
        "preview_manifest": str(PREVIEW.relative_to(ROOT)),
        "integrity_report": str(INTEGRITY.relative_to(ROOT)),
        "preview_audio": [item["preview_file"] for item in data["examples"]],
        "archive_sha256": data["archive_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
