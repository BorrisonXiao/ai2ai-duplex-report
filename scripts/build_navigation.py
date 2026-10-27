"""Build collection pages and refresh navigation without rerunning experiments.

Run this LAST after any individual page generator. Data, audio, source snapshots,
code excerpts and recorded model outputs are left intact.
"""
from html import escape
import hashlib
import os
from pathlib import Path
import re

from site_navigation import (
    project_tabs, review_tabs, experiment_subtabs, proposal_tabs,
)
from project_language import prethinking_prose

ROOT = Path(__file__).resolve().parents[1]
REVIEW_KEYS = {
    'index.html': 'landscape', 'context-assistance.html': 'context',
    'benchmarks.html': 'benchmarks', 'mpbench.html': 'mpbench',
    'msi-bench.html': 'msi', 'multitalk-bench.html': 'multitalk',
    'full-duplex-bench-v2.html': 'fdb2', 'full-duplex-bench.html': 'fdb',
}
EXPERIMENT_KEYS = {
    'index.html': 'overview', 'duplexomni.html': 'duplex',
    'single-request.html': 'basic', 's1-investigation.html': 'basic',
    'trajectory.html': 'replay', 'interruption.html': 'replay',
    'natural-study.html': 'evidence', 's2-single.html': 's2',
    's1-reproduction.html': 'reproduction', 'prethinking-pilot.html': 'prethinking',
    'ami-questions.html': 'ami-original', 'ami-question-audio.html': 'ami-audio',
    'question-expansion.html': 'ami-expansion',
    'question-pilot.html': 'ami-pilot', 'question-scale.html': 'ami-scale',
    'question-audio.html': 'ami-library', 'question-overview.html': 'ami-overview',
}
SUBNAV_LABELS = (
    'Literature review sub-tabs', 'Benchmark pages', 'Experiment sub-tabs',
    'DuplexOmni experiments', 'Proposal pages', 'AMI question pages',
)


def cards(items):
    return '<div class="card-grid">' + ''.join(
        '<article class="card"><h3><a href="' + escape(url) + '">' +
        escape(title) + '</a></h3><p>' + escape(description) + '</p></article>'
        for title, description, url in items) + '</div>'


def section(title, description, items):
    return '<section class="collection-section"><h2>' + title + '</h2><p>' + description + '</p>' + cards(items) + '</section>'


def collection(path, category, title, lead, body, subnav, prefix=''):
    page = '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="color-scheme" content="light dark"><meta name="description" content="' + escape(lead, quote=True) + '"><title>' + title + ' · AI2AI Duplex</title><link rel="stylesheet" href="' + prefix + 'assets/site.css"></head><body><a class="skip-link" href="#main">Skip to content</a><header class="site-nav"><div class="nav-inner"><a class="brand" href="' + prefix + 'index.html">AI2AI Duplex</a>' + project_tabs(category, prefix) + '</div></header><main id="main"><div class="container">' + subnav + '<header class="hero"><h1>' + title + '</h1><p class="lede">' + lead + '</p></header>' + body + '</div></main></body></html>\n'
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(page)


