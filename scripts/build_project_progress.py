"""Build the project TODO and daily log from reviewed plan and log records."""
from html import escape as e
import hashlib
import json
from pathlib import Path
import re
from site_navigation import project_tabs
from project_language import prethinking_prose
import thinking_design

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'research/project-progress'
CSS = '''.progress-page{padding-bottom:2rem}.progress-page .hero{padding:30px 0 22px}.progress-page h1{font-size:clamp(32px,4vw,48px)}.progress-page .section{padding:26px 0}.progress-page ul{padding-left:1.4rem}.progress-page li{margin:.7rem 0}.progress-page .brief li{max-width:900px}.progress-page .task-list{list-style:none;padding:0;margin:1rem 0}.progress-page .task-list li{display:grid;grid-template-columns:1.1rem minmax(0,1fr);gap:.7rem;align-items:start;margin:.85rem 0}.progress-page .task-list .status-checkbox{appearance:auto;margin:.2rem 0 0;width:1.05rem;height:1.05rem;accent-color:var(--accent);opacity:1}.progress-page .task-list .task-copy{min-width:0}.progress-page .task-list .task-copy p{margin:.35rem 0}.progress-page .task-state{font-size:.85rem;font-weight:650;color:var(--muted)}.progress-page .status-legend,.progress-page .definition{font-size:.92rem;color:var(--muted);max-width:900px}.progress-page details{margin:1rem 0}.progress-page summary{cursor:pointer;font-weight:650;color:var(--accent)}.progress-page details[open]>summary{margin-bottom:1.3rem}.progress-page .status{font-size:.85rem;font-weight:650;color:var(--muted)}.progress-page .stage{padding:22px 0;border-top:1px solid var(--border);scroll-margin-top:10rem}.progress-page h3{margin-top:1.3rem}.progress-page .stage li p{margin:.35rem 0}.progress-page .jump-links{gap:10px 22px}.progress-page code.state-schema{display:block;white-space:normal;overflow-wrap:anywhere;padding:1rem;border:1px solid var(--border)}.progress-page .table-wrap{max-width:100%;overflow-x:auto}.progress-page table{width:100%;border-collapse:collapse}.progress-page th,.progress-page td{padding:.8rem;text-align:left;vertical-align:top;border-bottom:1px solid var(--border)}.progress-page .table-caption{font-weight:650}.progress-page .table-scroll-hint{display:none}.progress-page .catalog-question{border:1px solid var(--border);border-radius:10px;padding:1rem;margin:1rem 0;min-width:0}.progress-page .catalog-question p{overflow-wrap:anywhere}.progress-page .question{font-weight:650}.progress-page figure{margin:1rem 0}.progress-page figcaption{font-size:.9rem}.progress-page section,.progress-page article{scroll-margin-top:10rem}.progress-page .log-date{font-size:1.5rem}.progress-page .log-note{font-size:.9rem;color:var(--muted)}@media(max-width:700px){.progress-page .table-scroll-hint{display:block;font-weight:400}.progress-page .hero{padding-top:24px}}'''
JS = '''function revealProgressHash(){const id=decodeURIComponent(location.hash.slice(1));if(!id)return;const target=document.getElementById(id);if(!target)return;if(target.tagName==='DETAILS')target.open=true;for(let p=target.parentElement;p;p=p.parentElement)if(p.tagName==='DETAILS')p.open=true;requestAnimationFrame(()=>target.scrollIntoView());}addEventListener('hashchange',revealProgressHash);addEventListener('load',revealProgressHash);'''
STATUS_JS = '''document.querySelectorAll('.status-checkbox[data-state="partial"]').forEach(box=>{box.indeterminate=true;});'''


def read(path):
    return json.loads(path.read_text())


def bullets(items):
    return '<ul class="brief">' + ''.join(
        '<li>' + e(x['text']) + (' <a href="' + e(x['url'], quote=True) + '">' + e(x.get('label', 'Details')) + '</a>' if x.get('url') else '') + '</li>'
        for x in items) + '</ul>'


