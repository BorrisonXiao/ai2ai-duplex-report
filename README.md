# AI2AI Duplex — Research and Experiments

[Project webpage](https://borrisonxiao.github.io/ai2ai-duplex-report/)

Current focus: [human-recorded S1 interruption](https://borrisonxiao.github.io/ai2ai-duplex-report/experiments/interruption.html) and [the evidence review](https://borrisonxiao.github.io/ai2ai-duplex-report/experiments/natural-study.html). Original DailyTalk conversation 656 supplies one human question about outlet stores and one same-speaker clarification, “Faulty products?”; its timing is adapted to actual model speech. Job `1035079` used one H100 80 GB, all S1 components sharing GPU 0, with S2 absent. Matched greedy conditions have identical first 12 returned-field ticks. The clarification genuinely overlaps model speech by 0.40 s; native STOP clears 0.28 s of queued audio, with no obsolete-epoch speech after STOP. The model answers the clarification aloud. Independent audio transcription verifies the cut and new reply. This is a single interaction demonstration, not a general robustness or factual-accuracy claim.

Current IDs `N2a` (uninterrupted human question) and `N2b` (one clarification during speech) name conditions; Slurm IDs name attempts. `research/current-natural.json` contains lossless actual replay, and `natural-interruption-review.json` records the evidence. Source bounds, hashes and CC BY-SA 4.0 attribution are in `research/natural-dailytalk/`. `scripts/build_current_experiments.py` renders `build_natural_interruption.py` and preserves [basic S1 checks](https://borrisonxiao.github.io/ai2ai-duplex-report/experiments/single-request.html), [earlier handoff](https://borrisonxiao.github.io/ai2ai-duplex-report/experiments/handoff.html), [earlier synthetic interruption](https://borrisonxiao.github.io/ai2ai-duplex-report/experiments/archive-interruption.html), and the [historical archive](https://borrisonxiao.github.io/ai2ai-duplex-report/experiments/archive.html). Earlier recipe silence, stochastic greeting/S2 stalls and long-history cache spikes remain explicitly documented.

The project webpage is live on GitHub Pages. It deploys the rendered static files from **main → / (root)**; no separate build service is required. A successful Git push is followed by a deployment/content check before an update is called live.

The site has Literature review and Experiments collections. The literature review, revised on 2 October 2026 with an evidence cutoff of 30 September 2026, compares duplex system architectures, code/weight/training availability, benchmarks, natural and generated training data, and implications for incremental, revision-aware, speaker-aware reasoning. It uses primary papers, official repositories and dataset/model cards, with reported results kept separate from this review’s synthesis.

The focused architecture gallery now has eight original-paper screenshots: TWL/Moshi, FLAIR, StepAudio 3, Realtime-Venus, MiniCPM-o, [DuplexOmni](https://arxiv.org/pdf/2606.09186v1), [NemotronLabs VoiceChat](https://arxiv.org/pdf/2609.21967v1) and [Spoken Language Models that Think Aloud](https://arxiv.org/pdf/2609.26488v1), using its Figure 2. Twelve model/benchmark profiles include a coverage matrix, within-protocol radars, unit-preserving bar plots, and exact-value tables with representative models and closed source leaders where reported. The plots and tables share one audited data source; 67 model/configuration vectors match eleven primary PDFs. DuplexOmni's scores include its Gemini thinking backend; VoiceChat's tool-execution barge-in restriction is explicit. Think-Aloud is a think-while-speaking framework, not demonstrated full duplex; its two plots distinguish cumulative reasoning silence from speech overhang and show S2S QA with the paper's GPT-4o-Realtime reference. Its proprietary corpus cannot be released, and study code/weights were not located as of 2 October. Missing scores are NR, never zero. Incompatible protocols, mixed units and text-only controls are not combined into a global ranking.

The updated [29-page detailed LaTeX report](report/build/detailed-report.pdf) has the same figures and scores, eight system/design anchors, five entries in each other literature category, synchronization-centered research questions, equations and pilot plans. See its [rendered preview](report/preview/detailed/contact-sheet.png) and [report documentation](report/README.md). The separate [six-page meeting brief](report/build/duplex-report.pdf) remains unchanged ([preview](report/preview/contact-sheet.png)); the [original nine-page report](report/build/archived-report.pdf) is preserved. The [Overleaf-ready source ZIP](report/build/duplex-report-source.zip) contains all three editable sources. The Literature review collection contains five sub-tabs; the existing landscape and PDF URLs are unchanged.

The new [Context-aware assistance webpage](https://borrisonxiao.github.io/ai2ai-duplex-report/context-assistance.html) reviews the tentative 4 October scope: use authorized multi-party conversation context to disambiguate a later assistant-directed request, clarifying when needed. It covers 15 verified papers, five close resources (MSI-Bench, GroupMemBench, MultiTalk, ASK-QA and MISeD), five system designs, nine complementary benchmarks and eight training resources/ingredients. Three original-paper screenshots and three source-specific result plots accompany exact-value tables. Broad multi-party context use is already studied; causal speech synchronization, clarification and context-dependent requests define a more specific candidate direction. Unsolicited intervention remains a separate optional extension. No new experiments or training annotations were created, and the existing LaTeX reports retain their earlier scope.

The [MP-Bench preview](https://borrisonxiao.github.io/ai2ai-duplex-report/mpbench.html) adds three complete original audio clips with their upstream ASR transcripts, task labels, dataset composition, and paper-reported text-only Gemini-3.1-Pro reference results. The expanded scoring notes explain that turn-taking is a single task-level decision after a full conversation clip, how timestamp detection and answer/appropriateness scores work, and the paper's unspecified conversion from text-only outputs to turn-taking labels. Reference values remain identified as paper results, not local reruns. Its manifest and generator are in `research/mpbench/` and `scripts/build_mpbench.py`. MP-Bench is licensed CC BY-NC 4.0 and designated for evaluation only; the full local attribution record is `research/mpbench/ATTRIBUTION.md`. Rebuild with `python scripts/build_mpbench.py`; the generator checks each preview WAV against its recorded SHA-256.

The [MSI-Bench preview](https://borrisonxiao.github.io/ai2ai-duplex-report/msi-bench.html) plays selected English and Mandarin source turns and shows three complete cases marked `call_policy=no_calls`, with their reference answers and rubrics. In the pinned 1,152-case snapshot, 395 cases expect a response under that policy: 126 speaker-authority, 191 selective-disclosure and 78 background-speech retrieval cases. The page audits balanced languages/patterns/scenes, 10,001 WAV files and speak/hear probe design, then separates those data facts from the paper’s reported model results. Its case timelines combine unchanged source WAVs with text-only turns where no WAV exists; its reference answers are dataset targets, not outputs from an evaluated model. The full 4.29 GB release remains local at `data/benchmarks/msi_bench_v1`; the page includes the CC BY 4.0 license, per-source ambience credits and the full upstream attribution list. The current release checksum file misses the changed README hash; all other 11,162 entries pass. The mismatch is recorded in the page’s [integrity audit](research/msi-bench/integrity.json). Rebuild with `python scripts/build_msi_bench.py`; the generator reads the local case index and checks each selected WAV against the pinned release checksum before copying it to the site.

The visual design follows [JSALT 2026 Downsampling](https://borrisonxiao.github.io/jsalt26-downsampling/). Text wraps naturally in the browser; comparison tables scroll on narrow displays. Search fields filter table entries, and paper notes expand for detail. No external JavaScript, fonts, model calls or analytics are loaded.

The [Pre-thinking proposal](https://borrisonxiao.github.io/ai2ai-duplex-report/prethinking.html) is a tentative design discussion dated 10 October 2026, with 18 verified papers. It explains causal transcript-teacher/audio-student supervision, private reasoning distributions and loss, S1 scheduling, request-time preemption, grounded notes, speaker memory, MultiTalkFT data construction and fair controls. An interactive request-arrival illustration is explicitly hypothetical. MathJax is bundled locally for offline equations. This update uses 0 GPUs and launches no inference or training; the existing S1/S2 examples are preserved. The literature collection now has five sub-tabs; earlier reviews retain their evidence cutoffs. Rebuild with `python scripts/build_prethinking.py`; run `python scripts/validate_prethinking.py` and `python scripts/check_prethinking_browser.py` alongside the existing validators. Sources and Markdown/JSON digests are in `research/prethinking/`.

The [Pre-thinking pilot](https://borrisonxiao.github.io/ai2ai-duplex-report/experiments/prethinking-pilot.html) uses real AMI EN2003a workshop audio (37.3 minutes, three participants) and manual speaker/word annotations. It includes 12 brainstorming categories, source examples and an interactive timing explorer for 10–100 tokens/s, setup overhead and sentence/batch delivery. Rates are assumptions; local Qwen teacher generations and content review are reported separately. The pinned Qwen3-30B-A3B Thinking teacher uses one A100-SXM4 80 GB on GPU 0, without S1 or speech; CPU asset/visualization work uses 0 GPUs, maximum one experiment GPU. A pending H100 request was cancelled at zero allocation. At the user’s explicit follow-up request, the appendix publishes all 64 exact Qwen prompts and full captured private-thinking outputs; the original local files are unchanged. The category table now pairs actual transcripts with verbatim thinking passages. A second, shorter horizontal timeline shows one input update at a time, with complete numbered transcript cards and matching speech spans. All 10/30/60/100-token/s rows project the identical captured token sequence from one call; only timing and truncation differ. Original prompts/history are held fixed, so this display is a timing comparison rather than a newly generated causal replay. Source excerpts are attributed CC BY 4.0 audio. Regenerate the trace/token bundle in the workspace with `envs/duplexomni/bin/python scripts/export_prethinking_traces.py` (CPU tokenizer only); rebuild the study bundle with `../envs/data/bin/python ../scripts/export_prethinking_pilot.py` from the site checkout, then render with `python scripts/build_prethinking_pilot.py` and validate with `python scripts/validate_prethinking_pilot.py`.

## Review sources and maintenance

The [single-request S2 study](experiments/s2-single.html) adds the observed human
outlet-store handoff, matched controls, real model playback, the initial
arithmetic token-limit failure and provider diagnostics. The follow-up compares
dialogue/user-ASR context and forced/model-triggered S2, and verifies a spoken
391 without forced delegation. Its generator is
`scripts/build_s2_single_study.py`; the workspace exporter is
`../scripts/export_s2_single_site.py`, and its evidence/audio bundle is
`research/s2-single-study.json`. Both full audio trials and the provider controls
are complete; the original failure remains documented as a diagnostic attempt.

The [S1 reproduction report](experiments/s1-reproduction.html) is an Experiments
sub-tab comparing the working native/greedy S1 runs with earlier failed controls.
It quotes source code directly, links line-numbered snapshots, and includes the
minimal one-H100 batch command, output checks and the independent author-harness
recipe. A [second appendix](experiments/s1-reproduction.html#inference-loop)
walks through packet preparation, the paced input loop, history and model calls,
concurrent speech/playback, and shutdown, with a clickable task diagram.
Generate it with `python scripts/build_current_experiments.py` from this
site checkout in the migrated workspace; `scripts/build_s1_reproduction.py`
checks all frozen inference source/config/input hashes before rendering. The
source manifest is `research/s1-reproduction/manifest.json`. Published launcher
views substitute private workspace/account names and are labeled accordingly.

Publishing preference (1 October 2026): after a validated webpage update, commit and push the relevant page/report changes to `origin/main` by default. Do not ask for publication confirmation again unless the user requests local-only work or the destination/scope changes. Exclude private proposals, downloaded papers, secrets and unrelated edits.

- `research/review_data.py`: curated facts, artifact statuses and synthesis; the editable source.
- `research/literature.json`: generated, structured digest for reuse.
- `research/LITERATURE.md`: generated readable review.
- `research/source-audit.json`: primary-link checks and arXiv bibliographic metadata; link success is not model reproduction.
- `scripts/build_site.py`: dependency-free, offline generator for the HTML and digests.
- `scripts/validate_site.py`: structure, citation, table and wrapping checks.
- `scripts/report_content.py`: architecture and numeric sections rendered from the report's shared evidence and generated plot manifest.
- `report/research/reported-performance.json`: version-pinned score vectors, units, conversion rules and primary-table locators.
- `report/scripts/build_performance.py`: shared PDF/SVG/PNG figures and exact-value LaTeX tables; requires Matplotlib and NumPy.
- `scripts/check_browser.py`: desktop/mobile/theme rendering and interaction checks; requires Playwright and Chromium.
- `research/context-assistance/review_data.py`: editable evidence and synthesis for the narrowed scope; its Markdown/JSON digests and primary-source audit are stored alongside it.
- `scripts/build_context_assistance.py`: offline focused sub-tab/digest generator; optional `--paper-dir` renders the three documented screenshot crops from a private PDF cache.
- `scripts/verify_context_sources.py`: explicit primary-page and artifact-link audit, without corpus/model downloads.
- `scripts/validate_context_assistance.py`: focused-page structure, bibliography, scores and wrapping checks.
- `scripts/check_context_browser.py`: both sub-tab routes, desktop/mobile/dark rendering, filtering and expandable figures.

Rebuild and validate:

```bash
python report/scripts/build_performance.py
python scripts/build_site.py
python scripts/build_context_assistance.py
python scripts/validate_site.py
python scripts/validate_context_assistance.py
python scripts/check_browser.py
python scripts/check_context_browser.py
python -m http.server 8000
```

To refresh source reachability and arXiv metadata explicitly:

```bash
python scripts/verify_sources.py
python scripts/build_site.py
python scripts/validate_site.py
```

Availability means the specific artifact inspected as of the review date. “Not located” does not mean an artifact cannot exist. Reported corpus sizes include gated, reconstructed and partially released data, labeled separately. No experiments were run and no model weights or training datasets were downloaded.

The focused review uses its own 4 October evidence snapshot; it does not silently change the broader review's September cutoff. Refresh it with `python scripts/verify_context_sources.py` followed by `python scripts/build_context_assistance.py`. Link reachability is not proof of a complete, reproducible release. Unspecified reuse terms are not described as open licences, and benchmark test cases must stay out of training.

## Experiment trajectory tool (5 October 2026)

The [Experiments collection](experiments/) contains the [trajectory viewer](experiments/trajectory.html). Updated 7 October with actual continuous run 1816185 on one A100: User → S1 → S2 → Talker content blocks, buffered prefixes distinct from delivered guidance, and playable user/full Talker/pre-guidance audio. S1 was called six times while S2 was pending but returned empty pre-guidance tts. It generated an assistance clause and a follow-up afterward; automatic waveform transcription recovered only the follow-up, so audible reproduction of the S2 clause is unverified. No acknowledgment or complete paper replication is claimed. The older 24-chunk text-only replay remains a separate diagnostic with silent user input and no Talker. Word alignment, realtime playback and automatic delegation are unverified. The optional synthetic demo is clearly labeled; local imports never upload.

- `research/trajectory-example.json`: reviewed public text/timing manifest with source-file hashes; no raw audio or private reasoning. The workspace exporters are `../scripts/export_html_trajectory_example.py` (older run) and `../scripts/export_continuous_html_example.py` (current continuous run).
- `scripts/build_trajectory.py`: deterministic offline generator of the collection, measured example, interactive chunk view and optional synthetic demo.
- `scripts/templates/trajectory.html.in`: viewer markup source.
- `assets/trajectory/viewer.js`, `viewer.css`: local interaction and layout assets.
- `research/trajectory-schema.md`: versioned JSON schema and timing semantics.
- `scripts/check_trajectory_browser.py`: browser replay, audio, import, navigation, safety and responsive checks.

Rebuild with `python scripts/build_trajectory.py`; validate the full site with the html-report validator and the existing review validators. Run browser checks using the workspace's uv-created `../envs/report` environment and an existing Chromium binary. Shared collection navigation is generated by `scripts/site_navigation.py`; original review/PDF URLs remain stable.


The input clip is a public DailyTalk excerpt (Keon Lee, Kyumin Park, Daeyoung Kim; Kyutai stereo adaptation), extracted as the right channel’s first 10 seconds and supplied under CC BY-SA 4.0. It is not a private user recording. `research/audio-provenance.json` verifies the original against its public LFS SHA-256 and verifies exact excerpt samples. Generated decoder clips are labeled separately.


The [interaction reproduction and evidence review](experiments/interaction-review.html) documents complete paced DailyTalk input, bounded Code2Wav decoding, the A100/H100 experiment grid and remaining response-quality failures. The [trajectory viewer](experiments/trajectory.html) defaults to measured clocked software PCM replay; lossless embedded FLAC retains waiting gaps and decodes to the exact recorded PCM.

The completion follow-up on the same [Pre-thinking pilot](https://borrisonxiao.github.io/ai2ai-duplex-report/experiments/prethinking-pilot.html#pilot-completion) labels the new history-free case single-round and compares two real two-round samples (conditioned reasoning, literal prefill, reset). It publishes ten additional exact prompts/outputs and frozen recipes. The single-round reference reaches 4,660 private / 4,878 total tokens; short-window rate projections now show prefixes of that complete reference, and a whole-output view shows the natural stop. Measured weighted speed is 25.43 tokens/s including prefill, 25.55 after first receipt, with two explicit 64-token warmups per allocation. Three sequential jobs each use one A100-SXM4 80 GB, teacher alone on GPU 0, maximum one GPU; total allocation 0.53944 GPU h. Nine traces close CoT, one literal continuation does not; content review finds wrong quotations, evidence-ID drift and incomplete note schemas. The teacher/student probability models and target masking are explained, without a claim that raw CoT is ready for distillation. New data: `research/prethinking-pilot/completion.json`; renderer: `scripts/prethinking_completion_content.py`. Original 64 traces and S1/S2 examples are preserved.

The [AMI question pilot](https://borrisonxiao.github.io/ai2ai-duplex-report/experiments/ami-questions.html) compares local text-model prompts and assistant-authored requests at four source times in EN2003a, with proposed reference answers, exact supporting speech, explicit review decisions and withheld-answer history controls. It is a text-only development study; no TTS or streaming speech-model result is implied. Run `python ../scripts/export_ami_questions.py` from the site checkout, then `python scripts/build_ami_questions.py` after other experiment page builders.