def build_collections():
    duplex = [
        ('S1 speech', 'Basic spoken-answer tests with the fast speech model (S1), without the reasoning model (S2).', 'single-request.html'),
        ('Interruption replay', 'Listen to a human question and a clarification that interrupts the model’s speech.', 'interruption.html'),
        ('Interruption results', 'Stopping delay, discarded audio, transcripts and limits of the one-case demonstration.', 'natural-study.html'),
        ('S2 reasoning', 'Arithmetic and outlet-store questions with a separate reasoning model; compare model-triggered and forced calls.', 's2-single.html'),
        ('S1 reproduction', 'Working and failed inference callers, source code and commands to reproduce the selected example.', 's1-reproduction.html'),
        ('Earlier studies', 'Earlier failures and timing tests, kept with their original evidence and limitations.', 'archive.html'),
    ]
    ami = [
        ('Question overview and aggregate statistics', 'All retained questions, insertion-time distributions, source coverage and audio coverage.', 'question-overview.html'),
        ('All question audio', 'All 105 question events, with short source excerpts and original-voice comparisons.', 'question-audio.html'),
        ('Larger AMI batch', 'Forty additional questions from twenty more meetings, with source checks and recorded Codex edits.', 'question-scale.html'),
        ('Question/audio pilot', 'Earlier checkpoints, reader controls and ten inserted questions in eight requester voices.', 'question-pilot.html'),
        ('More meeting questions', 'Four new AMI meetings and two earnings calls, checked with a 30B Instruct reader and document retrieval fixtures.', 'question-expansion.html'),
        ('AMI questions', 'Questions that require earlier meeting details, with supporting transcripts and a review of generated answers.', 'ami-questions.html'),
        ('AMI question audio', 'Compare three TTS models inserting the same questions into the meeting in the requester’s voice.', 'ami-question-audio.html'),
    ]
    pilot = [('Pre-thinking pilot', 'A preliminary study of preparing for likely requests while listening to a group conversation.', 'prethinking-pilot.html')]
    collection('experiments/index.html', 'experiments', 'Experiments',
        'Speech-model tests, meeting questions and early work on reasoning during conversation.',
        section('Project progress', 'The project plan and daily work record.', [
            ('Project TODO', 'The four project stages and the next pre-thinking experiments.', '../todo.html'),
            ('Daily log', 'One-sentence updates with links to results and examples.', '../daily-log.html')]) +
        section('DuplexOmni', 'Tests of speech generation, interruption handling and reasoning with the DuplexOmni model.', [
            ('DuplexOmni experiments', 'Start with the overview, then choose S1 speech, interruption or S2 reasoning tests.', 'duplexomni.html')]) +
        section('Meeting questions', 'Text questions and synthetic speech based on the AMI Meeting Corpus.', ami) +
        section('Pre-thinking', 'Preparing useful reasoning before a request arrives.', pilot),
        experiment_subtabs('overview'), '../')
    collection('experiments/duplexomni.html', 'experiments', 'DuplexOmni experiments',
        'S1 handles streaming speech. S2 is a separate reasoning model that can send guidance to S1. These tests examine their speech, interruption and reasoning behavior.',
        section('Speech and reasoning tests', 'The pages report both working examples and failures. A successful example does not establish general reliability.', duplex),
        experiment_subtabs('duplex'), '../')
    collection('benchmarks.html', 'literature', 'Speech benchmarks',
        'Reviews of multi-party listening, turn-taking and full-duplex speech evaluation. Reported paper results are separate from local experiments.',
        section('Multi-party speech', 'Understanding who said what, using conversation history and deciding when to respond.', [
            ('MP-Bench', 'Multi-party understanding, discussion, games and turn-taking, with original audio examples.', 'mpbench.html'),
            ('MSI-Bench', 'Speaker-specific instructions and responses in multi-party audio.', 'msi-bench.html'),
            ('MultiTalkBench', 'Long multi-party conversations in English and Chinese, with audio and scoring details.', 'multitalk-bench.html')]) +
        section('Full-duplex interaction', 'Live conversation, corrections, interruptions and tool use.', [
            ('Full-Duplex-Bench v2', 'The live multi-turn evaluation protocol, task prompts and reported results.', 'full-duplex-bench-v2.html'),
            ('Full-Duplex-Bench v3', 'Tool use during speech with hesitations, corrections and other disfluencies.', 'full-duplex-bench.html')]),
        review_tabs('benchmarks'))
    collection('proposals/index.html', 'proposal', 'Proposal',
        'Research plans and proposed experiments for speech assistants.',
        section('Pre-thinking', 'Preparing for a likely request while continuing to listen.', [
            ('Thinking before the request', 'Motivation, related work, model design and evaluation plan. This is a proposal, not a completed result.', '../prethinking.html'),
            ('Preliminary experiment', 'Read the separate pilot and its measured results under Experiments.', '../experiments/prethinking-pilot.html')]),
        proposal_tabs('overview', '../'), '../')


# Editorial changes apply only to prose, never code, scripts or model data.
PLAIN_LABELS = {
    'Duplex landscape': 'Duplex Overview',
    'duplex landscape': 'duplex overview',
    'Context-aware Assistance': 'Conversation Context',
    'Context-aware assistance': 'Conversation context',
    'context-aware assistance': 'conversation-based assistance',
    'Context assistance': 'Conversation context',
    'Reasoning while listening, revising while speaking.': 'Full-duplex speech models',
    'Research landscape · September 2026': 'Duplex overview · September 2026',
    'Listen to the conversation. Understand the request.': 'Using conversation history to answer requests',
    'Conversation context from multi-party speech: speaker-specific memory, instruction disambiguation, clarification and appropriate participation.': 'How speech assistants use earlier turns, speaker identity and clarification to understand a request.',
    'Preparing while a group talks.': 'Preparing for requests during conversation',
    'Questions that need the meeting so far.': 'Questions about earlier meeting details',
    'S1 yields and answers the clarification.': 'S1 stops speaking and answers the clarification',
    'S1 asks S2 and speaks the result.': 'S2 reasoning and spoken answers',
    'Superseded diagnostics.': 'Earlier experiments',
}


