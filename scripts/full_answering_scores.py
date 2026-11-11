"""Readable tables and figures for the saved preliminary 105-question scores."""
import json
from html import escape as e
from pathlib import Path
from build_answering_results import table, link

P = Path(__file__).resolve().parents[1] / 'research/full-answering/preliminary'
ORDER = ['reactive', 'reactive_guided', 'summary_all', 'summary_latest', 'legacy_all',
         'legacy_latest', 'linked', 'linked_guided', 'linked_no_links_guided']
TIMING = ['reactive_guided', 'summary_latest_guided', 'legacy_latest_guided',
          'linked_guided', 'linked_no_links_guided']
CSS = '''
.results .score-warning{border-left:4px solid var(--accent);padding:.8rem 1rem;background:var(--bg-soft,var(--surface));margin:1rem 0}
.results .score-plot{max-width:100%;overflow-x:auto;background:white;border-radius:6px}
.results .score-plot img{min-width:760px;width:100%;max-width:none}
.results .score-controls{display:grid;grid-template-columns:1fr;gap:.7rem;max-width:100%}
.results .score-controls label{display:block;margin:0}.results .score-controls select{width:100%;min-width:0}
.results .score-buttons{display:flex;flex-wrap:wrap;gap:.5rem;margin:.7rem 0}
.results .score-buttons button{padding:.45rem .7rem;border:1px solid var(--border);border-radius:5px;background:var(--bg);color:var(--text);cursor:pointer}
.results .score-card{border-top:1px solid var(--border);padding:1rem 0;overflow-wrap:anywhere}
.results .score-reference{padding:.8rem 1rem;border-left:3px solid var(--border)}
.results .score-card dl{display:grid;grid-template-columns:minmax(8rem,auto) 1fr;gap:.3rem 1rem}
.results .score-card dd{margin:0}.results .score-card dt{font-weight:600}
.results .score-source{max-height:350px;overflow-y:auto}.results #score-status{min-height:1.5em}
.results .methods-appendix>summary{font-size:1.15rem}.results .methods-appendix section{scroll-margin-top:10rem}
@media(min-width:900px){.results .score-controls{grid-template-columns:2fr 2fr 1fr}}
'''

