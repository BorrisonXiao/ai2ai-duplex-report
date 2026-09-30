#!/usr/bin/env python3
"""Build a static review and stable literature digests from audited primary facts.

Offline and dependency-free. Generated prose occupies one source line per block;
CSS, not author-inserted line breaks, controls browser wrapping.
"""
from copy import deepcopy
from html import escape
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'research'))
import review_data as data

AUDIT = json.loads((ROOT / 'research/source-audit.json').read_text())
SOURCES = {row['url']: row for row in AUDIT['sources']}
SYSTEMS = deepcopy(data.SYSTEMS)
BENCHMARKS = deepcopy(data.BENCHMARKS)
DATASETS = deepcopy(data.DATASETS)
N = data.NARRATIVE


def arxiv_id(url):
    match = re.search(r'arxiv\.org/(?:abs|html|pdf)/(\d{4}\.\d{4,5})', url or '')
    return match.group(1) if match else None


def author_name(value):
    # arXiv's citation_author uses Family, Given. Preserve unpunctuated teams.
    parts = value.split(', ', 1)
    return parts[1] + ' ' + parts[0] if len(parts) == 2 else value


def plain_title(value):
    return value.replace('$\\tau$', 'τ').replace('\\tau', 'τ').replace('$', '')


def compact_authors(authors):
    return ', '.join(authors[:3]) + (' et al.' if len(authors) > 3 else '')


PAPERS = {}
for source in AUDIT['sources']:
    ident = arxiv_id(source['url'])
    if not ident or 'metadata' not in source:
        continue
    m = source['metadata']
    required = ('citation_title', 'citation_author', 'citation_date')
    if source['status'] != 'reachable' or not all(m.get(k) for k in required):
        raise ValueError('Missing verified bibliographic metadata: ' + source['url'])
    date = m['citation_date'][0].replace('/', '-')
    authors = [author_name(a) for a in m['citation_author']]
    PAPERS[ident] = dict(id=ident, title=plain_title(m['citation_title'][0]), authors=', '.join(authors), author_list=authors, year=int(date[:4]), date=date, venue='Preprint / technical report', arxiv_id=ident, doi=None, status='verified', source=source['url'])

for system in SYSTEMS:
    p = PAPERS[system['id']]
    system.update(title=p['title'], authors=compact_authors(p['author_list']), date=p['date'])
    if system['id'] == '2505.15670':
        system['name'] = 'SALM-Duplex'
    p.update(venue=system['venue'], problem=system['relevance'], method=' '.join(system[k] for k in ('backbone', 'stream', 'decoder', 'control')), results=system['result'], relevance=system['relevance'], limitations=system['limitation'], artifacts={k: system[k] for k in ('code', 'weights', 'training', 'data', 'license')})

for bench in BENCHMARKS:
    ident = arxiv_id(bench['paper'])
    if not ident:
        continue
    p = PAPERS[ident]
    bench.update(authors=compact_authors(p['author_list']), date=p['date'])
    if 'method' not in p:
        p.update(venue=bench['venue'], problem=bench['scope'], method=bench['scope'] + ' Metrics: ' + bench['metrics'], results=bench['result'], relevance=bench['use'], limitations=bench['caveat'], artifacts={'evaluation': bench['artifact'], 'access': bench['access']})

for dataset in DATASETS:
    ident = arxiv_id(dataset['source']) or arxiv_id(dataset.get('extra'))
    if ident and 'method' not in PAPERS[ident]:
        PAPERS[ident].update(problem=dataset['use'], method=dataset['kind'] + '; ' + dataset['annotation'], results=dataset['scale'], relevance=dataset['use'], limitations=dataset['access'], artifacts={'data': dataset['source'], 'access': dataset['access']})

PAPERS = dict(sorted(PAPERS.items(), key=lambda item: (item[1]['date'], item[0])))
NUMBERS = {ident: i for i, ident in enumerate(PAPERS, 1)}


def e(value):
    return escape(str(value), quote=True)


def link(label, url, cls=''):
    return f'<a href="{e(url)}"' + (f' class="{e(cls)}"' if cls else '') + f'>{e(label)}</a>'


def cite(*ids):
    return ' '.join(link(f'[{NUMBERS[i]}]', '#ref-' + i.replace('.', '-'), 'citation') for i in ids)