def simplify_prose(source):
    pieces = re.split(r'(<(?:script|style|pre|code)\b[^>]*>.*?</(?:script|style|pre|code)>)', source, flags=re.S | re.I)
    for i in range(0, len(pieces), 2):
        for old, new in PLAIN_LABELS.items():
            pieces[i] = pieces[i].replace(old, new)
    return ''.join(pieces)


def page_category(relative):
    if relative in {'todo.html', 'what-to-think.html', 'notation.html', 'experiments/question-plan.html', 'experiments/question-checks.html'}:
        return 'todo'
    if relative == 'daily-log.html':
        return 'log'
    if relative == 'prethinking.html' or relative.startswith('proposals/'):
        return 'proposal'
    return 'experiments' if relative.startswith(('experiments/', 'research/')) else 'literature'


def refresh_page(path, original, navigation_only=False):
    """Apply the shared navigation to one document without changing its body."""
    relative = path.relative_to(ROOT).as_posix()
    native = path.parent == ROOT or path.parent in {ROOT/'experiments', ROOT/'proposals'}
    if not native and 'aria-label="Project tabs"' not in original:
        return original
    prefix = os.path.relpath(ROOT, path.parent).replace(os.sep, '/') + '/'
    if prefix == './':
        prefix = ''
    category = page_category(relative)
    project = project_tabs(category, prefix)
    page = re.sub(r'<nav\b[^>]*aria-label="Project tabs"[^>]*>.*?</nav>', lambda _: project, original, flags=re.S)
    if native and 'aria-label="Project tabs"' not in page:
        header = '<header class="site-nav"><div class="nav-inner"><a class="brand" href="' + prefix + 'index.html">AI2AI Duplex</a>' + project + '</div></header>'
        page = page.replace('<body>', '<body>' + header, 1)
    subnav = None
    if category in {'todo', 'log'}:
        pattern = r'<nav\b[^>]*aria-label="(?:' + '|'.join(SUBNAV_LABELS) + r')"[^>]*>.*?</nav>'
        page = re.sub(pattern, '', page, flags=re.S)
    elif path.parent == ROOT and path.name in REVIEW_KEYS:
        subnav = review_tabs(REVIEW_KEYS[path.name])
    elif path.parent == ROOT/'experiments':
        subnav = experiment_subtabs(EXPERIMENT_KEYS.get(path.name, 'archive'))
    elif category == 'proposal':
        subnav = proposal_tabs('prethinking' if path.name == 'prethinking.html' else 'overview', prefix)
    if subnav is not None:
        pattern = r'<nav\b[^>]*aria-label="(?:' + '|'.join(SUBNAV_LABELS) + r')"[^>]*>.*?</nav>'
        # Always put collection menus before the page title, including replays.
        page = re.sub(pattern, '', page, flags=re.S)
        page = page.replace('<div class="container collection-nav"></div>', '')
        page = page.replace('<div class="container"></div>', '')
        page = page.replace('</header>', '</header><div class="container collection-nav">' + subnav + '</div>', 1)
    if native and not navigation_only:
        page = simplify_prose(page)
    if relative in {'todo.html', 'daily-log.html', 'prethinking.html', 'experiments/prethinking-pilot.html', 'experiments/question-checks.html'}:
        page = prethinking_prose(page)
    css = prefix + 'assets/site.css'
    digest = hashlib.sha256((ROOT/'assets/site.css').read_bytes()).hexdigest()[:12]
    pattern = r'href="' + re.escape(css) + r'(?:\?[^"]*)?"'
    if re.search(pattern, page):
        page = re.sub(pattern, 'href="' + css + '?v=' + digest + '"', page)
    else:
        page = page.replace('</head>', '<link rel="stylesheet" href="' + css + '?v=' + digest + '"></head>', 1)
    return page


def refresh_pages(navigation_only=False):
    changed = []
    for path in sorted(ROOT.rglob('*.html')):
        if any(part in {'preview', '.git', 'vendor', 'protocol-source'} for part in path.relative_to(ROOT).parts):
            continue
        original = path.read_text()
        page = refresh_page(path, original, navigation_only)
        if page != original:
            path.write_text(page)
            changed.append(path.relative_to(ROOT).as_posix())
    return changed


def main():
    build_collections()
    changed = refresh_pages()
    print('Built 4 collection pages; refreshed navigation/labels in', len(changed), 'pages.')


if __name__ == '__main__':
    main()