JS = r'''
(()=>{
 const $=id=>document.getElementById(id);
 const section=$('score-examples'); if(!section)return;
 let data=null, loading=null;
 const el=(tag,value,cls)=>{const n=document.createElement(tag);if(value!==undefined)n.textContent=value;if(cls)n.className=cls;return n;};
 function label(value){return value===null?'Awaiting score review':value?'Yes':'No';}
 function render(){
  if(!data)return;
  const qid=$('score-question').value, setting=$('score-setting').value, seed=$('score-seed').value;
  const q=data.questions.find(q=>q.id===qid), host=$('score-answer-list');host.replaceChildren();
  const intro=el('div',undefined,'score-reference');intro.append(el('p','Question: '+q.question),el('p','Reference answer: '+q.reference_answer));
  const required=el('ol');q.minimum_facts.forEach(f=>required.append(el('li',f)));intro.append(el('p','Minimum facts required:'),required);
  const sources=el('details'), summary=el('summary','Reference speech excerpts');sources.append(summary);
  const speech=el('ul',undefined,'score-source');q.source_evidence.forEach(s=>speech.append(el('li',
   (s.speaker||'Speaker')+' · '+(s.start===undefined?'':s.start.toFixed(2)+' s')+' · '+s.text)));
  sources.append(speech);intro.append(sources);host.append(intro);
  const rows=data.answers.filter(r=>r.question_id===qid&&r.setting===setting&&(seed==='all'||String(r.seed)===seed));
  rows.forEach(r=>{
   const card=el('article',undefined,'score-card');card.append(el('h4',$('score-setting').selectedOptions[0].textContent+' · seed '+r.seed));
   card.append(el('div',r.answer||'No native text was produced in the selected response window.','native'));
   const scores=el('dl');[
    ['Required facts correct',label(r.required_facts_correct)],['Fully supported answer',label(r.fully_supported)],
    ['Request-time thinking tokens',r.thinking_tokens===null?'Not exposed by this model':r.thinking_tokens.toLocaleString()],
    ['Time to first answer text',r.first_answer_seconds===null?'Not available for this output':r.first_answer_seconds.toFixed(2)+' seconds']
   ].forEach(([k,v])=>scores.append(el('dt',k),el('dd',v)));card.append(scores);
   if(r.score_validation_errors.length){const reasons=r.score_validation_errors.map(code=>code.startsWith('invalid_source_id:')?'The evaluator cited a transcript passage that was not supplied ('+code.split(':').slice(1).join(':')+').':code==='incomplete_core_judge_output'?'The evaluator did not produce a complete required-fact check.':'The evaluator response did not pass its format checks.');card.append(el('p','This automatic score needs review. '+reasons.join(' ')));}
   const facts=el('ul');r.fact_checks.forEach(f=>facts.append(el('li',f.id.replace(/^F([0-9]+)$/,'Fact $1')+' · '+f.status+': '+f.reason)));
   card.append(el('p','Automatic evaluator fact checks:'),facts);
   if(r.unsupported_claims.length){const list=el('ul');r.unsupported_claims.forEach(c=>list.append(el('li',typeof c==='string'?c:JSON.stringify(c))));card.append(el('p','Claims flagged as unsupported:'),list);}
   if(r.question_onset_answer!==null&&r.question_onset_answer!==r.answer){const extra=el('details');extra.append(el('summary','Alternative S1 window: include text emitted during the question'),el('div',r.question_onset_answer||'No native text.','native'),el('p','Fully supported: '+label(r.question_onset_fully_supported)));card.append(extra);}
   host.append(card);
  });
  if(!rows.length)host.append(el('p','No saved answer matches this seed; select all saved seeds.'));
  $('score-status').textContent=rows.length+' saved answer'+(rows.length===1?'':'s')+' shown for '+q.meeting+'. Scores are preliminary.';
 }
 async function load(){
  const button=$('score-load');button.disabled=true;$('score-status').textContent='Loading saved answers…';
  try{if(!loading)loading=fetch(section.dataset.source).then(r=>{if(!r.ok)throw new Error('HTTP '+r.status);return r.json();});data=await loading;render();button.textContent='Show selected answers';}
  catch(error){loading=null;$('score-status').textContent='Could not load saved answers: '+error.message;}
  finally{button.disabled=false;}
 }
 $('score-load').addEventListener('click',load);
 ['score-question','score-setting','score-seed'].forEach(id=>$(id).addEventListener('change',()=>{if(id==='score-setting')$('score-seed').value='all';if(data)render();}));
 document.querySelectorAll('[data-score-example]').forEach(b=>b.addEventListener('click',()=>{$('score-question').value=b.dataset.scoreExample;$('score-setting').value='S2|instruct|reactive';$('score-seed').value='all';load();}));
 function reveal(){const target=document.getElementById(decodeURIComponent(location.hash.slice(1)));if(!target)return;for(let p=target;p;p=p.parentElement)if(p.tagName==='DETAILS')p.open=true;requestAnimationFrame(()=>{const nav=document.querySelector('.site-nav');window.scrollTo({top:scrollY+target.getBoundingClientRect().top-(nav?nav.getBoundingClientRect().bottom:0)-18,behavior:'instant'});});}
 addEventListener('hashchange',reveal);addEventListener('load',reveal);
})();
'''


def percent(metric):
    return '—' if metric['mean'] is None else f"{100*metric['mean']:.1f}%"


def number(metric, decimals=0):
    return '—' if metric['mean'] is None else f"{metric['mean']:,.{decimals}f}"


def figure(index, name, caption, alt):
    base = '../research/full-answering/preliminary/' + name
    return ('<figure id="fig-'+name+'"><div class="score-plot"><img loading="lazy" src="'+base+'.svg" alt="'+e(alt, quote=True)+'"></div>'
            '<figcaption><strong>Figure '+str(index)+'.</strong> '+e(caption)+' '+link(base+'.svg','SVG')+' · '+link(base+'.pdf','PDF')+'</figcaption></figure>')


