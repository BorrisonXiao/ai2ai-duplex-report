#!/usr/bin/env python3
"""Verify reported-score vectors against primary PDF text and record provenance."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from build_performance import all_groups

ROOT = Path(__file__).resolve().parents[1]

def normalized(text):
    return re.sub(r"\s+", "", text)

def after(text, marker):
    # Match wrapped model names without joining adjacent numeric table cells.
    pattern = r"\s*".join(re.escape(char) for char in normalized(marker))
    match = re.search(pattern, text)
    if match is None:
        raise ValueError(f"Source marker not found: {marker}")
    return text[match.end():]

def numbers(text):
    return [float(value) for value in re.findall(r"(?<![\d.])[-+]?\d+(?:\.\d+)?", text)]

def extract(group, row, pages):
    name = row["model"]
    if group in {"thinkaloud_timing", "thinkaloud_qa"}:
        if group == "thinkaloud_timing":
            text = after(pages[9], "Table 3")
            aliases = {"Direct baseline (Think-Aloud study)": "Baseline", "Serial CoT (Think-Aloud study)": "Baseline + CoT", "Think-Aloud without dynamic balance": "Proposed Model w/o DB Stgy."}
            if name.startswith("Think-Aloud:"):
                text = after(text, "Proposed Model (varying generation speed)")
                marker = name.split(": ")[1].split()[0]
                text = re.split(r"(?m)^" + re.escape(marker) + r"\s*$", text, maxsplit=1)[1]
            else:
                text = after(text, aliases[name])
            cells = re.findall(r"(?m)^\s*(\d+(?:\.\d+)?|-)\s*$", text)[:4]
        else:
            text = after(pages[9], "Speech-to-Speech (S2S)").split("Speech-to-Text (S2T)")[0]
            aliases = {"Think-Aloud SLM (Ao et al.)": "Baseline + Think-Aloud CoT (ours)", "Serial CoT (Think-Aloud study)": "Baseline + CoT", "Direct baseline (Think-Aloud study)": "Baseline"}
            text = after(text, aliases.get(name, name))
            cells = re.findall(r"(?m)^\s*(\d+(?:\.\d+)?|-)\s*$", text)[:2]
        return [None if value == "-" else float(value) for value in cells]
    if group == "duplexomni":
        aliases = {"DuplexOmni + Gemini-3.1-Flash-Lite": "DuplexOmni", "Gemini-3.1-Flash-Lite (thinking only)": "Gemini-3.1-Flash-Lite"}
        text = after(pages[8], aliases.get(name, name))
        cells = re.findall(r"(?m)^\s*(\d+(?:\.\d+)?|–)\s*$", text)[:5]
        return [None if value == "–" else float(value) for value in cells]
    if group == "voicechat_fdb3":
        if row["source"] in {"fdb_original", "fdb_venus"}:
            return extract("fdb3", row, pages)
        text = after(pages[9], "Table 4")
        return numbers(after(text, "Ours" if name == "NemotronLabs VoiceChat" else name))[:3]
    if group == "srqa":
        text = pages[8]
        aliases = {"Moshi + CoT (TWL study)": "Moshi + CoT (ours)", "Moshi baseline": "Moshi (baseline)", "Helium": "Helium†"}
        if name == "TWL: early length-DPO":
            threshold = re.search(r"θ\s*=\s*(0\.\d+)", pages[9])
            assert threshold and float(threshold.group(1)) == row["qc_threshold"]
            block = after(pages[9], "Eval Set")
            scores, delays = [], []
            for task in ("ARC-E", "ARC-C", "SIQA", "PIQA", "GSM8K"):
                values = numbers(after(block, task))[:4]
                scores.append(values[1]); delays.append(values[3])
            assert delays == row["latency_tokens"], (name, delays)
            return scores
        values = numbers(after(text, aliases.get(name, name)))
        result = values[1:6]  # first number is the pretraining-token count
        if name == "Helium":
            result[4] = None  # source marks GSM8K as unavailable
        return result
    if group == "tau_original":
        block = after(pages[7], "Table 6.")
        aliases = {"Grok Voice": "grok-voice", "GPT-Realtime-1.5": "gpt-realtime-1.5", "Gemini Live 2.5": "gemini-live-2.5"}
        values = numbers(after(block, aliases[name]))
        return [values[2], values[5]] if name == "Gemini Live 2.5" else [values[0], values[3]]
    if group == "tau_aa":
        text = pages[18]
        assert normalized(name) in normalized(text)
        values = numbers(after(text, "Macro Average"))[:4]
        order = ["StepAudio 3 Realtime", "Grok Voice Think Fast 2.0 High", "Qwen Audio 3.0 Realtime Plus", "GPT-Realtime-2.1 High"]
        return [values[order.index(name)]]
    if group == "fdb3":
        text = pages[22] if row["source"] == "fdb_venus" else pages[5]
        values = numbers(after(text, name))
        return values[:3] if row["source"] == "fdb_venus" else [values[0], values[1], values[3]]
    if group == "echo":
        text = after(pages[8], "MCP (%)")
        alias = "Gemini Live-2.5-flash-native-audio" if name == "Gemini Live 2.5 native audio" else name
        values = numbers(after(text, alias))
        return values[5:7]  # four failure categories, total failures, MPR, MCP
    if group == "mpe":
        text = pages[8]
        alias = "MiniCPM-o 4.5" if name.startswith("MiniCPM") else name.split(" (")[0]
        values = numbers(after(text, alias))
        start = 6 if "implicit" in name else 0
        return values[start:start+4]  # four scores, followed by two coverage diagnostics
    if group in {"flair_qa", "flair_interaction"}:
        text = pages[7] if group == "flair_qa" else pages[8]
        marker = "MMSU" if group == "flair_qa" else "Latency (↓)"
        # Limit parsing to the table, not later prose mentioning a model.
        text = after(text, marker)
        alias = "Gemini Live 1" if name == "Gemini Live" else name
        values = numbers(after(text, alias))
        if name in {"Moshi", "Freeze-Omni", "Kimi-Audio"}:
            values = values[1:]  # citation year belongs to the model label
        return [values[index] for index in (0, 1, 2, 3, 6, 7)] if group == "flair_qa" else values[:5]
    raise ValueError(group)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--render-dir", type=Path, help="Optional private evidence-page renders for visual review")
    args = parser.parse_args()
    import pymupdf
    data = json.loads((ROOT / "research" / "reported-performance.json").read_text())
    source_pages, sources, checks = {}, {}, []
    for key, source in data["sources"].items():
        path = args.evidence_dir / source["local_pdf"]
        document = pymupdf.open(path)
        source_pages[key] = {number: document[number-1].get_text() for number in source["pages"]}
        sources[key] = {**source, "pdf_sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        if args.render_dir:
            args.render_dir.mkdir(parents=True, exist_ok=True)
            number = source["pages"][0]
            if key == "fdb_original": number = 5
            if key == "fdb_venus": number = 22
            document[number-1].get_pixmap(dpi=120, alpha=False).save(args.render_dir / f"{key}-page-{number:02d}.png")
        document.close()
    for group in all_groups(data):
        for row in group["rows"]:
            actual = extract(group["id"], row, source_pages[row["source"]])
            assert actual == row["source_values"], (group["id"], row["model"], actual, row["source_values"])
            checks.append({"group": group["id"], "model": row["model"], "source_values": actual, "status": "matches_primary_pdf"})
            if "domain_scores" in row:
                assert group["id"] == "tau_aa"
                order = ["StepAudio 3 Realtime", "Grok Voice Think Fast 2.0 High", "Qwen Audio 3.0 Realtime Plus", "GPT-Realtime-2.1 High"]
                text = after(source_pages[row["source"]][18], "GPT-Realtime-2.1 High")
                actual_domains = [numbers(after(text, label))[order.index(row["model"])] for label in data["domain_metric_labels"]]
                assert actual_domains == row["domain_scores"], (row["model"], actual_domains)
                checks.append({"group": "tau_aa_domains", "model": row["model"], "source_values": actual_domains, "status": "matches_primary_pdf"})
    mpe_text = source_pages["mpe"][25]
    for row in data["text_controls"]:
        if row["benchmark"] == "mpe":
            marker = "Implicit" if "implicit," in row["model"] else "Explicit"
            actual = numbers(after(mpe_text, marker))[:3]
        else:
            block = after(source_pages["tau_original"][7], "Table 6.")
            actual = [numbers(after(block, "gemini-live-2.5"))[0]]
        assert actual == row["source_values"], (row["model"], actual)
        checks.append({"group": row["benchmark"], "model": row["model"], "source_values": actual, "status": "matches_primary_pdf"})
    result = {"status": "passed", "checked": "2026-10-02", "evidence_cutoff": data["evidence_cutoff"], "data_sha256": hashlib.sha256((ROOT / "research" / "reported-performance.json").read_bytes()).hexdigest(), "sources": sources, "checks": checks, "scope": "Primary PDF table-value verification; not experimental reproduction. Raster evidence-page renders remain private and are not packaged."}
    (ROOT / "research" / "reported-performance-audit.json").write_text(json.dumps(result, indent=2) + "\n")
    print(f"PASS: {len(checks)} reported model/configuration vectors matched to {len(sources)} primary PDF sources.")

if __name__ == "__main__":
    main()
