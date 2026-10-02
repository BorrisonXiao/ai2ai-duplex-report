#!/usr/bin/env python3
"""Portable structural, citation and natural-wrapping checks for this review."""
from collections import Counter
from html.parser import HTMLParser
from html import unescape
import json
from pathlib import Path
import re
from report_content import verified_sources, evidence
from report_content import PROFILES, all_groups, scores
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


class Parser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = []
        self.links = []
        self.filters = []
        self.tables = []
        self.labels = []
        self.title = []
        self.capture = None
        self.text = []
        self.viewport = False
        self.figures = 0
        self.images_missing_alt = []

    def handle_starttag(self, tag, raw):
        attrs = dict(raw)
        if attrs.get('id'):
            self.ids.append(attrs['id'])
        if attrs.get('data-filter'):
            self.filters.append(attrs['data-filter'])
        for key in ('href','src'):
            if attrs.get(key): self.links.append((tag, attrs[key]))
        if tag == 'table': self.tables.append(attrs.get('id'))
        if tag == 'figure': self.figures += 1
        if tag == 'meta' and attrs.get('name') == 'viewport': self.viewport = True
        if tag == 'img' and not attrs.get('alt'): self.images_missing_alt.append(attrs.get('src'))
        if tag in ('title','caption','figcaption'):
            self.capture = tag
            self.text = []

    def handle_data(self, text):
        if self.capture:
            self.text.append(text)

    def handle_endtag(self, tag):
        if tag == self.capture:
            text = ''.join(self.text).strip()
            if tag == 'title': self.title.append(text)
            else: self.labels.append(text)
            self.capture = None


