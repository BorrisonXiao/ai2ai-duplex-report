"""Check timing, source labels and exact requested Qwen trace publication."""
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
    completed=(ROOT/'research/prethinking-pilot/completion.json').exists()
    table_count=9 if completed else 6
    assert len(parser.tables)==table_count and parser.figures==5
    for kind,count in [('Table',table_count),('Figure',5)]:
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
        prose=re.sub(r'<pre\b.*?</pre>','',m[2],flags=re.S)
        assert '\n' not in prose and not re.search(r'<br\b|&nbsp;|\u00a0',prose)
    assert text.count('class="equation"')==(5 if completed else 3)
    assert 'median of 17' in text and '19.7%' in text
    assert 'prethinking-pilot.html)' in (ROOT/'README.md').read_text()
    traces=json.loads((ROOT/'research/prethinking-pilot/traces.json').read_text())['calls']
    assert len(traces)==64 and all('appendix-call-'+str(c['index']) in parser.ids for c in traces)
    assert len(d['trace_examples'])==8
    for item in d['trace_examples']:
        c=traces[item['call_index']]
        assert c['private_reasoning'][item['cot_start']:item['cot_end']]==item['cot_excerpt']
        assert all(next(x for x in chunks if x['id']==i)['available']<=c['at'] for i in item['transcript_chunk_ids'])
    if completed:
        bundle=json.loads((ROOT/'research/prethinking-pilot/completion.json').read_text());assert len(bundle['calls'])==10
        assert bundle['review']['completion_passes']==9 and bundle['review']['normal_response_stops']==10
        assert bundle['accounting']['maximum_gpus_active']==1 and bundle['accounting']['sequential_verified']
        assert bundle['calls'][0]['retained_history_entries']==0 and bundle['calls'][0]['private_token_count']==4660
        assert all('completion-call-'+str(c['index']) in parser.ids for c in bundle['calls'])
        for f in bundle['review']['qualitative_findings']:
            c=bundle['calls'][f['call_index']];assert c['private_reasoning'][f['cot_start']:f['cot_end']]==f['cot_excerpt']
    print('PASS: causal data/timing, 8 verbatim example pairs, all 64 trace records, numbered tables/5 figures/rendered equations including new completed-run evidence; summaries remain separate from the full requested appendix.')

if __name__=='__main__':main()
