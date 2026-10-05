#!/usr/bin/env python3
"""Validate both review routes and focused evidence/number consistency offline."""
from collections import Counter
from html import unescape
import json
from pathlib import Path
import re
from urllib.parse import urlsplit, unquote
from validate_site import Parser

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'research/context-assistance'

def validate():
    digest=json.loads((OUT/'literature.json').read_text())
    audit={r['url']:r for r in json.loads((OUT/'source-audit.json').read_text())['sources']}
    pages={}
    for filename in ('index.html','context-assistance.html'):
        text=(ROOT/filename).read_text()
        parser=Parser()
        parser.feed(text)
        pages[filename]=(text,parser)
        tabs=re.search(r'<nav[^>]*aria-label="Literature review sub-tabs"[^>]*>(.*?)</nav>',text,re.S)
        assert tabs and tabs[1].count('<a ') == 2 and tabs[1].count('aria-current="page"') == 1
        current=re.search(r'<a[^>]*href="([^"]+)"[^>]*aria-current="page"',tabs[1])[1]
        assert urlsplit(current).path == filename
        project=re.search(r'<nav[^>]*aria-label="Project tabs"[^>]*>(.*?)</nav>',text,re.S)
        assert project and project[1].count('<a ') == 1 and '>Literature review</a>' in project[1]
        assert all(n == 1 for n in Counter(parser.ids).values())
        assert parser.viewport and parser.title and not parser.images_missing_alt
        for m in re.finditer(r'<(p|h[1-6]|td|th|dd|dt)\b[^>]*>(.*?)</\1>',text,re.S):
            assert '\n' not in m[2] and not re.search(r'<br\b|&nbsp;|&#160;|\u00a0',m[2],re.I)
    text,parser=pages['context-assistance.html']
    assert len(parser.tables) == 6 and parser.figures == 7
    for kind,count in [('Table',6),('Figure',7)]:
        labels=[int(m[1]) for label in parser.labels if (m:=re.match(kind+r' (\d+)\.',label))]
        assert labels == list(range(1,count+1)), labels
    for tag,url in parser.links:
        parts=urlsplit(url)
        if parts.scheme or parts.netloc:
            assert tag == 'a', 'External asset: '+url
            continue
        assert not parts.path.startswith('/'), 'Project-subpath unsafe link: '+url
        target=ROOT/unquote(parts.path) if parts.path else ROOT/'context-assistance.html'
        if target.is_dir(): target=target/'index.html'
        assert target.exists(), 'Broken local link: '+url
        if parts.fragment and target.name in pages:
            assert parts.fragment in pages[target.name][1].ids, 'Broken fragment: '+url
    for field in ('instruction','date','scope','sub_questions','papers','themes','gaps'):
        assert digest.get(field), field
    assert len(digest['papers']) == 15
    known={p['id'] for p in digest['papers']}
    for p in digest['papers']:
        for field in ('title','authors','year','venue','problem','method','results','relevance','limitations','status','source','version'):
            assert p.get(field), (p['id'],field)
        assert p['status'] == 'verified' and audit[p['source']]['status'] == 'reachable'
        assert 'ref-'+p['id'] in parser.ids and p['date'] <= digest['date']
        assert p['title'] in audit[p['source']]['metadata']['citation_title']
    assert all(set(g['refs']) <= known for g in digest['gaps'])
    expected={'context-systems':5,'context-benchmarks':9,'context-data':8}
    for g in digest['reported_scores']:
        ident='context-results-'+g['id']
        expected[ident]=len(g['rows'])
        body=re.search(r'<table id="'+ident+r'">.*?<tbody>(.*?)</tbody>',text,re.S)[1]
        found=[unescape(re.sub('<[^>]+>','',cell)).strip() for cell in re.findall(r'<td>(.*?)</td>',body)]
        assert found == [f'{value:.2f}' for _,value in g['rows']], g['id']
        svg=re.search(r'<svg[^>]*aria-labelledby="chart-'+g['id']+r'-title.*?</svg>',text,re.S)[0]
        widths=[float(w) for w in re.findall(r'<rect[^>]*width="([^"]+)"',svg)]
        assert all(abs(width-value*4.8)<1e-8 for width,(_,value) in zip(widths,g['rows']))
        assert len(widths)==len(g['rows'])
    for ident,n in expected.items():
        body=re.search(r'<table id="'+ident+r'">.*?<tbody>(.*?)</tbody>',text,re.S)[1]
        assert body.count('<tr>') == n,(ident,n)
    md=(OUT/'LITERATURE.md').read_text()
    assert not re.search(r' {2,}\n|\\\n|<br\b',md)
    assert not re.search(r'white-space\s*:\s*(?:pre|nowrap)',(ROOT/'assets/site.css').read_text())
    assert 'context-assistance.html)' in (ROOT/'README.md').read_text()
    manifest=json.loads((ROOT/'assets/context-assistance/manifest.json').read_text())
    assert len(manifest['sources'])==3 and all(len(x['pdf_sha256'])==64 for x in manifest['sources'])
    print('PASS: two stable sub-tab routes; 15 verified papers; 6 tables / 7 figures; all local links, exact score/SVG values and natural wrapping.')

if __name__ == '__main__':
    validate()
