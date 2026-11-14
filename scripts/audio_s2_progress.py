import html

def section(data,table):
    e=lambda s:html.escape(str(s))
    body='<section id="audio-s2"><h2>8. Audio-input S2 in parallel</h2><ul><li>The text diagnostic has saved '+str(data['text_outputs'])+' of 144 answers; '+('all source-reviewed.'if data.get('text_source_reviewed')else'every answer requires source review.')+'</li><li>The audio branch compares reactive answering with function-call notes under two speaker-identity conditions.</li><li>Each branch uses one GPU at a time, with at most two 80 GB GPUs active across the study.</li></ul>'
    body+='<p><strong>Current phase:</strong> '+e(data['audio_phase'])+'</p><p>Qwen3-Omni Thinking and MiniCPM-o 4.5 use native audio input and text output through vLLM. '+e(data['audio_output'])+'</p>'
    body+=table(10,'Audio-S2 pilot comparison; the same audio history and spoken question are retained within each speaker-identity condition.',['Condition','Before the request','At the request'],[[x['name'],x['before_request'],x['request_input']]for x in data['audio_conditions']])
    body+='<p>'+e(data['audio_notes'])+'</p><ul>'+''.join('<li>'+e(x)+'</li>'for x in data['audio_input_rules'])+'</ul>'
    body+='<p><strong>Speaker scoring:</strong> '+e(data['evaluation'][1])+'</p><details><summary>Evaluation, resources and actual input controls</summary><ul>'+''.join('<li>'+e(x)+'</li>'for i,x in enumerate(data['evaluation'])if i!=1)+'</ul>'
    body+='<p>The automatic text judge agreed on '+str(data['judge_core_agreements'])+' of '+str(data['judge_cases'])+' required-fact checks and did not qualify. The 12-question text diagnostic uses a frozen protocol requiring manual source review of every output; full scaling remains gated.</p>'
    body+='<p>GPU services are isolated: text and judge jobs use one A100 80 GB or H100 80 GB with weights and 8 GiB KV cache on GPU 0; both bounded audio pilots use one A100 80 GB, with audio encoder, language model and 8 GiB KV on GPU 0. Speech generation is disabled. MiniCPM retains an unused vision tower to avoid a vLLM initialization error; no image input is supplied. The bounded text pilot also uses A100s after pending H100 requests were cancelled before allocation; absolute timing is compared only within this pilot. Longer-history capacity is not established by the six-minute check. Jobs are sequential within each lane; audio models may continue after a different model’s failure. No old DuplexOmni worker or controller is resumed.</p>'
    if data['native_audio_controls']:
        for sample in data['native_audio_controls']:
            body+='<p><strong>'+e(sample['model']+' · '+sample['condition'])+':</strong></p><pre class="native">'+e(sample['native_text']or'[No final text]')+'</pre>'
    for example in data.get('native_audio_note_examples',[]):
        import json
        body+='<p><strong>'+e(example['model'])+' · executed audio note call:</strong></p><pre class="native">'+e(json.dumps(example,indent=2,ensure_ascii=False))+'</pre>'
    body+='</details><p>'+ ' · '.join('<a href="'+e(s['url'])+'">'+e(s['title'])+'</a>'for s in data['sources'])+'</p><p><a href="../research/note-functions/parallel.json">Current branch status and protocol</a></p></section>'
    return body

def results(d,table):
    e=lambda s:html.escape(str(s));body='<section id="audio-pilot-results"><h2>8.1 Audio pilot results</h2><ul><li>Both models completed all audio and note-function calls for the two early questions.</li><li>Qwen used more request-time thinking with notes in all four matched comparisons.</li><li>Labelled voice examples did not establish a consistent identity or accuracy benefit in this pilot.</li></ul>'
    body+='<p>Audio is replayed offline in causal order. Each condition contains two questions, inserted after 351 and 309 seconds in different meetings. Codex checked all 16 native text answers against past source speech; fully supported requires the requested facts and no material unsupported claim. The speaker conditions repeat the same questions and are correlated. These results establish a working pipeline and identify errors for further development; they are too small for a model ranking.</p>'
    rows=[]
    for r in d['summary']:
        rows.append(['MiniCPM-o 4.5'if r['model']=='minicpm'else'Qwen3-Omni Thinking','Audio alone'if r['identity']=='audio_only'else'Labelled past voices',
            'Reactive'if r['mode']=='reactive'else'Function notes',str(r['fully_supported'])+'/2',
            'Not exposed'if r['mean_thinking_tokens']is None else f"{r['mean_thinking_tokens']:,.0f}",f"{r['mean_first_answer_seconds']:.2f}",f"{r['earlier_generated_tokens']:,}"])
    body+=table(11,'Audio pilot: each row has two requests; earlier generation is the total note work for those two meetings under that speaker condition.',['Thinker','Speaker input','Mode','Fully supported','Mean thinking tokens','Mean first-answer s','Earlier generated tokens'],rows)
    body+='<p>For Qwen, notes increase mean thinking from 372 to 1,680 tokens with audio alone and from 589 to 1,074 with labelled examples. First-answer time also increases in both conditions. Notes restore the sending deadline and help one file-status answer retain the unresolved access problem, giving three fully supported answers out of four compared with zero out of four reactively. The labelled-voice notes still overstate the shared folder’s availability. MiniCPM omits the sending time or overstates file access across the eight answers; its small timing differences do not establish a useful quality–latency improvement.</p>'
    body+='<p><strong>What was saved:</strong> MiniCPM makes only five add and five update calls across 36 updates, with 26 no-change calls; it misses the key file-status facts. Qwen makes 29 add and 13 update calls, but one saved state changes a reported upload into an agreed availability claim. All operations pass the mechanical checks, illustrating why source correctness needs separate evaluation. Each writer receives one current state and bounded recent changes; previous snapshots are retained on disk.</p>'
    body+='<p><strong>Speaker identity:</strong> '+e(d['identity_rule'])+' <strong>Timing evidence:</strong> '+e(d['citation_rule'])+'</p><details><summary>All 16 actual audio-S2 answers and saved notes</summary>'
    for r in d['answers']:
        body+='<details><summary>'+e(r['model']+' · '+r['identity']+' · '+r['mode']+' · '+r['question'])+'</summary><pre class="native">'+e(r['answer'])+'</pre><p>Fully supported: '+('yes'if r['supported_correct']else'no')+'. '+e(r['reason'])+'</p></details>'
    import json
    body+='<details><summary>Final saved notes and event-change records</summary><pre class="native">'+e(json.dumps(d['saved_note_states'],indent=2,ensure_ascii=False))+'</pre></details></details>'
    body+='<p>'+e(d['input_protocol'])+' '+e(d['latency'])+'</p><details><summary>Question-duration label audit and repeated answers</summary><p>'+e(d['metadata_note'])+'</p></details><p><a href="../research/note-functions/audio-pilot.json">Reviewed audio-pilot outputs, evidence, costs and paired changes</a></p></section>'
    return body
