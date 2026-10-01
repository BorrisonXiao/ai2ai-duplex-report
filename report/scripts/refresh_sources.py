#!/usr/bin/env python3
"""Refresh primary link checks and bibliographic metadata; no model/data downloads."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research"))
sys.path.insert(0, str(ROOT.parent / "scripts"))
import focused_review as data
from verify_sources import check

def main():
    urls = {"https://arxiv.org/abs/" + value for value in data.PAPERS.values()}
    urls.update(data.EXTRA_URLS)
    for category in data.CATEGORIES:
        for row in category["rows"]:
            urls.update(url for _, url in row["links"])
    with ThreadPoolExecutor(max_workers=8) as pool:
        sources = list(pool.map(check, sorted(urls)))
    payload = {"checked_at": datetime.now(timezone.utc).isoformat(), "review_cutoff": data.DATE, "scope": "Focused report primary links and arXiv metadata; reachability does not establish artifact completeness", "sources": sources}
    (ROOT / "research" / "source-audit.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Checked {len(sources)} links: {sum(r['status'] == 'reachable' for r in sources)} reachable.")
    for source in sources:
        if source["status"] != "reachable":
            print(source["status"], source["url"], source.get("error"))
        elif "metadata" in source:
            m = source["metadata"]
            print(source["url"].rsplit("/", 1)[-1], m.get("citation_date"), m.get("citation_title"), m.get("citation_author", [])[:2])

if __name__ == "__main__":
    main()
