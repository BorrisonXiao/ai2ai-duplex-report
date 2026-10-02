"""Verified report evidence rendered in the existing webpage design."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "report"
sys.path.insert(0, str(REPORT / "research"))
from performance_profiles import PROFILES
sys.path.insert(0, str(REPORT / "scripts"))
from build_performance import all_groups, scores

def verified_sources():
    audit = json.loads((ROOT / "research/source-audit.json").read_text())
    extra = json.loads((REPORT / "research/source-audit.json").read_text())
    existing = {source["url"] for source in audit["sources"]}
    needed = {"https://arxiv.org/abs/2603.17837", "https://arxiv.org/abs/2604.16456"}
    audit["sources"] += [source for source in extra["sources"] if source["url"] in needed and source["url"] not in existing]
    return audit

def evidence():
    path = REPORT / "research/reported-performance.json"
    data = json.loads(path.read_text())
    plots = json.loads((REPORT / "research/performance-plots.json").read_text())
    audit = json.loads((REPORT / "research/reported-performance-audit.json").read_text())
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert audit["status"] == "passed" and audit["data_sha256"] == plots["data_sha256"] == digest
    assert len(PROFILES) == len(plots['profiles'])
    for spec, record in zip(PROFILES, plots['profiles']):
        assert all(record[key] == value for key, value in spec.items()), 'Rebuild plots after editing performance_profiles.py'
    for assets in [plots['coverage']] + [record['artifacts'] for record in plots['profiles']]:
        for asset in assets.values():
            assert hashlib.sha256((REPORT / asset['file']).read_bytes()).hexdigest() == asset['sha256'], 'Stale plot: ' + asset['file']
    return data, plots

def architecture_gallery(e, link, figure_number):
    manifest = json.loads((REPORT / "figures/papers/manifest.json").read_text())
    records = {Path(source["image"]).stem: source for source in manifest["sources"]}
    descriptions = [
        ("moshi", "Moshi / Think while listening", "Original parallel user-audio, assistant-text and assistant-audio architecture. TWL adds silent reasoning and streaming ASR to the text stream; that extension is not shown here."),
        ("minicpm", "MiniCPM-o 4.5", "Timed text backbone with separate speech-token and waveform decoders; the full multimodal architecture and legend are preserved."),
        ("flair", "FLAIR", "Listening-time latent embeddings and speaking-time text share a Qwen2.5-7B backbone. Full-context expert supervision is training-only."),
        ("step3", "StepAudio 3 Realtime", "Same-model formulation and articulation for think-while-speaking. Figure 7B is selected; routing panel A is omitted."),
        ("venus", "Realtime-Venus", "Concurrent interaction and capability loops, tracked background work and same-session return; the frontend selects reply-delivery timing."),
        ("duplexomni", "DuplexOmni", "Both original panels: asynchronous interaction/thinking layers above, and the interaction model’s internal Qwen Thinker/Talker below. These are different boundaries. Fixed 480 ms slices; reported full-system scores include a Gemini-3.1-Flash-Lite backend."),
        ("voicechat", "NemotronLabs VoiceChat", "Streaming FastConformer feeds a Nemotron text backbone with parallel agent-text/function heads, auxiliary RNN-T and separate streaming TTS. User transcription is not fed into the LLM. Tool execution currently disables user barge-in."),
    ]
    body = '<h3>Seven focused architecture views</h3><p>The original top-five gallery is expanded with DuplexOmni and NemotronLabs VoiceChat, both pinned to arXiv v1. Figures 2–8 retain the papers’ labels, arrows and legends; the broader system table follows. On narrow screens, pan the image horizontally or open it full-size. These are attributed screenshots, not redraws or latency comparisons.</p><div class="architecture-gallery">'
    for ident, title, description in descriptions:
        source = records[ident]
        image = "report/" + source["image"]
        caption = f"Figure {figure_number()}. {title}. Reproduced from source Figure {source['figure']} (PDF p. {source['page']}). {description}"
        body += '<figure class="paper-figure" id="architecture-' + ident + '"><h3>' + e(title) + '</h3><div class="plot-scroll" tabindex="0" role="region" aria-label="' + e(title + ' architecture image') + '"><a href="' + e(image) + '"><img src="' + e(image) + '" alt="' + e(title + ': ' + description) + '" loading="lazy"></a></div><figcaption>' + e(caption) + ' ' + link('Original paper PDF', source['source_url']) + ' · ' + link('Open full-size', image) + '</figcaption></figure>'
    return body + '</div>'

def performance_section(table, e, p, link, small, figure_number):
    data, plots = evidence()
    groups = {group['id']: group for group in all_groups(data)}
    profiles = {profile['id']: profile for profile in plots['profiles']}
    def plot(ident, title, caption, alt, artifacts):
        image = 'report/' + artifacts['svg']['file'] + '?v=' + artifacts['svg']['sha256'][:12]
        return '<figure class="performance-figure" id="plot-' + ident + '"><div class="plot-scroll" tabindex="0" role="region" aria-label="' + e(title + ' plot') + '"><img src="' + e(image) + '" alt="' + e(alt) + '" loading="lazy"></div><figcaption>' + e(f'Figure {figure_number()}. {title}. {caption}') + ' ' + link('Open full-size SVG', image) + ' · ' + link('Vector PDF', 'report/' + artifacts['pdf']['file']) + '</figcaption></figure>'
    body = p('The selected models do not share a complete evaluation grid. Compare individual metrics within a named protocol, not radar area or panels from different benchmarks. Raw percentages use 0–100 radars; seconds and judge scores retain their own bar axes. Missing results are NR, never zero. No cross-benchmark average or normalization to a reference is used.')
    body += p('On narrow screens, pan the figures horizontally or open the full-size SVG; exact values remain in the scrollable tables.', cls='scroll-note')
    body += plot('coverage', 'Selected-system benchmark coverage', 'Reported and NR cells, not performance scores. Original and Artificial Analysis τ-Voice stay separate. FLAIR’s and DuplexOmni’s study-specific scores do not fill SRQA or FDB-v3 cells.', 'Coverage for seven architectures: TWL has SRQA, MiniCPM-o has Duplex-MPE, StepAudio has AA tau-Voice, Venus and VoiceChat have FDB-v3; FLAIR and DuplexOmni have no matching result in these protocols.', plots['coverage'])
    body += '<nav class="jump-links" aria-label="Model performance profiles">' + ' '.join(link(label, '#profile-' + ident) for ident, label in [('twl','TWL'), ('flair-qa','FLAIR'), ('step3','StepAudio 3'), ('venus','Venus'), ('minicpm','MiniCPM-o'), ('duplexomni','DuplexOmni'), ('voicechat','VoiceChat'), ('tau-original','Closed references')]) + '</nav>'
    body += '<div class="callout amber"><h3>Best reported in a source is not global SoTA</h3>' + p('Named closed source leaders appear where evaluated, alongside representative models. Some references are imported from earlier studies or evaluated later in system reports, not a shared rerun. Plots show source-reported point estimates without invented error bars. Text-only and transcript-conditioned controls stay out of speech-model radars.') + '</div>'
    for spec in PROFILES:
        group, record = groups[spec['group']], profiles[spec['id']]
        rows = [row for row in group['rows'] if row['role'] != 'text_control']
        labels = data['domain_metric_labels'] + group['metric_labels'] if group['id'] == 'tau_aa' else group['metric_labels']
        definitions = group.get('metric_specs', [{'unit': '%', 'higher': True, 'decimals': rows[0]['decimals']} for _ in labels])
        numeric = [scores(group, row) for row in rows]
        winners = [(max if definition['higher'] else min)(values[index] for values in numeric if values[index] is not None) for index, definition in enumerate(definitions)]
        headers = ['Model / configuration'] + [label + ' (' + definition['unit'] + ('; higher' if definition['higher'] else '; lower') + ')' for label, definition in zip(labels, definitions)]
        rendered = []
        roles = {'selected':'Selected configuration','closed_voice':'Closed voice reference','ablation':'No-thinking ablation','foundation':'Foundation speech reference','representative':'Representative speech reference','api_comparator':'API comparator','backend_only':'Thinking-only backend; not a realtime voice competitor'}
        for row, values in zip(rows, numeric):
            name = ('<strong>' + e(row['model']) + '</strong>') if row['role'] == 'selected' else e(row['model'])
            name += small(roles.get(row['role'], row['role'])) + '<span class="inline-links">' + link('Primary score source', data['sources'][row['source']]['url']) + '</span>'
            cells = [name]
            for value, definition, winner in zip(values, definitions, winners):
                cell = 'NR' if value is None else f"{value:.{definition['decimals']}f}"
                if value is not None and abs(value-winner)<1e-9: cell = '<strong>' + cell + '</strong>'
                cells.append(cell)
            rendered.append(cells)
        body += '<article class="performance-profile" id="profile-' + spec['id'] + '"><h3>' + e(spec['title']) + '</h3>' + p(spec['note'])
        body += plot(spec['id'], spec['title'], 'Raw values, with units and directions labeled. Exact values and context references are in the table below.', spec['title'] + '. ' + spec['takeaway'], record['artifacts'])
        body += table('performance-' + group['id'], 0, group['benchmark'] + '. Bold: best among displayed references, not source-wide or current SoTA.', headers, rendered, searchable=False)
        body += p('Review interpretation: ' + spec['takeaway'], cls='meta')
        body += p('Source version: ' + '; '.join(data['sources'][key]['version'] + ' · Tables ' + ', '.join(data['sources'][key]['tables']) + ' · PDF pages ' + ', '.join(str(page) for page in data['sources'][key]['pages']) for key in group['source_ids']), cls='meta') + '</article>'
    body += '<h3>Text controls, not voice competitors</h3>'
    for control in data['text_controls']:
        values = ' / '.join(f"{value*control['scale']:.{control['decimals']}f}" for value in control['source_values'])
        body += p(control['model'] + ': ' + values + '% (' + ' / '.join(control['metric_labels']) + '). ' + control['notes'])
    audit = json.loads((REPORT / 'research/reported-performance-audit.json').read_text())
    body += p(f'The structured data retains source scores and conversion rules; the audit matches {len(audit["checks"])} model/configuration vectors to {len(audit["sources"])} primary PDFs. This verifies transcription, not experimental reproduction. The evidence cutoff remains 30 September 2026.')
    body += '<div class="button-row">' + ' '.join(link(label, target, 'button') for label, target in [('Detailed PDF','report/build/detailed-report.pdf'), ('Detailed preview','report/preview/detailed/contact-sheet.png'), ('Meeting brief','report/build/duplex-report.pdf'), ('Source ZIP','report/build/duplex-report-source.zip'), ('Score data','report/research/reported-performance.json'), ('Primary-value audit','report/research/reported-performance-audit.json'), ('Plot provenance','report/research/performance-plots.json')]) + '</div>'
    return body
