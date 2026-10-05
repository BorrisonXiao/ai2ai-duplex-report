#!/usr/bin/env python3
"""Offline build of the focused HTML sub-tab and structured literature digest."""
import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
from build_site import e, link, p, small, inline_links, table, section, next_label, ASSET_COUNTS, md_table
from site_navigation import review_tabs, project_tabs

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'research/context-assistance'
spec = importlib.util.spec_from_file_location('context_review', OUT / 'review_data.py')
data = importlib.util.module_from_spec(spec)
spec.loader.exec_module(data)
AUDIT = json.loads((OUT / 'source-audit.json').read_text())
SOURCES = {r['url']: r for r in AUDIT['sources']}
PAPERS = deepcopy(data.PAPERS)
for paper in PAPERS:
    source = SOURCES[paper['source']]
    assert source['status'] == 'reachable'
    m = source['metadata']
    authors = [a.split(', ',1)[1]+' '+a.split(', ',1)[0] if ', ' in a else a for a in m['citation_author']]
    date = (m.get('citation_date') or m['citation_publication_date'])[0]
    parts = date.split('/')
    date = '-'.join([parts[0]] + [x.zfill(2) for x in parts[1:]])
    paper.update(title=m['citation_title'][0], authors=', '.join(authors), author_list=authors, year=int(parts[0]), date=date, arxiv_id=m.get('citation_arxiv_id',[None])[0], doi=m.get('citation_doi',[None])[0], source_depth='Primary full manuscript: introduction, method, experiments and limitations/conclusion; release claims separately checked against cards/repositories.')
    paper['artifact_checks'] = [{'label':name, 'url':url, 'status':SOURCES[url]['status'], 'http_status':SOURCES[url].get('http_status'), 'checked_at':SOURCES[url]['checked_at']} for name,url in paper['artifacts']]
    if paper['id'] == 'qmsum':
        paper['authors'] = paper['authors'].replace('Ahmed Hassan,', 'Ahmed Hassan Awadallah,').replace('Xipeng Qiu (邱锡鹏)', 'Xipeng Qiu')
        paper['bibliographic_note'] = 'Full Ahmed Hassan Awadallah author name checked against PDF page 1; metadata shortens the name.'
    if paper['id'] == 'ask':
        paper['authors'] = paper['authors'].replace('Sercan O Arik','Sercan Ö. Arık')
        paper['bibliographic_note'] = 'Author diacritics checked against PDF page 1.'
BY_ID = {x['id']: x for x in PAPERS}
NUMBERS = {x['id']: i for i,x in enumerate(PAPERS,1)}

def cite(ident):
    return link('['+str(NUMBERS[ident])+']', '#ref-'+ident, 'citation') if ident else ''

def artifact_links(ident):
    return inline_links(BY_ID[ident]['artifacts'])

def label(ident, name):
    return e(name)+' '+cite(ident)

def figure(inner, caption, cls='performance-figure'):
    return '<figure class="'+cls+'">'+inner+'<figcaption>Figure '+str(next_label('Figure'))+'. '+caption+'</figcaption></figure>'

def score_svg(group):
    rows = group['rows']
    height = 110 + len(rows)*44
    svg = [f'<svg class="context-chart" viewBox="0 0 860 {height}" role="img" aria-labelledby="chart-{group["id"]}-title chart-{group["id"]}-description"><title id="chart-{group["id"]}-title">{e(group["title"]+": "+group["metric"])}</title><desc id="chart-{group["id"]}-description">'+e('; '.join(f'{name}: {value}' for name,value in rows))+'. Exact values appear in the following table.</desc>']
    svg.append('<text x="25" y="30" class="chart-label">'+e(group['metric'])+'</text>')
    for tick in (0,25,50,75,100):
        x=320+4.8*tick
        svg.append(f'<line class="chart-axis" x1="{x}" x2="{x}" y1="54" y2="{height-40}"></line><text x="{x}" y="{height-14}" text-anchor="middle">{tick}</text>')
    for i,(name,value) in enumerate(rows):
        y=64+i*44
        cls='chart-reference' if name == 'Human reference' else 'chart-bar'
        svg.append(f'<text x="304" y="{y+18}" text-anchor="end">{e(name)}</text><rect class="{cls}" x="320" y="{y}" width="{value*4.8}" height="26" rx="3"></rect><text x="{330+value*4.8}" y="{y+18}">{value:.2f}</text>')
    return ''.join(svg)+'</svg>'

