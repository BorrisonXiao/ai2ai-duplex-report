#!/usr/bin/env python3
"""Compile the report, then make rendered previews and an Overleaf-ready source ZIP."""
import argparse
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]

def preview(pdf, detailed=False):
    try:
        import pymupdf
        from PIL import Image, ImageDraw
    except ImportError:
        raise SystemExit("Preview rendering needs PyMuPDF and Pillow: pip install pymupdf pillow")
    target = ROOT / "preview" / "detailed" if detailed else ROOT / "preview"
    target.mkdir(parents=True, exist_ok=True)
    pages = pymupdf.open(pdf)
    # Remove only obsolete page renders from this generator, never source/user files.
    for old in target.glob("page-*.png"):
        if old.stem[5:].isdigit() and int(old.stem[5:]) > len(pages):
            old.unlink()
    thumbs = []
    for number, page in enumerate(pages, 1):
        pixmap = page.get_pixmap(matrix=pymupdf.Matrix(1.5, 1.5), alpha=False)
        path = target / f"page-{number:02d}.png"
        pixmap.save(path)
        thumb = Image.open(path).convert("RGB")
        thumb.thumbnail((480, 625))
        thumbs.append(thumb)
    columns = 3
    rows = (len(thumbs) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * 510, rows * 675), "#e8ebef")
    draw = ImageDraw.Draw(sheet)
    for index, thumb in enumerate(thumbs):
        left = (index % columns) * 510 + 15
        top = (index // columns) * 675 + 28
        sheet.paste(thumb, (left, top))
        draw.text((left, top - 18), f"Page {index + 1}", fill="#273b52")
    sheet.save(target / "contact-sheet.png")
    shutil.copyfile(target / "page-01.png", target / "first-page.png")
    print(f"Rendered {len(pages)} page previews and a contact sheet.")

def package():
    files = [ROOT / "duplex-report.tex", ROOT / "detailed-report.tex", ROOT / "archived-report.tex", ROOT / "brief-references.tex", ROOT / "references.bib", ROOT / "iclr2026_conference.sty", ROOT / "iclr2026_conference.bst", ROOT / "README.md", ROOT / "research" / "figure-sources.json", ROOT / "research" / "reported-performance.json", ROOT / "research" / "reported-performance-audit.json", ROOT / "research" / "performance-plots.json"] + sorted((ROOT / "tables").glob("*.tex")) + sorted((ROOT / "sections").glob("*.tex")) + [ROOT / "figures" / (name + ".tex") for name in ("styles", "commitment", "timing")] + sorted((ROOT / "figures" / "papers").glob("*")) + sorted((ROOT / "figures" / "performance").glob("*.pdf"))
    with zipfile.ZipFile(ROOT / "build" / "duplex-report-source.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, path.relative_to(ROOT))
    print("Packaged Overleaf-ready LaTeX sources (no private proposal or downloaded papers).")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tectonic", help="Explicit Tectonic executable; alternatively use latexmk on PATH")
    parser.add_argument("--preview-only", action="store_true")
    parser.add_argument("--detailed", action="store_true", help="Build/render the updated detailed literature and research report")
    args = parser.parse_args()
    subprocess.run([sys.executable, str(ROOT / "scripts" / "generate.py")], check=True, cwd=ROOT)
    subprocess.run([sys.executable, str(ROOT / "scripts" / "generate_brief.py")], check=True, cwd=ROOT)
    subprocess.run([sys.executable, str(ROOT / "scripts" / "make_table_reported_performance.py")], check=True, cwd=ROOT)
    subprocess.run([sys.executable, str(ROOT / "scripts" / "build_performance.py")], check=True, cwd=ROOT)
    output = ROOT / "build"
    output.mkdir(exist_ok=True)
    source = "detailed-report.tex" if args.detailed else "duplex-report.tex"
    if not args.preview_only:
        tectonic = args.tectonic or shutil.which("tectonic")
        if tectonic:
            subprocess.run([tectonic, "--keep-logs", "--keep-intermediates", "--outdir", str(output), source], check=True, cwd=ROOT)
        elif shutil.which("latexmk"):
            subprocess.run(["latexmk", "-pdf", "-interaction=nonstopmode", "-halt-on-error", "-outdir=" + str(output), source], check=True, cwd=ROOT)
        else:
            raise SystemExit("Install Tectonic or a TeX distribution with latexmk, or compile duplex-report.tex in Overleaf.")
    preview(output / source.replace(".tex", ".pdf"), detailed=args.detailed)
    package()

if __name__ == "__main__":
    main()
