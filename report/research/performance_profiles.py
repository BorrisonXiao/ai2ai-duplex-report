"""Plot/reading choices; every numeric value comes from reported-performance.json."""
PROFILES = [
    dict(id="twl", group="srqa", title="Think while listening: SRQA", kind="radar", models=["Moshi + CoT (TWL study)", "TWL: early length-DPO", "Moshi baseline", "Kimi-Audio-7B-Instruct"], axes=["ARC-E", "ARC-C", "SIQA", "PIQA", "GSM8K"], note="Two TWL-study checkpoints are distinct. Kimi-Audio is a speech reference, not a full-duplex system. The table also includes Qwen2-Audio; Helium's non-comparable text result is omitted.", takeaway="The CoT configuration is stronger on these tasks than foundation Moshi, but early length-DPO is a different accuracy/latency operating point, not the same high-accuracy checkpoint."),
    dict(id="flair-qa", group="flair_qa", title="FLAIR: spoken QA accuracy", kind="radar", models=["FLAIR w/ thk", "FLAIR w/o thk", "Moshi", "Kimi-Audio"], axes=["LlamaQ", "WebQ", "TriviaQA", "SDQA", "OpenbookQA", "MMSU"], note="FLAIR's own QA suite is not SRQA. Only accuracy-valued tasks are plotted; 1–5 open-ended judge scores are excluded. Published reference scores are imported, not all rerun. Kimi-Audio is half-duplex.", takeaway="Latent thinking improves several tasks over the no-thinking ablation, but not every task: TriviaQA is lower. No single curve wins across all tasks shown."),
    dict(id="flair-interaction", group="flair_interaction", title="FLAIR: earlier duplex interaction suite", kind="facets", note="Separate axes preserve percentages, seconds and 0–5 judge scores. TOR means takeover rate. Gemini Live is the study's sole closed reference; its API revision is unspecified. This is not FDB-v3 tool use.", takeaway="Response quality, takeover rate and response delay expose different trade-offs. A high takeover rate alone does not establish a useful answer."),
    dict(id="step3", group="tau_aa", title="StepAudio 3 Realtime: τ-Voice (AA)", kind="domain-radar", axes=["Airline", "Retail", "Telecom"], note="Artificial Analysis implementation and API versions from StepAudio's report. The radar shows three domain success rates; the bar panel shows the separately reported equal-domain macro. Grok is the macro leader, not the winner in every domain.", takeaway="The reported macro scores are close while the domain profiles differ. This comparison cannot be pooled with the original clean/realistic τ-Voice results."),
    dict(id="venus", group="fdb3", title="Realtime-Venus: Full-Duplex-Bench v3", kind="radar", models=["Realtime-Venus-Omni", "Realtime-Venus-Audio", "GPT-Realtime", "Gemini Live 3.1"], axes=["Tool selection F1", "Argument accuracy", "Task pass@1"], note="Both Venus frontends are from the revised system report; closed references are from the benchmark comparison. GPT-Realtime leads these three metrics in that source, not a current global leaderboard. This is not a common rerun.", takeaway="Tool-selection F1 is substantially higher than complete-task pass@1. These metrics have different success criteria, so their difference is not a stage-wise failure rate."),
    dict(id="minicpm", group="mpe", title="MiniCPM-o 4.5: Duplex-MPE", kind="paired-radar", axes=["Fresh onset", "Answer accuracy", "Silence", "Yield"], note="Explicit and implicit addressing are separate panels. Moshi and Voila are representative speech references. Answer accuracy is conditional on fresh responses; yield uses model-specific eligible speaking events. Polygon area is not an overall score. Gemini's transcript control is excluded.", takeaway="MiniCPM-o combines frequent fresh responses and silence preservation, but conditional answer accuracy is much lower. Voila's higher yield is conditional on different eligible events."),
    dict(id="tau-original", group="tau_original", title="Original τ-Voice: closed voice references", kind="facets", note="Original benchmark Table 6 All row; clean and realistic conditions remain separate. None of the five selected systems is evaluated here. GPT-5's text control is not plotted as a voice competitor.", takeaway="All three voice systems perform worse under realistic audio conditions in this source comparison; later τ-Voice implementations are separate evidence."),
    dict(id="echochain", group="echo", title="EchoChain: closed voice references", kind="facets", note="Paper Table 1, across 200 interrupted conversations. MPR requires every criterion in a conversation to pass; MCP scores individual criteria. None of the five selected systems is evaluated here.", takeaway="Passing many individual criteria does not guarantee complete conversation success. Even the strongest reported voice reference passes fewer than half of conversations."),
]

SHORT_NAMES = {
    "Moshi + CoT (TWL study)": "Moshi + CoT",
    "TWL: early length-DPO": "TWL early DPO",
    "Kimi-Audio-7B-Instruct": "Kimi-Audio (reference)",
    "FLAIR w/ thk": "FLAIR with thinking",
    "FLAIR w/o thk": "FLAIR without thinking",
    "StepAudio 3 Realtime": "StepAudio 3",
    "Grok Voice Think Fast 2.0 High": "Grok Think Fast 2.0 High",
    "Qwen Audio 3.0 Realtime Plus": "Qwen Audio 3.0 Plus",
    "GPT-Realtime-2.1 High": "GPT-Realtime 2.1 High",
    "Realtime-Venus-Omni": "Venus Omni",
    "Realtime-Venus-Audio": "Venus Audio",
    "GPT-realtime-2025-08-28": "GPT-realtime (2025-08-28)",
    "Gemini Live 2.5 native audio": "Gemini Live 2.5 native",
}
