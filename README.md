# AI2AI Duplex — Research and Experiments

[Project webpage](https://borrisonxiao.github.io/ai2ai-duplex-report/)

Current experiments: [E1 — Single-request handoff](https://borrisonxiao.github.io/ai2ai-duplex-report/experiments/trajectory.html), [E2 — S1 interruption](https://borrisonxiao.github.io/ai2ai-duplex-report/experiments/interruption.html), and [study status and results](https://borrisonxiao.github.io/ai2ai-duplex-report/experiments/controlled-study.html). E1 compares S2 off/forced with one complete bread question. E2 compares uninterrupted/corrected speech with S2 off. The current attempt is `1029543`, with dependent CPU audit `1029544`; GPU results are pending. Input previews are explicitly labeled. Earlier budget recordings and decoder variants live in the [historical archive](https://borrisonxiao.github.io/ai2ai-duplex-report/experiments/archive.html).

Experiment IDs (`E1a`, `E1b`, `E2a`, `E2b`) name conditions; Slurm IDs name attempts. Editable records are `research/current-study.json`, `current-handoff.json` and `current-interruption.json`. `scripts/build_current_experiments.py` generates both viewers, the collection and study overview; `build_trajectory.py` and `build_controlled_study.py` remain compatible entry points. Authored synthetic inputs use the Flite SLT voice; attribution is in `research/flite/COPYING`. The archived viewer has a separate frozen script/data bundle so old runs cannot become the current default.

The project webpage is live on GitHub Pages. It deploys the rendered static files from **main → / (root)**; no separate build service is required. A successful Git push is followed by a deployment/content check before an update is called live.

The site has Literature review and Experiments collections. The literature review, revised on 2 October 2026 with an evidence cutoff of 30 September 2026, compares duplex system architectures, code/weight/training availability, benchmarks, natural and generated training data, and implications for incremental, revision-aware, speaker-aware reasoning. It uses primary papers, official repositories and dataset/model cards, with reported results kept separate from this review’s synthesis.

The focused architecture gallery now has eight original-paper screenshots: TWL/Moshi, FLAIR, StepAudio 3, Realtime-Venus, MiniCPM-o, [DuplexOmni](https://arxiv.org/pdf/2606.09186v1), [NemotronLabs VoiceChat](https://arxiv.org/pdf/2609.21967v1) and [Spoken Language Models that Think Aloud](https://arxiv.org/pdf/2609.26488v1), using its Figure 2. Twelve model/benchmark profiles include a coverage matrix, within-protocol radars, unit-preserving bar plots, and exact-value tables with representative models and closed source leaders where reported. The plots and tables share one audited data source; 67 model/configuration vectors match eleven primary PDFs. DuplexOmni's scores include its Gemini thinking backend; VoiceChat's tool-execution barge-in restriction is explicit. Think-Aloud is a think-while-speaking framework, not demonstrated full duplex; its two plots distinguish cumulative reasoning silence from speech overhang and show S2S QA with the paper's GPT-4o-Realtime reference. Its proprietary corpus cannot be released, and study code/weights were not located as of 2 October. Missing scores are NR, never zero. Incompatible protocols, mixed units and text-only controls are not combined into a global ranking.

The updated [29-page detailed LaTeX report](report/build/detailed-report.pdf) has the same figures and scores, eight system/design anchors, five entries in each other literature category, synchronization-centered research questions, equations and pilot plans. See its [rendered preview](report/preview/detailed/contact-sheet.png) and [report documentation](report/README.md). The separate [six-page meeting brief](report/build/duplex-report.pdf) remains unchanged ([preview](report/preview/contact-sheet.png)); the [original nine-page report](report/build/archived-report.pdf) is preserved. The [Overleaf-ready source ZIP](report/build/duplex-report-source.zip) contains all three editable sources. The Literature review collection contains two sub-tabs; the existing landscape and PDF URLs are unchanged.

The new [Context-aware assistance webpage](https://borrisonxiao.github.io/ai2ai-duplex-report/context-assistance.html) reviews the tentative 4 October scope: use authorized multi-party conversation context to disambiguate a later assistant-directed request, clarifying when needed. It covers 15 verified papers, five close resources (MSI-Bench, GroupMemBench, MultiTalk, ASK-QA and MISeD), five system designs, nine complementary benchmarks and eight training resources/ingredients. Three original-paper screenshots and three source-specific result plots accompany exact-value tables. Broad multi-party context use is already studied; causal speech synchronization, clarification and context-dependent requests define a more specific candidate direction. Unsolicited intervention remains a separate optional extension. No new experiments or training annotations were created, and the existing LaTeX reports retain their earlier scope.

The visual design follows [JSALT 2026 Downsampling](https://borrisonxiao.github.io/jsalt26-downsampling/). Text wraps naturally in the browser; comparison tables scroll on narrow displays. Search fields filter table entries, and paper notes expand for detail. No external JavaScript, fonts, model calls or analytics are loaded.

## Review sources and maintenance

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
