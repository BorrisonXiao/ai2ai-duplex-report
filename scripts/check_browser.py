#!/usr/bin/env python3
"""Check local desktop/mobile/theme rendering, filters and expandable paper notes.

Requires Playwright and Chromium. No server or external requests are needed.
Use --chromium to choose an existing browser binary, otherwise Playwright's cache.
"""
import argparse
import json
from pathlib import Path
from report_content import PROFILES

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--chromium', help='Existing Chromium or headless-shell binary')
    parser.add_argument('--output', type=Path, default=ROOT / 'preview')
    args = parser.parse_args()
    from playwright.sync_api import sync_playwright
    args.output.mkdir(parents=True, exist_ok=True)
    checks = []
    with sync_playwright() as playwright:
        launch = {'headless': True}
        if args.chromium:
            launch['executable_path'] = args.chromium
        browser = playwright.chromium.launch(**launch)
        for name, width, height, scheme in [('desktop', 1366, 900, 'light'), ('mobile', 390, 844, 'light'), ('dark', 1366, 900, 'dark')]:
            context = browser.new_context(viewport={'width': width, 'height': height}, color_scheme=scheme, reduced_motion='reduce', device_scale_factor=1)
            page = context.new_page()
            errors, requests = [], []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.on('request', lambda request: requests.append(request.url))
            page.goto((ROOT / 'index.html').as_uri(), wait_until='load')
            page.evaluate("document.querySelectorAll('img').forEach(image => image.loading = 'eager')")
            page.wait_for_function("Array.from(document.images).every(image => image.complete && image.naturalWidth > 0)")
            assert not errors, errors
            assert all(url.startswith(('file:', 'data:')) for url in requests), requests
            dimensions = page.evaluate("({viewport: innerWidth, document: document.documentElement.scrollWidth, figures: document.querySelectorAll('figure').length, images: document.images.length, tables: document.querySelectorAll('table').length, projectTabs: document.querySelectorAll('[aria-label=\"Project tabs\"] a').length, background: getComputedStyle(document.body).backgroundColor})")
            assert dimensions['document'] <= width, dimensions
            assert (dimensions['figures'], dimensions['images'], dimensions['tables'], dimensions['projectTabs']) == (10+len(PROFILES), 9+len(PROFILES), 6+len(PROFILES), 1), dimensions
            page.screenshot(path=str(args.output / ('web-' + name + '.png')))
            for ident, suffix in [('architecture-minicpm', 'architecture'), ('profile-step3', 'performance'), ('profile-minicpm', 'multiparty'), ('architecture-duplexomni', 'duplexomni-architecture'), ('architecture-voicechat', 'voicechat-architecture'), ('profile-duplexomni', 'duplexomni-results'), ('profile-voicechat', 'voicechat-results'), ('architecture-thinkaloud', 'thinkaloud-architecture'), ('profile-thinkaloud-timing', 'thinkaloud-timing'), ('profile-thinkaloud-qa', 'thinkaloud-qa')]:
                target = page.locator('#' + ident)
                target.scroll_into_view_if_needed()
                target.screenshot(path=str(args.output / ('web-' + name + '-' + suffix + '.png')), style='.site-nav { visibility: hidden !important; }')
            field = page.locator('#systems-table-filter')
            field.fill('FLAIR')
            assert page.locator('#systems-table-count').inner_text() == '1 of 21 entries'
            field.fill('not-a-real-model-012345')
            assert page.locator('#systems-table-empty').is_visible()
            field.fill('')
            assert page.locator('#systems-table-count').inner_text() == '21 of 21 entries'
            details = page.locator('#paper-notes details').first
            details.locator('summary').click()
            assert details.get_attribute('open') is not None
            details.locator('summary').click()
            assert details.get_attribute('open') is None
            scrollable = page.locator('.plot-scroll').evaluate_all('(items) => items.filter(item => item.scrollWidth > item.clientWidth).length')
            assert scrollable == (9+len(PROFILES) if name == 'mobile' else 0), scrollable
            checks.append({'view': name, **dimensions, 'plot_regions_with_horizontal_pan': scrollable, 'filter_and_paper_notes': 'passed', 'javascript_errors': errors, 'external_requests': 0})
            context.close()
        browser.close()
    (args.output / 'browser-validation.json').write_text(json.dumps({'status': 'passed', 'checks': checks}, indent=2) + '\n')
    print('PASS: desktop/mobile/dark rendering, all local images, no page-wide overflow or external requests, working filters and paper notes.')


if __name__ == '__main__':
    main()
