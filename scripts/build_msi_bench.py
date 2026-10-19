#!/usr/bin/env python3
"""Build the MSI-Bench data preview from the locally verified release."""
from collections import Counter
from html import escape
import hashlib
import json
from pathlib import Path
import shutil
import sys
import wave

ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT.parent
DATA = PROJECT_ROOT / "data/benchmarks/msi_bench_v1"
RESEARCH = ROOT / "research/msi-bench"
PREVIEW = RESEARCH / "preview.json"
ASSETS = ROOT / "assets/msi-bench"
sys.path.insert(0, str(ROOT / "scripts"))
from site_navigation import project_tabs, review_tabs


PATTERN_LABELS = {
    "speaker_authority_constraint": "Speaker authority constraint",
    "selective_disclosure": "Selective disclosure",
    "constraint_prioritization": "Constraint prioritization",
    "sequential_constraint_integration": "Sequential constraint integration",
    "scope_tracking": "Scope tracking",
    "background_speech_retrieval": "Background speech retrieval",
}
FAMILY_BY_PATTERN = {
    "speaker_authority_constraint": "Instruction following",
    "selective_disclosure": "Instruction following",
    "constraint_prioritization": "Reasoning",
    "sequential_constraint_integration": "Reasoning",
    "scope_tracking": "Memory",
    "background_speech_retrieval": "Memory",
}


def e(value):
    return escape(str(value), quote=True)


def digest(path):
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def read_checksums():
    result = {}
    for line in (DATA / "CHECKSUMS.sha256").read_text(encoding="utf-8").splitlines():
        value, relative = line.split("  ", 1)
        result[relative] = value
    return result


def audio_info(path):
    with wave.open(str(path), "rb") as source:
        rate = source.getframerate()
        frames = source.getnframes()
        return {
            "duration_seconds": frames / rate,
            "sample_rate_hz": rate,
            "channels": source.getnchannels(),
            "sample_width_bytes": source.getsampwidth(),
        }


def render_turn(case, sample, index, checksums):
    turn = case["turns"][index]
    if not turn.get("audio"):
        raise ValueError(f"Selected turn has no WAV: {sample['case_id']} turn {index}")
    source_relative = f"{case['path']}/{turn['audio']}"
    source_path = DATA / source_relative
    expected = checksums.get(source_relative)
    source_digest = digest(source_path)
    if not expected or source_digest != expected:
        raise ValueError(f"Source WAV does not match release hash: {source_relative}")

    filename = f"{sample['case_id']}-{index:02d}.wav"
    target_path = ASSETS / filename
    shutil.copyfile(source_path, target_path)
    target_digest = digest(target_path)
    if target_digest != source_digest:
        raise ValueError(f"Copied WAV hash mismatch: {filename}")
    info = audio_info(target_path)
    if info["sample_rate_hz"] != 24000 or info["channels"] != 1 or info["sample_width_bytes"] != 2:
        raise ValueError(f"Unexpected sample format for {source_relative}: {info}")

    name = turn.get("speaker") or "Assistant"
    recipient = turn.get("addressed_to") or "group"
    player_url = f"assets/msi-bench/{filename}?v={target_digest[:12]}"
    output = (
        '<article class="msi-turn"><div class="msi-turn-heading"><strong>Turn '
        + str(index + 1)
        + " · "
        + e(name)
        + " to "
        + e(recipient)
        + f'</strong><span class="meta">{info["duration_seconds"]:.1f} s · 24 kHz mono PCM16</span></div>'
        + '<audio controls preload="none" aria-label="Play source turn '
        + str(index + 1)
        + " from "
        + e(sample["case_id"])
        + '"><source src="'
        + e(player_url)
        + '" type="audio/wav">Audio playback is unavailable. <a href="'
        + e(player_url)
        + '">Download this WAV</a>.</audio><p class="msi-transcript">'
        + e(turn["text"])
        + "</p>"
    )
    gloss = sample.get("english_glosses", {}).get(str(index))
    if gloss:
        output += '<p class="msi-gloss"><strong>English gloss added for this page:</strong> ' + e(gloss) + "</p>"

    overlays = [item for item in case.get("acoustic", {}).get("competing_overlays", [])
                if item.get("anchor_turn_index") == index]
    for overlay in overlays:
        output += (
            '<p class="msi-overlay"><strong>Overlapping background voice in this WAV:</strong> '
            + e(overlay["speaker"])
            + " says “"
            + e(overlay["text"])
            + f'” from about {overlay["line_start"]:.2f} to {overlay["line_end"]:.2f} seconds.</p>'
        )
    output += "</article>"

    return output, {
        "case_id": sample["case_id"],
        "turn_index_zero_based": index,
        "source_file": source_relative,
        "site_file": f"assets/msi-bench/{filename}",
        "sha256": target_digest,
        **info,
    }


def render_text_turn(case, index):
    turn = case["turns"][index]
    speaker = turn.get("speaker") or "Assistant"
    recipient = turn.get("addressed_to") or "group"
    return (
        '<article class="msi-turn msi-context-turn"><div class="msi-turn-heading"><strong>Turn '
        + str(index + 1)
        + " · "
        + e(speaker)
        + " to "
        + e(recipient)
        + '</strong><span class="meta">Text context · no WAV in the release</span></div><p class="msi-transcript">'
        + e(turn["text"])
        + "</p></article>"
    )


def expects_no_tool_call(case):
    return case.get("eval", {}).get("tool_validation", {}).get("call_policy") == "no_calls"


def exact_argument_value(spec):
    if isinstance(spec, dict) and spec.get("op") == "exact":
        return spec.get("value")
    return spec