def html():
    ASSET_COUNTS.update(Table=0,Figure=0)
    example = '<div class="context-example">'
    for title,text in [('Listen to the group','Alex: “Move the poster session to Friday.” Sam: “Keep the demo on Thursday.” The assistant listens without treating every human turn as a command.'),('Interpret a later request','User → assistant: “When did we move it to?” The intended event depends on the speaker and the preceding discussion, not the final sentence alone.'),('Answer or clarify','If context identifies the poster session: “Friday.” If poster and demo remain plausible: “Do you mean the poster session or the demo?”')]:
        example+='<div class="card"><h3>'+e(title)+'</h3>'+p(text)+'</div>'
    example+='</div>'
    scope=p('Yes—there is already closely related work. MSI-Bench tests a later assistant-directed request after group speech; GroupMemBench explicitly tests speaker-conditioned ambiguity; MultiTalk trains a full-duplex model for long multi-party conversations. The opportunity is narrower than “an assistant that overhears a meeting.”')+' '+cite('msi')+' '+cite('groupmem')+' '+cite('multitalk')
    scope+=figure(example,'Illustrative target behavior for the tentative project, not an example copied from a benchmark or a demonstrated system. The assistant uses only authorized speech already heard.')
    scope+='<div class="callout"><h3>Primary scope: proactive listening, assistance when asked</h3>'+p('Using prior conversation to resolve a later instruction is different from interrupting the group with unsolicited advice. SocialMind and ProMediate cover adjacent proactive intervention settings; keep that branch optional.')+cite('socialmind')+' '+cite('promediate')+'</div>'

    closest='<div class="card-grid">'
    for ident,title,description in data.CLOSEST:
        closest+='<article class="card"><span class="tag">'+e({'msi':'MSI-Bench','groupmem':'GroupMemBench','multitalk':'MultiTalk','ask':'ASK-QA','mised':'MISeD'}[ident])+'</span><h3>'+e(title)+'</h3>'+p(description)+cite(ident)+artifact_links(ident)+'</article>'
    closest+='</div>'
    closest+='<details id="context-paper-figures"><summary>Original-paper figures: what these tasks actually test</summary><div class="context-paper-gallery">'
    for f in data.FIGURES:
        path='assets/context-assistance/'+f['file']
        closest+=figure('<a href="'+path+'"><img src="'+path+'" alt="'+e(f['alt'])+'" loading="lazy"></a>',e({'msi':'MSI-Bench task overview','groupmem':'GroupMemBench speaker-dependent memory','multitalk':'MultiTalkBench participant-replacement evaluation'}[f['id']])+'. Screenshot of original '+f['original']+', manuscript page '+str(f['page'])+'. '+link('Source PDF', pdf_url(BY_ID[f['id']]))+' '+cite(f['id'])+'. Cropped without redrawing; click for full resolution.','paper-figure')
    closest+='</div></details>'

    systems=table('context-systems',1,'Five relevant system designs; public data is not automatically a released model.', ['System / paper','Design','Verified artifact scope','Role in this project'], [[label(ident,name),e(design),e(access)+artifact_links(ident),e(use)] for ident,name,design,access,use in data.SYSTEMS])
    systems+='<div class="callout amber"><h3>A useful implementation starting point, not a promised full system</h3>'+p('A public Moshi or MiniCPM-o backbone can serve as a reproducible baseline while MultiTalk’s checkpoint release remains unverified. Pair native audio with a transcript + diarization + speaker-scoped memory control. Neither approach has yet been implemented for this narrowed project.')+link('Backbone releases in the original review','index.html#availability')+'</div>'
    benches=table('context-benchmarks',2,'Nine complementary evaluations; choose the protocol by the capability being tested.', ['Benchmark / input','Relevant behavior','Metrics','Release / scope limitation'], [[label(ident,name)+small(setting),e(capability),e(metric),e(access)+small(caveat)+artifact_links(ident)] for ident,name,setting,capability,metric,access,caveat in data.BENCHMARKS])

    results=p('Figure 5–7 and Tables 3–5 give three source-specific views of the difficulty. They are author-reported results, not our experiments or a unified ranking. Memory-pipeline scores cannot rank speech models, and the human reference is not a closed-system result.',cls='section-intro')
    for g in data.SCORES:
        results+='<article class="context-results"><h3>'+e(g['title'])+' '+cite(g['id'])+'</h3>'
        results+=figure('<div class="plot-scroll">'+score_svg(g)+'</div>',e(g['title']+'; '+g['metric']+'. '+g['locator']+'. '+g['caveat'])+' '+cite(g['id']))
        results+=table('context-results-'+g['id'],0,g['title']+' exact values; '+g['locator']+'.',['Model / pipeline',g['metric']],[[e(name),f'{value:.2f}'] for name,value in g['rows']],searchable=False)+'</article>'

    datasets=table('context-data',6,'Training resources and ingredients, kept separate from benchmark test sets.', ['Resource / size','Available supervision','Access / reuse conditions','Potential use and missing labels'], [[label(ident,name)+small(scale)+inline_links([('Source / release',url)]),e(supervision),e(access),e(use)] for ident,name,scale,supervision,access,use,url in data.DATASETS])
    datasets+='<div class="callout amber"><h3>Keep evaluation data held out</h3>'+p('MSI-Bench, MultiTalkBench, ContextDialog and the released GroupMemBench questions are evaluation resources, not default training sets. MISeD, QMSum and some MultiTalkBench examples share underlying meeting corpora: deduplicate and split by meeting and participant before training. Reconstructing new speech or clarification labels is proposed work, not an existing release.')+'</div>'

    implications='<div class="card-grid">'
    questions=[('Does the overheard context actually change interpretation?','Hold the final request fixed; swap a relevant earlier speaker, referent or corrected plan. Compare final-request-only, full-transcript, speaker-aware memory and native-audio inputs. Score the intended referent and evidence source, not just fluent answer quality.',['msi','groupmem','mised']),('When should the assistant ask instead of guess?','Include context that resolves an ambiguous request, context that leaves two viable interpretations, and missing evidence. Score targeted clarification, successful completion after the reply, unsupported guesses and unnecessary questions.',['ask','groupmem']),('Can the intended answer change while the model is listening or speaking?','Use timestamped prefixes only. Inject a correction before answer onset and during the answer; measure memory-update delay, stale spoken commitments, correction uptake and interruption recovery. This retains the original synchronization concern.',['multitalk','mpe']),('Can it stay quiet and respect the audience?','Pair assistant-directed requests with human-to-human versions. Evaluate false activation separately from answer correctness, and test whether useful private context is disclosed to an unauthorized listener.',['speak','msi','muppet'])]
    for title,text,refs in questions:
        implications+='<article class="card"><span class="tag blue">Proposed evaluation</span><h3>'+e(title)+'</h3>'+p(text)+' '.join(cite(x) for x in refs)+'</article>'
    implications+='</div>'+p('A scoped initial recipe: meeting-grounded QA from MISeD/QMSum + speaker-conditioned ambiguity from GroupMemBench + answer/clarify decisions inspired by ASK-QA, evaluated with MSI-Bench and duplex restraint controls. Natural meeting prefixes still need assistant-directed requests, intended referents, evidence timestamps and human-validated clarification labels. Establish consent and permissible retention before using new meeting recordings.',cls='section-intro')
    implications+='<div class="callout"><h3>Novelty boundary</h3>'+p('The reviewed resources already establish multi-party context use, speaker-dependent interpretation and proactive intervention individually. A defensible candidate contribution is their causal combination in synchronized speech: a later request grounded in a real conversation, clarification when needed, and revisions without inappropriate interruptions or disclosures. This is a review-based hypothesis, not an exhaustive novelty claim.')+'</div>'

    notes=p('Fifteen verified papers, selected for task proximity rather than popularity. Expand for concise method, result and limitation notes. Months are retained when the publisher supplies no exact publication day.',cls='section-intro')
    for paper in PAPERS:
        ident=paper['id']
        notes+='<details><summary>'+e(paper['title'])+' '+cite(ident)+'</summary><div class="paper-note"><dl>'
        for name,key in [('Problem','problem'),('Method','method'),('Author-reported result / resource','results'),('Relevance','relevance'),('Limitations / review assessment','limitations')]:
            notes+='<dt>'+name+'</dt><dd>'+e(paper[key])+'</dd>'
        notes+='</dl>'+link('Primary manuscript',paper['source'])+artifact_links(ident)+'</div></details>'
    method=p('Focused review as of 4 October 2026. Search facets: ambient group speech, speaker-scoped memory, contextual intent/reference resolution, clarification, meeting QA, participation timing and privacy. Bibliography was independently checked against arXiv or publisher metadata; factual analysis used full primary manuscripts and author release cards/repositories. Recent preprints are not presumed peer-reviewed. No models were run or corpus/model files downloaded.')
    method+=p('Important evidence checks: MultiTalkPT is dyadic (54.4k h), MultiTalkFT multi-party (3.2k h). GroupMemBench’s paper and HF card give different corpus counts, so no single merged size is asserted. MP-Bench’s landing-page and PDF abstracts disagree on comprehension performance, so that claim is excluded from plots. “Not located” is a dated search result, not proof of nonexistence. Public availability is not a reuse licence.')
    method+='<ol class="references">'
    for paper in PAPERS:
        method+='<li id="ref-'+paper['id']+'">'+link(paper['title'],paper['source'])+small(paper['authors']+' · '+paper['date']+' · '+paper['venue']+' · '+paper['version'])+artifact_links(paper['id'])+'</li>'
    method+='</ol>'+inline_links([('Readable literature digest','research/context-assistance/LITERATURE.md'),('Structured digest','research/context-assistance/literature.json'),('Primary-source audit','research/context-assistance/source-audit.json'),('Figure provenance','assets/context-assistance/manifest.json')])

    hero='<header class="hero" id="context-review"><p class="eyebrow">Literature review · Narrowed project scope</p><h1>Listen to the conversation. Understand the request.</h1><p class="lede">Context-aware assistance from multi-party speech: speaker-specific memory, instruction disambiguation, clarification and appropriate participation.</p><p class="meta">4 October 2026 · 15 verified papers · 5 closest resources · Primary-source review, not a new benchmark or experiment</p><div class="button-row">'+link('Closest prior work','#closest','button primary')+link('Benchmarks','#context-benchmarks-section','button')+link('Training resources','#context-data-section','button')+'</div></header>'
    nav='<nav class="jump-links" aria-label="Context review sections">'+''.join(link(title,'#'+ident) for ident,title in [('scope','Scope'),('closest','Closest work'),('context-systems-section','Systems'),('context-benchmarks-section','Benchmarks'),('context-performance','Reported results'),('context-data-section','Training data'),('context-questions','Research questions'),('context-notes','Paper notes'),('context-references','References')])+'</nav>'
    body='\n'.join(['<a class="skip-link" href="#main">Skip to review</a>','<header class="site-nav"><div class="nav-inner"><a class="brand" href="./">AI2AI Duplex</a>'+project_tabs('literature')+'</div></header>','<main id="main"><div class="container">',review_tabs('context'),hero,nav,section('scope','What is already studied?',scope),section('closest','The five closest resources',closest),section('context-systems-section','Relevant system designs',systems),section('context-benchmarks-section','Benchmarks: what each one measures',benches),section('context-performance','Reported results: three different bottlenecks',results),section('context-data-section','Training data and supervision',datasets),section('context-questions','Implications for the narrowed project',implications),section('context-notes','Paper notes',notes),section('context-references','References and evidence boundaries',method),'<footer class="site-footer"><p>AI2AI Duplex · Literature review · '+link('Back to duplex landscape','index.html')+' · '+link('Source repository','https://github.com/BorrisonXiao/ai2ai-duplex-report')+'</p></footer>','</div></main>'])
    css=hashlib.sha256((ROOT/'assets/site.css').read_bytes()).hexdigest()[:12]
    return '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n<meta name="color-scheme" content="light dark">\n<meta name="description" content="Review of duplex assistants using multi-party conversation context to interpret requests: models, benchmarks, clarification and training data.">\n<title>AI2AI Duplex — Context-aware Assistance</title>\n<link rel="stylesheet" href="assets/site.css?v='+css+'">\n<script src="assets/site.js" defer></script>\n</head>\n<body>\n'+body+'\n</body>\n</html>\n'