def source_cite(url):
    ident = arxiv_id(url)
    if ident:
        return cite(ident)
    if '75c45fca2aa416ada062b26cc4fb7641' in url:
        return cite('2510.07497')
    return link('Primary source', url)


def p(text, citations=(), cls=''):
    return '<p' + (f' class="{cls}"' if cls else '') + '>' + e(text) + (' ' + cite(*citations) if citations else '') + '</p>'


def small(text):
    return '<span class="sub">' + e(text) + '</span>'


def inline_links(items):
    return '<span class="inline-links">' + ' '.join(link(label, url) for label, url in items) + '</span>' if items else ''


def row(cells):
    return '<tr><th scope="row">' + cells[0] + '</th>' + ''.join('<td>' + cell + '</td>' for cell in cells[1:]) + '</tr>'


def table(ident, number, caption, headers, rows, searchable=True):
    pieces = []
    if searchable:
        pieces.append(f'<div class="filter"><label for="{ident}-filter">Filter entries</label><input id="{ident}-filter" data-filter="{ident}" type="search" placeholder="Search any feature or model" autocomplete="off"><output id="{ident}-count" aria-live="polite">{len(rows)} of {len(rows)} entries</output></div>')
    pieces.append('<p class="scroll-note">On narrow screens, scroll the table horizontally; all text wraps within its cells.</p>')
    pieces.append(f'<div class="table-wrap" tabindex="0" role="region" aria-label="Table {number}: {e(caption)}"><table id="{ident}"><caption>Table {number}. {e(caption)}</caption><thead><tr>' + ''.join('<th scope="col">' + e(h) + '</th>' for h in headers) + '</tr></thead><tbody>')
    pieces.extend(row(cells) for cells in rows)
    pieces.append('</tbody></table></div>')
    if searchable:
        pieces.append(f'<p id="{ident}-empty" class="empty-message" hidden>No entries match. Clear the filter to restore the complete table.</p>')
    return '\n'.join(pieces)


def section(ident, title, body, intro=None):
    return f'<section id="{ident}" class="section"><h2>{e(title)}</h2>\n' + (p(intro, cls='section-intro') + '\n' if intro else '') + body + '\n</section>'


def system_label(s):
    return e(s['name']) + ' ' + cite(s['id']) + small(s['date'] + ' · ' + s['venue'])


def architecture_figure():
    families = [
        ('Native parallel streams', 'User audio ∥ assistant text ∥ assistant audio', ['Shared temporal state', 'Depth / acoustic heads'], 'Moshi, PersonaPlex, Lychee-FD. Streams are synchronized; text semantics and speech bandwidth need not advance at the same rate.', ['2410.00037', '2602.06053', '2607.06540']),
        ('Serialized token modeling', 'Speech + text + control token blocks', ['Single causal LLM', 'Speech tokens → waveform'], 'OmniFlatten and BayLing-Duplex. Chunk sizes and token order determine when the model can hear, decide and emit.', ['2410.17799', '2606.14528']),
        ('Text backbone + speech modules', 'Streaming encoder embeddings', ['Text reasoning LLM', 'Separate speech decoder'], 'MiniCPM-o 4.5, Freeze-Omni and VoiceChat. Speech output capacity is decoupled from the backbone’s text vocabulary.', ['2604.27393', '2411.00774', '2609.21967']),
        ('Delegated reasoning / tools', 'Persistent duplex frontend', ['Asynchronous text backend', 'Result admission into frontend'], 'Realtime-Venus, DuplexOmni and Context Spanning. The foreground may continue, but that behavior must be verified, especially during tools.', ['2609.13814', '2606.09186', '2609.33443']),
    ]
    cards = []
    for title, input_text, stages, description, refs in families:
        pipeline = '<div class="pipeline">' + '<i aria-hidden="true">→</i>'.join('<span>' + e(t) + '</span>' for t in [input_text] + stages) + '</div>'
        cards.append('<div class="card"><h3>' + e(title) + '</h3>' + pipeline + p(description, refs) + '</div>')
    return '<figure class="architecture"><div class="card-grid">' + '\n'.join(cards) + '</div><figcaption>Figure 1. Four recurring design patterns, redrawn as a conceptual synthesis of the cited architectures. Delegation can be combined with any of the first three; arrows indicate information flow, not measured latency or strictly sequential execution.</figcaption></figure>'


