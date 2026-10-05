"""Shared collection navigation and stable literature-review sub-tabs."""
def project_tabs(current, prefix=""):
    items = [("literature", "Literature review", "index.html"), ("experiments", "Experiments", "experiments/index.html")]
    return '<nav class="nav-links" aria-label="Project tabs">' + ''.join('<a href="' + prefix + url + '"' + (' aria-current="page"' if key == current else '') + '>' + label + '</a>' for key, label, url in items) + '</nav>'


def review_tabs(current):
    items = [('landscape', 'Duplex landscape', 'index.html#literature-review'), ('context', 'Context-aware assistance', 'context-assistance.html')]
    return '<nav class="review-tabs" aria-label="Literature review sub-tabs">' + ''.join('<a href="' + url + '"' + (' aria-current="page"' if key == current else '') + '>' + label + '</a>' for key, label, url in items) + '</nav>'
