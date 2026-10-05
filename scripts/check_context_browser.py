#!/usr/bin/env python3
"""Render the narrowed review and test real sub-tab navigation in Chromium."""
import argparse
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--chromium')
    parser.add_argument('--output',type=Path,default=ROOT/'preview/context-assistance')
    args=parser.parse_args()
    from playwright.sync_api import sync_playwright
    args.output.mkdir(parents=True,exist_ok=True)
    checks=[]
    with sync_playwright() as p:
        opts={'headless':True}
        if args.chromium: opts['executable_path']=args.chromium
        browser=p.chromium.launch(**opts)
        for name,width,height,scheme in [('desktop',1366,900,'light'),('mobile',390,844,'light'),('narrow',320,740,'light'),('dark',1366,900,'dark')]:
            context=browser.new_context(viewport={'width':width,'height':height},color_scheme=scheme,reduced_motion='reduce')
            page=context.new_page()
            errors=[]
            requests=[]
            page.on('pageerror',lambda err:errors.append(str(err)))
            page.on('request',lambda r:requests.append(r.url))
            page.goto((ROOT/'index.html').as_uri(),wait_until='load')
            page.locator('[aria-label="Literature review sub-tabs"] a').filter(has_text='Context-aware assistance').click()
            page.wait_for_url('**/context-assistance.html')
            assert page.locator('[aria-label="Literature review sub-tabs"] [aria-current="page"]').inner_text() == 'Context-aware assistance'
            assert page.evaluate('document.documentElement.scrollWidth') <= width
            page.screenshot(path=str(args.output/(name+'.png')))
            page.locator('#context-paper-figures summary').click()
            page.evaluate("document.querySelectorAll('img').forEach(i=>i.loading='eager')")
            page.wait_for_function('Array.from(document.images).every(i=>i.complete && i.naturalWidth>0)')
            assert page.locator('figure').count()==7 and page.locator('table').count()==6
            for ident,suffix in [('scope','scope'),('context-performance','results'),('context-paper-figures','papers')]:
                target=page.locator('#'+ident)
                target.scroll_into_view_if_needed()
                target.screenshot(path=str(args.output/(name+'-'+suffix+'.png')),style='.site-nav { visibility: hidden !important; }')
            field=page.locator('#context-benchmarks-filter')
            field.fill('MSI-Bench')
            assert page.locator('#context-benchmarks-count').inner_text()=='1 of 9 entries'
            field.fill('nothing-matches-1234')
            assert page.locator('#context-benchmarks-empty').is_visible()
            field.fill('')
            assert page.locator('#context-benchmarks-count').inner_text()=='9 of 9 entries'
            page.locator('#context-notes details summary').first.click()
            assert page.locator('#context-notes details').first.get_attribute('open') is not None
            assert not errors and all(x.startswith(('file:','data:')) for x in requests)
            page.locator('[aria-label="Literature review sub-tabs"] a').filter(has_text='Duplex landscape').click()
            page.wait_for_url('**/index.html#literature-review')
            assert page.locator('[aria-label="Literature review sub-tabs"] [aria-current="page"]').inner_text()=='Duplex landscape'
            assert page.evaluate('document.documentElement.scrollWidth') <= width
            checks.append(dict(view=name,width=width,theme=scheme,sub_tab_navigation='passed',filters='passed',figures='passed',page_wide_overflow=False,external_requests=0,javascript_errors=errors))
            context.close()
        browser.close()
    (args.output/'browser-validation.json').write_text(json.dumps(dict(status='passed',checks=checks),indent=2)+'\n')
    print('PASS: both sub-tab routes; desktop / 390px / 320px / dark; figures, filters and paper notes; no overflow, JavaScript errors or external assets.')

if __name__=='__main__':
    main()
