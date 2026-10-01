# AI2AI Duplex — Literature Review

[Project webpage](https://borrisonxiao.github.io/ai2ai-duplex-report/)

The project webpage is live on GitHub Pages. It deploys the rendered static files from **main → / (root)**; no separate build service is required. A successful Git push is followed by a deployment/content check before an update is called live.

The only project tab is Literature review. Revised on 1 October 2026 with an evidence cutoff of 30 September 2026, it compares duplex system architectures, code/weight/training availability, benchmarks, natural and generated training data, and implications for incremental, revision-aware, speaker-aware reasoning. It uses primary papers, official repositories and dataset/model cards, with reported results kept separate from this review’s synthesis.

The webpage now includes five original-paper architecture screenshots and model-based performance profiles: benchmark-coverage matrix, within-protocol radars and bar plots, and exact-value tables. Profiles cover TWL, FLAIR, StepAudio 3, Realtime-Venus and MiniCPM-o, with representative models and closed source leaders where reported. The plots and tables share one audited data source; 43 model/configuration vectors match eight primary PDFs. Missing scores are NR, never zero. Incompatible protocols, mixed units and text-only controls are not combined into a global ranking.

The updated [20-page detailed LaTeX report](report/build/detailed-report.pdf) has the same figures and scores, top-five literature categories, synchronization-centered research questions, equations and pilot plans. See its [rendered preview](report/preview/detailed/contact-sheet.png) and [report documentation](report/README.md). The separate [six-page meeting brief](report/build/duplex-report.pdf) remains compact ([preview](report/preview/contact-sheet.png)); the [original nine-page report](report/build/archived-report.pdf) is preserved. The [Overleaf-ready source ZIP](report/build/duplex-report-source.zip) contains all three editable sources. These additions keep the webpage's single-tab structure.

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

Rebuild and validate:

```bash
python report/scripts/build_performance.py
python scripts/build_site.py
python scripts/validate_site.py
python scripts/check_browser.py
python -m http.server 8000
```

To refresh source reachability and arXiv metadata explicitly:

```bash
python scripts/verify_sources.py
python scripts/build_site.py
python scripts/validate_site.py
```

Availability means the specific artifact inspected as of the review date. “Not located” does not mean an artifact cannot exist. Reported corpus sizes include gated, reconstructed and partially released data, labeled separately. No experiments were run and no model weights or training datasets were downloaded.