def status_list(items, labels):
    rows = []
    for item in items:
        status = item['status']
        text = item['text']
        checkbox = '<input class="status-checkbox" type="checkbox" disabled' + (' checked' if status == 'complete' else '') + ' data-state="' + e(status, quote=True) + '" aria-label="' + e(labels[status] + ': ' + text, quote=True) + '">'
        link = ' <a href="' + e(item['url'], quote=True) + '">' + e(item.get('label', 'Details')) + '</a>' if item.get('url') else ''
        rows.append('<li>' + checkbox + '<div class="task-copy"><strong><span class="task-state">' + e(labels[status]) + '</span> · ' + e(text) + '</strong>' + link + '</div></li>')
    return '<ul class="task-list brief">' + ''.join(rows) + '</ul>'


def table(number, caption, headers, rows):
    key = 'catalog-table-' + str(number)
    return '<p class="asset-label table-caption" id="' + key + '">Table ' + str(number) + '. ' + e(caption) + '<span class="table-scroll-hint">Scroll sideways to see every column on a narrow screen.</span></p><div class="table-wrap" tabindex="0" role="region" aria-labelledby="' + key + '"><table aria-labelledby="' + key + '"><thead><tr>' + ''.join('<th scope="col">' + e(h) + '</th>' for h in headers) + '</tr></thead><tbody>' + ''.join('<tr>' + ''.join('<td>' + str(v) + '</td>' for v in row) + '</tr>' for row in rows) + '</tbody></table></div>'


def document(name, title, category, body, js=''):
    css_version = hashlib.sha256((ROOT / 'assets/site.css').read_bytes()).hexdigest()[:12]
    text = '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="color-scheme" content="light dark"><meta name="description" content="' + e(title) + '"><title>' + e(title) + ' · AI2AI Duplex</title><link rel="stylesheet" href="assets/site.css?v=' + css_version + '"><style>' + CSS + thinking_design.CSS + '</style></head><body><a class="skip-link" href="#main">Skip to content</a><header class="site-nav"><div class="nav-inner"><a class="brand" href="index.html">AI2AI Duplex</a>' + project_tabs(category) + '</div></header><main id="main" class="progress-page"><div class="container">' + body + '</div></main><script>' + JS + js + '</script></body></html>\n'
    text = prethinking_prose(text)
    (ROOT / name).write_text(text)
    return text


def root_links(html):
    """Resolve links in the former experiment-level plan from the site root."""
    def change(m):
        url = m.group(1)
        if url.startswith('question-plan.html'):
            url = url.replace('question-plan.html', 'todo.html', 1)
        elif url.startswith('../'):
            url = url[3:]
        elif not url.startswith(('#', 'https:', 'http:', 'mailto:')):
            url = 'experiments/' + url
        return 'href="' + url + '"'
    return re.sub(r'href="([^"]+)"', change, html)


