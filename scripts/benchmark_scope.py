"""One shared scope matrix for benchmark detail and overview pages."""
from html import escape
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCOPE = json.loads((ROOT / "research/benchmark-scope.json").read_text(encoding="utf-8"))


def render_scope_section(ids=None, number=1):
    selected = set(ids) if ids is not None else None
    rows = [row for row in SCOPE["rows"] if selected is None or row["id"] in selected]
    if selected is not None and len(rows) != len(selected):
        raise ValueError("Unknown benchmark scope identifier")
    columns = SCOPE["columns"]
    header = "".join('<th scope="col">' + escape(label) + "</th>" for _, label in columns)
    body = []
    for row in rows:
        name = escape(row["name"])
        if row.get("page"):
            name = '<a href="' + escape(row["page"], quote=True) + '">' + name + "</a>"
        sources = " · ".join('<a href="' + escape(url, quote=True) + '">' + escape(label) + "</a>" for label, url in row["sources"])
        cells = '<th scope="row">' + name + '<p class="benchmark-scope-sources">' + sources + "</p></th>"
        cells += "".join("<td>" + escape(row[key]) + "</td>" for key, _ in columns[1:])
        body.append('<tr data-benchmark="' + escape(row["id"], quote=True) + '">' + cells + "</tr>")
    caption = "Published benchmark coverage" if selected is not None else "Nine context-assistance benchmarks and two versioned Full-Duplex-Bench references"
    return (
        '<section class="section benchmark-scope" id="benchmark-scope"><h2>What this benchmark tests</h2>'
        if selected is not None else
        '<section class="section benchmark-scope" id="benchmark-scope"><h2>Benchmark scope at a glance</h2>'
    ) + (
        '<p class="section-intro">' + escape(SCOPE["definition"]) + '</p>'
        '<p class="benchmark-scope-hint">The same columns and benchmark rows are used on the individual dataset pages and this comparison. Scroll horizontally for the full table. “No dedicated test” means the published protocol has no task or metric for that capability.</p>'
        '<div class="benchmark-scope-scroll" role="region" aria-label="Benchmark scope comparison" tabindex="0">'
        '<table id="benchmark-scope-table"><caption>Table ' + str(number) + ". " + caption + "; source check " + escape(SCOPE["reviewed_on"]) + '.</caption>'
        '<thead><tr>' + header + '</tr></thead><tbody>' + "".join(body) + '</tbody></table></div>'
        '<p class="meta">MSI-Bench has limited live bystander probes; MP-Bench has task-level participation and onset latency. Neither provides the full interruption, backchannel and speech-delivery suite of Full-Duplex-Bench. Synthetic scripts/TTS are distinguished from human recordings and hybrid datasets. <a href="research/benchmark-scope.json">Shared scope data and sources</a> · <a href="context-assistance.html#benchmark-scope">Compare all benchmarks</a>.</p></section>'
    )
