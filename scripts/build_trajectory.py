#!/usr/bin/env python3
"""Build the trajectory tool with a reviewed real example and optional demo.

The public manifest contains reviewed text/timing and the user-requested captured audio; no private reasoning.
Both payloads are embedded so the viewer opens directly from disk.
"""
import base64
import hashlib
import io
import json
import math
from pathlib import Path
import struct
import wave
from html import escape
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
    example = json.loads((ROOT / "research/trajectory-example.json").read_text())
    waiting = example["waiting"]
    intro = f'''<section class="section" aria-labelledby="example-title"><h2 id="example-title">Recorded example · text and audio observations</h2><p class="section-intro">S1’s complete generated reply contains the supplied S2 answer. Changing the supplied answer also changes S1’s core sentence. Audio playback and automatic delegation are not demonstrated by the continuation test.</p><blockquote class="example-answer">{escape(waiting['s2_answer'])}</blockquote><div class="example-cards"><article class="card"><span class="tag blue">Before S2</span><h3>S1 transcribed the user</h3><p>ASR: “{escape(waiting['s1_asr'])}”</p><p>Speech text: <code>tts = ""</code>. The source smoke test forced S2 to start; S1 had not issued THINK.</p></article><article class="card"><span class="tag amber">While S2 reasoned</span><h3>No new S1 text was generated</h3><p>{waiting['s2_seconds']:.3f} s of S2 processing; {waiting['s2_reasoning_characters']:,} received reasoning characters. S1 Thinker was not called during that interval.</p><p>Talker processed the earlier payload for {waiting['request_overlap_seconds']:.3f} s concurrently. Its waveform has no verified spoken transcript; this is not evidence of filler speech.</p></article><article class="card"><span class="tag">After S2 feedback</span><h3>Continue beyond chunk zero</h3><p>The original history’s first chunk was empty. The separate continuation replay recovered the complete S2 answer in chunks 5–11, followed by a budget question.</p><p>Figure 1 shows User → S1 → S2 → Talker, with text or (silent) inside the blocks. Figure 2 aligns the same rows over continued input chunks.</p></article></div><p class="meta">Phase A: job 1815810, 2 × A100 80 GB; GPU 0 Thinker, GPU 1 Talker/MTP/Code2Wav + Qwen3-4B S2. Phase B: job 1816006, 1 × A100 80 GB; GPU 0 Thinker only, saved S2 reply replayed. The jobs did not overlap; maximum allocation was 2 GPUs.</p><div class="callout amber"><strong>Two recordings, two time axes</strong><p>These phases were recorded in different jobs. They are shown separately, with no invented continuous wall clock. Phase B has no generated waveform or spoken-word timing. Audio audition includes the actual phase A user recording and its short Talker clips; the near-silent old feedback clip is labeled.</p></div></section>'''
    if "active_recording" in example:
        current=example["active_recording"]
        reply=escape(current["generated_tts"])
        intro=f'<section class="section" aria-labelledby="example-title"><h2 id="example-title">Continuous run · actual text and audio</h2><p class="section-intro">Job 1816185 ran S1, S2 and Talker continuously on one A100. S1 was called six times while S2 was pending, but its pre-guidance tts fields stayed empty. This example does not reproduce a spoken acknowledgment during reasoning.</p><blockquote class="example-answer">{reply}</blockquote><div class="example-cards"><article class="card"><span class="tag blue">User</span><h3>Recorded input</h3><p>The 10 s user clip and its automatic transcript are available below. S1 initially transcribed “{escape(waiting["s1_asr"])}”. Further budget questions occur in the same recording.</p><p>The clip was submitted whole, followed by silent input chunks; this is a functional test rather than real-time microphone capture.</p></article><article class="card"><span class="tag amber">During S2</span><h3>Active calls, empty speech text</h3><p>S2 ran for {waiting["s2_seconds"]:.3f} s, with {waiting["s2_reasoning_characters"]:,} received reasoning characters. S1 continued to make calls; it generated no speech text before guidance.</p><p>S2 was forced for this simple question. S1 had not emitted THINK, so automatic delegation and its acknowledgment policy remain unverified.</p></article><article class="card"><span class="tag">After guidance</span><h3>A response and a waveform</h3><p>S2 supplied two complete clauses. S1 included the second in its generated text and added a follow-up question; the first clause was omitted.</p><p>Talker returned {current["audio_seconds"]:.3f} s of actual waveform. Listen below. The automatic audio transcript recovered only “What can I help you with?”; spoken reproduction of the S2 clause is therefore unverified. Text blocks show intended speech, not acoustic word alignment.</p></article></div><p class="meta">Completed job 1816185: 1 × A100 80 GB. Thinker, Talker/MTP/Code2Wav and Qwen3-4B S2 shared GPU 0 via private MPS. No GPU job overlapped. The held two-GPU fallback was cancelled; this completed run used one GPU.</p></section>'
    intro += '<section class="section" aria-labelledby="protocol-title"><h2 id="protocol-title">Why was S1 silent after partial S2 text?</h2><p>The streamed prefixes visible in the old trace were buffered text, not messages delivered to S1. Only complete guidance clauses were eligible for delivery. Our old smoke harness also awaited S2 completion before calling S1 again, so it did not test continuous interaction during reasoning.</p><p><a href="https://arxiv.org/html/2606.09186v1#S3.SS1.SSS1">DuplexOmni §3.1</a> describes ongoing 480 ms interaction and incorporation of completed intermediate results. Appendix B includes acknowledgments and pauses. Speech is not required in every slice.</p><p class="meta">The continuous driver now keeps S1 running and queues Talker in order. In completed one-A100 test 1816185, S1 still returned empty text before guidance. Forced delegation, greedy decoding and whole-file input differ from the paper’s natural continuous interaction; this trace is not proof of the paper’s acknowledgment behavior.</p></section>'
    facts=json.loads((ROOT / "research/native-loop-investigation.json").read_text())
    decoder=facts["decoder"]
    intro += f'<section class="section" aria-labelledby="native-investigation"><h2 id="native-investigation">Acknowledgment and native-loop investigation</h2><p>Completed CPU test {facts["decoder_job"]} used 0 GPUs and decoded the same released reference speech codes two ways. Independent six-frame decoding produced {decoder["stock_seconds"]:.3f} s; preserving context produced {decoder["context_seconds"]:.3f} s. Resetting the decoder removes 23.125 ms per chunk after the first: {decoder["lost_samples_when_resetting"]/24000:.3f} s across {decoder["chunk_count"]} chunks. The continuous decode’s earlier waveform remained stable when more codes were added.</p><p>Both variants contained recognizable acknowledgment in automatic Chinese ASR. This establishes a decoder timing defect, but it does not establish that this defect caused the missing S2 words in the generated example. Reference speech codes are training supervision, not a newly generated S1 response.</p><p>Native replay {facts["native_job"]}: {escape(facts["native_status"])}. It uses 480 ms packets, native THINK/WAIT/STOP handling, clocked simulated playback and S1’s own delegation decisions. It tests DailyTalk and a released two-request example, without supplying reference assistant responses or control tokens. Stock and context-preserving decodes use identical newly generated codes.</p><p class="meta">Native GPU job: {facts["native_gpus"]} × {escape(facts["native_gpu_type"])}. {escape(facts["native_layout"])}. Decoder diagnostic and dependent audio audit {facts["audit_job"]}: 0 GPUs. Maximum GPU allocation in this plan: {facts["maximum_gpus"]}. The first audit ran after the failed native job ended; CPU diagnostics can overlap a GPU run.</p></section>'
    intro += f'<section class="section" aria-labelledby="native-results"><h2 id="native-results">What the first native replay produced</h2><p>DailyTalk produced an unrelated color discussion. The prime/title example audibly listed 101, 103, 107, 109 and 113, then acknowledged the user’s correction. It did not provide the requested title or the revised prime list. Neither case generated THINK; the S2 service was loaded but never called. These are partial results, not a successful S1–S2 reasoning loop.</p><p>Select “S1 correction acknowledgment” in Audio audition to hear the actual generated phrase, approximately “Understood, I’ll increase the range and work it out again.” It comes from a separate recording, so its player has no timing anchor on the main displayed trace.</p><p>The longer case failed with GPU out-of-memory during the added full-history Code2Wav diagnostic. Follow-up {facts["followup_job"]} compares a specialist botany question under the original prompt and an explicit S2-availability prompt. It saves codecs on the GPU and performs the full-history comparison in the dependent CPU audit {facts["followup_audit_job"]}. Status at this update: {escape(facts["followup_status"])}.</p><p class="meta">Follow-up: 1 × A100 80 GB, all S1 components and 4B S2 share GPU 0. It starts after 1816643 has ended; no GPU overlap, maximum one A100. The dependent audit uses 0 GPUs. Prompt sensitivity in a single sampled replay is exploratory evidence.</p></section>'
    intro += f'<section class="section" aria-labelledby="native-ack"><h2 id="native-ack">Natural waiting acknowledgment is now reproduced</h2><p>In completed one-A100 botany replay 1816647, S1 generated THINK under the original released prompt and continued speaking while the local 4B S2 was active. Actual Talker audio contains “稍等哈，我查查” (“Give me a moment; I’ll check”). Independent CPU Whisper recovered this waiting speech. Use “Native spoken acknowledgment” above to inspect User → S1 → S2 → Talker on its own measured clock and listen to the generated clips.</p><p>The full answer loop still failed: each finished S2 request used all 2,048 output tokens on reasoning and returned no final guidance. S1 also claimed to search even though no search tool was connected, and its ASR misheard the specialist name. Speech during waiting is established; completed guidance, factual reliability and realtime performance are not.</p><p>Follow-up {facts["instruct_job"]} replays the full recorded interaction, including the next question and hang-up, with <a href="https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507">Qwen3-4B-Instruct</a> as the independent S2 backend. Unlike the <a href="https://huggingface.co/Qwen/Qwen3-4B-Thinking-2507">Thinking variant</a>, it returns answers without a separate internal-reasoning stream. This is an explicit backend comparison, not a reproduction of the paper’s Gemini backend.</p><p class="meta">Follow-up GPU job: 1 × A100 80 GB; Thinker, Talker/MTP/Code2Wav and the 4B instruction S2 share GPU 0. Earlier GPU jobs have ended; no GPU overlap, maximum one A100. Dependent audit {facts["instruct_audit_job"]} uses 0 GPUs. Status: {escape(facts["instruct_status"])}.</p></section>'
    intro += f'<section class="section" aria-labelledby="full-loop-result"><h2 id="full-loop-result">The complete communication path works; answer quality is unreliable</h2><p>Completed run {facts["instruct_job"]} used real 480 ms input packets across {facts["instruct_turns"]} S1 turns. S1 naturally requested THINK at chunk 15. The 4B instruction S2 returned a complete clause in {facts["instruct_s2_seconds"]:.3f} s; it reached S1 at chunk 17 and appeared in S1 text at chunks 18–22. Independent CPU Whisper recovered the corresponding phrase in the actual Talker waveform. The replay continued through the user’s next question and hang-up.</p><p>Select “Full interaction loop” to inspect this separate clock. Native STOP handling omitted five returned audio chunks from simulated playback. No WAIT token was emitted, so model-driven WAIT remains unverified; the CPU control check verifies the handler only. S2 supplied generic “I’ll check” guidance, not botanical facts. S1 misheard the specialist name, repeated itself and made unsupported factual claims.</p><p>Talker returned {facts["instruct_audio_seconds"]:.3f} s of waveform. The complete local user-left/Talker-right transport replay is 194.0 s with waiting gaps, including all 52.32 s of released user packets. Public clips contain generated speech only. Processing took about {facts["instruct_rtf"]:.2f}× the duration of the 133 input packets, including the silent tail; this is not a realtime performance result.</p><p class="meta">Completed GPU run: 1 × A100 80 GB, all S1 and 4B instruction S2 on GPU 0 via MPS; sampled maximum {facts["instruct_sampled_gpu_mib"]:,} MiB, with inference coverage. Audio audit {facts["instruct_audit_job"]}: 0 GPUs. The GPU runs were sequential; maximum one A100, no active GPU allocation after these tests.</p></section>'
    if "interactive_traces" in example:
        from interactive_section import build as interactive_section
        intro = interactive_section(ROOT)
    if (ROOT / 'research/controlled-study-plan.json').exists():
        study=json.loads((ROOT / 'research/controlled-study-plan.json').read_text())
        if study['status']=='queued_no_gpu_results':
            intro='<section class="section" aria-labelledby="controlled-status"><h2 id="controlled-status">New controlled study · queued</h2><p>Separate a single-request forced-S2 handoff from S1-only interruption handling, each with a matched control. Job '+escape(study['gpu_job_id'])+' requests two H100 80 GB GPUs and must pass a contention calibration before behavioral cases run. <a href="controlled-study.html">Read the setup and pass criteria</a>. GPU results are pending; the measured grid below is the previous reproduction.</p></section>'+intro
    page = (ROOT / "scripts/templates/trajectory.html.in").read_text()
    page = page.replace("{{NAV}}", project_tabs("experiments", "../")).replace("{{DEMO}}", payload)
    page = page.replace("{{EXAMPLE}}", json.dumps(example, ensure_ascii=False).replace("<", "\\u003c")).replace("{{EXAMPLE_INTRO}}", intro)
    page = page.replace('The hosted demo contains no dataset speech, private paths, model checkpoints or live inference endpoint.', 'The hosted measured example publishes reviewed text and timing only. It includes the requested recorded/generated audio clips, but no private paths, model checkpoints or private reasoning. The optional synthetic demo uses invented timings and tones.')
    (ROOT / "experiments/trajectory.html").write_text(version_assets(page))
    (ROOT / "assets/trajectory/demo.json").write_text(json.dumps(trace, indent=2, ensure_ascii=False) + "\n")
    collection = '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="description" content="Measured duplex speech replays, evidence audits and controlled experiment setups."><title>Experiments · AI2AI Duplex</title><link rel="stylesheet" href="../assets/site.css"></head>
