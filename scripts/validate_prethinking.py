#!/usr/bin/env python3
"""Check proposal evidence, rendered math, navigation and preserved baselines."""
from collections import Counter
from html import unescape
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit
from validate_site import Parser

ROOT=Path(__file__).resolve().parents[1]

def main():
    text=(ROOT/'prethinking.html').read_text()
    parser=Parser();parser.feed(text)
    assert parser.viewport and parser.title and all(n==1 for n in Counter(parser.ids).values())
    assert len(parser.tables)==6 and parser.figures==1
    for kind,count in [('Table',6),('Figure',1)]:
        labels=[int(m[1]) for v in parser.labels if (m:=re.match(kind+r' (\d+)\.',v))]
        assert labels==list(range(1,count+1)),labels
    for tag,url in parser.links:
        parts=urlsplit(url)
        if parts.scheme or parts.netloc:
            assert tag=='a', 'Unexpected external asset: '+url
            continue
        assert not parts.path.startswith('/')
        target=ROOT/unquote(parts.path) if parts.path else ROOT/'prethinking.html'
        if target.is_dir():target=target/'index.html'
        assert target.exists(),url
        if parts.fragment:
            parsed=Parser();parsed.feed(target.read_text())
            assert parts.fragment in parsed.ids,url
    for filename in ['index.html','context-assistance.html','prethinking.html']:
        html=(ROOT/filename).read_text()
        nav=re.search(r'<nav[^>]*aria-label="Literature review sub-tabs"[^>]*>(.*?)</nav>',html,re.S)[1]
        assert nav.count('<a ')==3 and nav.count('aria-current="page"')==1
        current=re.search(r'<a[^>]*href="([^"]+)"[^>]*aria-current="page"',nav)[1]
        assert urlsplit(current).path==filename
    for m in re.finditer(r'<(p|h[1-6]|td|th|dd|dt)\b[^>]*>(.*?)</\1>',text,re.S):
        assert '\n' not in m[2] and not re.search(r'<br\b|&nbsp;|&#160;|\u00a0',m[2],re.I)
    eq=re.findall(r'<div class="equation"[^>]*>(.*?)</div>',text,re.S)
    assert len(eq)==5
    assert all(x.startswith('\\[') and x.endswith('\\]') and '<' not in x for x in eq)
    assert '\\mid x,c' in text and 'x_{\\text{text}}' in text and '\\mathcal L_{\\mathrm{SFT}}' in text
    assert text.index('window.MathJax')<text.index('id="MathJax-script"')
    digest=json.loads((ROOT/'research/prethinking/literature.json').read_text())
    audit={r['id']:r for r in json.loads((ROOT/'research/prethinking/source-audit.json').read_text())['sources']}
    assert len(digest['papers'])==18 and digest['status']=='tentative_proposal_not_implemented'
    assert digest['new_inference_gpus']==0
    ids={x['id'] for x in digest['papers']}
    for item in digest['papers']:
        for key in ['title','authors','date','venue','problem','method','results','relevance','limitations','source','version']:
            assert item[key],(item['id'],key)
        assert item['status']=='verified' and audit[item['id']]['status']=='reachable'
        assert 'ref-'+item['id'] in parser.ids and item['date']<=digest['date']
        assert item['source']==audit[item['id']]['url']
    assert all(set(g['refs'])<=ids for g in digest['gaps'])
    assert audit['multitalk-code']['status']=='unreachable' and audit['multitalk-code']['error'].endswith('Not Found')
    assert 'prethinking.html)' in (ROOT/'README.md').read_text()
    print('PASS: 3 sub-tabs, 18 verified papers, 6 tables, 1 illustration, 5 escaped equations, all links and natural wrapping; 0 GPUs.')

if __name__=='__main__':main()
