"""Verbatim category examples, complete appendix and time-aligned trace controls."""
import json
import re
from pathlib import Path
from build_site import e,link,p,small,table

ROOT=Path(__file__).resolve().parents[1]

def load_traces():return json.loads((ROOT/'research/prethinking-pilot/traces.json').read_text())

def verbatim(text):
    # Preserve literal model whitespace in the DOM without trailing whitespace in HTML source.
    return re.sub(r'[ \t]+(?=\r?\n|$)',lambda m:''.join('&#32;' if c==' ' else '&#9;' for c in m[0]),e(text))

def example_table(data,traces):
    calls={c['index']:c for c in traces['calls']};chunks={c['id']:c for c in data['chunks']};rows=[]
    for item in data['trace_examples']:
        call=calls[item['call_index']]
        assert call['private_reasoning'][item['cot_start']:item['cot_end']]==item['cot_excerpt']
        context=[]
        for ident in item['transcript_chunk_ids']:
            c=chunks[ident];assert c['available']<=call['at']
            context.append('<div class="trace-example-source">'+small(ident+' · '+c['speaker']+' · '+f"{c['start']:.2f}–{c['end']:.2f} s")+'<blockquote>'+e(c['text'])+'</blockquote></div>')
        rows.append([e(item['category'])+small('Grounded excerpt' if item['status']=='useful_partial' else 'Failure example'),
            ''.join(context),'<pre class="trace-excerpt">'+verbatim(item['cot_excerpt'])+'</pre>'+link('Full thinking and prompt · call '+str(call['index']),'#appendix-call-'+str(call['index']),'trace-link'),
            e(item['assessment'])])
    return table('pilot-categories',0,'Actual transcript and verbatim Qwen thinking excerpts. “Grounded excerpt” applies to the selected passage, not its whole trace; failure examples are labeled.',
        ['Category / assessment','Actual transcript / speaker / source time','Actual private-thinking excerpt','Why it is useful, or what fails'],rows)

def thinking_figure():
    return '''<figure class="pilot-figure" id="thinking-timeline"><h3>Transcript above, generated thinking below</h3><p>The upper lanes show actual transcript text over its original speech duration. Each lower block starts after a delivered input update and contains the recorded thinking conditioned on that update and its earlier context. Move the cursor to inspect how many captured tokens have been emitted. Token ticks appear when space permits; a close view exposes individual token text.</p><div class="pilot-controls"><label>History condition<select id="thinking-history"><option value="raw_private">Retained private history</option><option value="reset">Reset control</option></select></label><label>Seed<select id="thinking-seed"><option value="17">17</option><option value="29">29</option></select></label><label>View<select id="thinking-window"><option value="575,675">Participation-count sequence</option><option value="590,600">First thought, close view</option><option value="590.5,592.5">First tokens, two-second view</option><option value="75,175">Commitments</option><option value="1785,1860">Deadline discussion</option></select></label><label>Focus<select id="thinking-call"><option value="sequence">Archived 10/60-tokens/s sequence</option></select></label></div><label for="thinking-cursor">Conversation time: <output id="thinking-cursor-label">625.00 s</output></label><input id="thinking-cursor" type="range" min="575" max="675" step="0.01" value="625"><p class="scroll-note">Scroll horizontally for the full time axis. Transcript and thinking previews wrap within their blocks; click a block for its exact text and appendix link.</p><p id="thinking-method" class="trace-method"></p><div class="thinking-scroll" tabindex="0" role="region" aria-label="Time-aligned transcript and captured teacher thinking"><svg id="thinking-svg" viewBox="0 0 1600 680" role="img" aria-labelledby="thinking-title"><title id="thinking-title">Actual transcript chunks and captured pre-thinking tokens</title></svg></div><div id="thinking-counts" class="thinking-counts" aria-live="polite"></div><div class="trace-inspector" id="thinking-inspector" aria-live="polite"></div><figcaption>Figure 2. Actual transcript spans and Qwen thinking are aligned to the conversation clock. Archived 10/60-tokens/s runs contain real, separately budgeted outputs; their displayed emission times assume uniform token rates and 0.5 s setup, not measured streaming timestamps. The 30/100 rows project captured 60-rate traces with fixed original prompts/history and do not represent new causal replays. Projection stops at the next input update or the recorded token cap, with no invented continuation. Selecting a scout call makes all four rate rows projections of that one recorded call. The appendix preserves every complete captured output, including budget-truncated endings.</figcaption></figure>'''