def validate():
    errors = []
    source = (ROOT / 'index.html').read_text(encoding='utf-8')
    parser = Parser()
    parser.feed(source)
    if not parser.title or not parser.viewport:
        errors.append('Missing page title or viewport metadata')
    duplicates = [ident for ident,count in Counter(parser.ids).items() if count > 1]
    if duplicates: errors.append('Duplicate IDs: ' + ', '.join(duplicates))
    for tag,url in parser.links:
        parts = urlsplit(url)
        if parts.scheme or parts.netloc:
            if tag != 'a': errors.append('Unexpected external asset: ' + url)
            continue
        target = ROOT / unquote(parts.path.lstrip('/')) if parts.path else ROOT / 'index.html'
        if target.is_dir(): target = target / 'index.html'
        if not target.exists(): errors.append('Broken local link: ' + url)
        if target == ROOT / 'index.html' and parts.fragment and parts.fragment not in parser.ids:
            errors.append('Broken anchor: ' + url)
        if parts.path.startswith('/'):
            errors.append('Root-absolute link would break the GitHub Pages project subpath: ' + url)
    tabs = re.search(r'<nav\b[^>]*aria-label="Project tabs"[^>]*>(.*?)</nav>',source,re.S)
    if not tabs or len(re.findall('<a ',tabs.group(1))) != 1 or '>Literature review</a>' not in tabs.group(1):
        errors.append('Project navigation must contain only Literature review')
    for kind,count in [('Table',len(parser.tables)),('Figure',parser.figures)]:
        actual = [int(match.group(1)) for text in parser.labels if (match := re.match(kind + r' (\d+)\.',text))]
        if actual != list(range(1,count+1)): errors.append('Missing or non-sequential ' + kind + ' captions')
    if len(parser.tables) != 6 + len(PROFILES): errors.append('Expected six landscape tables and one table per performance profile')
    if parser.figures != 9 + len(PROFILES): errors.append('Expected a taxonomy, seven paper screenshots, coverage and profile plots')
    for ident in parser.filters:
        for required in (ident,ident+'-filter',ident+'-count',ident+'-empty'):
            if required not in parser.ids: errors.append('Missing filter component: ' + required)
    for match in re.finditer(r'<(p|h[1-6]|td|th|dd|dt)\b[^>]*>(.*?)</\1>',source,re.S):
        if '\n' in match.group(2) or re.search(r'<br\b|&nbsp;|&#160;|\u00a0',match.group(2),re.I):
            errors.append('Prose block contains a manual line break or nonbreaking space: ' + match.group(1))
    if re.search(r'<br\b',source,re.I): errors.append('Manual <br> element found')
    css = (ROOT / 'assets/site.css').read_text()
    if re.search(r'white-space\s*:\s*(?:pre|nowrap)',css):
        errors.append('CSS disables natural prose wrapping')
    markdown = (ROOT / 'research/LITERATURE.md').read_text()
    if re.search(r' {2,}\n|\\\n|<br\b',markdown): errors.append('Markdown contains a forced line break')
    digest = json.loads((ROOT / 'research/literature.json').read_text())
    audit = verified_sources()
    audited = {s['url']:s for s in audit['sources']}
    for field in ('instruction','date','scope','sub_questions','papers','themes','gaps'):
        if not digest.get(field): errors.append('Missing digest field: ' + field)
    paper_ids = []
    for paper in digest['papers']:
        paper_ids.append(paper['id'])
        for field in ('title','authors','year','venue','arxiv_id','problem','method','results','relevance','status','source'):
            if not paper.get(field): errors.append('Missing paper field: ' + paper['id'] + '/' + field)
        if paper['status'] != 'verified' or audited.get(paper['source'],{}).get('status') != 'reachable':
            errors.append('Paper lacks verified source: ' + paper['id'])
        if paper['date'] > digest['date']: errors.append('Paper beyond review cutoff: ' + paper['id'])
        if 'ref-' + paper['id'].replace('.','-') not in parser.ids:
            errors.append('Missing bibliography anchor: ' + paper['id'])
    if len(set(paper_ids)) != len(paper_ids): errors.append('Duplicate papers in digest')
    for gap in digest['gaps']:
        if any(ident not in paper_ids for ident in gap['refs']): errors.append('Gap cites an unknown paper: ' + gap['id'])
    expected = dict(zip(['systems-table','availability-table','benchmarks-table','datasets-table','recipes-table','implications-table'],[len(digest['systems']),len(digest['systems']),len(digest['benchmarks']),len(digest['datasets']),len(digest['training_recipes']),3]))
    performance, plot_manifest = evidence()
    expected.update({'performance-' + group['id']: len([row for row in group['rows'] if row['role'] != 'text_control']) for group in all_groups(performance)})
    for ident,count in expected.items():
        match = re.search(r'<table id="'+ident+r'">.*?<tbody>(.*?)</tbody>',source,re.S)
        if not match or match.group(1).count('<tr>') != count:
            errors.append('Incorrect table row count: ' + ident)
    for group in all_groups(performance):
        match = re.search(r'<table id="performance-' + group['id'] + r'">.*?<tbody>(.*?)</tbody>', source, re.S)
        if not match:
            continue
        numeric_rows = re.findall(r'<tr>(.*?)</tr>', match.group(1), re.S)
        source_rows = [row for row in group['rows'] if row['role'] != 'text_control']
        for actual, row in zip(numeric_rows, source_rows):
            values = scores(group, row)
            definitions = group.get('metric_specs', [{'decimals': row['decimals']} for _ in values])
            wanted = ['NR' if value is None else f"{value:.{definition['decimals']}f}" for value, definition in zip(values, definitions)]
            found = [unescape(re.sub(r'<[^>]+>', '', cell)).strip() for cell in re.findall(r'<td>(.*?)</td>', actual, re.S)]
            if wanted != found:
                errors.append('Numeric table does not match source scores: ' + group['id'] + '/' + row['model'])
    readme = (ROOT / 'README.md').read_text()
    if '[Project webpage](https://borrisonxiao.github.io/ai2ai-duplex-report/)' not in readme:
        errors.append('README lacks the webpage link')
    if not any(status in readme.lower() for status in ('live on github pages', 'pending repository pages configuration')):
        errors.append('README must state whether GitHub Pages is live or awaiting configuration')
    if parser.images_missing_alt: errors.append('Images missing alt text')
    for ident in [profile['id'] for profile in PROFILES]:
        if 'profile-' + ident not in parser.ids: errors.append('Missing model/benchmark profile: ' + ident)
    if 'NR, never zero' not in source or 'not global SoTA' not in source:
        errors.append('Missing sparse-coverage or source-specific leadership caveat')
    return errors, digest


if __name__ == '__main__':
    errors,digest = validate()
    if errors:
        for error in errors: print('ERROR:',error)
        raise SystemExit(1)
    print(f'Validation passed: one project tab, {6+len(PROFILES)} tables, {9+len(PROFILES)} labeled figures, {len(digest["papers"])} verified papers, complete local links/citations, natural text wrapping.')
