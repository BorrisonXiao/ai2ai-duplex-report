"""Build the AMI and ConEC dataset page from the published inventory."""
from collections import Counter
from hashlib import sha256
from html import escape
import json
from pathlib import Path
from statistics import mean

from site_navigation import experiment_subtabs, project_tabs

SITE = Path(__file__).resolve().parents[1]
CORPORA = ('AMI', 'ConEC')
KINDS = ('Semantic', 'Controlled sound', 'Natural laughter')
BY_KIND = {
    'Semantic': ('semantic', 'Questions about what people said',
                 'Each clip plays the conversation around the insertion point, including the synthesized question in the requester’s voice. Earlier turns can also contribute to the reference answer.'),
    'Controlled sound': ('controlled', 'Questions about an edited sound',
                         'Play either version. Both use the same two excerpts and the same requester’s question. Moving the muffling or chime changes which remarks answer the question. F5-TTS uses earlier speech from each requester. We match their speaking level and mix in background sound from the recording. In both demos we use noise with the same level and frequency profile as the quietest 5% of the earlier recording. For AMI, the first attempt at using recorded room tone produced recognizable words in the background check. The earlier sound-cue experiments used a stock Flite voice.'),
    'Natural laughter': ('natural', 'Questions about laughter in the original recording',
                         'Each clip plays the two excerpts judged by the listener, followed by the same question in a participant’s voice. AMI uses speaker C and ConEC uses speaker S0. The listener checked the laughter and topic in the original excerpts.'),
}


def clock(seconds):
    minutes, seconds = divmod(round(seconds), 60)
    return f'{minutes}:{seconds:02d}'


def table(caption, headings, rows):
    cols = ''.join(f'<th scope="col">{escape(h)}</th>' for h in headings)
    lines = []
    for name, *numbers in rows:
        cells = ''.join(f'<td>{n}</td>' for n in numbers)
        lines.append(f'<tr><th scope="row">{escape(name)}</th>{cells}</tr>')
    return f'<table><caption>{escape(caption)}</caption><thead><tr>{cols}</tr></thead><tbody>{"".join(lines)}</tbody></table>'


