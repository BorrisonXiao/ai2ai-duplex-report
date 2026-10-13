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
    return '''<figure class="pilot-figure" id="thinking-timeline"><h3>Transcript above, generated thinking below</h3><p>Compare one captured output at 10, 30, 60 and 100 tokens/s. Every row uses the same prompt and token sequence; only emission time and truncation change. The default shows a single input update around 640 s, rather than the former 100-second sequence.</p><p>The numbered cards contain the complete newly delivered transcript chunks, including short replies from B and C. Their matching bars show actual speech durations on a common time axis. These chunks enter S2 together at the marked input delivery; thinking starts 0.5 s later. Earlier context and the original thinking history are in the linked prompt.</p><div class="pilot-controls thinking-controls"><label>Captured output<select id="thinking-call"></select></label><label>Time window<select id="thinking-window"><option value="input">Input speech → next update</option><option value="thinking">Thinking only, close view</option></select></label><div class="thinking-navigation"><button type="button" id="thinking-previous">Previous update</button><button type="button" id="thinking-next">Next update</button></div></div><label for="thinking-cursor">Conversation time: <output id="thinking-cursor-label">650.00 s</output></label><input id="thinking-cursor" type="range" min="624.57" max="651" step="0.01" value="650"><p id="thinking-method" class="trace-method"></p><div class="thinking-pan-controls"><span class="scroll-note">Pan the time axis horizontally; transcript cards and output text stay readable. Their widths are for reading, not duration.</span><button type="button" id="thinking-pan-left">← Earlier speech</button><button type="button" id="thinking-pan-right">Thinking / right end →</button></div><div class="thinking-scroll" tabindex="0" role="region" aria-label="One input update and identical captured thinking at four token rates"><div class="thinking-wide"><h4 id="thinking-input-label"></h4><div id="thinking-transcripts" class="thinking-transcripts"></div><svg id="thinking-svg" viewBox="0 0 2000 240" role="img" aria-labelledby="thinking-title"><title id="thinking-title">Numbered transcript speech spans and input delivery time</title></svg><p class="thinking-output-heading">Same captured S2 output at four assumed rates. Bars encode time; text panels contain exact prefixes at the cursor and do not encode duration.</p><div id="thinking-rate-rows"></div></div></div><div id="thinking-counts" class="thinking-counts" aria-live="polite"></div><div class="trace-inspector" id="thinking-inspector" aria-live="polite"></div><figcaption>Figure 2. All four rows project the same captured Qwen output with its original prompt and history held fixed. The numbered transcript cards correspond only to that call’s new input chunks; the speech bars and thinking bars share one conversation clock. Uniform output rates and 0.5 s setup are assumptions, not measured streaming timestamps. Output stops at the next input update or the captured token cap, whichever comes first. Faster rows cannot invent an unrecorded continuation. This comparison isolates timing and truncation; independently generated causal rate replays remain in the appendix.</figcaption></figure>'''

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