def build_html():
    summary_refs = [ ['2604.27393','2606.14528','2607.06540','2609.13814','2606.09186'], ['2410.00037','2604.27393','2505.17060'], ['2510.07497','2609.31948','2609.13814'], ['2603.13686','2510.07838','2604.04847','2609.31948','2410.17196','2508.13992'] ]
    overview = p(N['scope']) + p(N['proposal_context'])
    overview += '<div class="stat-grid">' + ''.join(f'<div class="stat"><strong>{count}</strong><span>{e(label)}</span></div>' for count, label in [(len(SYSTEMS),'system designs'), (len(BENCHMARKS),'evaluation suites'), (len(DATASETS),'data sources'), (len(PAPERS),'verified papers')]) + '</div>'
    overview += '<div class="prose">' + '\n'.join(p(text, refs) for text, refs in zip(N['summary'], summary_refs)) + '</div>'
    overview += '<div class="callout amber"><h3>Read comparisons as evidence, not a unified leaderboard</h3>' + p('All numerical results below are author-reported. Models, judges, hardware, audio conditions, task versions and latency definitions differ. We did not reproduce these measurements.') + '</div>'
    overview += '<nav class="jump-links" aria-label="Review sections">' + ' '.join(link(label, '#' + ident) for ident, label in [('systems','System designs'), ('availability','Open releases'), ('benchmarks','Benchmarks'), ('training-data','Training data'), ('implications','Proposal implications'), ('paper-notes','Paper notes'), ('references','References')]) + '</nav>'

    system_rows = [[system_label(s) + small(s['family']), e(s['backbone']), e(s['stream']), e(s['decoder']), e(s['control'])] for s in SYSTEMS]
    architectures = architecture_figure() + table('systems-table', 1, 'System designs: backbone, time/stream representation, speech generation and control.', ['System / first submission', 'Backbone', 'Time and input representation', 'Speech decoder / output', 'Control and reasoning location'], system_rows)
    architectures += '<div class="callout"><h3>A finer distinction than “Moshi versus LLM decoder”</h3>' + p('Moshi’s temporal model is initialized from the Helium text LLM. The more useful comparison is parallel streams versus serialized tokens, text versus speech prediction in the main backbone, and internal versus delegated reasoning. An “inner monologue” aligned to spoken words is also not automatically a private chain of thought.', ['2410.00037','2510.07497','2604.27393','2606.14528']) + '</div>'
    release_rows = []
    for s in SYSTEMS:
        inference = link(*s['code']) if s['code'] else e('Not located')
        weights = link(*s['weights']) if s['weights'] else e('Not located')
        release_rows.append([system_label(s), inference, weights, e(s['training']) + inline_links(s['extra']), e(s['data']) + small(s['license'])])
    releases = table('availability-table', 2, 'Artifact availability as inspected on 30 September 2026; a demo is not a source release.', ['System', 'Code / demo: exact scope', 'Checkpoint', 'Training implementation', 'Training mixture / license'], release_rows)
    releases += '<div class="callout amber"><h3>Full duplex during speech is not full duplex during tools</h3>' + p('VoiceChat’s paper/card restrict barge-in during tool execution. The NVIDIA frontend–backend design suppresses foreground output during backend execution. Realtime-Venus explicitly targets continued interaction under asynchronous delegation. Treat these as different experimental conditions when studying late corrections.', ['2609.21967','2609.19334','2609.13814']) + '</div>'

    bench_rows = []
    for b in BENCHMARKS:
        label = e(b['name']) + (' ' + source_cite(b['paper']) if b['paper'] else '') + small(b['venue'])
        access = e(b['access']) + (inline_links([('Official artifact', b['artifact'])]) if b['artifact'] else '')
        bench_rows.append([label, e(b['scope']), e(b['metrics']), access, e(b['use']) + small(b['caveat'])])
    benchmarks = table('benchmarks-table', 3, 'Benchmarks compared by test setting, metrics, release status and relevance to incremental reasoning.', ['Benchmark', 'Interaction / content', 'Measured outcome', 'Availability', 'Use for this project / caveat'], bench_rows)
    benchmarks += '<div class="callout">' + p(N['evaluation_note'], ['2510.07497','2604.04847','2603.13686','2609.31948']) + '</div>'
    benchmarks += p('τ-Voice’s original tasks and protocol should be distinguished from the actively updated τ³-bench repository. Pin a commit and task files before comparing against a number in the March paper. Tool-call recall, tool-selection F1, argument accuracy and grounded task success answer different questions.', ['2603.13686','2609.19334','2604.04847'])

    data_rows = []
    for d in DATASETS:
        artifacts = [('Source / card', d['source'])]
        if d.get('extra'): artifacts.append(('Additional primary source', d['extra']))
        data_rows.append([e(d['name']) + small(d['scale']) + inline_links(artifacts), e(d['kind']), e(d['annotation']), e(d['access']), e(d['use'])])
    training_data = table('datasets-table', 4, 'Data sources: reported scale is not equivalent to downloadable, licensed or reasoning-labeled training hours.', ['Corpus / reported size', 'Capture and interaction', 'Supervision / alignment', 'Access and reuse conditions', 'Potential use / limitation'], data_rows)
    recipe_rows = [[e(name), e(recipe), e(access) + '<span class="inline-links">' + source_cite(first) + (' ' + source_cite(second) if second else '') + '</span>'] for name, recipe, access, first, second in data.RECIPES]
    training_data += table('recipes-table', 5, 'Reported training recipes, separated from released corpora.', ['Model / recipe', 'Reported supervision', 'Reproducibility / primary source'], recipe_rows, searchable=False)
    training_data += '<div class="callout amber">' + p(N['access_note']) + inline_links([('SmoothConv card', DATASETS[0]['source']), ('DuplexConv card', DATASETS[1]['source']), ('otoSpeech card', DATASETS[2]['source']), ('DuplexChat card', DATASETS[10]['source'])]) + '</div>'

    implications_rows = [
        ['Semantic sufficiency', 'Early question-completeness-triggered CoT and correctness/length DPO already appear in Think while listening.', 'Separate correct useful answer timing from CoT onset; stress incomplete or misleading prefixes.', ['2510.07497']],
        ['Revision-aware reasoning', 'Adaptive reasoning, correction tasks and asynchronous delegation are established individually.', 'Test a late constraint between delegation and result admission; score false commitments and stale-result use.', ['2510.07497','2510.07838','2609.13814','2609.33443']],
        ['Speaker / stream awareness', 'Overlap rejection and multi-party addressability now have dedicated evaluations.', 'Test whose correction changes which task hypothesis; distinguish addressing and diarization from role/persona control.', ['2507.23159','2609.31948','2602.06053']],
    ]
    implications = table('implications-table', 6, 'How the reviewed evidence updates the three questions in the March proposal; remaining questions are this review’s synthesis.', ['Original question', 'Established evidence', 'Unresolved question in this review'], [[e(a), e(b) + ' ' + cite(*refs), e(c)] for a,b,c,refs in implications_rows], searchable=False)
    implications += '<h3>Open gaps, with evidence boundaries</h3><div class="card-grid">'
    for gap in data.GAPS:
        implications += '<div class="card"><span class="tag blue">Review synthesis</span><h3>' + e(gap['statement']) + '</h3>' + p(gap['evidence'], gap['refs']) + '</div>'
    implications += '</div>' + p('These are gaps relative to the reviewed evidence, not validated claims that nobody has studied them. A full novelty audit would be needed before selecting a new project contribution.', cls='meta')
    implications += '<h3 class="reading-title">Suggested reading order</h3><div class="card-grid">'
    for title, description, refs in N['reading']:
        implications += '<div class="card"><h3>' + e(title) + '</h3>' + p(description, refs) + '</div>'
    implications += '</div>'

    notes = p('Expand a system for its reported result, relevance and limitations. Numerical claims remain attached to their original protocols; this is not our experimental evaluation.', cls='section-intro')
    for s in SYSTEMS:
        notes += '<details><summary>' + e(s['name']) + ' · ' + e(s['authors']) + ' · ' + e(s['date']) + '</summary><div class="paper-note"><dl>'
        for label, text in [('Research problem / relevance',s['relevance']), ('Method', ' '.join(s[k] for k in ('backbone','stream','decoder','control'))), ('Author-reported result',s['result']), ('Limitations and review assessment',s['limitation'])]:
            notes += '<dt>' + e(label) + '</dt><dd>' + e(text) + ' ' + cite(s['id']) + '</dd>'
        notes += '</dl>' + inline_links([('Primary manuscript', 'https://arxiv.org/abs/' + s['id'])] + ([s['code']] if s['code'] else []) + ([s['weights']] if s['weights'] else [])) + '</div></details>'

    references = '<div class="prose">' + p(N['methodology']) + p(N['limitations']) + p('Bibliographic title, full authors and first-submission date come from verified arXiv metadata. Conference status is labeled separately. This page does not infer acceptance from a submission notice. Source-link success is a reachability check, not verification that code reproduces the reported result.') + '</div>'
    references += '<ol class="references">'
    for ident, paper in PAPERS.items():
        supplementary = next((s['extra'] for s in SYSTEMS if s['id'] == ident), [])
        references += f'<li id="ref-{ident.replace(".", "-")}">' + link(paper['title'], paper['source']) + ' ' + small(compact_authors(paper['author_list']) + ' · ' + paper['date'] + ' · ' + paper['venue'] + ' · arXiv:' + ident) + inline_links(supplementary) + '</li>'
    reachable = sum(s['status'] == 'reachable' for s in SOURCES.values())
    references += '</ol>' + p(f'Source audit: {reachable} of {len(SOURCES)} primary links returned successfully at the recorded check. The JSON records exact URLs, redirects, HTTP status and bibliographic metadata; it does not contain downloaded papers, model weights or training audio.') + inline_links([('Source audit JSON','research/source-audit.json'), ('Structured literature digest','research/literature.json'), ('Readable Markdown digest','research/LITERATURE.md')])

    body = '\n'.join([
        '<a class="skip-link" href="#main">Skip to review</a>',
        '<header class="site-nav"><div class="nav-inner"><a class="brand" href="./">AI2AI Duplex</a><nav class="nav-links" aria-label="Project tabs"><a href="#literature-review" aria-current="page">Literature review</a></nav></div></header>',
        '<main id="main"><div class="container">',
        '<header id="literature-review" class="hero"><p class="eyebrow">Research landscape · September 2026</p><h1>Reasoning while listening, revising while speaking.</h1><p class="lede">A literature review of modern full-duplex speech architectures, open releases, training resources and evaluations for incremental, speaker-aware reasoning.</p><p class="meta">Updated 30 September 2026 · Primary-source review · Author-reported results, not a reproduced leaderboard</p><div class="button-row">' + link('Explore system designs','#systems','button primary') + link('Structured digest','research/literature.json','button') + link('Source repository','https://github.com/BorrisonXiao/ai2ai-duplex-report','button') + '</div></header>',
        section('overview','What changed since the original proposal',overview),
        section('systems','System designs',architectures,N['architecture_lead']),
        section('availability','What is actually open?',releases,N['availability_lead']),
        section('benchmarks','Benchmarks and measurement',benchmarks,N['benchmarks_lead']),
        section('training-data','Training data and supervision',training_data,N['data_lead']),
        section('implications','Implications for the original proposal',implications,'Literature-derived implications only: no experiments or new implementation proposal are presented.'),
        section('paper-notes','System paper notes',notes),
        section('references','Primary references and review method',references),
        '<footer class="site-footer"><p>AI2AI Duplex · Literature review only · ' + link('Source and maintenance notes','https://github.com/BorrisonXiao/ai2ai-duplex-report') + ' · Visual direction adapted from ' + link('JSALT 2026 Downsampling','https://borrisonxiao.github.io/jsalt26-downsampling/') + '</p></footer>',
        '</div></main>',
    ])
    return '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n<meta name="description" content="Primary-source review of modern full-duplex speech models: architectures, releases, benchmarks and training data for incremental reasoning.">\n<meta name="color-scheme" content="light dark">\n<title>AI2AI Duplex — Literature Review</title>\n<link rel="stylesheet" href="assets/site.css">\n<script src="assets/site.js" defer></script>\n</head>\n<body>\n' + body + '\n</body>\n</html>\n'


