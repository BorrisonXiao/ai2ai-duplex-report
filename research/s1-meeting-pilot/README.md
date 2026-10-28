# Fresh S1 GPU pilot

[Review the requests, actual replies and source facts](https://borrisonxiao.github.io/ai2ai-duplex-report/study-progress.html#fresh-pilot).

Three distinct existing questions are tested at 5:09, 9:21 and 21:40 in two AMI meetings; these are caller-validation cases, not a full-bank accuracy result.

- Buffered input supplies the complete earlier audio and recorded question before generation.
- Native-packet diagnostics retain the earlier audio as a user turn, then submit the request in 480 ms frames; this does not demonstrate listening throughout the meeting.
- One correct plain-text response is rejected by the speech interface; no complete spoken answer is found in the final three-case native-packet check.
- The automatic judge produces inconsistent fact judgments; source-checked Codex reviews are stored separately and the original verdicts are retained.
- One quiet buffered response remains pending listening; quiet audio is not automatically scored incorrect.
- The full evaluation protocol remains unvalidated, and all 105 reference answers still require unified verification before full-bank runs.

Each of four sequential jobs uses one A100 SXM 80 GB: Thinker, Talker, MTP and Code2Wav share GPU 0; after they exit, Parakeet ASR and then the offline Qwen3-30B Instruct judge use GPU 0. Language-model inference uses vLLM. S2 is disabled. The maximum concurrent allocation is one GPU, no CUDA OOM occurs, and no two-GPU fallback is used. Total allocation is 1,291 seconds / 0.35861 GPU hours, including every attempt and post-processing stage. All jobs are finished.

`progress.json` contains input hashes, processor lengths, reference passages, model outputs, score explanations, source-checked audits and per-job cost; `manifest.json` checks every exported file. Players contain short exact excerpts of existing inputs and actual model playback. Full meeting prefixes and private runtime logs are not hosted here.

The earlier evaluator snapshot remains under `../s1-evaluation/`; `code/` here contains the current v0.1.2 scoring code, 46-check suite and source-audit script. The three new checks distinguish a completed input with output failure, reject a positive verdict on an empty answer, and reject an incomplete verdict that simultaneously claims every fact is supported without unsupported claims. These checks catch logical inconsistencies; they cannot guarantee a judge's semantic accuracy. `regression.json` is the actual CPU check result.
