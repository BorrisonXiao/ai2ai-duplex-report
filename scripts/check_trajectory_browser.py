#!/usr/bin/env python3
"""Check imported traces, linked audio, timing replay and collection navigation.

Requires Playwright and Chromium. Uses file URLs, with no server or uploads.
"""
import argparse
import json
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--chromium")
    parser.add_argument("--output", type=Path, default=ROOT / "preview/trajectory")
    parser.add_argument("--measured-trace", type=Path)
    parser.add_argument("--archive-trace", type=Path)
    args = parser.parse_args()
    from playwright.sync_api import sync_playwright
    args.output.mkdir(parents=True, exist_ok=True)
    results = []
    demo = json.loads((ROOT / "assets/trajectory/demo.json").read_text())
    with tempfile.TemporaryDirectory(prefix="trajectory-browser-") as temp:
        bad = Path(temp) / "invalid.json"
        bad.write_text(json.dumps(demo | {"schema": "bad"}))
        external = Path(temp) / "external.json"
        external_data = json.loads(json.dumps(demo))
        external_data["media"][0]["data_uri"] = "https://example.com/no-download.wav"
        external.write_text(json.dumps(external_data))
        text = Path(temp) / "safe-text.json"
        text_data = json.loads(json.dumps(demo))
        text_data["title"] = '<img src="https://example.com/x" onerror="alert(1)">'
        text.write_text(json.dumps(text_data))
        with sync_playwright() as p:
            options = {"headless": True}
            if args.chromium:
                options["executable_path"] = args.chromium
            browser = p.chromium.launch(**options)
            for name, width, height, theme in [("desktop", 1366, 900, "light"), ("mobile", 390, 844, "light"), ("narrow", 320, 740, "light"), ("dark", 1366, 900, "dark")]:
                context = browser.new_context(viewport={"width": width, "height": height}, color_scheme=theme)
                page = context.new_page()
                errors, requests = [], []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.on("request", lambda request: requests.append(request.url))
                page.goto((ROOT / "index.html").as_uri(), wait_until="load")
                page.locator('[aria-label="Project tabs"] a').filter(has_text="Experiments").click()
                page.wait_for_url("**/experiments/index.html")
                page.locator('a[href="trajectory.html"]').filter(has_text="Open trajectory viewer").click()
                page.wait_for_url("**/trajectory.html")
                page.wait_for_function("document.querySelectorAll('#timeline [data-event]').length > 0")
                assert page.locator('[aria-label="Project tabs"] [aria-current="page"]').inner_text() == "Experiments"
                assert "Measured" in page.locator("#evidence-note").inner_text()
                assert "1815810" in page.locator("#run-title").inner_text()
                assert page.locator("#chunk-grid button").count() == 24
                assert "personal projects" in page.locator("#chunk-transcript").inner_text()
                page.locator("#scrub").evaluate("el => {el.value=32; el.dispatchEvent(new Event('input'));}")
                assert "Empty tts" in page.locator("#s1-text").inner_text()
                assert "What are you working on?" in page.locator("#s1-asr").inner_text()
                assert "S2 audio-derived context" in page.locator("#active-layers").inner_text()
                assert "S1" not in page.locator("#active-layers").inner_text()
                assert page.locator("#timeline .absence").count() == 1
                assert page.locator("#timeline polyline").count() == 1
                assert "selected trace clock" in page.locator("#time-label").inner_text()
                page.locator("#timeline-title").scroll_into_view_if_needed()
                page.screenshot(path=str(args.output / (name + "-recorded-wait.png")))
                page.locator("#chunk-reset").click()
                assert "No generated speech text yet" in page.locator("#chunk-transcript").inner_text()
                page.locator('#chunk-grid [data-chunk="3"]').click()
                assert page.locator("#chunk-fragment").inner_text() == "I see."
                page.locator('#chunk-grid [data-chunk="11"]').click()
                assert "complete supplied S2 answer" in page.locator("#answer-status").inner_text()
                assert "What budget" not in page.locator("#chunk-transcript").inner_text()
                page.locator("#reply-case").select_option("prior_THINK_plaintext_contrast")
                assert "audio-only speech assistant project" in page.locator("#chunk-transcript").inner_text()
                assert "personal projects" not in page.locator("#chunk-transcript").inner_text()
                assert "Diagnostic intervention" in page.locator("#case-note").inner_text()
                page.locator("#reply-case").select_option("original_continuation")
                page.locator("#chunk-play").click()
                page.wait_for_function("Number(document.querySelector('#chunk-cursor').value) >= 1")
                page.locator("#chunk-play").click()
                assert page.locator("#chunk-play").inner_text() == "Replay text chunks"
                page.locator('#chunk-grid [data-chunk="23"]').click()
                page.locator("#continuation-title").scroll_into_view_if_needed()
                page.screenshot(path=str(args.output / (name + "-recorded-reply.png")))
                page.locator('figure').filter(has=page.locator('#chunk-grid')).screenshot(path=str(args.output / (name + '-chunks.png')))
                assert page.evaluate("document.documentElement.scrollWidth") <= width
                page.locator("#load-demo").click()
                assert "Illustrative" in page.locator("#evidence-note").inner_text()
                assert page.evaluate("document.documentElement.scrollWidth") <= width
                page.locator("#scrub").evaluate("el => {el.value=4.85; el.dispatchEvent(new Event('input'));}")
                assert "360 received characters" in page.locator("#reasoning-progress").inner_text()
                assert "S2 reasoning" in page.locator("#active-layers").inner_text()
                page.locator("#event-search").fill("command_forwarded")
                assert page.locator("#event-rows tr").count() == 1
                page.locator("#event-rows button").click()
                assert "391" in page.locator("#event-detail").inner_text()
                page.locator("#event-search").fill("")
                page.locator("#warmup").check()
                assert page.locator("#scrub").get_attribute("min") == "0"
                page.locator("#warmup").uncheck()
                assert page.locator("#scrub").get_attribute("min") == "2"
                page.locator("#zoom").evaluate("el => {el.value=2; el.dispatchEvent(new Event('input'));}")
                assert int(page.locator("#timeline").get_attribute("width")) >= 2000
                assert page.evaluate("document.documentElement.scrollWidth") <= width
                page.locator("#zoom").evaluate("el => {el.value=1; el.dispatchEvent(new Event('input'));}")
                page.locator("#reset").click()
                page.locator("#play").click()
                page.wait_for_function("Number(document.querySelector('#scrub').value) > 2.1")
                page.locator("#play").click()
                assert page.locator("#play").inner_text() == "Replay timing"
                page.locator("#clip-select").select_option("response")
                page.evaluate("async () => {await document.querySelector('#clip-player').play();}")
                page.wait_for_function("Number(document.querySelector('#scrub').value) > 8.6")
                page.evaluate("document.querySelector('#clip-player').pause()")
                assert page.locator("#waveform line").count() > 0
                assert abs(page.evaluate("document.querySelector('#clip-player').duration") - 1.5) < .01
                page.locator("#load-demo").click()
                page.locator("#trace-file").set_input_files(str(bad))
                page.wait_for_function("document.querySelector('#load-status').textContent.includes('Could not load')")
                assert "Illustrative two-GPU" in page.locator("#run-title").inner_text()
                page.locator("#trace-file").set_input_files(str(external))
                page.wait_for_function("document.querySelector('#load-status').textContent.includes('embedded WAV')")
                page.locator("#trace-file").set_input_files(str(text))
                page.wait_for_function("document.querySelector('#run-title').textContent.startsWith('<img')")
                assert page.locator("#run-title img").count() == 0
                if args.measured_trace:
                    page.locator("#trace-file").set_input_files(str(args.measured_trace))
                    page.wait_for_function("document.querySelector('#evidence-note strong').textContent.includes('Measured')")
                    assert page.locator("#event-rows tr").count() > 0
                if args.archive_trace:
                    page.locator("#trace-file").set_input_files(str(args.archive_trace))
                    page.wait_for_function("document.querySelector('#evidence-note strong').textContent.includes('Summary only')")
                    assert page.locator("#play").is_disabled()
                    assert page.locator("#clip-select option").count() > 0
                    assert page.locator("#event-rows tr").count() == 0
                page.locator("#load-real").click()
                assert "1815810" in page.locator("#run-title").inner_text()
                assert not errors, errors
                assert all(url.startswith(("file:", "data:")) for url in requests), requests
                results.append(dict(view=name, width=width, theme=theme, recorded_wait="passed", separate_asr_tts="passed", s1_idle_interval="passed", recorded_chunks="passed", changed_answer_control="passed", chunk_replay="passed", timing_replay="passed", audio_cursor="passed", local_import="passed", rejected_remote_audio="passed", safe_text="passed", page_overflow=False, external_requests=0, javascript_errors=errors))
                context.close()
            browser.close()
    (args.output / "browser-validation.json").write_text(json.dumps(dict(status="passed", checks=results), indent=2) + "\n")
    print("PASS: desktop / mobile / 320px / dark; navigation, replay, audio cursor, import, invalid/external input rejection; no overflow or external requests.")


if __name__ == "__main__":
    main()
