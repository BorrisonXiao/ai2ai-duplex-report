"""Reviewed periodic-overview pilot, appended to the established S2 report."""
import base64
import json
from html import escape as e

MODELS={'instruct':'Qwen3 Instruct','thinking':'Qwen3 Thinking','qwen-thinking':'Qwen3-Omni Thinking','minicpm':'MiniCPM-o 4.5'}
VOICES={'ground_truth_transcript':'Reference transcript','audio_only':'Audio alone','labelled_voices':'Labelled past voices'}


def condition(name):
    if name=='reactive':return 'Reactive'
    if name=='function_notes':return 'Detailed notes'
    stem,period=name.rsplit('_p',1)
    content={'overview_topics':'Topics','overview_topics_speakers':'Topics + speakers','overview_topics_speakers_voice':'Topics + speakers + voice'}[stem]
    return content+' / '+period+' chunks'


def render(root,table,link):
    d=json.loads((root/'research/note-functions/periodic-overview-results.json').read_text())
    rows=[r for r in d['summary']if r['input_order']!='overview_after_question']
    def get(model,identity,name):
        return next(r for r in rows if (r['model'],r['identity'],r['condition'])==(model,identity,name))
    def number(value,digits=0):return '—'if value is None else f'{value:,.{digits}f}'
    def time(r):
        if r['model']=='instruct':return 'Batched; excluded'
        return number(r['first_answer_seconds_mean'],2)+(f" ({r['first_answer_timed']}/8 timed)"if r['first_answer_timed']!=8 else'')
    def cells(r):return [MODELS[r['model']],VOICES[r['identity']],condition(r['condition']),str(r['supported'])+'/8',number(r['thinking_tokens_mean']),time(r),number(r['cost']['complete_generated_tokens'])]
    body='<section id="periodic-overviews"><h2>3. Periodic conversation overviews: eight-question pilot</h2><ul>'
    body+='<li>All 608 evaluation records are saved and source-checked across eight questions from five meetings.</li>'
    body+='<li>Text Thinking shows no joint improvement in answer quality and first-answer time over Reactive.</li>'
    body+='<li>With audio alone, one Qwen overview setting matches detailed notes at 7/8 and reduces request-time thinking by 17.2%, while adding earlier generation cost.</li>'
    body+='<li>MiniCPM frequently repeats the question or produces corrupted text, so its short onset times give little evidence of useful answering.</li>'
    body+='<li>The new overview methods have not yet been evaluated on all 105 questions.</li></ul>'
    body+='<p>Every pilot row evaluates the same eight questions at seed 23. The 480 main evaluations cover text and audio conditions; a further 128 text evaluations check input order, and 20 source-only probes inspect overview generation. Reused controls appear in these matched comparisons without being counted as new questions. These are descriptive development results; the earlier 105-question tables retain their published scope and labels.</p>'
    body+='<p><strong>Inputs:</strong> Reactive receives the available history and the question; Detailed notes adds the current function-call notes; overview conditions add a compact analysis of the broad topic, current discussion, speakers and, for audio, optional voice delivery or tentative emotion. Every condition retains the same raw history within its model and speaker condition. The text writer receives new reference-transcript segments, recent detailed facts and its previous overview; audio writers receive the corresponding new audio, audio-derived facts and previous overview. The final text prompt places the question last.</p>'
    body+='<p><strong>Update period:</strong> every 2, 4 or 8 processed chunks corresponds to mean intervals of 60.5, 121.0 or 241.8 seconds in the frozen streams. Chunk boundaries are unchanged; no update is triggered by the future question. Versioned function calls retain earlier changes while the current overview is limited to 768 tokens.</p>'
    selected=[]
    for model,identity,names in [('thinking','ground_truth_transcript',['reactive','function_notes','overview_topics_p8','overview_topics_speakers_p8']),('qwen-thinking','audio_only',['reactive','function_notes','overview_topics_speakers_voice_p4']),('qwen-thinking','labelled_voices',['reactive','function_notes','overview_topics_p8'])]:
        selected += [get(model,identity,name)for name in names]
    body+=table(5,'Selected pilot settings; each row has eight questions and source-checked labels. Thinking and first-text time are per-request means; complete generation counts all eight requests and every earlier update once per meeting and speaker condition.',['Model','Speaker input','Condition / period','Fully supported','Thinking tokens','First text (s)','Complete generated tokens'],[cells(r)for r in selected])
    body+='<p>Table 5 highlights settings that explain the observed patterns; all tested periods and contents appear below. For text Thinking, Topics every eight chunks uses 1,498 thinking tokens versus 1,565 for Reactive, but first text starts at 14.34 versus 14.03 seconds. Both score 6/8 under the frozen checklist. Among the six pairs where both answers are fully supported, the mean reduction is only 44.5 thinking tokens. Topics plus speakers at the same period instead uses 2,160 tokens and 19.92 seconds.</p>'
    q=get('qwen-thinking','audio_only','overview_topics_speakers_voice_p4');fine=get('qwen-thinking','audio_only','function_notes')
    change=100*(q['cost']['complete_generated_tokens']/fine['cost']['complete_generated_tokens']-1)
    body+='<p>For Qwen audio alone, Topics + speakers + voice every four chunks and Detailed notes support the same seven answers. The overview reduces thinking from 1,118 to 926 tokens and mean first-text time from 11.00 to 9.62 seconds. Complete generation increases by '+number(change,1)+'%. Reactive is faster at 372 thinking tokens and 4.78 seconds, with 6/8 supported answers. The overview result is a candidate for confirmation; this pilot does not isolate which of topic, speaker or voice entries accounts for the change.</p>'
    instr=[r for r in rows if r['model']=='instruct'];mini=[r for r in rows if r['model']=='minicpm']
    body+='<p>Instruct has '+str(min(r['supported']for r in instr))+'–'+str(max(r['supported']for r in instr))+'/8 fully supported answers across settings, with no exposed native thinking channel and batched baseline timing. MiniCPM ranges from '+str(min(r['supported']for r in mini))+' to '+str(max(r['supported']for r in mini))+'/8; 8/176 outputs are empty and 37/176 reach the output limit. Qwen has 2/176 empty final outputs, concentrated in the labelled-voice conditions. Empty and capped generations remain in all accuracy denominators and token totals; first-text means state how many nonempty outputs are timed.</p>'
    image=(root/'research/note-functions/periodic-overview-cost.png').read_bytes()
    body+='<figure id="fig-periodic-overview-cost"><div class="overview-plot"><img src="data:image/png;base64,'+base64.b64encode(image).decode()+'" alt="Selected eight-question pilot: native request-time thinking above and complete generated token cost below for text Thinking and Qwen audio alone."></div><figcaption><strong>Figure 3.</strong> Selected pilot settings with the question last in text prompts. Top panels show mean request-time native thinking and fully supported counts; bottom panels count all generated tokens for eight requests, including earlier detailed-note and overview updates once per meeting. Vertical scales differ between panels; token counts are compared within each model. These descriptive results have no error bars. '+link('../research/note-functions/periodic-overview-cost.pdf','PDF')+' · '+link('../research/note-functions/periodic-overview-cost.svg','SVG')+' · '+link('../research/note-functions/periodic-overview-cost.png','Full-size PNG')+'</figcaption></figure>'
    body+='<details id="overview-all-settings"><summary>All periods, speaker conditions and input costs</summary><p>Each condition adds its named overview to detailed notes; Reactive has neither. Complete input tokens count all processed prompts, and complete generated tokens include earlier writing plus request-time reasoning, final text and control tokens. The same earlier notes may be reused physically between experiments, but each hypothetical condition is charged its full required work.</p>'
    index=6
    for model,identity in [('instruct','ground_truth_transcript'),('thinking','ground_truth_transcript'),('qwen-thinking','audio_only'),('qwen-thinking','labelled_voices'),('minicpm','audio_only'),('minicpm','labelled_voices')]:
        data=[r for r in rows if(r['model'],r['identity'])==(model,identity)]
        data.sort(key=lambda r:(0 if r['condition']=='reactive'else 1 if r['condition']=='function_notes'else 2,r['condition']))
        body+=table(index,MODELS[model]+' · '+VOICES[identity]+'; eight questions per row, source-checked labels.',['Condition / period','Fully supported','Required facts','Thinking tokens','First text (s)','Complete input tokens','Complete generated tokens'],[[condition(r['condition']),str(r['supported'])+'/8',str(r['required_facts'])+'/8',number(r['thinking_tokens_mean']),time(r),number(r['cost']['complete_input_tokens']),number(r['cost']['complete_generated_tokens'])]for r in data]);index+=1
    body+='</details><details id="overview-input-order"><summary>Input-order control: why the apparent text saving changed</summary><p>The initial text prompt placed the added overview after the user question; the control moves the same question to the end while retaining the same transcript, saved notes, overview and decoding settings. Table 12 shows that the earlier Topics + speakers result is sensitive to this ordering. The main pilot comparisons use the question-last condition consistently.</p>'
    order=[]
    for name in ['overview_topics_p8','overview_topics_speakers_p8']:
        for mode,label in [('overview_after_question','Overview after question'),('request_last','Question last')]:
            r=next(r for r in d['summary']if r['model']=='thinking'and r['condition']==name and r['input_order']==mode)
            order.append([condition(name),label,str(r['supported'])+'/8',number(r['thinking_tokens_mean']),time(r)])
    body+=table(12,'Text Thinking input-order check on the same eight questions; saved overview content is identical.',['Condition','Input order','Fully supported','Thinking tokens','First text (s)'],order)+'</details>'
    body+='<details id="overview-grounding"><summary>Actual saved-note errors and source-input probes</summary><p>Source inspection found two distinct problems: a brief side discussion can become a false meeting theme, and a mistaken owner in detailed notes can be copied into the higher-level overview. These observations establish errors in saved notes; they do not establish that each error caused a particular final-answer failure.</p>'
    for ex in d['overview_examples']:
        body+='<article class="case-card"><h3>'+e(ex['meeting'])+' at '+number(ex['source_cutoff'],1)+' seconds</h3><p>'+e(ex['explanation'])+'</p>'
        if ex.get('prior_detailed_note'):body+='<p><strong>Earlier detailed note:</strong> '+e(ex['prior_detailed_note'])+'</p>'
        body+='<p><strong>Generated overview:</strong></p><pre class="native">'+e(json.dumps(ex['generated'],indent=2,ensure_ascii=False))+'</pre>'
        if ex.get('full_prefix_probe'):body+='<p><strong>Later source-only probe with the full available transcript:</strong></p><pre class="native">'+e(json.dumps(ex['full_prefix_probe'],indent=2,ensure_ascii=False))+'</pre>'
        body+='<ul>'+''.join('<li>'+e(u['id']+' · '+u['speaker']+': '+u['text'])+'</li>'for u in ex['source_evidence'])+'</ul></article>'
    body+='<p>The 20 source-only probes compare the full transcript with and without compact detailed facts at five checkpoints for Instruct and Thinking. They recover the remote-control theme in the air-conditioning example, but several outputs omit speaker entries, so this test does not establish reliable identity analysis. A successful name example is D’s explicit introduction as Freek Van Ponnen, Market Expert; inferred names and relationships still require source support.</p></details>'
    body+='<details id="overview-scoring"><summary>Pilot scoring, cost accounting and execution scope</summary><ul><li>Codex checked every distinct final answer against the complete past reference transcript and the frozen minimum-fact checklist; exact same-question answers reuse that decision, and empty final answers count as failures.</li><li>Fully supported correctness requires all requested facts and no material unsupported additions; source-location errors and minor non-verbatim paraphrases are recorded separately when the answer content remains correct.</li><li>The frozen poster-session checklist requires the earlier 36-talk maximum, the revised 30-talk plan and a half-day poster allocation; the browser separately states whether the answer gets the 36-to-30 comparison right.</li><li>Two reused poster-answer strings had earlier source labels that accepted counts alone; this pilot corrects those labels consistently, while preserving the historical 105-question results.</li><li>All available raw history is retained in this pilot; the current overview is extra input, so it does not reduce transcript or audio length.</li><li>Every earlier detailed-note and overview call is charged once per meeting and speaker condition up to its last evaluated request, including invalid edits and unused updates; input and generated-token costs remain separate.</li><li>Each job used one A100 SXM4 80 GB, with model weights, audio encoder where used and an 8 GiB KV cache on GPU 0; writer and answer stages shared a job-private vLLM engine, with no shared service or TTS.</li><li>Text and audio jobs used two independent lanes with at most two GPUs active; all pilot jobs are complete, and this report update uses zero GPUs.</li><li>Final pilot, probe and input-order jobs used 3.025 GPU hours; including earlier prompt-development attempts raises this to 3.391 GPU hours, excluding the historical generation of reused detailed notes.</li><li>The source cutoffs are causal, while real-time completion of background writing remains untested; first-text time is measured from the question-time model call, with audio loading and preprocessing included for audio models.</li></ul></details>'
    body+='<details id="overview-answers"><summary>Browse all pilot answers and source checks</summary><div class="case-controls"><label>Question<select id="overview-question">'+''.join('<option value="'+e(c['id'],quote=True)+'">'+e(c['meeting']+' · '+c['question'])+'</option>'for c in d['cases'])+'</select></label><label>Model<select id="overview-model">'+''.join('<option value="'+m+'"'+(' selected'if m=='thinking'else'')+'>'+label+'</option>'for m,label in MODELS.items())+'</select></label><label>Text input order<select id="overview-order"><option value="request_last">Question last</option><option value="overview_after_question">Original: overview last</option></select></label></div><button id="overview-load" type="button">Load pilot answers</button><p id="overview-status" role="status">Answer text loads on request.</p><div id="overview-answer-list"></div></details>'
    body+='<p>'+link('../research/note-functions/periodic-overview-results.json','Reviewed pilot data, counters and full cost breakdown (JSON)')+' · '+link('../todo.html#periodic-overview-study','Checklist and full-evaluation gate')+'</p></section>'
    return body, JS.replace('OVERVIEW_MODELS',json.dumps(MODELS)).replace('OVERVIEW_VOICES',json.dumps(VOICES)), CSS