def build_plan():
    r = read(ROOT / 'research/question-catalog/plan.json')
    brief = read(DATA / 'todo-summary.json')
    labels = {'complete': 'Done', 'partial': 'Partly complete', 'pending': 'To do', 'planned': 'Later', 'optional': 'Optional; not collected'}
    body = '<header class="hero"><h1>Project TODO</h1></header><section class="section" id="at-a-glance"><span id="next"></span><h2>Now</h2>' + status_list(brief['now'], labels) + '<p class="status-legend">Checked means done; an empty box means not done yet. The label distinguishes work to do, later work and optional work.</p><p class="definition"><strong>Pre-thinking:</strong> ' + e(brief['definition']['text']) + ' <a href="' + e(brief['definition']['url'], quote=True) + '">How it works</a></p></section><nav class="jump-links" aria-label="On this page"><a href="#stages">Four stages</a><a href="#appendix">Detailed checklist and design</a><a href="daily-log.html">Daily log</a></nav><section class="section" id="stages"><h2>The four project stages</h2>'
    for s in brief['stages']:
        body += '<article id="' + s['id'] + '"><h3>' + e(s['title']) + '</h3>' + status_list(s['items'], labels) + '</article>'
    body += '</section><section class="section" id="appendix"><h2>Appendix</h2><details id="full-plan"><summary>Open the detailed checklist and experiment design</summary><section id="choices"><h3>Choices already made</h3><ul>' + ''.join('<li>' + e(t) + '</li>' for t in r['choices']) + '</ul></section>'
    body += table(1, 'Stage status records the completed checks, not a general model capability.', ['Stage', 'Status', 'Purpose'], [[e(s['title']), labels[s['status']], e(s['goal'])] for s in r['stages']])
    for s in r['stages']:
        body += '<section class="stage" id="' + s['id'] + '-details"><h3>' + e(s['title']) + '</h3><p class="status">' + labels[s['status']] + '</p><p>' + e(s['goal']) + '</p>'
        if s['id'] == 'history':
            body += '<p>Meeting-state record:</p><code class="state-schema">' + e(r['meeting_state_schema']) + '</code>'
        if s['id'] == 'comparison':
            body += '<p><strong>Current plan:</strong> <a href="what-to-think.html">all 105 questions and what to think</a> · <a href="notation.html">notation table</a>.</p><details><summary>Earlier three-question integration proposal, deferred</summary>' + table(2, 'Earlier integration proposal; the current content study evaluates all 105 questions.', ['Condition', 'Available history', 'Purpose'], [[e(c['condition']), e(c['history']), e(c['establishes'])] for c in r['conditions']]) + '<p>The pre-thinking process must not see the future question, and all its work counts toward cost.</p></details>'
        body += '<ul class="task-list">'
        for t in s['tasks']:
            status = t['status']
            checkbox = '<input class="status-checkbox" type="checkbox" disabled' + (' checked' if status == 'complete' else '') + ' data-state="' + e(status, quote=True) + '" aria-label="' + e(labels[status] + ': ' + t['text'], quote=True) + '">'
            evidence_url = t.get('project_url') or ('experiments/' + t['url'] if t.get('url') else None)
            body += '<li data-status="' + e(status, quote=True) + '">' + checkbox + '<div class="task-copy"><strong><span class="task-state">' + labels[status] + '</span> · ' + e(t['text']) + '</strong>' + ('<p>' + e(t['evidence']) + '</p>' if t.get('evidence') else '') + ('<p><a href="' + e(evidence_url, quote=True) + '">Evidence</a></p>' if evidence_url else '') + '</div></li>'
        body += '</ul>'
        if s['id'] == 'comparison':
            body += '<details><summary>Earlier timing and content design, retained for later work</summary><p>The <a href="what-to-think.html">current 105-question content plan</a> supersedes this earlier scope.</p>' + root_links(thinking_design.render(r['comparison_design'], table)) + '</details>'
        body += '</section>'
    body += '<p>' + e(r['resource_note']) + '</p><p><a href="research/question-catalog/plan.json">Full plan data</a> · <a href="research/project-progress/todo-summary.json">Short checklist data</a></p></details></section><footer class="section"><ul><li>Keep this plan and the <a href="daily-log.html">daily log</a> in sync as work finishes.</li><li>This report edit uses zero GPUs and runs no inference.</li></ul></footer>'
    full = document('todo.html', 'Project TODO', 'todo', body, thinking_design.JS + STATUS_JS)
    # Preserve links and fragments used by earlier reports and bookmarks.
    ids = sorted(set(re.findall(r'\bid="([^"]+)"', full)) - {'main'})
    css_version = hashlib.sha256((ROOT / 'assets/site.css').read_bytes()).hexdigest()[:12]
    alias = '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="description" content="Project TODO"><title>Project TODO · AI2AI Duplex</title><link rel="canonical" href="../todo.html"><link rel="stylesheet" href="../assets/site.css?v=' + css_version + '"></head><body><header class="site-nav"><div class="nav-inner"><a class="brand" href="../index.html">AI2AI Duplex</a>' + project_tabs('todo', '../') + '</div></header><main id="main" class="container"><h1>Project TODO</h1><p><a href="../todo.html">Open the project TODO.</a></p>' + ''.join('<span hidden id="' + key + '"></span>' for key in ids) + '</main><script>location.replace("../todo.html"+location.hash);</script></body></html>\n'
    (ROOT / 'experiments/question-plan.html').write_text(alias)