def render():
    d = json.loads((P / 'summary.json').read_text())
    settings = {r['key']: r for r in d['settings']}
    base = '../research/full-answering/preliminary/'
    body = '<section id="scores"><h2>2. Preliminary scores on 105 questions</h2>'
    body += '<div class="score-warning"><strong>Saved automatic scores; final source review pending.</strong> These scores were generated on November 5. This publication adds tables, figures and answer inspection from the saved files. Experiments and automatic controllers remain paused; no new inference or scoring was run.</div>'
    body += '<p><strong>Required-fact accuracy</strong> is the percentage of answers containing all minimum facts needed to answer the question. <strong>Fully supported accuracy</strong> also requires the absence of material unsupported claims. An empty reply or an acknowledgement without the required facts fails both scores.</p>'
    body += '<p>All conditions use the same 105 distinct questions across 26 meetings. Qwen3 Thinking has two seeds in the main accuracy run; their scores are averaged within each question. Instruct has one greedy run. Three unique judge verdicts need review: two affect primary scores and one affects the alternative S1 response window. Unresolved scores are omitted from the percentages and shown in the scored-answer counts.</p>'
    body += '<p>'+link(base+'summary.csv','Download summary tables (CSV)')+' · '+link(base+'summary.json','Saved means, confidence intervals and paired comparisons (JSON)')+' · '+link(base+'scored-answers.json','All scored final answers and fact checks (JSON)')+'</p>'
    body += '<nav class="jump-links" aria-label="Score sections">'+''.join(link('#'+a,t) for a,t in [('s1-scores','Audio models'),('text-scores','Text thinkers'),('controlled-timing','Controlled timing'),('cost-score','Token cost'),('score-examples','Inspect answers')])+'</nav>'
    body += '<div id="s1-scores"><h3>Audio models and thinkers with reference transcripts</h3><p>With all supplied history, MiniCPM produces fully supported answers on 25.7% of questions and Moshi on 0.0%; reactive thinkers with reference transcripts score 87.6% (Figure 1). Audio systems receive recordings through their native loops. The text thinkers receive annotated transcripts and speaker labels; model size, modality and retained context differ across these systems.</p>'
    body += figure(1,'audio-text-accuracy','All supplied audio versus reactive thinking with reference transcripts. Points show fully supported accuracy; bars show saved 95% confidence intervals from resampling meetings. Each system covers 105 questions.','Fully supported accuracy: Moshi 0%, MiniCPM 25.7%, reactive Qwen3 Instruct and Thinking both 87.6%.')
    rows=[]
    for model in ['moshi','minicpm']:
        for condition in ['request_only','recent_240s','full']:
            r=settings['S1|'+model+'|'+condition]
            rows.append([e(r['model_label']),e(r['label']),percent(r['core_correct']),percent(r['supported_correct']),f"{r['valid_outputs']}/{r['outputs']}"])
    body += table(2,'Native text scores for the three audio-history conditions.',['Model','Supplied audio history','Required facts','Fully supported','Answers scored'],rows)
    body += '<p class="small">The primary native-text window is the first 19.2 seconds after the supplied input ends. All histories use the same full-prefix reference. MiniCPM’s question-only row has one unresolved score, so its percentages use 104 scored questions. DuplexOmni has 154/315 completed input cases and has not yet been scored; it is excluded from these accuracy plots.</p></div>'
    body += '<div id="text-scores"><h3>Text S2 with reference transcripts: saved notes and thinker prompts</h3><p>Instruct scores 91.4% fully supported answers with the focused reactive prompt and 90.5% with source notes plus that prompt. Thinking scores 90.0% and 87.6%, respectively. These point estimates do not establish an accuracy gain from adding source notes. Figure 2 shows the full condition comparison; Tables 3 and 4 give the exact percentages.</p>'
    body += figure(2,'text-method-accuracy','Fully supported accuracy for the nine saved main-run conditions. The axis runs from 60% to 100%; error bars are saved 95% confidence intervals from resampling meetings. Thinking seeds are averaged within each question.','Nine-condition accuracy comparison for Instruct and Thinking, with confidence intervals.')
    for model, index in [('instruct',3),('thinking',4)]:
        rows=[]
        for condition in ORDER:
            r=settings['S2|'+model+'|'+condition]
            row=[e(r['label']),percent(r['core_correct']),percent(r['supported_correct'])]
            if model=='thinking':row.append(number(r['native_thinking_tokens']))
            row.append(f"{r['valid_outputs']}/{r['outputs']}");rows.append(row)
        headers=['Condition','Required facts','Fully supported']+(['Request thinking tokens'] if model=='thinking' else [])+['Answers scored']
        body += table(index,d['models'][model]+' with the complete available reference transcript.',headers,rows)
    body += '<p class="small">Thinking token counts are mean native reasoning tokens generated after the question. Earlier note-generation tokens are counted separately below. Instruct does not expose a separate thinking channel. The source-notes-without-links row has 209/210 valid Thinking scores; all 105 questions contribute, with one question having only one valid seed.</p></div>'
    body += '<div id="controlled-timing"><h3>Controlled timing: no established response-latency gain</h3><p>The isolated timing run contains 105 questions in each of five conditions, using Thinking seed 23, serial requests and a cleared prefix cache. Every condition uses the focused thinker prompt. Source notes average 1,533 request-time thinking tokens versus 1,616 for reactive thinking, while first answer text arrives at about 10 seconds in both conditions. The saved paired confidence intervals include zero for accuracy, thinking tokens and latency.</p>'
    rows=[]
    for condition in TIMING:
        r=settings['S2_latency|thinking|'+condition]
        rows.append([e(r['label']),percent(r['supported_correct']),number(r['native_thinking_tokens']),number(r['first_answer_seconds'],2),number(r['complete_output_seconds'],2),f"{r['first_answer_seconds']['questions']}/105"])
    body += table(5,'Isolated serial timing and automatic accuracy; every condition has 105 saved outputs.',['Condition','Fully supported','Request thinking tokens','First answer (s)','Complete output (s)','First-answer times recorded'],rows)
    body += '<p>On the 103 questions with first-answer measurements in both the reactive and source-note conditions, source notes change latency by +0.03 seconds (95% interval: −1.45 to +1.55 seconds). Among 81 questions where both answers are automatically scored as fully supported and both times are available, the difference is +0.22 seconds (−1.51 to +2.32 seconds).</p>'
    body += figure(3,'paired-timing-differences','Paired changes relative to reactive thinking with the same focused prompt. Negative thinking-token and time differences mean lower request cost; positive accuracy differences mean higher accuracy. Bars are saved 95% intervals from resampling meetings; timing comparisons use only questions with both measurements.','Paired accuracy, thinking-token and first-answer latency differences; all displayed intervals include zero.')
    body += '<p class="small">A missing first-answer timestamp remains missing and is counted in the final column of Table 5; it is not replaced by zero. Main accuracy-run request times include concurrent requests and are kept separate from this isolated latency comparison.</p></div>'
    body += '<div id="cost-score"><h3>Earlier thinking and total generated tokens</h3><p>Reducing request-time thinking does not remove the earlier note-generation work. Figure 4 and Table 6 count one earlier writer pass over the 26 meetings, including unused updates and revision checks, plus the 105 controlled-timing requests for each condition.</p>'
    body += figure(4,'total-generated-tokens','Generated-token accounting for one shared meeting pass and 105 requests, all with the focused prompt. Earlier outputs, request-time reasoning, and answer and format outputs are separated. Bars are alternative method costs and should not be summed across methods.','Stacked earlier and request-time generated-token costs for five methods.')
    rows=[]
    for r in d['generated_token_cost']:
        rows.append([e(r['label']),f"{r['earlier_generated_tokens']:,}",f"{r['request_thinking_tokens']:,}",f"{r['request_answer_and_delimiter_tokens']:,}",f"{r['total_generated_tokens']:,}"])
    body += table(6,'Generated tokens, counted once per method over the shared meeting streams.',['Condition','Earlier generation','Request thinking','Answer + format tokens','Total generated'],rows)
    body += '<p class="small">Generated format tokens mark boundaries in model output and are included with the answer tokens. These are generated-token counts. Logical input-token counts and input limits appear in the methods appendix; token counts alone do not measure total GPU work or live readiness. Source notes with and without links reuse the same writer outputs.</p></div></section>'
    answer_data=json.loads((P/'scored-answers.json').read_text())
    questions=sorted(answer_data['questions'],key=lambda q:(q['meeting'],q['insertion_seconds'],q['id']))
    default='scale:IB4003-S075-Q3'
    body += '<section id="score-examples" data-source="'+base+'scored-answers.json?v='+d['answers_sha256'][:16]+'"><h2>Inspect an answer and its score</h2><p>Choose a question and condition to inspect the exact saved final answer, minimum reference facts, source speech and automatic fact checks. Thinking conditions show both seeds unless a seed is selected. Each card shows the final answer and its score.</p><div class="score-controls"><label for="score-question">Question<select id="score-question" aria-label="Question">'
    body += ''.join('<option value="'+e(q['id'],quote=True)+'"'+(' selected' if q['id']==default else '')+'>'+e(q['meeting']+' · '+q['question'])+'</option>' for q in questions)+'</select></label><label for="score-setting">Model and condition<select id="score-setting" aria-label="Model and condition">'
    body += ''.join('<option value="'+e(r['key'],quote=True)+'"'+(' selected' if r['key']=='S2|instruct|reactive' else '')+'>'+e(('Controlled timing · ' if r['family']=='S2_latency' else '')+r['model_label']+' · '+r['label'])+'</option>' for r in d['settings'])
    body += '</select></label><label for="score-seed">Seed<select id="score-seed" aria-label="Seed"><option value="all">All saved seeds</option><option value="23">23</option><option value="47">47</option></select></label></div><div class="score-buttons"><button type="button" id="score-load">Load saved answers</button><button type="button" data-score-example="'+default+'">Example: office headcount</button></div><p id="score-status" role="status" aria-live="polite">Answers load when requested.</p><div id="score-answer-list"></div><noscript><p>'+link(base+'scored-answers.json','Download the answers and scores')+'</p></noscript></section>'
    return body
