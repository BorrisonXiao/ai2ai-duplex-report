# Full-duplex reasoning: detailed report and meeting brief

[Detailed PDF](build/detailed-report.pdf) · [Detailed preview](preview/detailed/contact-sheet.png) · [Meeting PDF](build/duplex-report.pdf) · [Meeting preview](preview/contact-sheet.png) · [Overleaf-ready source ZIP](build/duplex-report-source.zip) · [Project webpage](https://borrisonxiao.github.io/ai2ai-duplex-report/)

The updated 20-page detailed report includes five original-paper architecture screenshots, a benchmark-coverage matrix, eight performance profiles, exact-value tables, and the synchronization-centered research agenda. It retains the top-five selections in four literature categories and the longer reasoning, equations, caveats and pilot plan. The [original nine-page PDF](build/archived-report.pdf) and [source](archived-report.tex) are preserved separately.

The model profiles cover Think while Listening, FLAIR (QA and older interaction evaluations), StepAudio 3 Realtime, Realtime-Venus, and MiniCPM-o 4.5, followed by closed-reference comparisons on original τ-Voice and EchoChain. Radars use raw percentages within one protocol; mixed units and comparisons with fewer than three metrics use separate bar axes. No radar-area ranking, missing-score imputation, cross-benchmark average or claim about current global SoTA is made. The closed systems are named source references, with API revisions stated where available. The webpage uses the same generated plots and score data.

Five content pages plus one availability/reference page, aimed at speech researchers. The brief replaces long architectural descriptions with five screenshots from the original papers: Moshi (with Think while Listening explained in the caption), MiniCPM-o 4.5, FLAIR, StepAudio 3 Realtime, and Realtime-Venus. An original synchronization trace and a sourced timing-quantum plot support the research discussion. The plot compares published modeling parameters, not measured response latency.

Four compact literature tables retain exactly five entries each: systems, synchronization papers, benchmarks, and conversational training resources. The system-availability table is on the final reading-aid page, alongside references. A fifth table retains five unranked research questions: think while listening, think while speaking, listen while speaking, synchronize heterogeneous clocks, and revise while delegating. The discussion-route section and timetable have been removed.

Figure 6 in the meeting brief uses a concrete “Monday → Tuesday” spoken correction, with user speech, listening, reasoning and speech-output lanes. “Processed” means the model has used that input, not just received audio. “Already played” and “queued audio” distinguish speech that needs an audible correction from speech that can still be changed. The detailed report reuses this plain-language figure and retains the formal synchronization definitions in the surrounding text.

The brief's [reported-results page](preview/page-05.png) has one compact comparison table for SRQA, τ-Voice, Full-Duplex-Bench v3, EchoChain and Duplex-MPE. Original τ-Voice and StepAudio's Artificial Analysis implementation occupy separate rows. Missing results are NR, never zero. Text-only GPT-5 and transcript-conditioned Gemini references are shown separately, not as voice competitors. The detailed report and webpage add FLAIR's study-specific evaluations without treating its older Full-Duplex-Bench as v3. All 43 stored model/configuration score vectors, including contextual comparators and domain scores, match eight primary PDFs; this checks transcription, not experimental reproducibility.

The six-page brief remains the compact meeting version; the added profile pages are only in the detailed report and webpage. Automated word counts exclude text inside the raster screenshots, so page count and the rendered preview are the more useful measures of reading load.

The brief was revised on 1 October 2026; literature and availability retain the 30 September 2026 cutoff. No experiments, model calls, model/dataset downloads or GPU jobs were run. Availability is checked against primary manuscripts and official artifacts; “not located” does not mean “does not exist.” The original private proposal and downloaded paper PDFs are not included.

## Sources, diagrams and template

The unmodified `iclr2026_conference.sty` and `.bst` come from the [official ICLR master template](https://github.com/ICLR/Master-Template/tree/master/iclr2026), following the [ICLR 2026 author guide](https://iclr.cc/Conferences/2026/AuthorGuide). These are internal reports, not accepted papers or submissions; the sources replace the template's conference-status header. Architecture screenshots are attributed reproductions, not redraws; copyright remains with the original rights holders. The synchronization trace and timing plot remain original TikZ. Performance figures are generated vector PDF/SVG with PNG previews. Paragraphs and headings have no manually forced line breaks; LaTeX determines their wrapping. Table rows retain necessary structural line endings.

Source figures: Moshi Fig. 1 (p. 7); MiniCPM-o Fig. 4 (p. 4); FLAIR Fig. 2 (p. 5); StepAudio 3 Fig. 7B (p. 14); Realtime-Venus Fig. 3 (p. 5). Screenshots are rendered at 300 dpi, preserving source labels/arrows/legends. Only margins and surrounding prose are cropped, except for the explicitly labeled selection of StepAudio panel B (adaptive-routing panel A omitted). Full-resolution PNGs are in `figures/papers/`; their manifest records crop coordinates, source PDFs/pages and hashes.

- `duplex-report.tex`: editable five-page meeting narrative plus availability/references.
- `figures/papers/*.png` and `manifest.json`: original-paper screenshots and reproducible extraction provenance.
- `figures/commitment.tex`, `timing.tex` and `styles.tex`: editable vector trace, plot and shared styles. Earlier unused architecture redraws remain local but are not compiled or packaged.
- `research/figure-sources.json`: per-figure primary sources and verified architectural details.
- `research/brief_data.py`: editable compact comparison cells, research questions and timing values.
- `scripts/generate_brief.py`: generates compact tables and linked references from curated facts and archived metadata.
- `research/reported-performance.json`: reported score vectors, source versions/table/page locators, scaling rules and the five-system coverage matrix.
- `scripts/make_table_reported_performance.py`: generates the result comparison and quantitative prose macros from that JSON; never edit the generated table by hand.
- `scripts/audit_reported_performance.py` and `research/reported-performance-audit.json`: primary PDF table-value checks and source hashes, explicitly not a reproduction audit. Downloaded PDFs and private evidence-page renders are excluded from the source ZIP.
- `research/performance_profiles.py`: profile selections, reading notes and benchmark-specific axes.
- `scripts/build_performance.py`: generates nine shared figures, eight exact-value tables, `sections/performance.tex` and `research/performance-plots.json`; edit structured inputs, not generated tables or sections.
- `figures/performance/*.{pdf,svg,png}`: coverage matrix, within-protocol radars and unit-preserving bar charts shared with the webpage.
- `scripts/extract_paper_figures.py`: regenerates screenshot crops from locally obtained primary PDFs; normal compilation uses the included PNGs and does not download papers.
- `detailed-report.tex` and `sections/architecture-gallery.tex`: updated longer report with architecture screenshots, benchmark profiles, formal synchronization questions and pilot plan.
- `archived-report.tex` and `build/archived-report.pdf`: original nine-page version, kept for reference.
- `research/focused_review.py`: original top-five selections and grounded candidate notes.
- `tables/*.tex`, `brief-references.tex` and `references.bib`: generated files; edit their curated sources, not these files.
- `research/source-audit.json`: timestamped source reachability and arXiv metadata, not a reproduction audit.
- `research/LITERATURE.md` and `literature.json`: fuller readable and structured literature digests.
- `research/IDEAS.md` and `ideas.json`: eight unranked implementations grouped under the five questions, with risks and pilot estimates.
- `preview/page-*.png`: rendered meeting-page previews; `contact-sheet.png` shows the complete brief.
- `preview/detailed/page-*.png` and `contact-sheet.png`: rendered updated detailed report.

## Build and validate

Install a TeX distribution with `latexmk`, or [Tectonic](https://tectonic-typesetting.github.io/). Install `pymupdf`, `pillow`, `matplotlib` and `numpy` for the build, plots and preview rendering. Tectonic downloads its TeX/font bundle on first use; choose a cache on a filesystem with headroom. The compiler and temporary cache used to prepare this draft are not required by the source ZIP.

```bash
python scripts/build.py --tectonic /path/to/tectonic
python scripts/build.py --tectonic /path/to/tectonic --detailed
python scripts/validate.py
```

With Tectonic or latexmk on PATH, omit `--tectonic`. To regenerate shared plots without compiling, run `python scripts/build_performance.py`. For an existing PDF, regenerate previews with `python scripts/build.py --preview-only`; add `--detailed` for the updated detailed report. Generation is offline. To update citation/access snapshots explicitly, run `python scripts/refresh_sources.py` before rebuilding; it requires internet access.

For Overleaf, upload `build/duplex-report-source.zip` and select `duplex-report.tex` as the main file; select `detailed-report.tex` for the longer version. With a full local TeX installation, run `latexmk -pdf duplex-report.tex` here. The existing [project webpage](https://borrisonxiao.github.io/ai2ai-duplex-report/) remains a separate, broader literature review; its publication depends on repository Pages configuration.

To rerun the reported-score audit after editing its JSON, provide a directory containing the eight primary PDFs named in `research/reported-performance.json`: `python scripts/audit_reported_performance.py --evidence-dir /path/to/pdfs`. The audit does not download papers. Build and validation use the committed audit snapshot and reject stale result data. Validation checks plot hashes, exact table values, figure/table co-location, citations, margins and ZIP dependencies. A source ZIP already contains the generated tables and vector plots needed for compilation.

For an independent packaging check, extract the ZIP into a fresh directory, compile its three main files there, then run `python scripts/validate.py --source-check-dir /path/to/fresh/directory`. It checks that page counts and extracted contents match the prepared PDFs, with no overflow or unresolved references.
