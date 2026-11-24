"""Render the recording appendix and the transcripts on the question dataset page."""
import hashlib
import json
from html import escape
from pathlib import Path
from urllib.parse import urlencode
from site_navigation import experiment_subtabs, project_tabs

SITE=Path(__file__).resolve().parents[1]
PAGE='recording-review.html'

def stamp(t):
    n=round(t*10)
    return f'{n//600}:{(n//10)%60:02d}.{n%10}'

def link(case):
    return PAGE+'?'+urlencode({'case':case})

def corpus_links():
    return ('<nav class="review-links" aria-label="Review all recordings by corpus">'
            f'<a href="{PAGE}?corpus=ConEC">Review ConEC recordings</a> '
            f'<a href="{PAGE}?corpus=AMI">Review AMI recordings</a></nav>')

def transcript(row):
    out=[]
    for i,p in enumerate(row['parts'],1):
        title='Conversation' if len(row['parts'])==1 else f'Excerpt {i}'
        out.append(f'<h4>{title} <small>· source {stamp(p["start"])}–{stamp(p["end"])}</small></h4><ol class="speech-lines">')
        for line in p['transcript']:
            out.append(f'<li><span class="clip-clock">{stamp(p["clip_at"]+line["at"])}</span> <b>{escape(line["speaker"])}</b> {escape(line["text"])}</li>')
        out.append('</ol>')
    track=row['tracks'][0]
    out.append(f'<p class="request-line"><span class="clip-clock">{stamp(track["request_at"])}</span> <b>{escape(row["requester"])} · inserted question</b> {escape(row["question"])}</p>')
    out.append('<p class="minor">The clip ends with two seconds for a reply.</p>')
    return ''.join(out)

def read_review():
    return json.loads((SITE/'research/question-dataset/turn-review.json').read_text())['cases']

STYLE="""
.review-links,.review-controls,.pager{display:flex;flex-wrap:wrap;align-items:center;gap:.6rem;margin:.8rem 0}
.review-links a,.review-controls a,.pager button,.review-controls button{font:inherit;color:var(--ink);background:var(--surface);border:1px solid var(--border);border-radius:.45rem;padding:.4rem .7rem;cursor:pointer}
.review-controls [aria-pressed=true]{background:var(--accent);color:var(--bg);border-color:var(--accent)}
.review-wrap{max-width:55rem;padding:1.5rem 0 3rem}.review-wrap select,.review-wrap audio{width:100%;font:inherit;max-width:100%}
.review-wrap select{margin:.4rem 0;padding:.5rem}.review-wrap [hidden]{display:none}.review-wrap h1{font-size:clamp(1.9rem,4vw,2.8rem);margin:.4rem 0}
.review-wrap h3,.review-wrap h4,.transcription h4{margin:1rem 0 .3rem}.review-wrap .player{margin:.7rem 0}
.review-wrap article{border-top:1px solid var(--border);padding-top:.7rem}
.speech-lines{list-style:none;margin:.4rem 0 .8rem;padding:0}.speech-lines li{margin:.36rem 0;line-height:1.4}
.clip-clock,.minor,.review-wrap small,.transcription small{font-variant-numeric:tabular-nums;color:var(--muted);font-weight:400}
.clip-clock{font-size:.89em;margin-right:.35rem}.request-line{border-left:3px solid var(--accent);padding:.45rem .7rem}
.review-wrap summary,.transcription summary{cursor:pointer}.review-wrap output{font-variant-numeric:tabular-nums}.review-wrap button:disabled{opacity:.5;cursor:default}
.review-wrap .rating{margin:1rem 0;display:flex;flex-wrap:wrap;align-items:center;gap:.5rem}.rating select{width:auto}
"""

