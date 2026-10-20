#!/usr/bin/env python3
"""Check the FDB-v2 page at desktop/mobile/narrow widths and dark theme."""

import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
AUTHOR_AUDIO_ORIGIN = "https://ericsunkuan.github.io"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--chromium", help="Existing Chromium or headless-shell binary")
    parser.add_argument("--url", help="Page URL; defaults to the local generated page")
    parser.add_argument("--output", type=Path, default=ROOT.parent / ".migration/updates/2026-10-19-full-duplex-bench-v2/browser")
    args = parser.parse_args()
    from playwright.sync_api import sync_playwright

    target = args.url or (ROOT / "full-duplex-bench-v2.html").as_uri()
    parsed_target = urlsplit(target)
    allowed_origin = f"{parsed_target.scheme}://{parsed_target.netloc}" if parsed_target.scheme in ("http", "https") else None
    args.output.mkdir(parents=True, exist_ok=True)
    checks = []
    views = [
        ("desktop", 1366, 900, "light"),
        ("mobile", 390, 844, "light"),
        ("narrow", 320, 760, "light"),
        ("dark", 1366, 900, "dark"),
    ]
    with sync_playwright() as playwright:
        launch = {"headless": True}
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
            response = page.goto(target, wait_until="load")
            if response:
                assert response.status == 200, f"HTTP {response.status} at {target}"
            assert page.title() == "Full-Duplex-Bench v2 Preview — AI2AI Duplex"
            assert page.locator(".review-tabs a").count() == 8
            assert page.locator(".review-tabs a[aria-current='page']").inner_text() == "Full-Duplex-Bench v2"
            assert page.locator("#benchmark-scope-table tr[data-benchmark='fdb-v2']").count() == 1
            assert page.locator(".fdbv2-table caption").count() == 3
            assert page.locator("#examples .fdbv2-example").count() == 4
            assert page.locator("#audio-examples audio").count() == 3
            assert page.locator("#prompt-examples .fdbv2-prompt-card").count() == 2
            for player in page.locator("#audio-examples audio").all():
                assert player.get_attribute("src").startswith(AUTHOR_AUDIO_ORIGIN + "/full-duplex-bench-v2-demo/audio/")
                assert player.get_attribute("preload") == "none"
            body_text = page.locator("body").inner_text()
            assert "actual arrays contain 200 unique prompts" in body_text
            assert "No local model inference or benchmark scoring" in body_text
            assert "What prompts do the Examiner and judge use?" in body_text
            assert "The pinned runner sends the judge ASR transcript summaries and timestamps" in body_text
            dimensions = page.evaluate("""() => ({
                viewport: innerWidth,
                document: document.documentElement.scrollWidth,
                menuItems: document.querySelectorAll('.review-tabs a').length,
                scopeRows: document.querySelectorAll('#benchmark-scope-table tbody tr').length,
                tables: [...document.querySelectorAll('.fdbv2-table-scroll')].map(x => ({
                    scrollWidth: x.scrollWidth, clientWidth: x.clientWidth
                })),
                cards: document.querySelectorAll('#examples .fdbv2-example').length,
                audioPlayers: document.querySelectorAll('#audio-examples audio').length,
                promptCards: document.querySelectorAll('#prompt-examples .fdbv2-prompt-card').length
            })""")
            assert dimensions["document"] <= width, dimensions
            assert dimensions["scopeRows"] == 1 and dimensions["cards"] == 4, dimensions
            assert dimensions["audioPlayers"] == 3 and dimensions["promptCards"] == 2, dimensions
            assert not errors, errors
            bad_requests = [url for url in requests if not (url.startswith(("file:", "data:")) or (allowed_origin and url.startswith(allowed_origin + "/")) or url.startswith(AUTHOR_AUDIO_ORIGIN + "/"))]
            assert not bad_requests, bad_requests
            if name in ("desktop", "mobile", "narrow", "dark"):
                page.screenshot(path=str(args.output / f"{name}-top.png"), full_page=True)
            if name == "desktop":
                page.locator("#task-design").screenshot(path=str(args.output / "desktop-task-design.png"))
                page.locator("#audio-examples").screenshot(path=str(args.output / "desktop-audio-examples.png"))
                page.locator("#prompt-examples").screenshot(path=str(args.output / "desktop-prompt-examples.png"))
                page.locator("#paper-results").screenshot(path=str(args.output / "desktop-paper-results.png"))
            checks.append({
                "view": name,
                "http_status": response.status if response else None,
                **dimensions,
                "javascript_errors": errors,
                "unexpected_external_requests": bad_requests,
            })
            context.close()
        browser.close()

    result = {"status": "passed", "page": target, "checks": checks}
    (args.output / "browser-validation.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("PASS: FDB-v2 page, eight-tab navigation, source-hosted audio, prompt examples and layout at desktop, mobile, 320 px and dark theme.")


if __name__ == "__main__":
    main()
