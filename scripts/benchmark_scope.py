"""Shared compact scope matrix, with detailed evidence outside the table."""
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
    header = "".join('<th scope="col">' + escape(label) + "</th>" for _, label in SCOPE["columns"])
    body, notes = [], []
    for row in rows:
        name = escape(row.get("short_name", row["name"]))
        if row.get("page"):
            name = '<a href="' + escape(row["page"], quote=True) + '">' + name + "</a>"
        cells = '<th scope="row">' + name + '</th>'
        for key, _ in SCOPE["columns"][1:]:
            value = row['quick'][key]
            tone = {'Yes':'yes', 'No':'no', 'Limited':'partial', 'Mixed':'partial'}.get(value, 'label')
            cells += '<td class="scope-' + tone + '">' + escape(value) + '</td>'
        body.append('<tr data-benchmark="' + escape(row["id"], quote=True) + '">' + cells + "</tr>")
        sources = " · ".join('<a href="' + escape(url, quote=True) + '">' + escape(label) + "</a>" for label, url in row["sources"])
        definitions = ''.join('<dt>' + escape(label) + '</dt><dd>' + escape(row[key]) + '</dd>' for key, label in SCOPE['detail_columns'][1:])
        notes.append('<article class="benchmark-scope-note"><h3>' + escape(row['name']) + '</h3><dl>' + definitions + '</dl><p>' + sources + '</p></article>')
    heading = 'What this benchmark tests' if selected is not None else 'Benchmark scope at a glance'
    return (
        '<section class="section benchmark-scope" id="benchmark-scope"><h2>' + heading + '</h2>'
        '<p class="benchmark-scope-hint">Yes = tested; No = no dedicated test; Limited = partial coverage. Details and sources below.</p>'
        '<div class="benchmark-scope-scroll" role="region" aria-label="Benchmark scope comparison" tabindex="0">'
        '<table id="benchmark-scope-table"><caption>Table ' + str(number) + '. Benchmark coverage.</caption>'
        '<thead><tr>' + header + '</tr></thead><tbody>' + ''.join(body) + '</tbody></table></div>'
        '<details class="benchmark-scope-details"><summary>Definitions, caveats and sources</summary>'
        '<p>' + escape(SCOPE['definition']) + '</p>'
        '<p>Multi-party means a group setting, in text or audio. Synthetic describes the conversation/voice material; Mixed combines generated and human material. Target model: Text = text input/output; Audio→text = audio input, text/JSON output; Voice = voice interaction; Duplex = concurrent listening and speaking. Alternative adapters and text controls are listed below.</p>'
        '<p>Content = semantic response scoring; Tools = call correctness; Timing = participation or response timing; User interruption = yielding/recovery when a user interrupts; Backchannels = generation or tolerance of brief acknowledgments; Speech quality = acoustic/prosodic scoring. A Yes does not imply comprehensive coverage. MSI bystander interference is distinct from directed user interruption. Source check: ' + escape(SCOPE['reviewed_on']) + '.</p>'
        + ''.join(notes) + '<p><a href="research/benchmark-scope.json">Shared scope data</a> · <a href="context-assistance.html#benchmark-scope">Compare all benchmarks</a></p></details></section>'
    )