<body><a class="skip-link" href="#main">Skip to experiments</a><header class="site-nav"><div class="nav-inner"><a class="brand" href="../index.html">AI2AI Duplex</a>{{NAV}}</div></header><main id="main"><div class="container"><header class="hero"><p class="eyebrow">Experiments · Audio only</p><h1>Inspect the conversation as it unfolds.</h1><p class="lede">Measured speech replays, evidence-backed audits and controls that separate model behavior from infrastructure latency.</p><p class="meta">7 October 2026 · Local experiment files stay in your browser</p></header><section class="section" aria-labelledby="tools"><h2 id="tools">Experiment records</h2><div class="card-grid"><article class="card"><span class="tag">Measured replay</span><h3>Timing and answer quality</h3><p>Six local cases reproduce delayed input, decoder gaps and incomplete answers. Complete paced input and warmed H100/CUDA-graph execution remove accumulating input lag; recognition and answer correctness remain separate checks.</p><p><a class="button primary" href="trajectory.html">Open trajectory viewer</a></p></article><article class="card"><span class="tag amber">Standard evidence audit</span><h3>Claims against primary traces</h3><p>Review input/output transcripts, matched decoder evidence, three representative cases, failure mechanisms and unresolved questions.</p><p><a class="button" href="interaction-review.html">Read the evidence audit</a></p></article>{{CONTROLLED_CARD}}</div></section><footer class="site-footer"><p>AI2AI Duplex · <a href="../index.html">Project home</a> · <a href="trajectory.html">Trajectory viewer</a></p></footer></div></main></body></html>
'''.replace("{{NAV}}", project_tabs("experiments", "../"))
    controlled_card = ''
    if (ROOT / 'research/controlled-study-plan.json').exists():
        controlled_card = '<article class="card"><span class="tag amber">Queued study</span><h3>S2 handoff and S1 interruption</h3><p>Four matched conditions test forced S2 interaction and S1-only user correction. Infrastructure qualification runs first. Preparation passed CPU checks; GPU behavioral results are pending.</p><p><a class="button" href="controlled-study.html">Read the setup and criteria</a></p></article>'
    collection = collection.replace('{{CONTROLLED_CARD}}',controlled_card)
    (ROOT / "experiments/index.html").write_text(version_assets(collection))
    print("Built Experiments collection, recorded S2 wait, S1 chunk visualization and optional synthetic demo.")


if __name__ == "__main__":
    main()
