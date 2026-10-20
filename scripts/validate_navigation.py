"""Check shared navigation on every native page and linked source viewer."""
import hashlib
import os
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

from build_navigation import ROOT, REVIEW_KEYS, EXPERIMENT_KEYS
from site_navigation import project_tabs, review_tabs, experiment_subtabs, proposal_tabs
from validate_site import Parser


def main():
    checked = 0
    css_hash = hashlib.sha256((ROOT/'assets/site.css').read_bytes()).hexdigest()[:12]
    for path in sorted(ROOT.rglob('*.html')):
        if any(part in {'preview', '.git', 'vendor', 'protocol-source'} for part in path.relative_to(ROOT).parts):
            continue
        text = path.read_text()
        if 'aria-label="Project tabs"' not in text:
            continue
        relative = path.relative_to(ROOT).as_posix()
        prefix = os.path.relpath(ROOT, path.parent).replace(os.sep, '/') + '/'
        if prefix == './': prefix = ''
        category = 'proposal' if relative == 'prethinking.html' or relative.startswith('proposals/') else 'experiments' if relative.startswith(('experiments/', 'research/')) else 'literature'
        expected = project_tabs(category, prefix)
        assert text.count('aria-label="Project tabs"') == 1, relative
        assert expected in text, (relative, 'stale project tabs')
        if path.parent == ROOT and path.name in REVIEW_KEYS:
            assert review_tabs(REVIEW_KEYS[path.name]) in text, relative
            assert 'Pre-thinking proposal</a>' not in re.search(r'<nav[^>]*aria-label="Literature review sub-tabs"[^>]*>.*?</nav>', text, re.S)[0]
        elif path.parent == ROOT/'experiments':
            assert experiment_subtabs(EXPERIMENT_KEYS.get(path.name, 'archive')) in text, relative
            assert '>AMI questions</a>' in text and '>AMI question audio</a>' in text, relative
        elif category == 'proposal':
            assert proposal_tabs('prethinking' if path.name == 'prethinking.html' else 'overview', prefix) in text, relative
        assert prefix+'assets/site.css?v='+css_hash in text, (relative, 'stale stylesheet')
        # All navigation links must work beneath the GitHub Pages project prefix.
        for nav in re.findall(r'<nav\b[^>]*>.*?</nav>', text, re.S):
            parser = Parser(); parser.feed(nav)
            for _, href in parser.links:
                parts = urlsplit(href)
                if parts.scheme or parts.netloc: continue
                assert not parts.path.startswith('/'), (relative, href)
                target = path.parent/unquote(parts.path) if parts.path else path
                if target.is_dir(): target = target/'index.html'
                assert target.is_file(), (relative, href)
                if parts.fragment:
                    parsed = Parser(); parsed.feed(target.read_text())
                    assert parts.fragment in parsed.ids, (relative, href)
        checked += 1
    assert checked >= 48, checked
    print('PASS:', checked, 'pages have current collection menus, correct active tabs, visible AMI links and working navigation.')


if __name__ == '__main__':
    main()
