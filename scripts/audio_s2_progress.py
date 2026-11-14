import html

def section(data,table):
    e=lambda s:html.escape(str(s))
    body='<section id="audio-s2"><h2>8. Audio-input S2 in parallel</h2><ul><li>The text diagnostic has saved '+str(data['text_outputs'])+' of 144 answers; every answer requires source review.</li><li>The audio branch compares reactive answering with function-call notes under two speaker-identity conditions.</li><li>Each branch uses one GPU at a time, with at most two 80 GB GPUs active across the study.</li></ul>'
    body+='<p><strong>Current phase:</strong> '+e(data['audio_phase'])+'</p><p>Qwen3-Omni Thinking and MiniCPM-o 4.5 use native audio input and text output through vLLM. '+e(data['audio_output'])+'</p>'
    body+=table(10,'Planned audio-S2 comparison; the same audio history and spoken question are retained within each speaker-identity condition.',['Condition','Before the request','At the request'],[[x['name'],x['before_request'],x['request_input']]for x in data['audio_conditions']])
    body+='<p>'+e(data['audio_notes'])+'</p><ul>'+''.join('<li>'+e(x)+'</li>'for x in data['audio_input_rules'])+'</ul>'
    body+='<p><strong>Speaker scoring:</strong> '+e(data['evaluation'][1])+'</p><details><summary>Evaluation, resources and actual input controls</summary><ul>'+''.join('<li>'+e(x)+'</li>'for i,x in enumerate(data['evaluation'])if i!=1)+'</ul>'
    body+='<p>The automatic text judge agreed on '+str(data['judge_core_agreements'])+' of '+str(data['judge_cases'])+' required-fact checks and did not qualify. The 12-question text diagnostic uses a frozen protocol requiring manual source review of every output; full scaling remains gated.</p>'
    body+='<p>GPU services are isolated: text and judge jobs use one A100 80 GB or H100 80 GB with weights and 8 GiB KV cache on GPU 0; audio jobs use one A100 80 GB for MiniCPM or one H100 80 GB for Qwen, with audio encoder, language model and 8 GiB KV on GPU 0. Speech generation is disabled. MiniCPM retains an unused vision tower to avoid a vLLM initialization error; no image input is supplied. Jobs are sequential within each lane; audio models may continue after a different model’s failure. No old DuplexOmni worker or controller is resumed.</p>'
    if data['native_audio_controls']:
        for sample in data['native_audio_controls']:
            body+='<p><strong>'+e(sample['model']+' · '+sample['condition'])+':</strong></p><pre class="native">'+e(sample['native_text']or'[No final text]')+'</pre>'
    body+='</details><p>'+ ' · '.join('<a href="'+e(s['url'])+'">'+e(s['title'])+'</a>'for s in data['sources'])+'</p><p><a href="../research/note-functions/parallel.json">Current branch status and protocol</a></p></section>'
    return body
