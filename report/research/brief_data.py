"""Twenty-minute brief: shorten cells, preserve five entries per category."""
TABLES = [
    {"id": "systems", "label": "tab:systems", "caption": "Five system anchors: availability snapshot, 30 September 2026.", "headers": ["System", "Inference / weights", "Training reproducibility"], "widths": [0.31, 0.36, 0.33], "rows": [
        ("Think while listening", "thinklisten", "Study release not located; base Moshi is released.", "Recipe; full spoken-CoT data not located."),
        ("FLAIR", "flair", "Dedicated code / weights not located.", "Latent ELBO/SFT; full mixture not located."),
        ("MiniCPM-o 4.5", "minicpm", "Released code + weights; Apache-2.0.", "Fine-tuning tools; complete duplex mixture not released."),
        ("StepAudio 3 Realtime", "step3", "Report / demos; Realtime weights not located.", "Methods; full code / mixture not located."),
        ("Realtime-Venus", "venus", "Released harness + Audio/Omni weights; Apache-2.0.", "Methods; complete training package not located."),
    ]},
    {"id": "synchronization", "label": "tab:synchronization", "caption": "Five closest synchronization references: what already exists.", "headers": ["Paper", "Established mechanism"], "widths": [0.38, 0.62], "rows": [
        ("SyncLLM", "syncllm", "Clock-aligned chunks; speculative user tokens replaced by observations."),
        ("Moshi", "moshi", "Parallel user/agent codec streams on an 80 ms frame grid."),
        ("DuplexSLA", "duplexsla", "160 ms speech/listening/action clock; release marked forthcoming."),
        ("AdaptDuplex", "adapt", "Adaptive windows, bounded text lead, cancel / stale-result suppression."),
        ("Synchronization / turn-taking", "synchrony", "Moshi--Moshi hidden-state coupling and causal timing probes, not reasoning correctness."),
    ]},
    {"id": "benchmarks", "label": "tab:benchmarks", "caption": "Five evaluation choices: complementary, not one leaderboard.", "headers": ["Benchmark", "What it tests", "Access / interpretation"], "widths": [0.25, 0.34, 0.41], "rows": [
        ("SRQA", "thinklisten", "Streaming reasoning accuracy vs. post-question CoT delay.", "Synthetic; recipe verified, released evaluation not located. CoT onset is not a useful answer."),
        ("τ-Voice", "tauvoice", "Grounded tool/task success across 278 tasks.", "Code / tasks / simulator; APIs needed. Virtual time is not physical deadline validation."),
        ("Full-Duplex-Bench v3", "fdb3", "Human disfluencies, tools, argument accuracy and completion.", "Code + recordings. Tool F1 does not equal task success."),
        ("EchoChain", "echochain", "State revision during speech: inertia, amnesia, goal loss.", "200 synthetic interrupted conversations; standalone release not located."),
        ("Duplex-MPE", "mpe", "Addressee control, silence, answers and floor release.", "4,000 synthetic streams; standalone release not located."),
    ]},
    {"id": "data", "label": "tab:data", "caption": "Five supervision sources: natural timing is not a reasoning label.", "headers": ["Resource", "Useful content / scale", "Access / caution"], "widths": [0.25, 0.38, 0.37], "rows": [
        ("SmoothConv", "smoothconv", "100.53 h Chinese; speaker / turn-state / timing labels.", "HF; CC BY-NC 4.0; shared sources with DuplexConv."),
        ("DuplexConv", "duplexconv", "2,000.21 h Chinese; channels, VAD and machine-assisted labels.", "HF; CC BY-NC 4.0; split by source session."),
        ("otoSpeech Task", "ototask", "20.006 h / 58 English sessions; channels and task events.", "Gated; CC BY 4.0; verify task-outcome labels."),
        ("otoSpeech conversational", "otoconv", "280 h raw / 141 h curated English; separate speaker channels.", "Gated; CC BY 4.0; curated data is a subset."),
        ("Open Yap 1K", "openyap", "1,000 h English; word timing, familiar-speaker dyads.", "Public sample; full corpus requires request / DUA."),
    ]},
]
QUESTIONS = [
    ("RQ1: Think while listening", "When is a prefix sufficient?", "Late constraints with identical prefixes; risk-calibrated vs. fixed triggers.", "Correct useful-answer time; premature claims."),
    ("RQ2: Think while speaking", "How much speech lead is safe?", "Corrections before / after playback; bounded vs. unrestricted queue.", "Stale audible seconds; repair; underruns."),
    ("RQ3: Listen while speaking", "Whose correction updates what?", "Relevant correction vs. backchannel / side speech; oracle vs. predicted identity.", "Correction accuracy; false interruption; silence."),
    ("RQ4: Synchronize the clocks", "Which schedule survives load?", "Same audio under rate / jitter / contention; fixed vs. adaptive quantum.", "p95 evidence age; useful-answer delay; quality."),
    ("RQ5: Revise while delegating", "Which returned answer is valid?", "Correction during a simulated backend job; cancellation vs. joint result / playback validation.", "Stale-result use; task success; wasted work."),
]
TIMING_POINTS = [
    {"name": "Moshi codec frame", "values": [0.08], "cite": "moshi"},
    {"name": "DuplexSLA shared clock", "values": [0.16], "cite": "duplexsla"},
    {"name": "AdaptDuplex window", "values": [0.48, 0.64, 0.96], "cite": "adapt"},
    {"name": "MiniCPM-o / Venus window", "values": [1.0], "cite": "minicpm,venus"},
]
FIGURES = [
    {"id": "moshi", "file": "figures/papers/moshi.png", "paper_keys": ["moshi", "thinklisten"], "source_figures": ["Moshi Figure 1 (PDF p.7)", "TWL Section 2.2; silent-CoT/streaming-ASR definition"], "verified_details": "Original Moshi architecture screenshot. TWL is discussed in the caption but is not shown in the source figure."},
    {"id": "minicpm", "file": "figures/papers/minicpm.png", "paper_keys": ["minicpm"], "source_figures": ["MiniCPM-o Figure 4 (PDF p.4)", "Sections 2--3"], "verified_details": "Original full multimodal architecture screenshot, including the legend, video/audio inputs, text/hidden output and separate speech decoders."},
    {"id": "flair", "file": "figures/papers/flair.png", "paper_keys": ["flair"], "source_figures": ["FLAIR Figure 2 (PDF p.5)", "Section 4"], "verified_details": "Original latent-reasoning, data-stream and SDLM panels. The method's listening embedding is a soft vocabulary-weighted embedding; full-context expert is training-only."},
    {"id": "step3", "file": "figures/papers/step3.png", "paper_keys": ["step3", "mindpaced"], "source_figures": ["StepAudio 3 Figure 7B (PDF p.14)", "Section 6.3"], "verified_details": "Original Think-While-Speaking panel B, retaining same-model formulation/articulation, MTP and audio path; adaptive-routing panel A omitted and explicitly labeled."},
    {"id": "venus", "file": "figures/papers/venus.png", "paper_keys": ["venus"], "source_figures": ["Venus Figure 3 (PDF p.5)", "Sections 3.1--3.2 and 5"], "verified_details": "Original interaction/capability loops, tracked work, dispatch and same-session return. Harness prepares wording; frontend selects delivery timing."},
    {"id": "commitment", "file": "figures/commitment.tex", "paper_keys": [], "source_figures": [], "verified_details": "Original Monday-to-Tuesday correction example using plain user-speech, listening, reasoning and playback labels. Distinguishes received audio from processed input, answer-plan revision, already played speech and queued audio; not a published experiment or architecture guarantee."},
    {"id": "timing", "file": "figures/timing.tex", "paper_keys": ["moshi", "duplexsla", "adapt", "minicpm", "venus"], "source_figures": [], "verified_details": "Primary-paper modeling quanta only; distinct clock types, not measured response latencies."},
]
