"""Check the study bundle, timing model, privacy boundary and source labels."""
from collections import Counter
import json
import math
from pathlib import Path
import re
import statistics
from urllib.parse import urlsplit,unquote
from validate_site import Parser

ROOT=Path(__file__).resolve().parents[1]

def main():
    d=json.loads((ROOT/'research/prethinking-pilot/study.json').read_text());chunks=d['chunks']
    assert len(chunks)==650 and {c['speaker'] for c in chunks}=={'A','B','C'}
    assert d['allocation']['max_gpus_active']==1 and d['allocation']['teacher_gpus']==1
    assert len(d['categories'])==12 and d['provenance']['license']=='CC BY 4.0'
    assert all(c['end']<=c['available'] for c in chunks)
    assert [c['available'] for c in chunks]==sorted(c['available'] for c in chunks)
    for r in d['data']['simulation']:
        period={'sentence':0,'coalesce_2s':2,'coalesce_5s':5,'coalesce_10s':10}[r['policy']]
        arrivals=sorted(set(c['available'] if not period else math.ceil(c['available']/period)*period for c in chunks))
        gaps=[b-a for a,b in zip(arrivals,arrivals[1:])]
        budgets=[math.floor(r['rate']*max(0,g-r['overhead'])+1e-9) for g in gaps]
        assert r['updates']==len(arrivals) and r['median_tokens']==statistics.median(budgets)
        assert abs(r['zero_fraction']-sum(b==0 for b in budgets)/len(budgets))<1e-10
    for row in d['teacher']['calls']:
        assert row['output_tokens']<=row['budget']
        assert not any(k in row for k in ['private_reasoning','generated_text','generated_token_ids','prompt','input_payload'])
    text=(ROOT/'experiments/prethinking-pilot.html').read_text();parser=Parser();parser.feed(text)
    assert parser.viewport and parser.title and all(n==1 for n in Counter(parser.ids).values())
    assert len(parser.tables)==6 and parser.figures==4
    for kind,count in [('Table',6),('Figure',4)]:
        labels=[int(m[1]) for value in parser.labels if (m:=re.match(kind+r' (\d+)\.',value))]
        assert labels==list(range(1,count+1)),labels
    for tag,url in parser.links:
        parts=urlsplit(url)
        if parts.scheme or parts.netloc:assert tag=='a';continue
        target=(ROOT/'experiments'/unquote(parts.path)).resolve() if parts.path else ROOT/'experiments/prethinking-pilot.html'
        if target.is_dir():target=target/'index.html'
        assert target.exists(),url
        if parts.fragment:
            p=Parser();p.feed(target.read_text());assert parts.fragment in p.ids,url
    for m in re.finditer(r'<(p|h[1-6]|td|th|dd|dt)\b[^>]*>(.*?)</\1>',text,re.S):
        assert '\n' not in m[2] and not re.search(r'<br\b|&nbsp;|\u00a0',m[2])
    assert text.count('class="equation"')==3
    assert 'median of 17' in text and '19.7%' in text
    assert 'prethinking-pilot.html)' in (ROOT/'README.md').read_text()
    print('PASS: 650 causal chunks, 48 timing scenarios, 12 authored categories, 6 tables/4 figures/3 equations; private CoT excluded from public call records.')

if __name__=='__main__':main()