def render_expected_calls(case):
    validation = case.get("eval", {}).get("tool_validation", {})
    calls = validation.get("required_calls", [])
    if validation.get("call_policy") != "exact_multiset" or not calls:
        raise ValueError(f"Tool-call sample needs exact_multiset gold calls: {case['case_id']}")

    items = []
    used_speaker_refs = set()
    for call in calls:
        arguments = []
        for name, spec in call.get("arguments", {}).items():
            value = exact_argument_value(spec)
            if isinstance(value, str) and value.startswith("S") and value[1:].isdigit():
                used_speaker_refs.add(value)
            encoded = json.dumps(value, ensure_ascii=False, sort_keys=True)
            arguments.append("<li><code>" + e(name) + "</code> = <code>" + e(encoded) + "</code></li>")
        items.append(
            "<li><strong><code>" + e(call["name"]) + "</code></strong><ul>"
            + "".join(arguments)
            + "</ul></li>"
        )

    speaker_refs = []
    for index, participant in enumerate(case.get("participants", []), start=1):
        ref = f"S{index}"
        if ref in used_speaker_refs:
            speaker_refs.append("<code>" + ref + "</code> = " + e(participant.get("name", participant.get("role", ref))))
    ref_note = ""
    if speaker_refs:
        ref_note = '<p class="msi-rubric"><strong>Speaker references:</strong> ' + "; ".join(speaker_refs) + ".</p>"
    return (
        "<ol class=\"msi-tool-calls\">" + "".join(items) + "</ol>"
        + ref_note
    )


def render_model_prompt_details(case, dataset):
    """Show how the pinned runner exposes tools and normalizes a model reply."""
    eval_data = case["eval"]
    available_functions = eval_data.get("available_functions", [])
    catalog_lines = ["- Available functions for this conversation:"]
    for function in available_functions:
        if not isinstance(function, dict) or not isinstance(function.get("name"), str):
            continue
        arguments = function.get("arguments")
        if isinstance(arguments, dict) and arguments:
            rendered_arguments = ", ".join(
                f"{name}: {value}" for name, value in sorted(arguments.items())
            )
        else:
            rendered_arguments = "arguments_from_spoken_evidence"
        catalog_lines.append(
            f"  - {function['name']} arguments: {rendered_arguments}"
        )
    validation = eval_data.get("tool_validation", {})
    example_calls = []
    for call in validation.get("required_calls", []):
        example_calls.append(
            {
                "name": call["name"],
                "arguments": {
                    name: exact_argument_value(spec)
                    for name, spec in call.get("arguments", {}).items()
                },
            }
        )
    example_output = {
        "predicted_action": "respond",
        "answer_text": eval_data.get("standard_answer", ""),
        "tool_calls": example_calls,
    }

    code_base = dataset["code_url"].replace("/tree/", "/blob/")
    model_prompt_url = f"{code_base}/src/ib/llm/templates/understanding/system.j2"
    assembly_url = f"{code_base}/src/ib/scoring/multiturn_audio.py"
    catalog_url = f"{code_base}/src/ib/scoring/tool_catalog.py"
    native_url = f"{code_base}/src/ib/scoring/native_tool_schema.py"
    return (
        '<details class="msi-full-case msi-prompt-details"><summary>Inspect the model prompt, tool menu and normalized output</summary>'
        '<div class="msi-prompt-content"><h4>What the task prompt tells the model</h4>'
        '<p>This is a plain-language summary of the pinned turn-based prompt template. It directs the model to decide whether the latest speaker is addressing the assistant; answer or stay silent accordingly; use only available functions for supported external actions; and pair any calls with a brief spoken pre-action sentence that does not claim success. It asks for a structured response. The prompt does not ask the model to expose private reasoning. For this case, setup identifies the classroom-assistant role and date (May 25, 2026). The template says to bind <code>S1</code>/<code>S2</code> to voices by first appearance when no participant map is supplied; in this dialogue, Xiaolin speaks first and Awei second. The runner sends human WAVs as separate chronological audio messages rather than concatenating them into one clip.</p>'
        '<h4>Available functions for this roommate case</h4>'
        '<p>The <code>prompt_json</code> path inserts this function catalog into the setup instruction. It lists all four candidate functions and argument types, including unused distractors. The surrounding instruction says to use only these names and ground arguments in the conversation; it does not expose the gold calls or reference answer.</p>'
        '<pre class="msi-json-example msi-function-menu"><code>'
        + e("\n".join(catalog_lines))
        + '</code></pre><h4>Normalized prediction record</h4>'
        '<p>The normalized fields are <code>predicted_action</code> (<code>respond</code> or <code>silent</code>), <code>answer_text</code> (text or null) and <code>tool_calls</code> (a list of function names and argument objects). This format illustration uses the dataset reference answer and gold calls; it is not an evaluated model output. In <code>prompt_json</code> mode the model emits this one JSON object. In native-tool mode, the adapter combines the model’s text/action JSON with tool calls returned on the provider’s separate function-call channel.</p>'
        '<pre class="msi-json-example"><code>'
        + e(json.dumps(example_output, ensure_ascii=False, indent=2))
        + '</code></pre><p>The harness records and validates the proposed calls; for these fixed benchmark cases it does not execute restaurant or reminder actions and feed tool results back to the model.</p>'
        '<p class="msi-rubric">Exact source: '
        + f'<a href="{e(model_prompt_url)}">model prompt template</a>, '
        + f'<a href="{e(assembly_url)}">case prompt/audio assembly</a>, '
        + f'<a href="{e(catalog_url)}">text tool catalog</a> and '
        + f'<a href="{e(native_url)}">native function schema adapter</a>. '
        + 'The full-duplex adapters use their own live prompt and event collectors; this example describes the turn-based path.</p></div></details>'
    )


def render_atomic_rubric(rubric_row):
    criteria = rubric_row.get("atomic_criteria", [])
    if not criteria:
        return ""
    items = []
    for criterion in criteria:
        dimension = criterion.get("dimension", "criterion").replace("_", " ")
        items.append(
            '<li><strong>' + e(dimension) + "</strong><p>"
            + e(criterion.get("criterion", ""))
            + "</p></li>"
        )
    return (
        '<details class="msi-full-case"><summary>View the '
        + str(len(criteria))
        + ' atomic scoring criteria</summary><ol class="msi-rubric-criteria">'
        + "".join(items)
        + "</ol></details>"
    )


