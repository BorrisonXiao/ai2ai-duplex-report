# AI2AI Duplex — Literature Review

[Project webpage](https://borrisonxiao.github.io/ai2ai-duplex-report/)

The page is ready for GitHub Pages; publication is pending repository Pages configuration. Select **Deploy from a branch → main → / (root)**. The repository contains the rendered static files, so no build service is required.

The only project tab is Literature review. The review is dated 30 September 2026 and compares duplex system architectures, code/weight/training availability, benchmarks, natural and generated training data, and implications for incremental, revision-aware, speaker-aware reasoning. It uses primary papers, official repositories and dataset/model cards, with reported results kept separate from this review’s synthesis.

The visual design follows [JSALT 2026 Downsampling](https://borrisonxiao.github.io/jsalt26-downsampling/). Text wraps naturally in the browser; comparison tables scroll on narrow displays. Search fields filter table entries, and paper notes expand for detail. No external JavaScript, fonts, model calls or analytics are loaded.

## Review sources and maintenance

- `research/review_data.py`: curated facts, artifact statuses and synthesis; the editable source.
- `research/literature.json`: generated, structured digest for reuse.
- `research/LITERATURE.md`: generated readable review.
- `research/source-audit.json`: primary-link checks and arXiv bibliographic metadata; link success is not model reproduction.
- `scripts/build_site.py`: dependency-free, offline generator for the HTML and digests.
- `scripts/validate_site.py`: structure, citation, table and wrapping checks.

Rebuild and validate:

```bash
python scripts/build_site.py
python scripts/validate_site.py
python -m http.server 8000
```

To refresh source reachability and arXiv metadata explicitly:

```bash
python scripts/verify_sources.py
python scripts/build_site.py
python scripts/validate_site.py
```

Availability means the specific artifact inspected as of the review date. “Not located” does not mean an artifact cannot exist. Reported corpus sizes include gated, reconstructed and partially released data, labeled separately. No experiments were run and no model weights or training datasets were downloaded.
