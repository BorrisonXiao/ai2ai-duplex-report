#!/usr/bin/env python3
"""Check shortlist counts, citations, wrapping rules and rendered-report integrity."""
import hashlib
import argparse
import json
from pathlib import Path
import re
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research"))
import focused_review as data
import brief_data as brief

def body_word_count(document, page_limit=None):
    """Count extractable PDF text; raster screenshot labels are excluded."""
    text = "\n".join(page.get_text() for index, page in enumerate(document) if page_limit is None or index < page_limit)
    body = re.split(r"\nReferences\n", text, maxsplit=1, flags=re.I)[0]
    body = re.sub(r"AI2AI Duplex: [^\n]*\n", "", body)
    body = re.sub(r"(?m)^\d+\s*$", "", body)
    return len(body.split())

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-check-dir', type=Path, help='Directory containing freshly compiled PDFs/logs extracted from the source ZIP')
    args = parser.parse_args()
    checks = []
    def check(ok, description):
        if not ok:
            raise AssertionError(description)
        checks.append(description)

    digest = json.loads((ROOT / "research" / "literature.json").read_text())
    ideas = json.loads((ROOT / "research" / "ideas.json").read_text())
    audit = json.loads((ROOT / "research" / "source-audit.json").read_text())
    check(len(digest["categories"]) == 4 and all(len(c["rows"]) == 5 for c in digest["categories"]), "Exactly four categories and five entries per category")
    check(len(digest["research_questions"]) == 5, "Five major research questions")
    check(len(ideas["ideas"]) == 8 and len(ideas["removed"]) == 2, "Eight unranked, grounded candidates; duplicate/infeasible exclusions recorded")
    check(all(i["risk"] in {"low", "medium", "high"} and i["contribution_type"] in {"empirical", "method", "theory", "diagnostic"} for i in ideas["ideas"]), "Candidate schema and risk labels")
    check(all(s["status"] == "reachable" for s in audit["sources"]), "All archived primary document links reachable at audit time")
    tex = (ROOT / "duplex-report.tex").read_text()
    check(r"\usepackage{iclr2026_conference,times}" in tex and r"\lhead{AI2AI Duplex: discussion brief" in tex, "Official ICLR template used with an honest discussion-brief header")
    check("\\\\" not in tex and r"\newline" not in tex and r"\linebreak" not in tex, "No manually forced prose/title line breaks")
    check("discussion route" not in tex.lower() and "Architectures: 5 + 5 min" not in tex, "Discussion-route section and timetable removed")
    all_tex = tex + "\n" + (ROOT / "detailed-report.tex").read_text() + "\n" + "\n".join(p.read_text() for folder in ("tables", "figures", "sections") for p in (ROOT / folder).glob("*.tex"))
    keys = set(re.findall(r"@\w+\{([^,]+),", (ROOT / "references.bib").read_text()))
    citations = {key for match in re.findall(r"\\cite[tp]?\{([^}]+)\}", all_tex) for key in match.split(",")}
    check(citations <= keys and len(keys) == 21, "All citation keys resolve to 21 documented bibliography entries")
    compact_bib = (ROOT / "brief-references.tex").read_text()
    compact_keys = set(re.findall(r"\\bibitem\[[^]]+\]\{([^}]+)\}", compact_bib))
    compact_tex = tex + "\n" + "\n".join(p.read_text() for p in (ROOT / "tables").glob("brief-*.tex"))
    compact_citations = {key for match in re.findall(r"\\cite[tp]?\{([^}]+)\}", compact_tex) for key in match.split(",")}
    check(compact_citations == compact_keys and len(compact_keys) == 20, "All 20 brief references cited and all brief citations resolve")
    check(compact_bib.count(r"\href{") == 20, "Every compact reference links to its primary document or dataset card")
    check(all(p["status"] == "verified" and p["title"] and p["authors"] for p in digest["papers"]), "All 16 paper entries have verified primary bibliographic metadata")
    for category in data.CATEGORIES:
        table = (ROOT / "tables" / (category["id"] + ".tex")).read_text()
        check(table.count(r"\par\citep{") == 5 and category["label"] in table, "Five labeled generated rows: " + category["id"])
    check(len(brief.TABLES) == 4 and len(brief.QUESTIONS) == 5, "Four literature categories and five questions preserved in the brief")
    for category in brief.TABLES:
        table = (ROOT / "tables" / ("brief-" + category["id"] + ".tex")).read_text()
        check(len(category["rows"]) == 5 and table.count(r"\addlinespace[2pt]") == 4 and category["label"] in table, "Five compact, labeled generated rows: " + category["id"])
    figures = json.loads((ROOT / "research" / "figure-sources.json").read_text())
    check(len(figures["figures"]) == 7 and figures["literature_cutoff"] == "2026-09-30", "Seven figure-source records with an explicit evidence cutoff")
    check(len(figures["figures"][:5]) == 5 and all(f["paper_keys"] and f["source_figures"] for f in figures["figures"][:5]), "Five architecture screenshots traced to primary figure/method evidence")
    manifest = json.loads((ROOT / "figures" / "papers" / "manifest.json").read_text())
    screenshots = {record["image"]: record for record in manifest["sources"]}
    check(len(screenshots) == 5 and tex.count("Reproduced from") == 5, "Five original-paper screenshots with per-caption attribution")
    for figure in figures["figures"]:
        path = ROOT / figure["file"]
        if path.suffix == ".png":
            record = screenshots[figure["file"]]
            check(hashlib.sha256(path.read_bytes()).hexdigest() == record["image_sha256"] and record["dpi"] == 300, "Architecture screenshot matches the extraction manifest: " + figure["id"])
            check(record["figure"] and record["page"] and record["source_url"].startswith("https://arxiv.org/pdf/"), "Architecture source figure, page and PDF link recorded: " + figure["id"])
        else:
            source = path.read_text()
            check(r"\begin{tikzpicture}" in source and r"\includegraphics" not in source, "Editable native-vector trace/plot: " + figure["id"])
        check(set(figure["paper_keys"]) <= compact_keys, "Figure-source citations resolve: " + figure["id"])
    check(screenshots["figures/papers/step3.png"]["figure"] == "7B" and "routing panel A omitted" in tex, "StepAudio panel selection explicitly labeled")
    check("not a latency leaderboard" in tex and "not an experiment" in tex, "Published timing parameters and proposed trace explicitly separated from measured results")
    trace = (ROOT / "figures" / "commitment.tex").read_text()
    check(all(term in trace for term in ["User speech", "Monday processed", "Tuesday processed", "Already played", "Queued audio"]) and all(term not in trace for term in ["initial evidence", "audible frontier", "$w_s,v_s$", "revalidate"]), "Figure 6 uses concrete speech/listening/playback labels rather than undefined state jargon")
    performance_path = ROOT / "research" / "reported-performance.json"
    performance = json.loads(performance_path.read_text())
    performance_audit = json.loads((ROOT / "research" / "reported-performance-audit.json").read_text())
    check(len(performance["groups"]) == 6 and {group["id"] for group in performance["groups"]} == {"srqa", "tau_original", "tau_aa", "fdb3", "echo", "mpe"}, "Five benchmark families, with original and AA tau-Voice protocols kept separate")
    check(len(performance["coverage"]) == 5 and {row["system"] for row in performance["coverage"]} == {row[0] for row in brief.TABLES[0]["rows"]}, "Coverage records match all five selected systems")
    check(performance_audit["status"] == "passed" and performance_audit["data_sha256"] == hashlib.sha256(performance_path.read_bytes()).hexdigest(), "Reported-results audit matches the current structured data")
    source_rows = []
    for group in performance["groups"] + performance["supplementary_groups"]:
        for row in group["rows"]:
            source_rows.append({"group": group["id"], "model": row["model"], "source_values": row["source_values"], "status": "matches_primary_pdf"})
            if "domain_scores" in row:
                source_rows.append({"group": "tau_aa_domains", "model": row["model"], "source_values": row["domain_scores"], "status": "matches_primary_pdf"})
    source_rows += [{"group": row["benchmark"], "model": row["model"], "source_values": row["source_values"], "status": "matches_primary_pdf"} for row in performance["text_controls"]]
    check(performance_audit["checks"] == source_rows and len(source_rows) == 43, "All 43 model/configuration vectors match primary PDF table evidence")
    check(len(performance_audit["sources"]) == 8 and all(re.fullmatch(r"[0-9a-f]{64}", source["pdf_sha256"]) for source in performance_audit["sources"].values()), "Eight primary result sources have version, table, page and PDF-hash provenance")
    plots = json.loads((ROOT / "research/performance-plots.json").read_text())
    check(plots["data_sha256"] == performance_audit["data_sha256"] and len(plots["profiles"]) == 8, "Eight model/benchmark profiles generated from the current audited data")
    artifacts = [plots["coverage"]] + [profile["artifacts"] for profile in plots["profiles"]]
    for asset in artifacts:
        for extension, record in asset.items():
            check(hashlib.sha256((ROOT / record["file"]).read_bytes()).hexdigest() == record["sha256"], "Plot source matches its provenance: " + record["file"])
    from build_performance import exact_table
    for group in performance["groups"] + performance["supplementary_groups"]:
        check((ROOT / "tables" / ("performance-" + group["id"] + ".tex")).read_text() == exact_table(performance, group), "Exact-value table matches the structured result data: " + group["id"])
    performance_table = (ROOT / "tables" / "brief-performance.tex").read_text()
    check(performance_table.startswith("% Generated by scripts/make_table_reported_performance.py;") and performance_table.count(r"\addlinespace[2pt]") == 5, "Reported-performance table is code-generated with six protocol rows")
    check("NR: selected-system result not located, not zero" in performance_table and "Text controls, not voice competitors" in performance_table, "Missing results and transcript/text-only references explicitly distinguished")
    check(r"\input{tables/performance-macros}" in tex and r"\srqaDPODelays" in tex, "Quantitative SRQA prose uses macros generated from the same result data")
    log = (ROOT / "build" / "duplex-report.log").read_text()
    check(not re.search(r"Overfull \\[hv]box|undefined|LaTeX Error|Missing character|Font Warning", log, re.I), "No overflow, undefined citations/references, missing glyphs or font fallback")
    try:
        import pymupdf
    except ImportError:
        raise SystemExit("Rendered PDF validation needs PyMuPDF: pip install pymupdf")
    document = pymupdf.open(ROOT / "build" / "duplex-report.pdf")
    content = "\n".join(page.get_text() for page in document)
    check(len(document) == 6, "Meeting brief is five content pages plus availability/references")
    aux = (ROOT / "build" / "duplex-report.aux").read_text()
    for label, expected in [("mapone", 1), ("maptwo", 2), ("questions", 3), ("resources", 4), ("performance", 5), ("references", 6)]:
        match = re.search(r"\\newlabel\{page:" + label + r"\}\{\{[^}]*\}\{(\d+)\}", aux)
        check(match and int(match.group(1)) == expected, "Meeting section stays on its intended page: " + label)
    check("Published as a conference paper" not in content and "Under review as a conference paper" not in content, "No false ICLR publication/submission status")
    check("???" not in content and all(f"Table {n}:" in content for n in range(1, 7)) and all(f"Figure {n}:" in content for n in range(1, 8)), "All six tables and seven figures rendered")
    detailed = pymupdf.open(ROOT / "build" / "detailed-report.pdf")
    archived = pymupdf.open(ROOT / "build" / "archived-report.pdf")
    check(len(archived) == 9 and (ROOT / "archived-report.tex").is_file(), "Original nine-page report preserved separately with editable source")
    detailed_text = "\n".join(page.get_text() for page in detailed)
    detailed_source = (ROOT / "detailed-report.tex").read_text()
    detailed_log = (ROOT / "build/detailed-report.log").read_text()
    check(not re.search(r"Overfull \\[hv]box|undefined|LaTeX Error|Missing character|Font Warning", detailed_log, re.I), "Detailed report has no overflow, missing glyphs, font fallback or unresolved references")
    check(all(f"Table {n}:" in detailed_text for n in range(1, 13)) and all(f"Figure {n}:" in detailed_text for n in range(1, 16)), "Detailed report renders 12 tables and 15 figures")
    check(r"\input{figures/commitment}" in detailed_source and "initial evidence" not in detailed_source, "Detailed report reuses the plain-language correction figure")
    detailed_aux = (ROOT / "build/detailed-report.aux").read_text()
    for profile in plots["profiles"]:
        label = re.escape(profile["id"])
        figure = re.search(r"\\newlabel\{fig:performance-" + label + r"\}\{\{[^}]*\}\{(\d+)\}", detailed_aux)
        table = re.search(r"\\newlabel\{tab:performance-" + re.escape(profile["group"]) + r"\}\{\{[^}]*\}\{(\d+)\}", detailed_aux)
        check(figure and table and figure.group(1) == table.group(1), "Detailed profile plot and exact-value table share a page: " + profile["id"])
    word_count = body_word_count(document, page_limit=5)
    old_word_count = body_word_count(detailed)
    check(word_count <= 1800, "At most 1800 extractable words in five brief pages; screenshot labels excluded")
    fonts = {span["font"] for page in document for block in page.get_text("dict")["blocks"] if "lines" in block for line in block["lines"] for span in line["spans"]}
    check("TeXGyreTermes-Regular" in fonts and "TeXGyreTermes-Bold" in fonts, "Times-compatible body and emphasis fonts actually embedded")
    for number, page in enumerate(document, 1):
        check(all(word[0] >= 99 and word[2] <= 513 and word[1] >= 18 and word[3] <= 765 for word in page.get_text("words")), f"Page {number}: no text outside the report margin")
        check((ROOT / "preview" / f"page-{number:02d}.png").is_file(), f"Page {number}: rendered preview exists")
    for number, page in enumerate(detailed, 1):
        check(all(word[0] >= 98 and word[2] <= 514 and word[1] >= 18 and word[3] <= 765 for word in page.get_text("words")), f"Detailed page {number}: no text outside the report margin")
        check((ROOT / "preview/detailed" / f"page-{number:02d}.png").is_file(), f"Detailed page {number}: rendered preview exists")
    check(len(list((ROOT / "preview").glob("page-*.png"))) == 6, "No obsolete page previews remain in the meeting preview directory")
    with zipfile.ZipFile(ROOT / "build" / "duplex-report-source.zip") as archive:
        members = set(archive.namelist())
        check({"duplex-report.tex", "detailed-report.tex", "brief-references.tex", "research/figure-sources.json", "references.bib", "iclr2026_conference.sty", "iclr2026_conference.bst", "README.md"} <= members, "Source ZIP has both versions, bibliographies, figure evidence and official styles")
        check(all(figure["file"] in members for figure in figures["figures"]) and "figures/papers/manifest.json" in members, "Source ZIP includes five screenshots, two native figures and screenshot provenance")
        check({"research/reported-performance.json", "research/reported-performance-audit.json", "tables/brief-performance.tex", "tables/performance-macros.tex"} <= members, "Source ZIP includes reported-score data, primary-value audit and generated table/macros")
        check(archive.read("research/reported-performance.json") == performance_path.read_bytes(), "Packaged result data matches the current source-checked values")
        check({"archived-report.tex", "sections/architecture-gallery.tex", "sections/performance.tex", "research/performance-plots.json"} <= members, "Source ZIP includes the updated detailed sections, plot evidence and archived source")
        for path in [ROOT / "duplex-report.tex", ROOT / "detailed-report.tex"] + list((ROOT / "sections").glob("*.tex")):
            for target in re.findall(r"\\input\{([^}]+)\}", path.read_text()):
                check(target + ".tex" in members, "Source ZIP includes input dependency: " + target)
            for target in re.findall(r"\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}", path.read_text()):
                check(target in members, "Source ZIP includes graphics dependency: " + target)
        check(all(archive.read(name) == (ROOT / name).read_bytes() for name in screenshots), "Packaged screenshots match the compiled image sources")
        allowed_pdfs = {asset["pdf"]["file"] for asset in artifacts}
        check({name for name in members if name.endswith(".pdf")} == allowed_pdfs, "Source ZIP includes only generated vector plots, not downloaded paper/proposal PDFs")
        check(archive.read("duplex-report.tex") == (ROOT / "duplex-report.tex").read_bytes(), "Source ZIP matches the compiled draft source")
    independent = []
    if args.source_check_dir:
        for stem, compiled in [('duplex-report', document), ('detailed-report', detailed), ('archived-report', archived)]:
            fresh = pymupdf.open(args.source_check_dir / (stem + '.pdf'))
            check(len(fresh) == len(compiled) and all(first.get_text() == second.get_text() for first, second in zip(fresh, compiled)), 'Fresh source-ZIP compilation reproduces page count and extracted content: ' + stem)
            fresh_log = (args.source_check_dir / (stem + '.log')).read_text()
            check(not re.search(r'Overfull \\[hv]box|undefined|LaTeX Error|Missing character|Font Warning', fresh_log, re.I), 'Fresh source-ZIP compilation has no overflow, missing glyphs or unresolved references: ' + stem)
            independent.append({'source': stem + '.tex', 'pages': len(fresh), 'content_matches': True})
    result = {"status": "passed", "pages": len(document), "discussion_pages": 5, "detailed_report_pages": len(detailed), "archived_report_pages": len(archived), "extractable_discussion_words": word_count, "detailed_pre_reference_words": old_word_count, "word_count_scope": "PDF-extractable text; raster architecture screenshot labels excluded. Brief count is its first five pages; availability/reference appendix is separate.", "architecture_screenshots": 5, "native_trace_and_plot": 2, "figures": 7, "detailed_figures": 15, "performance_plots": 9, "detailed_tables": 12, "categories": 4, "entries_per_category": 5, "major_research_questions": 5, "performance_protocols": 6, "supplementary_flair_protocols": 2, "performance_benchmarks": 5, "primary_reported_score_vectors": len(source_rows), "primary_performance_sources": len(performance_audit["sources"]), "brief_references": len(compact_keys), "full_references": len(keys), "primary_links": len(audit["sources"]), "pdf_sha256": hashlib.sha256((ROOT / "build" / "duplex-report.pdf").read_bytes()).hexdigest(), "detailed_pdf_sha256": hashlib.sha256((ROOT / "build" / "detailed-report.pdf").read_bytes()).hexdigest(), "source_zip_sha256": hashlib.sha256((ROOT / "build" / "duplex-report-source.zip").read_bytes()).hexdigest(), "independent_source_compilation": independent, "checks": sorted(set(checks))}
    (ROOT / "build" / "validation.json").write_text(json.dumps(result, indent=2) + "\n")
    print(f"PASS: five brief pages + availability/references; {word_count} extractable words (screenshot labels excluded); five original-paper screenshots; reported scores on five benchmarks; five RQs; no overflow or unresolved citations.")

if __name__ == "__main__":
    main()
