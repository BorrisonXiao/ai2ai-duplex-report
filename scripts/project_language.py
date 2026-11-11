"""Use the project term in prose while preserving recorded prompts and outputs."""
import re
from html.parser import HTMLParser

THINKER_REPORT_PAGES = {
    'daily-log.html', 'todo.html', 'study-progress.html', 'what-to-think.html',
    'context-assistance.html', 'experiments/index.html',
    'experiments/answering-results.html', 'experiments/full-answering-results.html',
    'experiments/structured-notes.html', 'experiments/question-expansion.html',
    'experiments/question-overview.html', 'experiments/question-checks.html',
    'experiments/question-scale.html', 'experiments/ami-questions.html',
    'experiments/question-pilot.html',
}


def thinker_text(text):
    """Name the S2 role consistently without renaming people who read a report."""
    def noun(match):
        before = text[max(0, match.start()-14):match.start()].lower()
        if re.search(r'(?:human|screen|interested)\s+$', before):
            return match[0]
        value = 'thinkers' if match[0].lower().endswith('s') else 'thinker'
        return value.upper() if match[0].isupper() else value.capitalize() if match[0][0].isupper() else value
    text = re.sub(r'\breaders?\b', noun, text, flags=re.I)
    text = re.sub(r'\breactive reading of\b', 'reactive thinking with', text, flags=re.I)
    text = re.sub(r'\breactive reading\b', 'reactive thinking', text, flags=re.I)
    return text


class _ThinkerProse(HTMLParser):
    """Patch text spans only; markup and verbatim experiment blocks stay exact."""
    protected_tags = {'script', 'style', 'pre', 'code', 'blockquote', 'textarea', 'cite', 'q'}
    protected_classes = {'native', 'prompt', 'source', 'transcript', 'transcript-text',
                         'utterance', 'model-output', 'answer-text', 'code-block'}
    void_tags = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link',
                 'meta', 'param', 'source', 'track', 'wbr'}

    def __init__(self, source):
        super().__init__(convert_charrefs=False)
        self.source = source
        self.offsets = [0]
        for match in re.finditer('\n', source):
            self.offsets.append(match.end())
        self.stack = []
        self.edits = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = set((attrs.get('class') or '').split())
        parent = self.stack[-1][1] if self.stack else False
        paper = tag == 'a' and any(domain in (attrs.get('href') or '') for domain in
                                  ('arxiv.org', 'aclanthology.org', 'openreview.net', 'doi.org'))
        protected = parent or tag in self.protected_tags or bool(classes & self.protected_classes) or paper
        if not protected:
            original = self.get_starttag_text()
            changed = re.sub(r'''(\b(?:alt|title|aria-label)\s*=\s*)(["'])(.*?)\2''',
                             lambda m: m[1]+m[2]+thinker_text(m[3])+m[2], original,
                             flags=re.S|re.I)
            if changed != original:
                line, column = self.getpos()
                start = self.offsets[line-1] + column
                self.edits.append((start, start+len(original), changed))
        if tag not in self.void_tags:
            self.stack.append((tag, protected))

    def handle_startendtag(self, tag, attrs):
        depth = len(self.stack)
        self.handle_starttag(tag, attrs)
        del self.stack[depth:]

    def handle_endtag(self, tag):
        for i in range(len(self.stack)-1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break

    def handle_data(self, text):
        if self.stack and self.stack[-1][1]:
            return
        parts = re.split(r'(“[^”]*”|"[^"\n]*"|`[^`]*`)', text)
        value = ''.join(part if i % 2 else thinker_text(part) for i, part in enumerate(parts))
        if value != text:
            line, column = self.getpos()
            start = self.offsets[line-1] + column
            self.edits.append((start, start+len(text), value))


def thinker_prose(source):
    parser = _ThinkerProse(source)
    parser.feed(source)
    for start, end, value in reversed(parser.edits):
        source = source[:start] + value + source[end:]
    return source


def prethinking_prose(source):
    def replace(text):
        text = re.sub(r'\bpre-thinking\b', lambda m: 'Amortized thinking' if m[0][0].isupper() else 'amortized thinking', text, flags=re.I)
        text = re.sub(r'\b([Aa]) (?=[Aa]mortized thinking\b)', lambda m: 'An ' if m[1]=='A' else 'an ', text)
        return text
    pieces = []
    cursor = 0
    for match in re.finditer(r'<(?P<tag>script|style|pre|code|blockquote)\b[^>]*>.*?</(?P=tag)>|“[^”]*”|<[^>]+>', source, flags=re.S | re.I):
        pieces.extend([replace(source[cursor:match.start()]), match[0]])
        cursor = match.end()
    pieces.append(replace(source[cursor:]))
    return ''.join(pieces)
