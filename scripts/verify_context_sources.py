#!/usr/bin/env python3
"""Refresh focused-review bibliographic/link audit; never download data or models."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from html.parser import HTMLParser
import importlib.util
import json
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'research/context-assistance'
spec = importlib.util.spec_from_file_location('context_review', OUT / 'review_data.py')
data = importlib.util.module_from_spec(spec)
spec.loader.exec_module(data)

class Metadata(HTMLParser):
    def __init__(self):
        super().__init__()
        self.meta = {}
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        name = attrs.get('name', '')
        if tag == 'meta' and name.startswith('citation_'):
            self.meta.setdefault(name, []).append(attrs.get('content', ''))

def check(url):
    item = {'url': url, 'checked_at': datetime.now(timezone.utc).isoformat()}
    try:
        with urlopen(Request(url, headers={'User-Agent':'Mozilla/5.0 (context assistance literature review)'}), timeout=30) as r:
            item.update(status='reachable', http_status=r.status, final_url=r.url, content_type=r.headers.get('Content-Type'))
            if '/api/models' in url and 'huggingface.co' in url:
                model = json.loads(r.read(1_000_000))
                if isinstance(model, list):
                    item['model_ids_at_check'] = [m['id'] for m in model]
                else:
                    item['model_manifest_at_check'] = {k:model.get(k) for k in ('id','sha','private','gated','library_name','config')}
                    item['model_manifest_at_check']['files'] = [m['rfilename'] for m in model.get('siblings',[])]
            if '/abs/' in url or ('aclanthology.org' in url and url.endswith('/')):
                parser = Metadata()
                parser.feed(r.read(1_000_000).decode())
                parser.meta.pop('citation_abstract', None)
                item['metadata'] = parser.meta
    except Exception as exc:
        item.update(status='lookup_failure', error=str(exc))
        if hasattr(exc, 'code'):
            item['http_status'] = exc.code
    return item

def main():
    urls = set(data.EXTRA_SOURCES)
    for paper in data.PAPERS:
        urls.add(paper['source'])
        urls.update(url for _, url in paper['artifacts'])
    urls.update(row[-1] for row in data.DATASETS)
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(check, sorted(urls)))
    audit = dict(review_cutoff=data.DATE, scope='Primary pages, bibliographic metadata and artifact links. No model or corpus download; a reachable landing page does not prove completeness or reproduction.', sources=results)
    (OUT / 'source-audit.json').write_text(json.dumps(audit, indent=2, ensure_ascii=False)+'\n')
    for row in results:
        meta = row.get('metadata', {})
        print(row['status'], row['url'], meta.get('citation_title', []), meta.get('citation_author', [])[:2])
    papers = {p['source'] for p in data.PAPERS}
    assert all(r['status'] == 'reachable' and r.get('metadata', {}).get('citation_title') and r['metadata'].get('citation_author') for r in results if r['url'] in papers)

if __name__ == '__main__':
    main()