JS="""
const cases=Array.from(document.querySelectorAll('article[data-corpus]'));
const picker=document.querySelector('#choose');
const params=new URLSearchParams(location.search);
const ratingsKey='duplex-turn-review-v1';
let ratings={};
try{ratings=JSON.parse(localStorage.getItem(ratingsKey)||'{}')||{}}catch{}
let group='',active,subset;
function show(key,update=true){
  const i=Math.max(0,subset.findIndex(x=>x.dataset.key===key));
  if(active){active.hidden=true;active.querySelectorAll('audio').forEach(a=>a.pause())}
  active=subset[i];active.hidden=false;picker.value=active.dataset.key;
  document.querySelector('#counter').textContent=(i+1)+' of '+subset.length;
  document.querySelector('#prev').disabled=i===0;document.querySelector('#next').disabled=i===subset.length-1;
  document.querySelector('#rating').value=ratings[active.dataset.version]||'';
  if(update){const u=new URL(location.href);u.searchParams.set('corpus',group);u.searchParams.set('case',active.dataset.key);history.replaceState({},'',u)}
}
function filter(corpus,key,update=true){
  group=corpus;subset=cases.filter(x=>x.dataset.corpus===group);
  document.querySelectorAll('button[data-filter]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.filter===group)));
  picker.replaceChildren(...subset.map(a=>new Option(a.dataset.label,a.dataset.key)));
  show(key,update);
}
document.querySelectorAll('button[data-filter]').forEach(b=>b.addEventListener('click',()=>filter(b.dataset.filter)));
picker.addEventListener('change',()=>show(picker.value));
for(const [id,step] of [['prev',-1],['next',1]])document.getElementById(id).addEventListener('click',()=>show(subset[subset.indexOf(active)+step].dataset.key));
document.querySelector('#rating').addEventListener('change',e=>{
  if(e.target.value)ratings[active.dataset.version]=e.target.value;else delete ratings[active.dataset.version];
  try{localStorage.setItem(ratingsKey,JSON.stringify(ratings))}catch{document.querySelector('#storage').textContent='Review marks are available for this visit.'}
});
document.querySelectorAll('button[data-replay]').forEach(button=>button.addEventListener('click',()=>{
  const audio=button.closest('.player').querySelector('audio');
  function seek(){audio.currentTime=Number(button.dataset.replay);audio.play().catch(()=>audio.focus())}
  if(audio.readyState>=1)seek();
  else{audio.addEventListener('loadedmetadata',seek,{once:true});if(audio.networkState!==HTMLMediaElement.NETWORK_LOADING)audio.load()}
}));
document.addEventListener('play',e=>{if(e.target.tagName==='AUDIO')document.querySelectorAll('audio').forEach(a=>{if(a!==e.target)a.pause()})},true);
const initial=cases.find(x=>x.dataset.key===params.get('case'));
filter(initial?.dataset.corpus||(params.get('corpus')==='AMI'?'AMI':'ConEC'),initial?.dataset.key,false);
"""

