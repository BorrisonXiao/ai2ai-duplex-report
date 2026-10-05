#!/usr/bin/env python3
"""Build the static trajectory tool and a deterministic, illustrative audio demo.

No experiment outputs or third-party speech are copied into the public site.
The template embeds the demo so the viewer also opens directly from disk.
"""
import base64
import hashlib
import io
import json
import math
from pathlib import Path
import struct
import wave
from site_navigation import project_tabs

ROOT = Path(__file__).resolve().parents[1]


def version_assets(page):
    for asset in ("assets/site.css", "assets/trajectory/viewer.css", "assets/trajectory/viewer.js"):
        version = hashlib.sha256((ROOT / asset).read_bytes()).hexdigest()[:12]
        page = page.replace('"../' + asset + '"', '"../' + asset + '?v=' + version + '"')
    return page


def tone(media_id, label, anchor, frequency, role):
    sr, seconds = 8000, 1.5
    values = [int(5000 * math.sin(2 * math.pi * frequency * i / sr) *
                  min(1, i / 800, (sr * seconds - i) / 800)) for i in range(int(sr * seconds))]
    stream = io.BytesIO()
    with wave.open(stream, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sr)
        wav.writeframes(struct.pack("<" + "h" * len(values), *values))
    return dict(id=media_id, label=label, anchor=anchor, duration=seconds, role=role,
                mime="audio/wav", waveform=[max(abs(v) for v in values[i:i + 120]) / 32768 for i in range(0, len(values), 120)],
                data_uri="data:audio/wav;base64," + base64.b64encode(stream.getvalue()).decode())


def demo():
    lanes = [("startup", "Service startup"), ("input", "User audio / context"),
             ("thinker", "S1 · Thinker · GPU 0"), ("system2", "S2 · reasoning · GPU 1"),
             ("control", "Commands / feedback"), ("talker", "Talker + codec · GPU 1"),
             ("audio", "Generated audio available")]
    events = []

    def event(ident, lane, start, end, label, kind="request", **details):
        events.append(dict(id=ident, lane=lane, start=start, end=end, label=label, kind=kind, details=details))

    event("startup", "startup", 0, 2, "Illustrative service startup")
    event("input", "input", 2, 2, "Whole user recording submitted", "media", media_id="user", content_seconds=1.5)
    event("s1-initial", "thinker", 2, 3.3, "Audio-conditioned S1 request", asr="Please calculate seventeen times twenty-three.", tts="Let me check that.")
    event("delegation", "control", 3.3, 3.3, "[THINK] · start background assistance", "s1_control", system2_control="[THINK]", delegation_source="illustrative")
    event("s2", "system2", 3.4, 6.1, "S2 reasoning and final answer", model="Illustrative System-2", reasoning_characters=620, final_text="【The answer is 391.】")
    for i, (at, count) in enumerate([(3.8, 80), (4.3, 220), (4.8, 360), (5.3, 510), (5.7, 620)]):
        event(f"reason-{i}", "system2", at, at, "Reasoning delta received", "reasoning_progress", request="s2", characters=count)
    event("foreground", "talker", 3.4, 4.5, "Foreground speech synthesis", allocation_gpu=1)
    event("foreground-ready", "audio", 4.5, 4.5, "Foreground waveform available", "media", media_id="foreground")
    event("final-text", "system2", 5.9, 5.9, "Final text received", "final_delta", request="s2", text="【The answer is 391.】")
    event("queued", "control", 6, 6, "S2 command queued", "command_ready", command="【The answer is 391.】")
    event("forwarded", "control", 6.2, 6.2, "Final command forwarded to S1", "command_forwarded", command="【The answer is 391.】")
    event("feedback", "thinker", 6.2, 7.3, "S1 incorporates S2 feedback", tts="The answer is 391.", input="480 ms silent slice plus from_s2 final command")
    event("speech-final", "talker", 7.3, 8.5, "Feedback speech synthesis")
    event("response-ready", "audio", 8.5, 8.5, "Final waveform available", "media", media_id="response")
    return dict(schema="duplex-trajectory/v1", title="Illustrative two-GPU System-2 trajectory", evidence="illustrative",
                metadata={"status": "demo", "gpus": 2, "mode": "whole-turn API integration", "audio": "Synthetic tones; no recorded speech"},
                limitations=["All demo timings and messages are invented to explain the viewer; they are not benchmark results.",
                             "The tones mark audio clips and do not synthesize the displayed speech.",
                             "Request overlap does not establish simultaneous GPU kernel execution."],
                lanes=[dict(id=k, label=v) for k, v in lanes], events=sorted(events, key=lambda e: e["start"]),
                media=[tone("user", "User input · synthetic tone", 2, 220, "input"),
                       tone("foreground", "Foreground · synthetic tone", 4.5, 330, "generated"),
                       tone("response", "Final output · synthetic tone", 8.5, 440, "generated")])


def main():
    (ROOT / "experiments").mkdir(exist_ok=True)
    trace = demo()
    payload = json.dumps(trace, ensure_ascii=False).replace("<", "\\u003c")
    page = (ROOT / "scripts/templates/trajectory.html.in").read_text()
    page = page.replace("{{NAV}}", project_tabs("experiments", "../")).replace("{{DEMO}}", payload)
    (ROOT / "experiments/trajectory.html").write_text(version_assets(page))
    (ROOT / "assets/trajectory/demo.json").write_text(json.dumps(trace, indent=2, ensure_ascii=False) + "\n")
    collection = '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="description" content="Interactive tools for inspecting audio-only duplex experiments."><title>Experiments · AI2AI Duplex</title><link rel="stylesheet" href="../assets/site.css"></head>
<body><a class="skip-link" href="#main">Skip to experiments</a><header class="site-nav"><div class="nav-inner"><a class="brand" href="../index.html">AI2AI Duplex</a>{{NAV}}</div></header><main id="main"><div class="container"><header class="hero"><p class="eyebrow">Experiments · Audio only</p><h1>Inspect the conversation as it unfolds.</h1><p class="lede">Tools for checking model decisions, background reasoning, feedback and generated audio on a shared timeline.</p><p class="meta">5 October 2026 · Local experiment files stay in your browser</p></header><section class="section" aria-labelledby="tools"><h2 id="tools">Inspection tools</h2><div class="card-grid"><article class="card"><span class="tag">Trajectory viewer</span><h3>Aligned layers and audio</h3><p>Replay client request spans, System-2 stream progress and command delivery. Listen to available clips with a linked cursor, inspect event details and import a portable run trace.</p><p><a class="button primary" href="trajectory.html">Open trajectory viewer</a></p></article><article class="card"><span class="tag amber">Evidence boundary</span><h3>Demo first, measured traces when available</h3><p>The hosted demo uses invented timestamps and synthetic tones. The DuplexOmni baseline and local System-2 tests were still queued when this tool was published; completed earlier smoke tests lack detailed event timestamps.</p><p>A real trace records client-observed events. The tool makes no claims about word alignment, GPU kernel overlap or live conversation latency.</p></article></div></section><footer class="site-footer"><p>AI2AI Duplex · <a href="../index.html">Literature review</a> · <a href="trajectory.html">Trajectory viewer</a></p></footer></div></main></body></html>
'''.replace("{{NAV}}", project_tabs("experiments", "../"))
    (ROOT / "experiments/index.html").write_text(version_assets(collection))
    print("Built Experiments collection, trajectory viewer and synthetic demo.")


if __name__ == "__main__":
    main()