def timing_panel(questions):
    timed = [q for q in questions if q['insertion_seconds'] is not None]
    bars, descriptions = [], []
    intervals = ('Before 10 min', '10 to <20 min', '20 to <30 min', '30 min or later')
    for corpus in CORPORA:
        rows = [q for q in timed if q['corpus'] == corpus]
        times = [q['insertion_seconds'] for q in rows]
        counts = Counter(min(int(t // 600), 3) for t in times)
        durations = mean(times)/60
        percent = mean(q['fraction'] for q in rows)*100
        descriptions.append(f'{corpus} averaged <strong>{durations:.1f} min</strong> ({percent:.0f}% through the recording)')
        group = [f'<div class="times"><h3>{corpus} <small>· {len(rows)} questions</small></h3>']
        for i, label in enumerate(intervals):
            value = 100 * counts[i] / len(rows)
            group.append(f'<div class="bar-row"><span>{escape(label)}</span><span class="rail" aria-hidden="true"><i style="width:{value:.2f}%"></i></span><b>{counts[i]} <small>({value:.0f}%)</small></b></div>')
        bars.append(''.join(group)+'</div>')
    return (f'<section id="timing"><h2>When are questions asked?</h2><p>{" and ".join(descriptions)}. '
            f'The {len(timed)} timed questions average <strong>{mean(q["insertion_seconds"] for q in timed)/60:.1f} minutes</strong> from the start. '
            'The continuous earnings-call previews use reviewed pauses at sentence endings. The controlled sound cases use their evaluation cutoffs. The two laughter cases use paired excerpts without a full-recording insertion time.</p>'
            f'<figure><figcaption><strong>Figure 1.</strong> Question counts and percentages by time since the recording began. Each percentage uses the timed questions from that corpus.</figcaption><div class="pair">{"".join(bars)}</div></figure></section>')


def demo_card(q, demo):
    cutoff = '' if q['insertion_seconds'] is None else ' · Question at '+clock(q['insertion_seconds'])
    if q['kind']=='Controlled sound':
        cutoff = ' · Paired excerpts · Evaluation time '+clock(q['insertion_seconds'])
    label = f'{q["corpus"]} · {q["recording"].removeprefix("EC")}{cutoff}'
    anchor='demo-'+q['id'].replace(':','-')
    parts = [f'<article class="sample" id="{escape(anchor)}"><p class="meta">{escape(label)}</p><h4>{escape(demo["title"])}</h4>',
             f'<blockquote>{escape(q["question"])}</blockquote>']
    if demo.get('requester') and q['corpus']=='AMI':
        parts.append('<p>The AMI recording is quiet. Both listening versions raise the meeting and the question together by 14 dB.</p>')
    if demo.get('turn_end'):
        parts.append('<p>The caller finishes “'+escape(demo['turn_end'])+'” before the requester speaks. The clip leaves two seconds for a reply.</p>')
    for i, track in enumerate(demo['tracks']):
        caption = f'{track["label"]} · {clock(track["duration"])}'
        file = escape(track['file'], quote=True)
        if demo.get('reference_voice'):
            # Cache the previous comparison separately when its input audio changes.
            version = sha256((SITE/'experiments'/track['file']).read_bytes()).hexdigest()[:12]
            file += '?v='+version
        audio_id = f'audio-{q["id"]}-{i}'
        accessible = f'{demo["title"]}, {track["label"]}'
        parts.append(f'<div class="track"><p>{escape(caption)}</p><audio id="{audio_id}" controls preload="none" aria-label="{escape(accessible, quote=True)}" src="{file}"><a href="{file}">Download audio</a></audio>'
                     f'<button type="button" class="jump" hidden data-track="{audio_id}" data-start="{track["request_at"]:.4f}">Play from question <span>({clock(track["request_at"])})</span></button></div>')
    if 'reference_voice' in demo:
        voice=escape(demo['requester'])
        parts.append(f'<details class="voice-check"><summary>Compare requester {voice} with the synthesized question</summary>')
        for field,caption in [('reference_voice','Original requester'),('question_audio','Synthesized question')]:
            parts.append(f'<p>{caption}</p><audio controls preload="none" aria-label="{caption}, {escape(demo["title"])}" src="{escape(demo[field],quote=True)}"></audio>')
        parts.append('</details>')
    parts.append('<details class="answer"><summary>Reference answer'+('s by version' if len(demo['answers'])>1 else '')+'</summary>')
    for i, answer in enumerate(demo['answers'], 1):
        prefix = f'<b>Version {i}.</b> ' if len(demo['answers'])>1 else ''
        parts.append(f'<p>{prefix}{escape(answer)}</p>')
    parts.append('</details></article>')
    return ''.join(parts)


def recording_picker(questions):
    options=[]
    for corpus in CORPORA:
        group=sorted((q for q in questions if q['corpus']==corpus),key=lambda q:(q['recording'],q['insertion_seconds'] or 0,q['id']))
        options.append(f'<optgroup label="{corpus}">')
        for q in group:
            label=q['recording']+' · '+q['question']
            options.append(f'<option data-id="{escape(q["id"],quote=True)}" value="{escape(q["request_audio"],quote=True)}" data-context="{escape(q.get("context_audio",""),quote=True)}" data-note="{escape(q.get("speech_check_note",""),quote=True)}" data-reference="{escape(q.get("name_reference",""),quote=True)}">{escape(label)}</option>')
        options.append('</optgroup>')
    return ('<div class="recording-picker"><label for="recording-select">Choose a question</label>'
            '<select id="recording-select">'+''.join(options)+'</select>'
            '<audio id="recording-player" controls preload="none" aria-label="Selected question"></audio>'
            '<a id="recording-context" hidden>Listen with the preceding conversation</a><p id="recording-note" hidden></p><a id="recording-reference" hidden>Hear the name in the original Culp call (4 seconds)</a></div>')


def render():
    public = json.loads((SITE/'research/question-dataset/overview.json').read_text())
    questions = public['questions']
    cases = {q['id']: q for q in questions}
    counts = Counter((q['kind'], q['corpus']) for q in questions)
    audio_status = Counter(q['request_audio_status'] for q in questions)
    groups = Counter(q['group'] for q in questions)
    records = {c:len({q['recording'] for q in questions if q['corpus']==c}) for c in CORPORA}
    per_corpus = [sum(counts[k, c] for k in KINDS) for c in CORPORA]
    balanced = [q for q in questions if q['group']=='Balanced set']
    balanced_by_corpus = Counter(q['corpus'] for q in balanced)
    subsets = Counter((q['split'], q['kind'], q['corpus']) for q in balanced)
    subset_count = sum(q['equal_type'] for q in balanced)
    by_type = []
    for kind in KINDS:
        values = [counts[kind,c] for c in CORPORA]
        by_type.append([kind, *values, sum(values)])
    by_type.append(['All cases', *per_corpus, len(questions)])
    components = []
    for split,label in [('development','Development'),('held-out','Held-out')]:
        cells = [subsets[split,k,'AMI'] for k in KINDS[:2]]
        assert cells == [subsets[split,k,'ConEC'] for k in KINDS[:2]]
        components.append([label,*cells,sum(cells)])
    totals = [sum(row[i] for row in components) for i in range(1,4)]
    components.append(['Total per corpus', *totals])
    title = 'AMI and ConEC question dataset'
    body = [f'<header><h1>{title}</h1><ul class="summary">',
            f'<li><strong>{len(questions)} question–recording cases</strong> cover {records["AMI"]} AMI meetings and {records["ConEC"]} ConEC financial conversations. <a href="#inventory">Corpus and question counts</a></li>',
            f'<li>The balanced evaluation set has <strong>{balanced_by_corpus["AMI"]} AMI and {balanced_by_corpus["ConEC"]} ConEC questions</strong>, with the same mix of semantic and sound questions in each corpus. <a href="#balanced">Evaluation split</a></li>',
            '<li>Listen to six examples in context or choose any participant question from the full recording list. <a href="#demos">Question text and audio</a> · <a href="#sources">All recordings</a></li></ul></header>',
            '<section id="inventory"><h2>What does the dataset contain?</h2><p>A case is one question about one recording. A controlled question has two audio versions and counts once. The same laughter question appears on two different recordings and contributes two cases.</p>',
            table('Table 1. All question–recording cases, including reserve questions and the two listener-reviewed examples.',
                  ['Question type',*CORPORA,'Total'],by_type),
            '<p><strong>Semantic</strong> questions ask about the words people spoke. <strong>Controlled sound</strong> questions use an edited chime or muffled voice to identify which remarks the question refers to. <strong>Natural laughter</strong> questions ask which excerpt contained laughter and what people were discussing.</p></section>',
            f'<section id="balanced"><h2>Which questions are in the balanced evaluation?</h2><p>We selected {len(balanced)} questions for comparisons across corpora. The development and held-out questions come from different recordings within each corpus.</p>',
            table('Table 2. Counts per corpus in the balanced set. Each row applies separately to AMI and to ConEC.',
                  ['Split','Semantic','Controlled sound','Total'],components),
            f'<p>The inventory also includes <strong>{groups["AMI reserve"]} AMI semantic questions in reserve</strong> and <strong>{groups["Natural laughter"]} separate natural-laughter development cases</strong>, one from each corpus. For an equal-weight comparison, a {subset_count}-question subset of the balanced set contains four semantic and four controlled sound questions per corpus.</p></section>',
            timing_panel(questions), '<section id="demos"><h2>Listen to the questions</h2><nav class="jump-links" aria-label="Audio example types">']
    for kind in KINDS:
        anchor = BY_KIND[kind][0]
        body.append(f'<a href="#{anchor}">{kind}</a>')
    body.append('</nav>')
    for kind in KINDS:
        anchor, heading, lead = BY_KIND[kind]
        body.append(f'<section id="{anchor}"><h3>{heading}</h3><p>{lead}</p><div class="pair">')
        for demo in public['demos']:
            q = cases[demo['id']]
            if q['kind']==kind:
                body.append(demo_card(q,demo))
        body.append('</div></section>')
    body.extend(['</section><section id="sources"><h2>Inventory and recordings</h2>',
                 f'<p>All {audio_status["Requester voice with matched background"]} cases have an F5-TTS question in the requester’s voice. AMI uses recorded room tone when it passes the speech check. ConEC and the remaining AMI cases use noise matched to the quietest earlier frames. Earlier experiment scores describe the audio used in those runs.</p>',
                 recording_picker(questions),
                 '<p><a href="../research/question-dataset/overview.json" download>Download the full question list (JSON)</a> for question text, recording IDs, set membership and insertion times. The <a href="question-audio.html">earlier audio library</a> contains the first 105 question events. <a href="../research/question-dataset/conec-turns.json">Revised earnings-call times</a> · <a href="../research/question-dataset/participant-recordings.json">All recording files and checks</a> · <a href="../research/question-dataset/requester-voices.json">Requester voices and speech checks</a>.</p>',
                 '<p>Meeting excerpts are from the AMI Consortium. Financial conversations use Rev’s Earnings-21 recordings with ConEC transcripts. The listening copies join short excerpts with the synthesized request. The controlled copies also include the sound edits. <a href="https://groups.inf.ed.ac.uk/ami/corpus/license.shtml">AMI recording licence</a> · <a href="https://github.com/revdotcom/speech-datasets/tree/c05ab6fd8b4b627d123c922a22a39e993dd37635/earnings21">Earnings-21 recordings and credits</a> · <a href="https://aclanthology.org/2024.lrec-main.328/">ConEC corpus</a></p></section>'])
    version = sha256((SITE/'assets/site.css').read_bytes()).hexdigest()[:12]
    page = (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light dark"><title>{title} · AI2AI Duplex</title>'
            f'<meta name="description" content="Question counts, insertion times and spoken examples from AMI meetings and ConEC financial conversations."><link rel="stylesheet" href="../assets/site.css?v={version}"><style>{CSS}</style></head><body>'
            '<a class="skip-link" href="#main">Skip to content</a><header class="site-nav"><div class="nav-inner"><a class="brand" href="../index.html">AI2AI Duplex</a>'+project_tabs('experiments','../')+'</div></header>'
            '<div class="container collection-nav">'+experiment_subtabs('dataset')+'</div><main id="main" class="dataset container">'+''.join(body)+f'</main><script>{JS}</script></body></html>\n')
    (SITE/'experiments/question-dataset.html').write_text(page)


CSS = """
.recording-picker{display:grid;gap:.6rem;max-width:52rem}.recording-picker select{width:100%;min-width:0;font:inherit;padding:.45rem}.recording-picker audio{width:100%}
.dataset{max-width:64rem;padding:1.7rem 0 3.5rem}.dataset h1{font-size:clamp(2rem,5vw,3.4rem);line-height:1.08;margin:0 0 1rem}
.dataset .summary{padding-left:1.4rem}.dataset li{margin:.55rem 0}.dataset section{margin-top:2.3rem;scroll-margin-top:5rem}
.dataset h2{font-size:clamp(1.4rem,3vw,2rem)}.dataset h3{margin:0 0 .5rem}.dataset p{line-height:1.55}
.dataset table{min-width:0;width:100%;border-collapse:collapse;margin:.8rem 0}.dataset caption,.dataset figcaption{text-align:left;color:var(--muted);font-size:.93rem;padding:.4rem 0 .8rem}
.dataset td,.dataset th{padding:.55rem;text-align:right;font-variant-numeric:tabular-nums}.dataset th:first-child{text-align:left}
.dataset tr:last-child th,.dataset tr:last-child td{font-weight:bold}
.dataset figure{margin:.8rem 0}.dataset .pair{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:1rem}
.dataset .times,.dataset .sample{min-width:0;border:1px solid var(--border);background:var(--surface);border-radius:.7rem;padding:1.05rem}
.dataset .bar-row{display:grid;grid-template-columns:6.6rem minmax(2rem,1fr) 5.2rem;align-items:center;gap:.5rem;font-size:.88rem;margin:.5rem 0}
.dataset .times small,.dataset .bar-row small{font-weight:400;color:var(--muted)}.dataset .bar-row b{text-align:right}
.dataset .rail{height:.6rem;border-radius:1rem;background:var(--surface-2)}.dataset .rail i{display:block;height:100%;border-radius:inherit;background:var(--accent)}.dataset .times:nth-child(2) i{background:var(--blue)}
.dataset .meta{font-size:.83rem;color:var(--muted);margin:0}.dataset h4{font-size:1.15rem;margin:.35rem 0}
.dataset blockquote{border-left:3px solid var(--accent);margin:.85rem 0;padding:.2rem 0 .2rem .75rem;font-weight:600}
.dataset audio{width:100%;min-width:0;display:block}.dataset .track p{margin:.65rem 0 .3rem;font-size:.86rem}
.dataset .jump{border:0;background:transparent;color:var(--accent);text-decoration:underline;cursor:pointer;padding:.4rem 0;font:inherit;font-size:.88rem}
.dataset .sample details{margin:.8rem 0 0}.dataset summary{cursor:pointer}.dataset .jump-links{flex-wrap:wrap}
@media(max-width:750px){.dataset .pair{grid-template-columns:1fr}.dataset .sample,.dataset .times{padding:.85rem}.dataset .bar-row{grid-template-columns:6rem minmax(1rem,1fr) 4.7rem}}
"""
JS = """
const select=document.getElementById('recording-select');
function selectRecording(){
  const option=select.selectedOptions[0];
  document.getElementById('recording-player').src=option.value;
  const link=document.getElementById('recording-context');
  link.hidden=!option.dataset.context;
  if(link.hidden)link.removeAttribute('href');else link.href=option.dataset.context;
  const note=document.getElementById('recording-note');
  note.textContent=option.dataset.note;
  note.hidden=!option.dataset.note;
  const reference=document.getElementById('recording-reference');
  reference.hidden=!option.dataset.reference;
  if(reference.hidden)reference.removeAttribute('href');else reference.href=option.dataset.reference;
}
const requested=new URLSearchParams(location.search).get('question');
const initial=Array.from(select.options).find(option=>option.dataset.id===requested);
if(initial)select.value=initial.value;
select.addEventListener('change',selectRecording);
selectRecording();

document.querySelectorAll('audio').forEach(player => player.addEventListener('play', () => {
  document.querySelectorAll('audio').forEach(other => { if (other !== player) other.pause(); });
}));
document.querySelectorAll('button[data-track]').forEach(button => {
  button.hidden = false;
  button.addEventListener('click', () => {
    const player = document.getElementById(button.dataset.track);
    const start = () => {
      player.currentTime = Number(button.dataset.start);
      player.play().catch(() => player.focus());
    };
    if (player.readyState >= 1) {
      start();
    } else {
      player.addEventListener('loadedmetadata', start, {once: true});
      if (player.networkState !== HTMLMediaElement.NETWORK_LOADING) player.load();
    }
  });
});
"""

if __name__ == '__main__':
    render()
