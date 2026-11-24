"""Render the completed AMI/ConEC sound-note experiment from reviewed results."""
from html import escape
import hashlib
import json
from pathlib import Path
from site_navigation import project_tabs, experiment_subtabs

SITE=Path(__file__).resolve().parents[1]
LABELS={'reactive':'Audio alone','original_notes':'Broad meeting notes','thinker_events':'Thinker listens for sounds',
        'known_location':'Known edit time','auto_time':'Automatic sound time','auto_time_and_topic':'Automatic time and topic note'}
def table(number,caption,headers,rows):
    head=''.join('<th scope="col">'+escape(h)+'</th>' for h in headers)
    rendered_rows=[]
    for row in rows:
        first,*rest=row
        cells='<th scope="row">'+escape(str(first))+'</th>'
        cells+=''.join('<td>'+escape(str(value))+'</td>' for value in rest)
        rendered_rows.append('<tr>'+cells+'</tr>')
    body=''.join(rendered_rows)
    return f'<div class="scroll"><table><caption>Table {number}. {escape(caption)}</caption><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'

def render():
    data=json.loads((SITE/'research/cue-notes/results.json').read_text())
    title='Saving sound cues before a question'
    sections=['<p class="back"><a href="index.html">All experiments</a></p>',f'<h1>{title}</h1>','<ul>']
    for item in data['findings']:
        sections.append(f'<li>{escape(item["text"])} <a href="#{item["section"]}">{escape(item["label"])}</a></li>')
    sections.extend(['</ul>','<section id="setup"><h2>What the thinker heard</h2><p>We tested Qwen3-Omni-30B-A3B-Thinking on AMI design meetings and ConEC earnings calls. Before anyone asked a question, the note writer heard each excerpt once. At question time, the thinker heard both excerpts in order and the spoken request. Each excerpt lasted at most 40 seconds.</p>',
        '<ul><li><strong>Audio alone.</strong> The thinker answered immediately from the recording.</li><li><strong>Broad meeting notes.</strong> A function call saved facts, commitments and any distinctive sounds that the thinker noticed.</li><li><strong>Thinker listens for sounds.</strong> The writer specifically listened for laughter, muffled speech and chimes. It could save the sound, its start and end, the speaking turn and the nearby topic, or record that it heard none.</li><li><strong>Automatic sound time.</strong> A CPU detector supplied a sound type, excerpt and estimated interval. A bandwidth check detected muffled speech, and YAMNet detected laughter.</li><li><strong>Automatic time and topic note.</strong> For each detection, the thinker also heard that excerpt and saved a phrase identifying the speaking turn and what was being discussed.</li><li><strong>Known edit time.</strong> For comparison, the answerer received the interval where we had applied the muffling edit.</li></ul></section>',
        '<section id="answers"><h2>Did the notes help answer the question?</h2><p>Each controlled question has two recordings. We kept the words fixed and moved the muffling from one speaker to another. A correct answer identifies the indicated contribution and gives source-supported details. Both versions must pass to count a question as correct on both recordings.</p>'])
    for number,split,caption in [(1,'held-out','Held-out muffled speech, two questions across four recordings.'),(2,'development','Development muffled speech, four questions across eight recordings.')]:
        rows=[]
        for method,name in LABELS.items():
            group=next((r for r in data['answers'] if r['split']==split and r['condition']==method),None)
            if group is None:continue
            sec=group['mean_first_answer_seconds']
            rows.append([name,f"{group['supported']}/{group['versions']}",f"{group['both']}/{group['questions']}",f"{group['mean_thinking']:.0f}",f'{sec:.1f}' if sec is not None else '—'])
        sections.append(table(number,caption,['Condition','Supported answers','Both versions correct','Mean thinking tokens at request','Mean seconds to first answer text'],rows))
    sections.append('<p>Tables 1 and 2 use the native text answer from the same thinker. Time runs from the start of the request call through the first answer text, including audio processing and thinking. A dash means a timing was missing or at least one run produced no final answer. Earlier work is counted separately below. Each held-out question contributes two related outcomes.</p>')
    sections.append('<p>'+escape(data['cost'])+'</p><p>'+escape(data['muffled_detection'])+'</p></section>')
    sections.extend(['<section id="laughter"><h2>Could the system hear natural laughter?</h2>',
        '<p>One listener confirmed the excerpt with laughter and its topic in an AMI meeting and an American Express interview. We used those two recordings for development. We then used laughter annotations on four other meetings and four other calls. Every 16-second excerpt containing a laughter tag had a nearby 16-second speech control from the same recording without a tag.</p>'])
    sections.append('<p>'+escape(data['natural_answers'])+'</p>')
    rows=[[r['label'],r['corpus'],f"{r['flagged']}/{r['positives']}",f"{r['overlap']}/{r['positives']}",f"{r['control_flags']}/{r['controls']}"] for r in data['laughter']]
    sections.append(table(3,'Laughter detections on independent recordings. The middle column checks whether the predicted interval touched the source annotation.',['Detector','Corpus','Tagged excerpts flagged','At annotated time','Controls flagged'],rows))
    sections.append('<p>'+escape(data['laughter_detail'])+'</p>')
    sections.append('<p>Table 3 measures detection only. AMI annotations can give a single timestamp. For ConEC, the nearest aligned words bracket the laughter tag. Controls have no laughter annotation. The comparison uses corpus labels and does not require additional listener ratings.</p>')
    sections.append('<p>YAMNet used a score threshold of 0.10, selected on the two listener examples. The dedicated wav2vec2 laughter detector used the authors’ threshold of 0.5 and their duration settings. The Qwen writer used the same sound-focused prompt on all 30 excerpts. The dedicated detector ran in a separate detection test. <a href="https://github.com/tensorflow/models/tree/master/research/audioset/yamnet">YAMNet</a> · <a href="https://www.isca-archive.org/interspeech_2024/omine24_interspeech.html">Omine et al., Interspeech 2024</a></p></section>')
    sections.extend(['<section id="examples"><h2>What the notes actually said</h2>'])
    for ex in data['examples']:
        sections.append('<article><h3>'+escape(ex['title'])+'</h3><p>'+escape(ex['context'])+'</p>')
        if 'clip' in ex:
            sections.append('<audio controls preload="none" aria-label="'+escape(ex['title'])+'" src="../research/listening-check/'+escape(ex['clip'])+'"></audio>')
        for label,field in [('Saved note','note'),('Answer','answer')]:
            if ex.get(field):sections.append('<p><b>'+label+'</b></p><blockquote>'+escape(ex[field])+'</blockquote>')
        sections.append('</article>')
    sections.append('<p><a href="listening-check.html">Listening task and recording credits</a></p></section>')
    sections.append('<section id="next"><h2>Next test</h2><p>'+escape(data['next'])+'</p><p><a href="../research/cue-notes/results.json">Download reviewed results</a> · <a href="../todo.html">Project checklist</a></p></section>')
    css='main.cue{max-width:58rem;margin:auto;padding:1.2rem 1rem 4rem}.cue h1{font-size:clamp(2rem,5vw,3.4rem);line-height:1.1}.cue li{margin:.55rem 0}.cue section{margin-top:2.4rem}.cue .scroll{overflow-x:auto;margin:1.1rem 0}.cue table{border-collapse:collapse;width:100%;font-size:.95rem}.cue td,.cue th{padding:.48rem;text-align:left;border-bottom:1px solid var(--border)}.cue caption{text-align:left;font-weight:650;margin:.5rem 0}.cue blockquote{margin:.35rem 0 1rem;padding:.6rem 1rem;border-left:3px solid var(--border)}.cue article{margin:1rem 0}.cue audio{max-width:100%}'
    nav='<header class="site-nav"><div class="nav-inner"><a class="brand" href="../index.html">AI2AI Duplex</a>'+project_tabs('experiments','../')+'</div></header>'
    nav+='<div class="container collection-nav">'+experiment_subtabs('overview')+'</div>'
    meta='<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="description" content="Timing, topic notes and answer quality for natural laughter and edited speech in meetings and earnings calls.">'
    html='<!doctype html><html lang="en"><head>'+meta+'<title>'+title+' · AI2AI Duplex</title><link rel="stylesheet" href="../assets/site.css"><style>'+css+'</style></head><body>'+nav+'<main id="main" class="cue">'+''.join(sections)+'</main></body></html>\n'
    css_version=hashlib.sha256((SITE/'assets/site.css').read_bytes()).hexdigest()[:12]
    html=html.replace('href="../assets/site.css"', f'href="../assets/site.css?v={css_version}"')
    (SITE/'experiments/cue-notes.html').write_text(html)
if __name__=='__main__':render()