def summarize(cases):
    languages = Counter(case["language"] for case in cases)
    patterns = Counter(case["pattern"] for case in cases)
    scenes = Counter(case["scene"] for case in cases)
    speaker_counts = Counter(len(case["participants"]) for case in cases)
    no_tool_cases = [case for case in cases if expects_no_tool_call(case)]
    no_tool_patterns = Counter(case["pattern"] for case in no_tool_cases)
    line_counts = [sum(turn.get("audio") is not None for turn in case["turns"]) for case in cases]
    speak_rows = sum(1 for _ in (DATA / "probes/speak_probe.jsonl").open(encoding="utf-8"))
    hear_rows = sum(1 for _ in (DATA / "probes/hear_probe.jsonl").open(encoding="utf-8"))
    base_line_files = sum(line_counts)
    speak_audio_files = len(list((DATA / "probes/audio_live").glob("*.wav")))
    wav_count = len(list(DATA.rglob("*.wav")))
    if wav_count != base_line_files + speak_audio_files:
        raise ValueError("WAV inventory does not equal case turns plus speak-probe clips")
    return {
        "case_count": len(cases),
        "languages": dict(sorted(languages.items())),
        "patterns": dict(sorted(patterns.items())),
        "scenes": dict(sorted(scenes.items())),
        "speakers_per_case": {str(k): v for k, v in sorted(speaker_counts.items())},
        "wav_backed_human_turns": base_line_files,
        "mean_wav_backed_turns_per_case": sum(line_counts) / len(line_counts),
        "minimum_wav_backed_turns_per_case": min(line_counts),
        "maximum_wav_backed_turns_per_case": max(line_counts),
        "speak_probe_rows": speak_rows,
        "speak_probe_audio_files": speak_audio_files,
        "hear_probe_rows": hear_rows,
        "total_wav_files": wav_count,
        "no_tool_case_count": len(no_tool_cases),
        "no_tool_cases_by_pattern": dict(sorted(no_tool_patterns.items())),
    }


def composition_table(stats):
    pattern_description = "6 patterns × 192 cases each; 96 cases per language in each pattern"
    scene_description = "8 scenes × 144 cases each; 72 cases per language in each scene"
    speaker_description = (
        f"{stats['speakers_per_case']['2']} cases with 2 speakers; "
        f"{stats['speakers_per_case']['3']} cases with 3 speakers"
    )
    rows = [
        ("Language", f"English {stats['languages']['en']} · Mandarin {stats['languages']['zh']}", "Equal-sized language splits"),
        ("Interaction patterns", pattern_description, "Two patterns in each of the three capability families"),
        ("Scenes", scene_description, "Eight settings are equally represented"),
        ("Cast size", speaker_description, "Two- and three-speaker cases are balanced"),
        ("Probes", f"{stats['speak_probe_rows']:,} speak-time · {stats['hear_probe_rows']:,} hear-time", "Hear probes cover selective disclosure and background retrieval"),
    ]
    return (
        '<div class="msi-table-scroll" role="region" aria-label="Table 1: MSI-Bench release composition" tabindex="0">'
        '<table class="msi-table"><caption>Table 1. MSI-Bench v1 case composition and probe coverage, recomputed from the local case index.</caption>'
        '<thead><tr><th scope="col">Dimension</th><th scope="col">Counts</th><th scope="col">Reading</th></tr></thead><tbody>'
        + "".join("<tr><th scope=\"row\">" + e(a) + "</th><td>" + e(b) + "</td><td>" + e(c) + "</td></tr>" for a, b, c in rows)
        + "</tbody></table></div>"
    )


def file_figure(stats):
    width = 640
    line_width = width * stats["wav_backed_human_turns"] / stats["total_wav_files"]
    probe_width = width - line_width
    return (
        '<figure class="msi-file-figure" aria-labelledby="msi-file-caption">'
        '<svg viewBox="0 0 720 118" role="img" aria-labelledby="msi-file-title msi-file-desc">'
        '<title id="msi-file-title">MSI-Bench WAV file inventory</title>'
        '<desc id="msi-file-desc">A stacked bar showing '
        + str(stats["wav_backed_human_turns"])
        + " base human speech-turn WAV files and "
        + str(stats["speak_probe_audio_files"])
        + " separate speak-time probe WAV files.</desc>"
        '<text x="40" y="24" class="msi-chart-label">10,001 WAV files in this release</text>'
        '<rect x="40" y="42" width="'
        + f"{line_width:.2f}"
        + '" height="38" rx="10" class="msi-bar-lines"/><rect x="'
        + f"{40 + line_width:.2f}"
        + '" y="42" width="'
        + f"{probe_width:.2f}"
        + '" height="38" rx="0" class="msi-bar-probes"/><rect x="40" y="42" width="640" height="38" rx="10" class="msi-bar-outline"/>'
        '<text x="40" y="106" class="msi-chart-sub">'
        + f"{stats['wav_backed_human_turns']:,} case-turn WAVs"
        + '</text><text x="680" y="106" text-anchor="end" class="msi-chart-sub">'
        + f"{stats['speak_probe_audio_files']:,} speak-probe WAVs"
        + '</text></svg><figcaption id="msi-file-caption">Figure 1. WAV assets in the checked release: base dialogue turns plus one separate speak-time injection per case. The 384 hear-time probes refer back to base turns and add no WAV files.</figcaption></figure>'
    )


