"""Shared literature-review sub-tabs; retain the existing landscape URL."""
def review_tabs(current):
    items = [('landscape', 'Duplex landscape', 'index.html#literature-review'), ('context', 'Context-aware assistance', 'context-assistance.html')]
    return '<nav class="review-tabs" aria-label="Literature review sub-tabs">' + ''.join('<a href="' + url + '"' + (' aria-current="page"' if key == current else '') + '>' + label + '</a>' for key, label, url in items) + '</nav>'
