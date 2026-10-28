# Shared S1 evaluator

- Extract the answer from actual model playback and keep native model text separately.
- Check required facts, then require an explicit review before certifying a semantic answer.
- Report absent thinking channels as N/A and unrecorded native output tokens as unavailable.
- Preserve all planned questions, failed runs and earlier evidence when resuming a run.
- Refresh local progress after each example and every 30 seconds during evaluation.

The current checks use three earlier DuplexOmni outputs and synthetic regression fixtures; no new model or ASR inference has run, and none of these cases belongs to the new 105-question evaluation. The full evaluation gate remains open until the small end-to-end S1 pilot and reference checks are complete.

## Inputs and outputs

| Input | What it contains | Output |
|---|---|---|
| Evaluation manifest | Distinct question IDs, exact recorded requests, input format and output-file locations | One extraction record per question |
| Model playback | Model-only mono audio, file checksum and declared scoring window | Audio properties and independent speech transcript |
| Verified references | Answer, required facts and earlier source evidence | Fact-match diagnostics; no keyword-only correctness pass |
| Review file | Human/Codex or future LLM judgment, bound to the exact candidate and reference checksums | Complete-answer score, missing facts and unsupported claims |
| Native token IDs, if recorded | Request-time text/control/audio groups | Separate counts and explicit availability status |

Each result folder contains immutable `candidate.json`, versioned `score-*.json`, the exact reference/review snapshots, a blinded `judge-input.json`, an event log, and atomic progress/summary files. Re-ingesting identical evidence leaves case counts unchanged. A changed run needs a separate attempt directory; the evaluator never picks the best answer from retries.

## Commands from the project workspace

```bash
envs/data/bin/python scripts/check_s1_evaluation.py /tmp/s1-evaluator-checks.json

envs/data/bin/python scripts/run_s1_evaluation.py evaluate \
  --manifest research/s1_evaluation/saved-output-manifest.json \
  --reviews research/s1_evaluation/control-reviews.json \
  --output exp/s1_evaluation/saved_outputs_v3 \
  --project-progress site/research/what-to-think/execution-progress.json

envs/data/bin/python scripts/run_s1_evaluation.py serve \
  --directory exp/s1_evaluation/saved_outputs_v3 --port 8765
```

The last command serves the local report at `http://127.0.0.1:8765/live.html`. The evaluation worker writes progress; the viewer polls every five seconds and marks stale running updates after 60 seconds. Public report pages are dated snapshots published at checkpoints.

## Caller contract for the next S1 pilot

Use `source.format = run_record` and export `s1-eval-run/v1` with `case_id`, `question`, `model`, `s2_enabled: false`, `status`, `complete_input`, `input_audio_path`, `input_audio_sha256`, `audio_path`, `audio_sha256`, `window_seconds`, `native_text`, `asr_text`, `asr_provenance`, `finish_reason`, `context_mode`, `thinking_channel: not_applicable`, and optional `token_ids`. Paths are relative to the run record. ASR provenance must identify the recognizer and match the audio checksum and window. Use model-only played audio; mixed replay channels and discarded synthesis are rejected.

Moshi, MiniCPM and DuplexOmni S1 share this contract; their actual new inference adapters still need end-to-end pilot checks. The first pilot starts with the existing DuplexOmni caller. Native token IDs must be explicitly limited to request-time output with `token_scope: request_time`; absent IDs remain unavailable, and output audio codes stay separate. A native S1 text stream is never relabeled as a thinking trace.

Before `main105` evaluation, every reference-inventory row must be verified and contain a validated answer, the manifest must bind that frozen inventory and scoring-reference file, the scoring answers/facts/evidence must exactly match the inventory, and all 105 IDs and request versions must match it. Historical published traces are rejected as main evaluation inputs. Missing runs remain pending until `--finalize`; then they count as failures. Missing judgments or unclear ASR keep final accuracy pending. Quiet audio requires listening; all-zero audio is a failure. Truncated answers need explicit completeness review.

The scoring interface exports blinded judge inputs but does not launch a judge model. Current saved-output judgments are Codex reviews of stored independent transcripts; connecting a local vLLM judge and checking its judgments are still pending. Software checks do not demonstrate long-history retention or validate the full evaluation protocol.