def pdf_url(paper):
    if paper['arxiv_id']:
        return 'https://arxiv.org/pdf/'+paper['version']
    return paper['source'].rstrip('/')+'.pdf'

def render_papers(directory):
    import pymupdf
    dest=ROOT/'assets/context-assistance'
    dest.mkdir(parents=True,exist_ok=True)
    sources=[]
    for f in data.FIGURES:
        src=directory/f['pdf']
        doc=pymupdf.open(src)
        page=doc[f['page']-1]
        pix=page.get_pixmap(matrix=pymupdf.Matrix(300/72,300/72),clip=pymupdf.Rect(f['clip']),alpha=False)
        pix.save(str(dest/f['file']))
        sources.append({**f,'source_url':pdf_url(BY_ID[f['id']]),'pdf_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'dpi':300,'extraction':'Original vector/image figure rendered with PyMuPDF and a documented page-coordinate crop; the skill extractor found no usable complete figures.'})
    (dest/'manifest.json').write_text(json.dumps(dict(date=data.DATE,sources=sources),indent=2)+'\n')

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--paper-dir',type=Path,help='Optional private PDF cache; render original-paper screenshots')
    args=parser.parse_args()
    if args.paper_dir:
        render_papers(args.paper_dir)
    digest=dict(instruction=data.INSTRUCTION,date=data.DATE,scope=data.SCOPE,sub_questions=data.QUESTIONS,papers=PAPERS,themes=data.THEMES,gaps=data.GAPS,systems=data.SYSTEMS,benchmarks=data.BENCHMARKS,training_resources=data.DATASETS,reported_scores=data.SCORES,search_queries=data.SEARCH_QUERIES)
    (OUT/'literature.json').write_text(json.dumps(digest,indent=2,ensure_ascii=False)+'\n')
    md=['# Literature Review — Context-aware assistance from multi-party speech','','**Instruction**: '+data.INSTRUCTION,'','**Date**: '+data.DATE+' · **Window**: 2023–2026, plus foundational meeting resources · **Depth**: standard','','## Scope & sub-questions','',data.SCOPE,'',*['- '+q for q in data.QUESTIONS],'','## Landscape summary','',*sum(([text,''] for text in data.THEMES),[]),'## Paper table','',md_table(['Paper / authors / date','Venue','Method','Reported result','Relevance / limitation','Status'],[['['+p['title']+']('+p['source']+') · '+p['authors']+' · '+p['date'],p['venue'],p['method'],p['results'],p['relevance']+' '+p['limitations'],p['status']] for p in PAPERS]),'','## Training resources','',md_table(['Resource','Scale','Supervision','Access','Use / limitation'],[[r[1],r[2],r[3],r[4],r[5]+' [Source]('+r[6]+')'] for r in data.DATASETS]),'','## Reported results','']
    for g in data.SCORES:
        md.extend(['### '+g['title'],'',g['metric']+'; '+g['locator']+'; [Primary paper]('+BY_ID[g['id']]['source']+').','',md_table(['Model / pipeline',g['metric']],g['rows']),'',g['caveat'],''])
    md.extend(['## Themes & consensus','',*['- '+t for t in data.THEMES],'','## Open gaps & opportunities',''])
    for gap in data.GAPS:
        md.extend(['### '+gap['statement'],'',gap['evidence']+' '+', '.join('['+ident+']('+BY_ID[ident]['source']+')' for ident in gap['refs'])+'.',''])
    md.extend(['These are synthesis-based candidate gaps, not exhaustive novelty claims. No experiments or new annotations were created.','', '## References','',*['- '+p['authors']+'. '+p['title']+'. '+p['venue']+'; '+p['version']+'. [Primary source]('+p['source']+').' for p in PAPERS],'','## Evidence caveats','','MP-Bench: PDF and landing-page abstracts disagree (33% vs. 22%); excluded from plots. GroupMemBench: paper and card corpus counts differ. MultiTalk: public data does not verify its claimed engine/scorer/checkpoint release. Dataset reuse licences are separated from code licences. Full primary manuscripts were read; all bibliography entries have independently checked metadata.',''])
    (OUT/'LITERATURE.md').write_text('\n'.join(md),encoding='utf-8')
    (ROOT/'context-assistance.html').write_text(html(),encoding='utf-8')
    print('Built context-assistance.html and digests: 15 papers, 5 systems, 9 benchmarks, 8 training resources, 7 figures, 6 tables.')

if __name__ == '__main__':
    main()
