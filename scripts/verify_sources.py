#!/usr/bin/env python3
"""Check primary links and archive bibliographic metadata without downloading data.

This checks document availability, not implementation correctness or all weight files.
Run explicitly when refreshing the review; the site build itself is entirely offline.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from html.parser import HTMLParser
import json
from pathlib import Path
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'research'))
import review_data as data

class Metadata(HTMLParser):
    def __init__(self):
        super().__init__()
        self.meta = {}
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        name = attrs.get('name', '')
        if tag == 'meta' and name.startswith('citation_'):
            self.meta.setdefault(name, []).append(attrs.get('content', ''))

def urls():
    links = set()
    for row in data.SYSTEMS:
        links.add('https://arxiv.org/abs/' + row['id'])
        for key in ('code', 'weights'):
            if row[key]: links.add(row[key][1])
        links.update(link for _, link in row['extra'])
    for row in data.BENCHMARKS:
        links.update(row[key] for key in ('paper', 'artifact') if row[key])
    for row in data.DATASETS:
        links.add(row['source'])
        if row.get('extra'): links.add(row['extra'])
    for _, _, _, first, second in data.RECIPES:
        links.add(first)
        if second: links.add(second)
    return sorted(links)

def check(url):
    result = {'url': url}
    request = Request(url, headers={'User-Agent': 'Mozilla/5.0 (duplex literature source audit)'})
    try:
        with urlopen(request, timeout=25) as response:
            result.update(http_status=response.status, final_url=response.url, content_type=response.headers.get('Content-Type', ''))
            if '/abs/' in url and 'arxiv.org' in url:
                parser = Metadata()
                parser.feed(response.read(1_000_000).decode('utf-8'))
                result['metadata'] = parser.meta
            result['status'] = 'reachable'
    except HTTPError as exc:
        result.update(status='http_error', http_status=exc.code, error=str(exc))
    except Exception as exc:
        result.update(status='lookup_failure', error=str(exc))
    return result

def main():
    links = urls()
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(check, links))
    audit = {'checked_at': datetime.now(timezone.utc).isoformat(), 'review_cutoff': data.DATE, 'scope': 'Primary document links and arXiv metadata; no data or model download', 'sources': results}
    path = ROOT / 'research' / 'source-audit.json'
    path.write_text(json.dumps(audit, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f'Checked {len(results)} primary source links; {sum(r["status"] == "reachable" for r in results)} reachable.')
    for result in results:
        if result['status'] != 'reachable':
            print(f'{result["status"]}: {result["url"]}: {result.get("error", "")}')
    for result in results:
        if 'metadata' in result:
            m = result['metadata']
            print(result['url'].rsplit('/', 1)[-1], m.get('citation_date'), m.get('citation_author', [])[:2], m.get('citation_title'))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
