#!/usr/bin/env python3
"""Check the MultiTalkBench preview in Chromium at desktop/mobile/theme sizes."""

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--chromium", help="Existing Chromium or headless-shell binary")
    parser.add_argument("--url", help="Deployed page URL; defaults to the local generated page")
    parser.add_argument("--output", type=Path, default=ROOT / "preview/multitalk-bench")
    args = parser.parse_args()
    from playwright.sync_api import sync_playwright

    args.output.mkdir(parents=True, exist_ok=True)
    checks = []
    views = [
        ("desktop", 1366, 900, "light"),
        ("mobile", 390, 844, "light"),
        ("narrow", 320, 760, "light"),
        ("dark", 1366, 900, "dark"),
    ]
    with sync_playwright() as playwright:
        launch = {"headless": True, "args": ["--autoplay-policy=no-user-gesture-required"]}
        if args.chromium:
            launch["executable_path"] = args.chromium
        browser = playwright.chromium.launch(**launch)
        for name, width, height, scheme in views:
            context = browser.new_context(
                viewport={"width": width, "height": height},
                color_scheme=scheme,
                reduced_motion="reduce",
                device_scale_factor=1,
            )
            page = context.new_page()
            errors, requests = [], []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.on("request", lambda request: requests.append(request.url))
            page.goto(args.url or (ROOT / "multitalk-bench.html").as_uri(), wait_until="load")
            assert page.title() == "MultiTalkBench Evaluation and Test Data — AI2AI Duplex"
            page.wait_for_function("window.MathJax && MathJax.typesetPromise && document.querySelectorAll('.equation mjx-container').length === 2")
            assert page.locator(".review-tabs a").count() == 8
            assert page.locator(".review-tabs a[aria-current='page']").inner_text() == "MultiTalkBench"
            assert page.locator("#benchmark-scope-table tr[data-benchmark='multitalk']").count() == 1
            assert page.locator("#audio-examples audio").count() == 2
            assert page.locator("#validation").inner_text().find("372 of 372 files present") >= 0
            assert page.locator("#validation").inner_text().find("No model evaluation is claimed") >= 0
            assert page.locator("#mtb-judge-calls tbody tr").count() == 6
            assert page.locator(".mtb-call").count() == 6
            assert "Gemma reads that written conversation six times" in page.locator("#evaluation-protocol").inner_text()
            assert "stronger and weaker replies" in page.locator("#simple-meeting").inner_text()
            assert "does not give the quality ratings" in page.locator("#explain-call1").inner_text()
            assert page.locator(".mtb-prompt").count() == 10
            assert "neither the transcript" in page.locator("#judge-retries").text_content()
            assert "without a participation multiplier" in page.locator("#paper-code-discrepancy").inner_text()
            page.evaluate("document.querySelectorAll('#judge-prompts details').forEach(el => el.open = true)")
            assert page.evaluate("document.documentElement.scrollWidth") <= width
            # Exercise intra-page prompt links and their complete message content.
            assert "Multi-Speaker State Tracking" in page.locator("#prompt-call2a pre").first.inner_text()
            assert "RETRY FORMAT OVERRIDE" in page.locator("#prompt-retry-call2a pre").first.inner_text()
            page.locator("#prompt-call2a").screenshot(path=str(args.output / (name + "-prompt.png")))
            page.locator("#scoring").screenshot(path=str(args.output / (name + "-scoring.png")))
            page.locator("#simple-meeting").screenshot(path=str(args.output / (name + "-simple-meeting.png")))
            page.locator("#explain-call2b").screenshot(path=str(args.output / (name + "-plain-example.png")))
            page.evaluate("document.querySelectorAll('#judge-prompts details').forEach(el => el.open = false)")

            audio = page.locator("#audio-examples audio").first
            audio.evaluate("el => { el.preload = 'auto'; el.load(); }")
            page.wait_for_function(
                "el => el.readyState >= 2 && el.error === null",
                arg=audio.element_handle(),
                timeout=30000,
            )
            playback = None
            if name == "desktop":
                audio.evaluate("el => el.play()")
                page.wait_for_function("el => el.currentTime > 0.1", arg=audio.element_handle(), timeout=15000)
                playback = audio.evaluate("""el => {
                    const result = {currentTime: el.currentTime, paused: el.paused, readyState: el.readyState};
                    el.pause();
                    return result;
                }""")
                assert playback["currentTime"] > 0.05 and not playback["paused"], playback

            dimensions = page.evaluate("""() => ({
                viewport: innerWidth,
                document: document.documentElement.scrollWidth,
                scopeRows: document.querySelectorAll('#benchmark-scope-table tbody tr').length,
                menuItems: document.querySelectorAll('.review-tabs a').length,
                auditCards: document.querySelectorAll('.mtb-audit-item').length,
                audioReady: [...document.querySelectorAll('#audio-examples audio')].map(x => x.readyState)
            })""")
            assert dimensions["document"] <= width, dimensions
            assert dimensions["scopeRows"] == 1 and dimensions["menuItems"] == 8, dimensions
            assert dimensions["auditCards"] == 6, dimensions
            assert not errors, errors
            if not args.url:
                assert all(url.startswith(("file:", "data:")) for url in requests), requests
            page.screenshot(path=str(args.output / (name + "-top.png")))
            page.locator("#audio-examples").screenshot(path=str(args.output / (name + "-audio.png")))
            checks.append({
                "view": name,
                **dimensions,
                "javascript_errors": errors,
                "prompt_panels": 10,
                "plain_language_examples": 6,
                "rendered_equations": 2,
                "expanded_prompts_no_overflow": True,
                "sample_playback": playback,
            })
            context.close()
        browser.close()

    report = {"status": "passed", "page": args.url or "multitalk-bench.html", "checks": checks}
    (args.output / "browser-validation.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("PASS: four responsive/theme views, all prompt panels, rendered equations, FLAC decode/playback, audit and navigation.")


if __name__ == "__main__":
    main()