def md_link(label, url):
    return '[' + label.replace('[','').replace(']','') + '](' + url + ')'


def md_cell(value):
    return str(value).replace('|','\\|').replace('\n',' ')


def md_table(headers, rows):
    return '\n'.join(['| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join('---' for _ in headers) + ' |'] + ['| ' + ' | '.join(md_cell(cell) for cell in row) + ' |' for row in rows])


def build_markdown():
    text = ['# Literature Review — Full-duplex incremental reasoning', '', '**Instruction**: ' + data.INSTRUCTION, '', '**Date**: ' + data.DATE + ' · **Window**: 2024–September 2026, plus established corpora · **Depth**: deep', '', '## Scope & sub-questions', '', data.SCOPE, '', *['- ' + q for q in data.QUESTIONS], '', '## Landscape summary', '']
    for paragraph in N['summary']:
        text.extend([paragraph, ''])
    text.extend(['## Paper table', '', md_table(['Paper (authors, first submission)', 'Venue', 'Method', 'Author-reported result', 'Relevance / limitation', 'Status'], [[md_link(p['title'], p['source']) + ' (' + compact_authors(p['author_list']) + ', ' + p['date'] + ')', p['venue'], p['method'], p['results'], p['relevance'] + ' ' + p['limitations'], p['status']] for p in PAPERS.values()]), '', '## Release availability', ''])
    text.append(md_table(['System', 'Code / demo', 'Weights', 'Training', 'Data / license'], [[s['name'], md_link(*s['code']) if s['code'] else 'Not located', md_link(*s['weights']) if s['weights'] else 'Not located', s['training'], s['data'] + '; ' + s['license']] for s in SYSTEMS]))
    text.extend(['', '## Benchmarks', '', md_table(['Benchmark', 'Scope', 'Metrics', 'Access', 'Use / caveat'], [[md_link(b['name'], b['paper'] or b['artifact']), b['scope'], b['metrics'], b['access'] + (' ' + md_link('Artifact',b['artifact']) if b['artifact'] else ''), b['use'] + ' ' + b['caveat']] for b in BENCHMARKS]), '', '## Training data', '', md_table(['Source', 'Scale / capture', 'Annotations', 'Access', 'Use / limitation'], [[md_link(d['name'], d['source']), d['scale'] + '; ' + d['kind'], d['annotation'], d['access'], d['use']] for d in DATASETS]), '', N['access_note'], '', '## Reported training recipes', '', md_table(['Model', 'Recipe', 'Availability / evidence'], [[name, recipe, access + ' ' + md_link('Source', first) + (' ' + md_link('Second source', second) if second else '')] for name, recipe, access, first, second in data.RECIPES]), '', '## Themes & consensus', '', *['- ' + theme for theme in data.THEMES], '', '## Open gaps & opportunities', ''])
    for gap in data.GAPS:
        refs = ', '.join(md_link(ident, PAPERS[ident]['source']) for ident in gap['refs'])
        text.extend(['### ' + gap['statement'], '', gap['evidence'] + ' ' + refs + '.', ''])
    text.extend(['These are this review’s inferences, not proof of exhaustive novelty.', '', '## Review method and limitations', '', N['methodology'], '', N['limitations'], '', N['evaluation_note'], '', '## References', ''])
    for ident, paper in PAPERS.items():
        text.append(f'{NUMBERS[ident]}. ' + md_link(paper['title'],paper['source']) + '. ' + paper['authors'] + '. ' + paper['venue'] + ', ' + paper['date'] + '; arXiv:' + ident + '. Verified.')
    return '\n'.join(text) + '\n'


def main():
    digest = dict(instruction=data.INSTRUCTION, date=data.DATE, scope=data.SCOPE, sub_questions=data.QUESTIONS, papers=list(PAPERS.values()), themes=data.THEMES, gaps=data.GAPS, systems=SYSTEMS, benchmarks=BENCHMARKS, datasets=DATASETS, training_recipes=data.RECIPES, methodology=N['methodology'], limitations=N['limitations'], source_audit='source-audit.json')
    (ROOT / 'index.html').write_text(build_html(),encoding='utf-8')
    (ROOT / 'research/LITERATURE.md').write_text(build_markdown(),encoding='utf-8')
    (ROOT / 'research/literature.json').write_text(json.dumps(digest,ensure_ascii=False,indent=2) + '\n',encoding='utf-8')
    print(f'Built index.html, LITERATURE.md and literature.json: {len(SYSTEMS)} systems, {len(BENCHMARKS)} benchmarks, {len(DATASETS)} datasets, {len(PAPERS)} verified papers.')


if __name__ == '__main__':
    main()
