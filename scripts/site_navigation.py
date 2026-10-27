"""Shared navigation for the literature, experiments and proposal collections."""
from html import escape


def tabs(items, current, label, prefix="", css="review-tabs"):
    return '<nav class="' + css + '" aria-label="' + label + '">' + ''.join(
        '<a href="' + escape(prefix + url, quote=True) + '"' +
        (' aria-current="page"' if key == current else '') + '>' + text + '</a>'
        for key, text, url in items) + '</nav>'


def project_tabs(current, prefix=""):
    return tabs([
        ("literature", "Literature Review", "index.html"),
        ("experiments", "Experiments", "experiments/index.html"),
        ("proposal", "Proposal", "proposals/index.html"),
    ], current, "Project tabs", prefix, "nav-links")


BENCHMARKS = [
    ('mpbench', 'MP-Bench', 'mpbench.html'),
    ('msi', 'MSI-Bench', 'msi-bench.html'),
    ('multitalk', 'MultiTalkBench', 'multitalk-bench.html'),
    ('fdb2', 'Full-Duplex-Bench v2', 'full-duplex-bench-v2.html'),
    ('fdb', 'Full-Duplex-Bench v3', 'full-duplex-bench.html'),
]


def review_tabs(current):
    if current == 'prethinking':
        return proposal_tabs(current)
    benchmark = current in {key for key, _, _ in BENCHMARKS}
    result = tabs([
        ('landscape', 'Duplex Overview', 'index.html#literature-review'),
        ('context', 'Conversation context', 'context-assistance.html'),
        ('benchmarks', 'Benchmarks', 'benchmarks.html'),
    ], 'benchmarks' if benchmark else current, 'Literature review sub-tabs')
    if benchmark:
        result += tabs(BENCHMARKS, current, 'Benchmark pages', css='review-tabs secondary-tabs')
    return result


DUPLEX_PAGES = [
    ('duplex', 'Overview', 'duplexomni.html'),
    ('basic', 'S1 speech', 'single-request.html'),
    ('replay', 'Interruption replay', 'interruption.html'),
    ('evidence', 'Interruption results', 'natural-study.html'),
    ('s2', 'S2 reasoning', 's2-single.html'),
    ('reproduction', 'S1 reproduction', 's1-reproduction.html'),
    ('archive', 'Earlier studies', 'archive.html'),
]


AMI_PAGES = [
    ('ami-overview', 'Overview &amp; stats', 'question-overview.html'),
    ('ami-library', 'All question audio', 'question-audio.html'),
    ('ami-scale', 'Larger batch', 'question-scale.html'),
    ('ami-pilot', 'Question/audio pilot', 'question-pilot.html'),
    ('ami-expansion', 'Earlier expansion', 'question-expansion.html'),
    ('ami-original', 'First pilot', 'ami-questions.html'),
    ('ami-audio', 'TTS comparison', 'ami-question-audio.html'),
    ('ami-plan', 'TODO &amp; plan', 'question-plan.html'),
]


def experiment_subtabs(current):
    duplex = current in {key for key, _, _ in DUPLEX_PAGES}
    ami = current in {key for key, _, _ in AMI_PAGES}
    parent = 'ami-library' if current in {'ami-library','ami-audio'} else ('ami' if ami else current)
    result = tabs([
        ('overview', 'All experiments', 'index.html'),
        ('duplex', 'DuplexOmni', 'duplexomni.html'),
        ('prethinking', 'Pre-thinking pilot', 'prethinking-pilot.html'),
        ('ami', 'AMI questions', 'question-overview.html'),
        ('ami-library', 'AMI question audio', 'question-audio.html'),
    ], 'duplex' if duplex else parent, 'Experiment sub-tabs')
    if duplex:
        result += tabs(DUPLEX_PAGES, current, 'DuplexOmni experiments', css='review-tabs secondary-tabs')
    if ami:
        result += tabs(AMI_PAGES, current, 'AMI question pages', css='review-tabs secondary-tabs')
    return result


def proposal_tabs(current, prefix=""):
    return tabs([
        ('overview', 'All proposals', 'proposals/index.html'),
        ('prethinking', 'Pre-thinking', 'prethinking.html'),
    ], current, 'Proposal pages', prefix)