CSS='.overview-plot{background:white;padding:.5rem;overflow-x:auto}.overview-plot img{display:block;width:100%;min-width:680px;height:auto}#periodic-overviews .table-wrap{overflow-x:auto}#periodic-overviews table{min-width:850px}#periodic-overviews th{white-space:normal;min-width:5rem}#periodic-overviews td{vertical-align:top}#overview-answer-list pre{max-height:16rem}#periodic-overviews details details{margin:.5rem 0}'

JS=r'''
(()=>{
const $=id=>document.getElementById(id),models=OVERVIEW_MODELS,voices=OVERVIEW_VOICES;
let data=null;
const make=(tag,text,cls)=>{const node=document.createElement(tag);if(text!==undefined)node.textContent=text;if(cls)node.className=cls;return node;};
function name(value){if(value==='reactive')return 'Reactive';if(value==='function_notes')return 'Detailed notes';return value.replace('overview_','').replaceAll('_',' ').replace(/ p(\d+)$/,' · every $1 chunks');}
function render(){
 if(!data)return;const q=data.cases.find(c=>c.id===$('overview-question').value),model=$('overview-model').value,host=$('overview-answer-list');host.replaceChildren();
 host.append(make('h3',q.question),make('p',q.meeting+' · question at '+(q.at_seconds/60).toFixed(2)+' minutes.'));
 const facts=make('ul');q.required_facts.forEach(f=>facts.append(make('li',f)));host.append(make('p','Frozen required facts:'),facts);
 const src=make('details');src.append(make('summary','Supporting transcript excerpts'));const list=make('ul');q.source_evidence.forEach(u=>list.append(make('li',u.id+' · '+u.speaker+' · '+u.start.toFixed(2)+' s: '+u.text)));src.append(list);host.append(src);
 const rows=data.answers.filter(r=>r.question_id===q.id&&r.model===model&&(r.input_order==='audio_native'||r.input_order===$('overview-order').value));
 rows.sort((a,b)=>(a.condition==='reactive'?-2:a.condition==='function_notes'?-1:0)-(b.condition==='reactive'?-2:b.condition==='function_notes'?-1:0)||a.identity.localeCompare(b.identity)||a.condition.localeCompare(b.condition));
 rows.forEach(r=>{const c=make('article',undefined,'case-card');c.append(make('h4',name(r.condition)+' · '+voices[r.identity]),make('pre',r.answer||'[No final answer text]','native'));
 c.append(make('p','Source check: '+(r.score.supported_correct?'fully supported':r.score.core_correct?'required facts supplied; an additional claim is unsupported':'does not supply the full required facts')+' · Codex source review.'));
 c.append(make('p',r.source_review.reason));
 const p=data.poster_count_only_sensitivity.find(x=>x.id===r.id);if(p)c.append(make('p','Narrow count-only check: '+(p.talk_count_change_only?'states the 36-to-30 change':'does not correctly state the 36-to-30 change')+'; the primary checklist also requires the half-day poster allocation.'));
 c.append(make('p','Request-time thinking: '+(r.request_thinking_tokens===null?(model==='minicpm'?'disabled in this setup':'not exposed'):r.request_thinking_tokens.toLocaleString()+' tokens')+'; request generation: '+r.generated_tokens.toLocaleString()+' tokens; first text: '+(r.first_answer_seconds===null?'unavailable':r.first_answer_seconds.toFixed(2)+' s')+'.'));
 if(r.finish_reason==='length')c.append(make('p','Generation reached the output-token limit.'));host.append(c);});
 $('overview-status').textContent=rows.length+' source-checked answer records shown; eight unique questions in this pilot.';
}
$('overview-load').addEventListener('click',async()=>{const b=$('overview-load');b.disabled=true;try{if(!data){const r=await fetch('../research/note-functions/periodic-overview-results.json');if(!r.ok)throw Error('HTTP '+r.status);data=await r.json();}render();}catch(error){$('overview-status').textContent='Could not load pilot results: '+error.message;}finally{b.disabled=false;}});
['overview-question','overview-model','overview-order'].forEach(id=>$(id).addEventListener('change',render));
})();
'''