def build(review):
    items=sorted(review.items(),key=lambda kv:(kv[1]['meeting'],kv[1]['parts'][-1]['end'],kv[0]))
    counts={c:sum(r['corpus']==c for r in review.values()) for c in ('ConEC','AMI')}
    css=hashlib.sha256((SITE/'assets/site.css').read_bytes()).hexdigest()[:12]
    title='Recording review appendix'
    html=[f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light dark"><meta name="description" content="Review each AMI and ConEC question in context with its speaker-labelled transcript."><title>{title} · AI2AI Duplex</title><link rel="stylesheet" href="../assets/site.css?v={css}"><style>{STYLE}</style></head><body>',
          '<a class="skip-link" href="#main">Skip to content</a><header class="site-nav"><div class="nav-inner"><a class="brand" href="../index.html">AI2AI Duplex</a>'+project_tabs('experiments','../')+'</div></header><div class="container collection-nav">'+experiment_subtabs('dataset')+'</div>',
          f'<main id="main" class="container review-wrap"><p><a href="question-dataset.html#demos">Back to the question dataset</a></p><h1>{title}</h1><p>Listen for whether the speaker finishes their thought before “Assistant.” The transcript follows the audio and identifies the requester.</p>',
          '<div class="review-controls" role="group" aria-label="Choose a corpus">'+''.join(f'<button type="button" data-filter="{c}">{c} ({counts[c]})</button>' for c in counts)+'</div>',
          '<label for="choose">Choose a recording and question</label><select id="choose"></select><div class="pager"><button id="prev" type="button">Previous</button><output id="counter" aria-live="polite"></output><button id="next" type="button">Next</button></div>']
    for key,r in items:
        label=r['meeting'].removeprefix('EC')+' · '+r['question']
        fingerprint=hashlib.sha256(''.join(t['sha256'] for t in r['tracks']).encode()).hexdigest()[:16]
        html.append(f'<article hidden data-version="{escape(key,quote=True)}-{fingerprint}"  data-key="{escape(key,quote=True)}" data-corpus="{r["corpus"]}" data-label="{escape(label,quote=True)}"><p class="minor">{escape(r["corpus"])} · {escape(r["meeting"].removeprefix("EC"))} · requester {escape(r["requester"])}</p><h2>{escape(r["question"])}</h2>')
        for t in r['tracks']:
            replay=max(0,t['request_at']-5)
            name='Conversation and question' if len(r['parts'])==1 else 'Two excerpts and question'
            if t['edited_part']:name+=f' · sound in excerpt {t["edited_part"]}'
            url='../'+t['file']+'?v='+t['sha256'][:10]
            html.append(f'<div class="player"><strong>{name}</strong><audio controls preload="none" src="{url}" aria-label="{escape(label,quote=True)} · {name}"></audio><button type="button" data-replay="{replay:.4f}">Play from 5 seconds before the question</button></div>')
        html.append('<h3>Clip transcript</h3><p class="minor">Times on the left are measured from the start of the player. Speaker labels come from the corpus. Overlapping remarks can share a time.</p>'+transcript(r))
        html.append('<details><summary>Independent transcript of the source audio</summary><p>Parakeet transcribed each source excerpt before sound edits and question insertion. It can miss quiet or overlapping voices.</p>')
        for n,part in enumerate(r['parts'],1):
            html.append(f'<p><b>Excerpt {n}.</b> {escape(part["full_asr"])}</p>')
        html.append('</details>')
        p=r['parts'][-1]
        html.append(f'<details><summary>Check the insertion against the source</summary><p>Source audio ends at <b>{stamp(p["end"])}</b> during a pause. Parakeet heard the following in the last few seconds of this excerpt.</p><blockquote>{escape(p["end_asr"])}</blockquote><p>The original conversation continues with <b>{escape(p["following"].split(" · ",1)[0])}</b> saying “{escape(p["following"].split(" · ",1)[-1])}”</p></details>')
        if r.get('speech_check_note'):html.append('<p>'+escape(r['speech_check_note'])+'</p>')
        if r.get('name_reference'):html.append('<a href="../'+escape(r['name_reference'],quote=True)+'">Hear the name in the original call</a>')
        html.append('</article>')
    html+=['<div class="rating"><label for="rating">Your review</label><select id="rating"><option value="">Unreviewed</option><option value="ok">Sounds right</option><option value="cut">Flag insertion</option><option value="transcript">Flag transcript</option><option value="voice">Flag voice</option></select><small id="storage">Marks are saved in this browser.</small></div>',
           '<p><a href="question-audio.html#alternate-voices">Archived AMI TTS comparisons</a> · <a href="../research/question-dataset/turn-review.json" download>Download the audio and transcript index</a></p>',
           '<noscript><p>Enable JavaScript to use the corpus buttons and recording selector. The <a href="../research/question-dataset/turn-review.json">audio and transcript index</a> also lists each recording.</p></noscript></main><script>'+JS+'</script></body></html>']
    (SITE/'experiments'/PAGE).write_text(''.join(html)+'\n')
