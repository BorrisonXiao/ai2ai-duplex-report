"""Shared collection navigation and stable literature-review sub-tabs."""
def project_tabs(current, prefix=""):
    items = [("literature", "Literature review", "index.html"), ("experiments", "Experiments", "experiments/index.html")]
    return '<nav class="nav-links" aria-label="Project tabs">' + ''.join('<a href="' + prefix + url + '"' + (' aria-current="page"' if key == current else '') + '>' + label + '</a>' for key, label, url in items) + '</nav>'


def review_tabs(current):
    items = [('landscape', 'Duplex landscape', 'index.html#literature-review'), ('context', 'Context-aware assistance', 'context-assistance.html')]
    return '<nav class="review-tabs" aria-label="Literature review sub-tabs">' + ''.join('<a href="' + url + '"' + (' aria-current="page"' if key == current else '') + '>' + label + '</a>' for key, label, url in items) + '</nav>'


def experiment_subtabs(current):
    items = [('overview', 'All experiments', 'index.html'),
             ('replay', 'Current replay', 'interruption.html'),
             ('reproduction', 'S1 reproduction report', 's1-reproduction.html'),
             ('evidence', 'Interruption evidence', 'natural-study.html')]
    return '<nav class="review-tabs" aria-label="Experiment sub-tabs">' + ''.join('<a href="' + url + '"' + (' aria-current="page"' if key == current else '') + '>' + label + '</a>' for key, label, url in items) + '</nav>'