def pattern_table():
    rows = [
        ("Instruction following", "Speaker authority · Selective disclosure", "48.9% · 46.7%"),
        ("Reasoning", "Constraint prioritization · Sequential constraint integration", "36.8% · 27.6%"),
        ("Memory", "Scope tracking · Background speech retrieval", "24.9% · 7.0%"),
    ]
    return (
        '<div class="msi-table-scroll" role="region" aria-label="Table 2: paper-reported mean pattern All-Pass Rates" tabindex="0">'
        '<table class="msi-table"><caption>Table 2. Mean pattern All-Pass Rate across the paper’s 15 evaluated model configurations; pattern values follow the displayed order.</caption>'
        '<thead><tr><th scope="col">Capability family</th><th scope="col">Patterns</th><th scope="col">Mean APR by pattern</th></tr></thead><tbody>'
        + "".join("<tr><th scope=\"row\">" + e(a) + "</th><td>" + e(b) + "</td><td>" + e(c) + "</td></tr>" for a, b, c in rows)
        + "</tbody></table></div>"
    )


def build():
    source_config = json.loads(PREVIEW.read_text(encoding="utf-8"))
    dataset = source_config["dataset"]
    cases = {}
    all_cases = []
    for line in (DATA / "index/cases.jsonl").read_text(encoding="utf-8").splitlines():
        case = json.loads(line)
        cases[case["case_id"]] = case
        all_cases.append(case)
    rubric_rows = {}
    for line in (DATA / "index/rubrics.jsonl").read_text(encoding="utf-8").splitlines():
        rubric_row = json.loads(line)
        rubric_rows[rubric_row["case_id"]] = rubric_row
    checksums = read_checksums()
    stats = summarize(all_cases)
    if stats["case_count"] != 1152 or stats["total_wav_files"] != 10001:
        raise ValueError(f"Unexpected MSI-Bench v1 inventory: {stats}")
    if any(count != 192 for count in stats["patterns"].values()):
        raise ValueError("MSI-Bench interaction patterns are not balanced at 192 cases each")
    if any(count != 144 for count in stats["scenes"].values()):
        raise ValueError("MSI-Bench scene counts are not balanced at 144 cases each")

    ASSETS.mkdir(parents=True, exist_ok=True)
    RESEARCH.mkdir(parents=True, exist_ok=True)
    cards, audio_manifest = [], []
    for sample in source_config["samples"]:
        case = cases[sample["case_id"]]
        if len(case["participants"]) not in (2, 3):
            raise ValueError(f"Unexpected cast size: {sample['case_id']}")
        turn_html = []
        for index in sample["turn_indices"]:
            markup, asset_row = render_turn(case, sample, index, checksums)
            turn_html.append(markup)
            audio_manifest.append(asset_row)
        pattern = PATTERN_LABELS[case["pattern"]]
        family = FAMILY_BY_PATTERN[case["pattern"]]
        eval_data = case["eval"]
        calls = eval_data["tool_validation"].get("required_calls", [])
        if eval_data["tool_validation"].get("call_policy") != "exact_multiset" or not calls:
            raise ValueError(f"Audio example is not a tool-call case: {sample['case_id']}")
        call_markup = render_expected_calls(case)
        atomic_rubric_markup = render_atomic_rubric(rubric_rows[case["case_id"]])
        model_prompt_markup = (
            render_model_prompt_details(case, dataset)
            if case["case_id"] == "msi-zh-seq-edu-00"
            else ""
        )
        case_json_url = (
            f"https://huggingface.co/datasets/{e(dataset['repository'])}/blob/"
            f"{e(dataset['revision'])}/{e(case['path'])}/case.json"
        )
        cards.append(
            '<article class="card msi-example"><div class="msi-example-tags"><span class="tag">'
            + e(family)
            + '</span><span class="tag blue">'
            + e(pattern)
            + " · "
            + e("English" if case["language"] == "en" else "Mandarin Chinese")
            + '</span></div><h3>'
            + e(sample["title"])
            + "</h3><p>"
            + e(sample["summary"])
            + '</p><p class="msi-case-id">Case: <code>'
            + e(case["case_id"])
            + '</code> · '
            + str(len(case["participants"]))
            + " speakers · "
            + str(sum(turn.get("audio") is not None for turn in case["turns"]))
            + ' WAV-backed turns in full case · '
            + str(len(eval_data.get("available_functions", [])))
            + ' candidate functions listed in case metadata · '
            + str(len(calls))
            + ' required calls · policy: exact_multiset · <a href="'
            + e(case_json_url)
            + '">source case JSON</a></p><div class="msi-turn-list">'
            + "".join(turn_html)
            + '</div><div class="msi-reference"><h4>Expected behavior</h4><p><strong>Assistant action:</strong> '
            + e(eval_data.get("expected_action", "respond"))
            + ". Make exactly the required calls listed below; no extra calls.</p>"
            + call_markup
            + '<p><strong>Dataset reference response:</strong> '
            + e(eval_data.get("standard_answer", ""))
            + '</p><p class="msi-rubric"><strong>Judge instruction:</strong> '
            + e(eval_data.get("rubric", ""))
            + "</p>"
            + atomic_rubric_markup
            + model_prompt_markup
            + "</div></article>"
        )

    answer_only_cards = []
    for sample in source_config.get("answer_only_samples", []):
        case = cases[sample["case_id"]]
        if not expects_no_tool_call(case):
            raise ValueError(f"Answer-only sample unexpectedly requires a tool call: {sample['case_id']}")
        if case.get("eval", {}).get("expected_action") != "respond":
            raise ValueError(f"Answer-only sample does not expect a response: {sample['case_id']}")
        if sample.get("turn_indices") != "all":
            raise ValueError(f"Answer-only sample must show the complete case: {sample['case_id']}")

        timeline = []
        for index, turn in enumerate(case["turns"]):
            if turn.get("audio"):
                markup, asset_row = render_turn(case, sample, index, checksums)
                timeline.append(markup)
                audio_manifest.append(asset_row)
            else:
                timeline.append(render_text_turn(case, index))

        eval_data = case["eval"]
        atomic_rubric_markup = render_atomic_rubric(rubric_rows[case["case_id"]])
        available_functions = eval_data.get("available_functions", [])
        family = FAMILY_BY_PATTERN[case["pattern"]]
        pattern = PATTERN_LABELS[case["pattern"]]
        case_json_url = (
            f"https://huggingface.co/datasets/{e(dataset['repository'])}/blob/"
            f"{e(dataset['revision'])}/{e(case['path'])}/case.json"
        )
        answer_only_cards.append(
            '<article class="card msi-example msi-answer-only"><div class="msi-example-tags"><span class="tag">'
            + e(family)
            + '</span><span class="tag blue">'
            + e(pattern)
            + '</span><span class="tag msi-no-tool-tag">No required tool call</span></div><h3>'
            + e(sample["title"])
            + "</h3><p>"
            + e(sample["summary"])
            + '</p><p class="msi-case-id">Case: <code>'
            + e(case["case_id"])
            + '</code> · '
            + str(len(case["participants"]))
            + " speakers · "
            + str(sum(turn.get("audio") is not None for turn in case["turns"]))
            + " audio turns · tool policy: no_calls · "
            + str(len(available_functions))
            + ' functions listed in case metadata · <a href="'
            + e(case_json_url)
            + '">source case JSON</a></p><details class="msi-full-case"><summary>Listen to the complete case in turn order</summary><div class="msi-turn-list">'
            + "".join(timeline)
            + '</div></details><div class="msi-reference"><h4>Dataset reference response</h4><p>'
            + e(eval_data.get("standard_answer", ""))
            + '</p><p class="msi-rubric"><strong>Judge instruction:</strong> '
            + e(eval_data.get("rubric", ""))
            + "</p><p class=\"msi-rubric\"><strong>Tool-call target:</strong> none. This is a reference answer and scoring target, not a prediction from an evaluated model.</p>"
            + atomic_rubric_markup
            + "</div></article>"
        )

    (RESEARCH / "audio_manifest.json").write_text(json.dumps({
        "source_dataset": dataset["dataset_url"],
        "source_revision": dataset["revision"],
        "audio_files": audio_manifest,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (RESEARCH / "analysis.json").write_text(json.dumps({
        "source_dataset": dataset["dataset_url"],
        "source_revision": dataset["revision"],
        **stats,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    shutil.copyfile(DATA / "ATTRIBUTION.md", RESEARCH / "ATTRIBUTION.md")
    (RESEARCH / "LICENSE").write_text((DATA / "LICENSE").read_text().rstrip() + "\n")
    shutil.copyfile(PROJECT_ROOT / "reports/msi_integrity.json", RESEARCH / "integrity.json")

    css_digest = digest(ROOT / "assets/site.css")[:12]
    all_files_gb = dataset["download_size_bytes"] / 1_000_000_000
    body = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Listen to MSI-Bench conversations and inspect its model prompt, normalized tool-call output and judge scoring inputs.">
<meta name="color-scheme" content="light dark">
<title>MSI-Bench Preview — AI2AI Duplex</title>
<link rel="stylesheet" href="assets/site.css?v={css_digest}">
<script src="assets/site.js" defer></script>
<style>
.msi-jump-links {{ display:flex; flex-wrap:wrap; gap:8px; margin:18px 0 34px; }}
.msi-jump-links a {{ color:var(--accent); border:1px solid var(--border); border-radius:999px; padding:7px 12px; text-decoration:none; font-size:13px; }}
.msi-stat-grid {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:14px; margin:22px 0; }}
.msi-stat {{ background:var(--surface); border:1px solid var(--border); border-radius:14px; padding:18px; }}
.msi-stat strong {{ display:block; font-size:26px; font-variant-numeric:tabular-nums; }}
.msi-stat span {{ color:var(--muted); font-size:13px; }}
.msi-table-scroll {{ overflow-x:auto; margin:18px 0; border:1px solid var(--border); border-radius:12px; background:var(--surface); }}
.msi-table {{ width:100%; min-width:690px; border-collapse:collapse; }}
.msi-table caption {{ padding:15px 16px; color:var(--muted); text-align:left; font-weight:700; }}
.msi-table th,.msi-table td {{ padding:12px 15px; border-top:1px solid var(--border); text-align:left; vertical-align:top; }}
.msi-table th[scope="row"] {{ min-width:160px; }}
.msi-file-figure {{ margin:24px 0; padding:20px; border:1px solid var(--border); border-radius:14px; background:var(--surface); }}
.msi-file-figure svg {{ display:block; width:100%; height:auto; }}
.msi-chart-label {{ fill:var(--text); font:700 18px system-ui,sans-serif; }}
.msi-chart-sub {{ fill:var(--muted); font:600 13px system-ui,sans-serif; }}
.msi-bar-lines {{ fill:#4677b7; }}
.msi-bar-probes {{ fill:#dda342; }}
.msi-bar-outline {{ fill:none; stroke:var(--border); stroke-width:1.5; }}
.msi-file-figure figcaption {{ margin-top:10px; color:var(--muted); font-size:13px; }}
.msi-examples {{ align-items:stretch; }}
.msi-examples > *,.msi-example {{ min-width:0; }}
.msi-example {{ display:flex; flex-direction:column; gap:8px; }}
.msi-example h3 {{ margin-bottom:0; }}
.msi-example-tags {{ display:flex; flex-wrap:wrap; gap:7px; }}
.msi-case-id {{ color:var(--muted); font-size:12px; }}
.msi-turn-list {{ display:flex; flex-direction:column; gap:13px; margin-top:4px; }}
.msi-turn {{ border-top:1px solid var(--border); padding-top:12px; }}
.msi-turn-heading {{ display:flex; align-items:baseline; justify-content:space-between; gap:12px; flex-wrap:wrap; }}
.msi-turn audio {{ display:block; width:100%; margin:9px 0; }}
.msi-transcript {{ margin:7px 0; overflow-wrap:anywhere; }}
.msi-gloss,.msi-overlay {{ border-left:3px solid var(--accent); padding-left:10px; color:var(--muted); font-size:13px; }}
.msi-no-tool-tag {{ background:color-mix(in srgb, var(--accent) 13%, var(--surface)); color:var(--accent); }}
.msi-full-case {{ margin-top:12px; border:1px solid var(--border); border-radius:10px; padding:11px 13px; background:var(--surface); }}
.msi-full-case summary {{ cursor:pointer; color:var(--accent); font-weight:700; }}
.msi-context-turn {{ background:color-mix(in srgb, var(--surface) 80%, var(--border)); border-radius:8px; padding:10px; }}
.msi-reference {{ min-width:0; max-width:100%; box-sizing:border-box; margin-top:14px; border-left:3px solid var(--accent); padding:8px 13px; background:var(--surface); border-radius:0 10px 10px 0; }}
.msi-reference h4 {{ margin:0 0 6px; }}
.msi-reference p {{ margin:7px 0; }}
.msi-rubric {{ color:var(--muted); font-size:13px; }}
.msi-tool-calls {{ padding-left:24px; }}
.msi-tool-calls > li,.msi-rubric-criteria > li {{ margin:10px 0; }}
.msi-tool-calls ul {{ margin:4px 0; padding-left:22px; }}
.msi-rubric-criteria p {{ margin:5px 0; }}
.msi-reference code,.msi-rubric-criteria p,.msi-case-id {{ overflow-wrap:anywhere; word-break:break-word; }}
.msi-reference li,.msi-rubric-criteria li,.msi-prompt-content {{ min-width:0; max-width:100%; }}
.msi-json-example {{ box-sizing:border-box; max-width:100%; overflow:auto; white-space:pre-wrap; overflow-wrap:anywhere; word-break:break-word; }}
.msi-json-example code {{ white-space:inherit; overflow-wrap:anywhere; word-break:break-word; }}
.msi-judge-details {{ min-width:0; }}
.msi-source-list {{ padding-left:22px; }}
.msi-source-list li {{ margin:9px 0; }}
.msi-license {{ overflow-wrap:anywhere; }}
@media (max-width:760px) {{ .msi-stat-grid {{ grid-template-columns:repeat(2,minmax(0,1fr)); }} }}
@media (max-width:420px) {{ .msi-stat-grid {{ grid-template-columns:1fr 1fr; gap:8px; }} .msi-stat {{ padding:13px; }} .msi-stat strong {{ font-size:22px; }} }}
</style>
</head>
<body>
<a class="skip-link" href="#main">Skip to MSI-Bench preview</a>
<header class="site-nav"><div class="nav-inner"><a class="brand" href="./">AI2AI Duplex</a>{project_tabs('literature')}</div></header>
<main id="main"><div class="container">{review_tabs('msi')}
<header class="hero"><p class="eyebrow">Literature review · Dataset preview</p>
<h1>MSI-Bench: shared speech, speaker-specific decisions</h1>
<p class="lede">Listen to selected source turns, then inspect complete cases where the target is a user-facing response with no required tool call. The full local snapshot contains {stats['case_count']:,} indexed cases and {stats['total_wav_files']:,} WAV files.</p>
<p class="meta">MSI-Bench v1 · 18 October 2026 · Hugging Face revision <code>{e(dataset['revision'])}</code> · Dataset license: <a href="{e(dataset['license_url'])}">{e(dataset['license'])}</a></p>
<div class="button-row"><a class="button primary" href="#no-tool-responses">Check no-tool responses</a><a class="button" href="#examples">Listen to sample turns</a><a class="button" href="#analysis">Read the analysis</a><a class="button" href="{e(dataset['dataset_url'])}">Hugging Face dataset</a><a class="button" href="{e(dataset['paper_url'])}">Paper</a></div></header>
<nav class="msi-jump-links" aria-label="MSI-Bench sections"><a href="#overview">At a glance</a><a href="#composition">Case mix</a><a href="#examples">Audio examples</a><a href="#no-tool-responses">No-tool responses</a><a href="#scoring">Scoring</a><a href="#analysis">Reported findings</a><a href="#provenance">Provenance</a></nav>
<section class="section" id="overview"><h2>At a glance</h2>
<p class="section-intro">MSI-Bench evaluates a voice assistant in scripted multi-party conversations. Each case includes speaker and scene context, per-turn dialogue, expected tool behavior and atomic scoring criteria.</p>
<div class="msi-stat-grid"><div class="msi-stat"><strong>{stats['case_count']:,}</strong><span>indexed evaluation cases</span></div><div class="msi-stat"><strong>{stats['languages']['en']} / {stats['languages']['zh']}</strong><span>English / Mandarin cases</span></div><div class="msi-stat"><strong>{len(stats['patterns'])}</strong><span>equally sized interaction patterns</span></div><div class="msi-stat"><strong>{all_files_gb:.2f} GB</strong><span>download size recorded in the asset inventory</span></div></div>
<p>The Hugging Face viewer shows 10,001 rows, which matches the release’s 10,001 WAV files. The versioned case index contains 1,152 evaluation cases; it is the right denominator for case-level analysis. Each case record has 6–12 dialogue entries, while 5–12 entries per case have a human-turn WAV in this snapshot (mean {stats['mean_wav_backed_turns_per_case']:.2f}). The audio is stored one utterance per WAV rather than as a single stitched conversation.</p>
</section>
<section class="section" id="composition"><h2>The release is deliberately balanced</h2>
<p class="section-intro">The current case index contains two equal language splits, six equally sized patterns and eight equally sized scene settings.</p>
{composition_table(stats)}
{file_figure(stats)}
<div class="callout"><h3>Two probe timings test different behavior</h3><p>There is one separate speak-time injected utterance for every case. The 384 hear-time probes apply to selective-disclosure and background-retrieval cases; they point back to existing case WAVs and expect silence before the assistant is addressed. This means the 10,001 WAV inventory is {stats['wav_backed_human_turns']:,} base dialogue turns plus {stats['speak_probe_audio_files']:,} injected lines. Probe counts and definitions come from the release files.</p></div>
</section>
<section class="section" id="examples"><h2>Listen to selected original turns</h2>
<p class="section-intro">The players contain unchanged single-turn WAVs from the release. Read the shown turns in order; other lines from each case are omitted. The transcript text comes from the case JSON. The tool-requiring examples below show their exact expected calls and reference responses; complete no-tool cases appear in the next section. No evaluated-model outputs are shown on this page.</p>
<div class="callout amber"><h3>These are synthesized scripts</h3><p>The benchmark authors report that the dialogue voices are synthesized from cloned Mozilla Common Voice reference clips. They report no real conversations in the release. Each case WAV also uses the scene’s listed ambience, and a background voice may overlap the foreground turn.</p></div>
<div class="card-grid msi-examples">{''.join(cards)}</div>
</section>
<section class="section" id="no-tool-responses"><h2>Cases scored on the spoken response</h2>
<p class="section-intro">{stats['no_tool_case_count']:,} of {stats['case_count']:,} cases have the dataset’s <code>no_calls</code> tool policy and expect the assistant to respond: {stats['no_tool_cases_by_pattern']['speaker_authority_constraint']} speaker-authority cases, {stats['no_tool_cases_by_pattern']['selective_disclosure']} selective-disclosure cases and {stats['no_tool_cases_by_pattern']['background_speech_retrieval']} background-speech retrieval cases. The three examples below cover refusal, keeping information private and answering from overlapping speech.</p>
<div class="callout"><h3>What the page shows</h3><p>Each card contains the complete case timeline, the dataset’s reference response and expandable atomic scoring criteria. A turn without a released WAV is shown as text context. These are dataset targets, not outputs from a model run. Some case records list candidate functions in their metadata, while their tool policy is explicitly <code>no_calls</code>. The scoring section links to the pinned public runner and explains its model prompt, tool delivery and judge inputs; it cannot reveal hidden provider instructions or private reasoning.</p></div>
<div class="card-grid msi-examples">{''.join(answer_only_cards)}</div>
</section>
<section class="section" id="scoring"><h2>What the model and judge receive</h2>
<p class="section-intro">The public runner turns a model’s response into a normalized prediction record. For the roommate case, expand “Inspect the model prompt, tool menu and normalized output” in that case card to see the available functions and a clearly labeled format example.</p>
<div class="callout"><h3>The judge receives the text and calls together</h3><p>The evaluator passes the judge three named JSON values: <code>manifest</code>, <code>prediction</code> and <code>rubric</code>. The manifest view contains the scene, expected action, interaction-pattern label, any contract field present, and dialogue lines with speech-control/acoustic markup removed. The prediction view contains <code>predicted_action</code>, <code>answer_text</code>, <code>tool_calls</code> and <code>confidence</code> when present. The rubric contains its judge instruction and atomic criteria (polarity, dimension and criterion). For a call criterion, the gold calls are written into that criterion; the gold validator specification is not passed as a separate field.</p><p>The judge prompt explicitly says to evaluate <code>prediction.answer_text</code> and <code>prediction.tool_calls</code> against the criteria, and not to re-judge <code>predicted_action</code>. So the text and the call list are judged as parts of the same normalized prediction, not as a whole JSON string matched against the reference response. The answer text is judged semantically, so equivalent wording can pass. The judge sees the dialogue as labeled text lines, not the WAVs or generated speech audio. MSI-Bench reports no spoken-audio quality score. A <code>no_calls</code> sample still has its text response judged; the calls array should be empty.</p><p>There is also a separate deterministic tool validator. It checks required function names, argument values, call multiplicity and extra calls (order-independent under the sample’s <code>exact_multiset</code> policy). This validator does not send its verdict to the LLM judge; its pass/fail contributes separately to the tool metric and, for tool-required cases, the paper’s All-Pass decision. Invalid model JSON/schema is recorded as a format error rather than semantic success.</p><p><strong>How the model is instructed:</strong> the turn-based template tells it to choose <code>respond</code> or <code>silent</code>. A response that needs an external action should include only supported calls from the offered menu and a short pre-action spoken sentence; it should not claim that an action succeeded. In <code>prompt_json</code> mode, action, text and calls are emitted in one JSON object. In native-tool mode, the provider returns tool calls through its function-call interface and the adapter combines those with the action/text fields into the same normalized record. For generated turn-based targets, the runner defaults OpenAI and Gemini to native declarations; other targets default to the text/JSON catalog unless configured otherwise. The paper also says open-weight targets use vLLM JSON-schema constrained decoding, while hosted targets use their public APIs.</p><p>The actual prompt placement depends on the adapter: some requests place the instruction in a system message, while some local chat templates place it at the start of the user message. Full-duplex adapters use a separate live prompt/event path. The pinned source exposes the benchmark’s own instructions and adapter requests; it does not expose vendor-internal hidden prompts or private reasoning layers.</p></div>
<details class="msi-full-case msi-judge-details"><summary>Inspect the judge’s normalized prediction object</summary><p>This example uses the dataset reference answer and required calls to illustrate the fields the judge receives. It is not a model prediction. In an actual run, the adapter puts the model-generated text and calls in these same fields.</p><pre class="msi-json-example"><code>{e(json.dumps({"prediction": {"predicted_action": "respond", "answer_text": cases["msi-zh-seq-edu-00"]["eval"]["standard_answer"], "tool_calls": [{"name": call["name"], "arguments": {name: exact_argument_value(spec) for name, spec in call.get("arguments", {}).items()}} for call in cases["msi-zh-seq-edu-00"]["eval"]["tool_validation"]["required_calls"]]}}, ensure_ascii=False, indent=2))}</code></pre><p>The other two objects provide the cleaned dialogue/context and rubric. The exact judge system and user prompt templates, the view-construction code and deterministic checker are in the <a href="{e(dataset['code_url'].replace('/tree/', '/blob/') + '/src/ib/llm/templates/evaluation/judge_system.j2')}">judge system template</a>, <a href="{e(dataset['code_url'].replace('/tree/', '/blob/') + '/src/ib/llm/templates/evaluation/judge_user.j2')}">judge input template</a>, <a href="{e(dataset['code_url'].replace('/tree/', '/blob/') + '/src/ib/scoring/judge.py')}">judge adapter</a> and <a href="{e(dataset['code_url'].replace('/tree/', '/blob/') + '/src/ib/scoring/tool_validation.py')}">tool validator</a>.</p></details>
<p>See the paper’s <a href="{e(dataset['paper_url'])}">evaluation protocol and metrics</a> for DeepSeek V4 Pro, All-Pass Rate, Atomic Rubric Score and Tool execution definitions. The pinned <a href="{e(dataset['code_url'])}">evaluation code</a> shows the request and parsing details.</p>
</section>
<section class="section" id="analysis"><h2>What the released cases and paper show</h2>
<p class="section-intro">The six case patterns form three balanced families. The paper reports mean All-Pass Rate across 15 evaluated model configurations by pattern.</p>
{pattern_table()}
<p>In the paper, Gemini 3.1 Pro reaches the highest reported all-rubric pass rate on English (66.8%), while GPT Realtime 2.1 (xhigh) leads on Mandarin (54.5%). The strongest open-weight configuration, Qwen3-Omni-30B, reaches 34.0% and 19.3% on those splits. All-Pass Rate counts a case only when every atomic rubric passes, including the deterministic tool-call check where one applies. These are paper results, not a local evaluation in this workspace. See the <a href="{e(dataset['paper_url'])}">paper</a> for model settings, uncertainty intervals and full scores.</p>
<div class="callout"><h3>How to read the pattern gap</h3><p>In the paper’s 15-configuration average, instruction-following patterns score highest, reasoning patterns fall in the middle, and memory patterns score lowest. Background-speech retrieval is the hardest pattern in that average. This is a pattern-level summary of the paper’s model runs, not a claim that every retrieval example is harder than every other case.</p></div>
</section>
<section class="section" id="provenance"><h2>Source, integrity and attribution</h2>
<p class="msi-license"><strong>Dataset:</strong> MSI-Bench v1 by Chenxu Xiong, Dongming Shen, Yuzhi Tang, Wentao Ma, Mu Li and Alex Smola. Source snapshot: <a href="{e(dataset['dataset_url'])}">Hugging Face commit {e(dataset['revision'][:7])}</a>; paper: <a href="{e(dataset['paper_url'])}">arXiv:2609.24812</a>; evaluation code: <a href="{e(dataset['code_url'])}">pinned GitHub source</a>. The dataset is licensed under <a href="{e(dataset['license_url'])}">CC BY 4.0</a>.</p>
<p>Every sample WAV is checked against its source hash in the dataset’s <code>CHECKSUMS.sha256</code>, then checked again after copying to this site. The current release checksum list does not match its updated <code>README.md</code>; the other 11,162 listed files match. The source checksum manifest is kept unchanged, and the <a href="research/msi-bench/integrity.json">integrity audit</a> records both README hashes. Sample ambience credits and the complete upstream attribution list are available in the <a href="research/msi-bench/ATTRIBUTION.md">attribution record</a>; the dataset license text is <a href="research/msi-bench/LICENSE">available here</a>.</p>
<ul class="msi-source-list"><li>Commerce/bank example: “Ambience Bank Kookmin Bank.wav” by tweeterdj, <a href="https://freesound.org/people/tweeterdj/sounds/30469/">Freesound source</a>, <a href="https://creativecommons.org/licenses/by/3.0/">CC BY 3.0</a>; included under the synthesized voices.</li><li>Protected-surprise/hotel example: “AMB_Recepcion_detras_escaleras_250508” by Dani_S.T., <a href="https://freesound.org/people/Dani_S.T./sounds/805983/">Freesound source</a>, <a href="https://creativecommons.org/publicdomain/zero/1.0/">CC0 1.0</a>.</li><li>Restaurant example: “ambience - restaurant.WAV” by soundtracvkradio, <a href="https://freesound.org/people/soundtracvkradio/sounds/394678/">Freesound source</a>, <a href="https://creativecommons.org/publicdomain/zero/1.0/">CC0 1.0</a>; the selected line also contains Marco’s overlapping stock update.</li><li>Pickup-counter/store example: “Grocery Store Ambience Checkout Line” by deleted_user_7146007, <a href="https://freesound.org/people/deleted_user_7146007/sounds/383718/">Freesound source</a>, <a href="https://creativecommons.org/publicdomain/zero/1.0/">CC0 1.0</a>; the selected case overlays Marco’s announcement on foreground speech.</li><li>Mandarin dormitory example: “indoors house dorm dormitory ambient room tone with halfway open window traffic.wav” by bulbastre, <a href="https://freesound.org/people/bulbastre/sounds/126938/">Freesound source</a>, <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>.</li></ul>
<p class="meta">The complete release remains in the local workspace at <code>{e(dataset['download_path'])}</code>. This preview publishes only the selected source turns and the required attribution; it does not contain the full 4.29 GB release.</p>
</section>
<footer class="site-footer"><p>MSI-Bench data preview · <a href="index.html#literature-review">Return to the duplex landscape</a> · <a href="{e(dataset['dataset_url'])}">Open the dataset source</a></p></footer>
</div></main>
</body>
</html>
'''
    target = ROOT / "msi-bench.html"
    target.write_text(body, encoding="utf-8")
    print(f"Built {target.name}: {stats['case_count']} cases, {stats['total_wav_files']} WAV files, {len(audio_manifest)} hash-checked preview turns.")


if __name__ == "__main__":
    build()
