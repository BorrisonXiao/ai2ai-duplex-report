#!/usr/bin/env python3
"""Check offline/live proposal math, transitions, navigation and responsive layout."""
import argparse
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--base-url')
    parser.add_argument('--chromium',default=str(ROOT.parent/'cache/playwright/chromium-1243/chrome-linux64/chrome'))
    parser.add_argument('--output',type=Path,default=ROOT.parent/'.migration/updates/2026-10-10-prethinking/browser-validation')
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    base=args.base_url or ROOT.as_uri()+'/'
    checks=[]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=args.chromium,headless=True)
        for name,width,height,theme in [('desktop',1366,900,'light'),('mobile',390,844,'light'),('narrow',320,740,'light'),('dark',1366,900,'dark')]:
            context=browser.new_context(viewport={'width':width,'height':height},color_scheme=theme,reduced_motion='reduce')
            page=context.new_page();errors=[];requests=[]
            page.on('pageerror',lambda err:errors.append(str(err)))
            page.on('request',lambda req:requests.append(req.url))
            page.goto(base+'index.html',wait_until='load')
            page.locator('[aria-label="Literature review sub-tabs"] a').filter(has_text='Pre-thinking proposal').click()
            page.wait_for_url('**/prethinking.html')
            page.wait_for_function('!!window.MathJax?.startup?.promise')
            page.evaluate('async()=>await window.MathJax.startup.promise')
            assert page.locator('[aria-label="Literature review sub-tabs"] [aria-current]').inner_text()=='Pre-thinking proposal'
            assert page.locator('.equation mjx-container').count()==5
            assert page.locator('[data-mml-node="merror"]').count()==0
            assert not page.evaluate('document.documentElement.scrollWidth>innerWidth+1')
            page.screenshot(path=str(args.output/(name+'.png')))
            page.locator('#proposal-distillation').scroll_into_view_if_needed()
            page.screenshot(path=str(args.output/(name+'-math.png')))
            for step in ['1','3','5']:
                page.locator('#arrival-step').fill(step);page.locator('#arrival-step').dispatch_event('input')
                for kind in ['related','correction','other']:
                    page.locator('#arrival-kind').select_option(kind)
                    content=page.locator('#arrival-events').inner_text()
                    assert 'Step '+step+': The assistant-directed request preempts' in content
                    assert ('A completed note records' in content)==(int(step)>2)
                    if kind=='correction':assert 'Monday correction' in content
                    if kind=='other':assert 'different request' in content
            page.locator('#arrival-demo').scroll_into_view_if_needed()
            page.screenshot(path=str(args.output/(name+'-arrival.png')))
            page.locator('a.citation[href="#ref-audio-opd"]').first.click()
            assert page.locator('#ref-audio-opd summary').is_visible()
            if not page.locator('#ref-audio-opd').evaluate('(el)=>el.open'):
                page.locator('#ref-audio-opd summary').click()
            assert page.locator('#ref-audio-opd .paper-note').is_visible()
            table=page.locator('#proposal-data').locator('xpath=..')
            if width<=390:
                assert table.evaluate('(el)=>el.scrollWidth>el.clientWidth')
                table.evaluate('(el)=>el.scrollLeft=el.scrollWidth')
                assert table.evaluate('(el)=>el.scrollLeft>0')
            assert not errors,errors
            if not args.base_url:
                assert all(u.startswith('file:') or u.startswith('data:') for u in requests),requests
            page.locator('[aria-label="Literature review sub-tabs"] a').filter(has_text='Context-aware assistance').click()
            assert page.locator('[aria-label="Literature review sub-tabs"] [aria-current]').inner_text()=='Context-aware assistance'
            page.locator('[aria-label="Literature review sub-tabs"] a').filter(has_text='Pre-thinking proposal').click()
            checks.append(dict(viewport=name,math_equations=5,math_errors=0,arrival_cases=9,navigation=True,local_renderer=True,no_page_overflow=True,js_errors=errors))
            context.close()
        browser.close()
    result=dict(status='pass',base_url=base,checks=checks,new_inference_gpus=0)
    target=args.output/('live-validation.json' if args.base_url else 'validation.json')
    target.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
