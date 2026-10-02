#!/usr/bin/env python3
"""Render attributed architecture screenshots from verified primary PDFs.

Crop page margins and surrounding prose/captions; select StepAudio's panel B.
Labels, arrows and legends inside the selected diagrams are not edited.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = [
    {"id": "moshi", "arxiv": "2410.00037", "page": 7, "figure": "1", "crop": [122, 90, 490, 254]},
    {"id": "minicpm", "arxiv": "2604.27393", "page": 4, "figure": "4", "crop": [113, 78, 504, 354]},
    {"id": "flair", "arxiv": "2603.17837", "page": 5, "figure": "2", "crop": [54, 64, 543, 226]},
    {"id": "step3", "arxiv": "2609.14005", "page": 14, "figure": "7B", "crop": [79, 169, 530, 397]},
    {"id": "venus", "arxiv": "2609.13814", "page": 5, "figure": "3", "crop": [76, 284, 536, 482]},
    {"id": "duplexomni", "arxiv": "2606.09186", "version": "v1", "page": 3, "figure": "2", "crop": [70, 72, 525, 430]},
    {"id": "voicechat", "arxiv": "2609.21967", "version": "v1", "page": 2, "figure": "1", "crop": [83, 95, 555, 430]},
    {"id": "thinkaloud", "arxiv": "2609.26488", "version": "v1", "page": 3, "figure": "2", "crop": [100, 65, 514, 290]},
]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-dir", type=Path, required=True, help="Directory containing arxiv.org_pdf_<ID>.pdf")
    parser.add_argument("--dpi", type=int, default=300)
    parser.add_argument("--ids", nargs="+", help="Render only these diagrams, retaining other manifest records")
    args = parser.parse_args()
    import pymupdf
    target = ROOT / "figures" / "papers"
    target.mkdir(parents=True, exist_ok=True)
    records = []
    existing = {record["id"]: record for record in json.loads((target / "manifest.json").read_text())["sources"]} if args.ids else {}
    for source in SOURCES:
        if args.ids and source["id"] not in args.ids:
            records.append(existing[source["id"]])
            continue
        pdf = args.evidence_dir / ("arxiv.org_pdf_" + source["arxiv"] + ".pdf")
        document = pymupdf.open(pdf)
        page = document[source["page"] - 1]
        clip = pymupdf.Rect(source["crop"])
        assert page.rect.contains(clip)
        pixmap = page.get_pixmap(dpi=args.dpi, clip=clip, alpha=False)
        path = target / (source["id"] + ".png")
        pixmap.save(path)
        modifications = "Selected original panel B; panel A (adaptive routing) omitted" if source["id"] == "step3" else "Page-margin/surrounding-prose crop only; original diagram retained"
        records.append({**source, "source_url": "https://arxiv.org/pdf/" + source["arxiv"] + source.get("version", ""), "image": str(path.relative_to(ROOT)), "dpi": args.dpi, "pixels": [pixmap.width, pixmap.height], "pdf_sha256": hashlib.sha256(pdf.read_bytes()).hexdigest(), "image_sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "crop_units": "PDF points; top-left origin", "modifications": modifications, "credit": "Reproduced from the cited paper; copyright remains with its original rights holders."})
        document.close()
    (target / "manifest.json").write_text(json.dumps({"created": "2026-10-02", "sources": records}, indent=2) + "\n")
    print(f"Recorded {len(records)} original-paper architecture screenshots at {args.dpi} dpi.")

if __name__ == "__main__":
    main()