def appendix(data,traces):
    chunks={c['id']:c for c in data['chunks']}
    result=p('All 64 calls from job 1071792 are included below, with the exact executed prompt, the complete captured private-thinking output and the new transcript chunks that triggered the call. Outputs are externally generated Qwen traces. They remain truncated exactly where the original token budget stopped them; no missing sentence or closing marker has been added. Publishing this audit appendix does not decide whether S1 should receive raw CoT in the proposed system.')
    result+='<p>'+link('Download the original calls as JSONL','../research/prethinking-pilot/teacher_calls.jsonl')+' · '+link('Download the trace/token-alignment bundle','../research/prethinking-pilot/traces.json')+'</p>'
    result+='<div class="appendix-tools"><label for="appendix-filter">Filter call metadata or new chunk IDs</label><input id="appendix-filter" type="search" placeholder="e.g. call 62, raw_private, chunk-0181"><button type="button" id="appendix-open-all">Expand visible calls</button><button type="button" id="appendix-open-prompts">Expand full prompts too</button><button type="button" id="appendix-close-all">Collapse calls</button><output id="appendix-count">64 calls</output></div>'
    for call in traces['calls']:
        index=call['index'];name='Call '+str(index)+' · '+f"{call['at']:.2f} s"+' · '+call['variant']+' / '+call['history_mode']+' · seed '+str(call['seed'])
        rate=str(call['rate'])+' tokens/s budget replay' if call.get('rate') else 'scout; no fixed emission rate'
        search='call '+str(index)+' '+call['stage']+' '+call['variant']+' '+call['history_mode']+' '+rate+' seed '+str(call['seed'])+' '+' '.join(call['new_ids'])
        result+='<details class="trace-record" id="appendix-call-'+str(index)+'" data-call="'+str(index)+'" data-search="'+e(search)+'"><summary>'+e(name)+'</summary>'
        result+=p(rate+' · input '+str(call['input_tokens'])+' tokens · output '+str(call['output_tokens'])+'/'+str(call['budget'])+' tokens · '+call['finish_reason']+' · '+str(call['retained_history_entries'])+' retained private entries · '+str(call['observed_chunk_count'])+' observed transcript chunks.')
        result+='<h3>New transcript available to this call</h3>'
        for ident in call['new_ids']:
            c=chunks[ident]
            result+='<div class="trace-input" data-chunk="'+ident+'">'+small(ident+' · speaker '+c['speaker']+' · speech '+f"{c['start']:.2f}–{c['end']:.2f} s"+' · available '+f"{c['available']:.2f} s")+'<blockquote>'+e(c['text'])+'</blockquote></div>'
        result+='<p>'+link('Inspect on the transcript/token timeline','#thinking-timeline','trace-focus-link')+'</p>'
        result+='<details class="trace-prompt-details"><summary>Full executed prompt · '+str(call['input_tokens'])+' input tokens</summary><pre class="trace-prompt" id="prompt-call-'+str(index)+'">'+verbatim(call['prompt'])+'</pre></details>'
        result+='<h3>Full captured private thinking</h3><pre class="trace-thinking" id="thinking-call-'+str(index)+'">'+verbatim(call['private_reasoning'])+'</pre>'
        if call['final_text']:result+='<h3>Final-channel output</h3><pre class="trace-final">'+verbatim(call['final_text'])+'</pre>'
        else:result+=p('No final-channel output was produced in this call.')
        result+='<details><summary>Exactness checks</summary>'+p('Prompt SHA-256: '+call['prompt_sha256'])+p('Thinking SHA-256: '+call['thinking_sha256'])+p('Original generated-output SHA-256: '+call['generated_sha256'])+'</details></details>'
    return result

def timeline_data(traces):
    fields=['index','stage','variant','at','new_ids','seed','history_mode','rate','budget','output_tokens','next_arrival','generated_text','generated_token_ids','token_byte_ends']
    return {'calls':[{k:c[k] for k in fields if k in c} for c in traces['calls']], 'setup_seconds':.5}