def build_log():
    log = read(DATA / 'daily-log.json')
    body = '<header class="hero"><h1>Daily log</h1></header><section class="section" id="log"><ul class="brief"><li>Recent work is listed first, with examples and results linked below.</li><li>Earlier entries cover selected milestones from existing reports.</li></ul>'
    for day in log['days']:
        body += '<section class="stage" id="day-' + day['date'] + '"><h2 class="log-date">' + e(day['date']) + '</h2>' + bullets(day['items']) + '</section>'
    body += '</section><section class="section" id="appendix"><h2>Appendix</h2><details id="question-complexity"><summary>How we added connections between facts</summary><ul><li>Codex selected earlier passages that could support a natural question connecting two facts.</li><li>Local model prompts received the full earlier transcript, a checked pair of passages, or short fact cards.</li><li>Reader controls removed each fact group or supplied it alone to test whether both were needed.</li><li>Several questions still admit shortcuts, so this is not a certified multi-hop benchmark.</li></ul>'
    qs = read(ROOT / 'research/question-pilot/questions.json')
    examples = [('P-EN-handoff', 'Identify a person, then recover their promise', 'First identify who offered to combine the sections, then find when that person expected the search interface to be ready.'), ('P-TS-target-change', 'Compare an earlier plan with its revision', 'Compare the earlier target ages of 16–45 with the later requirement for customers aged 40 and above.')]
    for key, title, note in examples:
        q = next(q for q in qs if q['id'] == key)
        body += '<article class="catalog-question"><h3>' + e(title) + '</h3><ul><li>' + e(note) + '</li><li><strong>Question:</strong> ' + e(q['question']) + '</li><li><strong>Source-based answer:</strong> ' + e(q['reference_answer']) + '</li><li><a href="experiments/question-pilot.html#' + key + '">Question and source review</a></li></ul></article>'
    body += '<ul><li><a href="experiments/question-pilot.html#reader">See the evidence-removal reader controls and their limits.</a></li><li><a href="experiments/question-expansion.html#harder-questions">See the question-generation literature review.</a></li></ul></details><details id="checks-and-next-tests"><summary>What the latest checks establish</summary><ul><li>The twenty-question reader study uses manual transcripts and Codex judgments, rather than streaming ASR or independent human ratings.</li><li>Full transcripts yield 13 complete answers, while the current notes plus new speech yield four.</li><li>The notes need better task owners, decision updates and retention of earlier rules before speech tests.</li><li>The proposed timing and work-content comparisons have not run.</li><li><a href="experiments/question-checks.html">Read all source evidence and answer judgments.</a></li><li><a href="todo.html#thinking-design">Read the when/what-to-think design and ten-paper review.</a></li></ul></details><details id="resources"><summary>Resources and detailed records</summary><ul><li>This page and navigation edit use zero GPUs, with no GPU roles, shared components or GPU dependencies.</li><li>Maximum active GPUs for this edit is zero, and no experiment is rerun.</li><li><a href="experiments/question-checks.html#inspect">Latest reader outputs and scoring facts</a></li><li><a href="experiments/question-checks.html#teacher">Teacher-data curation</a></li><li><a href="experiments/question-audio.html">All question recordings and per-clip provenance</a></li><li><a href="research/project-progress/daily-log.json">Saved daily entries</a></li></ul></details></section>'
    document('daily-log.html', 'Daily log', 'log', body)


def main():
    build_plan()
    build_log()
    print('Built project TODO, daily log and the stable former TODO URL.')


if __name__ == '__main__':
    main()
