"""Concise saved-run diagnosis and the next controlled comparison."""
import html

def sections(review,plan,table):
    e=lambda x:html.escape(str(x))
    names={'source':'Existing notes','json':'JSON edits','tools':'Native calls'}
    body='<section id="review"><h2>6. What changed when notes were added?</h2><ul>'
    for finding in review['findings'][:3]:body+='<li>'+e(finding['text'])+'</li>'
    body+='</ul><p>'+e(review['scope'])+' Observed note and answer errors do not establish causality; the follow-up below changes only the saved representation.</p>'
    rows=[]
    for setting in review['paired_outcomes']:
        outcomes={r['outcome']:r for r in setting['outcomes']}
        rows.append([setting['model'].title(),names[setting['condition']],*[outcomes[k]['count']for k in ['correct -> correct','wrong -> correct','correct -> wrong','wrong -> wrong']]])
    body+=table(7,'Paired answer changes after targeted source corrections; Instruct has105 trials and Thinking has210 trials across two seeds. Correct means fully supported.',['Thinker','Saved input','Both correct','Helped','Harmed','Both wrong'],rows)
    native=next(s for s in review['paired_outcomes']if s['model']=='thinking'and s['condition']=='tools')
    body+='<details><summary>Where the native-call thinking-token savings come from</summary>'
    body+=table(8,'Each row compares the same question and seed with reactive thinking; negative values mean fewer request-time thinking tokens.',['Answer outcome','Trials','Mean token change','Total token change'],[[r['outcome'],r['count'],f"{r['mean_thinking_change']:+,.1f}",f"{r['total_thinking_change']:+,}"]for r in native['outcomes']])
    token=review['token_diagnostic']
    body+='<p>The mean changes by '+f"{token['mean_change']:+.1f}"+' tokens, while the median changes by '+f"{token['median_change']:+.1f}"+' tokens. One microphone question changes from a 16,384-token call with no final answer to a correct 897-token answer; its 15,487-token saving is '+f"{100*token['microphone_fraction_of_net']:.1f}%"+' of the net saving. Removing trials where either call reaches the cap leaves a mean change of '+f"{token['mean_without_either_call_hitting_cap']:+.1f}"+' tokens; this is a descriptive sensitivity check.</p></details>'
    body+='<details><summary>Memory edits and evidence tracking</summary><p>Across both interfaces, 67 accepted updates keep exactly the same factual text while replacing all previous source IDs: 56 native-call updates and 11 JSON updates, out of 1,260 accepted updates. This is a structural count, not a count of proven false citations. The examples below show concrete unrelated citations.</p><p>The writer performs 1,414 repair calls for 2,554 updates. Of 3,165 rejected operations, 1,138 lack newly arrived evidence and 848 exceed the note text budget; repeated repair failures are included. There are 37 malformed outputs. Valid function syntax alone does not ensure that notes preserve meaning.</p></details>'
    body+='<details><summary>Source examples: note errors, useful evidence and scorer corrections</summary>'
    for x in review['examples']:
        if x['kind']=='open':continue
        body+='<article id="'+e(x['anchor'])+'"><h3>'+e(x['title'])+'</h3><p><strong>Question:</strong> '+e(x['question'])+'</p><p>'+e(x['observation'])+'</p><p class="small">'+e(x['model'].title()+' · '+names[x['condition']]+' · seed '+str(x['seed']))+'</p><p><strong>Reactive answer:</strong> '+e(x['reactive']['answer']or'[No final answer]')+'</p><p><strong>With notes:</strong> '+e(x['with_notes']['answer']or'[No final answer]')+'</p>'
        if x['notes']:
            body+='<ul>'+''.join('<li><strong>'+e(n['id'])+':</strong> '+e(n['fact'])+' <span class="small">Sources: '+e(', '.join(n['source_ids']))+'.</span></li>'for n in x['notes'])+'</ul>'
        body+='<details><summary>Original speech</summary><ul>'+''.join('<li><strong>'+e(s['id']+' · '+s['speaker'])+':</strong> '+e(s['text'])+'</li>'for s in x['source_speech'])+'</ul></details></article>'
    body+='</details><p>Source review added 60 answers from five questions and corrected 14 additional automatic labels; 84 answers across seven questions now have source review. The other 98 questions retain automatic judgments. This targeted review is not a random estimate of judge reliability. Original labels remain in the download.</p><p><a href="../research/note-functions/review.json">Review data and examples</a></p></section>'
    body+='<section id="followup"><h2>7. Follow-up: keep the speech, remove generated claims</h2><p><strong>Prepared; inference has not started.</strong> '+e(plan['question'])+' This diagnostic reuses the native-call notes from the completed study.</p>'
    body+=table(9,'The four conditions keep the same full causal transcript, question, answer instructions and output format; only saved_results changes.',['Condition','Input','What it tests'],[[c['id'].replace('_',' ').title(),c['input'],c['difference']]for c in plan['conditions']])
    body+='<p><strong>Output:</strong> the same brief answer, original evidence IDs and missing information. No question or reference answer is used to select saved speech. The speech-only conditions keep original words, speaker labels and times; they do not generate replacement facts.</p><ul>'
    for gate in plan['gates']:
        body+='<li><strong>'+e({'complete':'Done','pending':'To do','planned':'Later'}[gate['status']])+':</strong> '+e(gate['action'])+' '+e(gate['criterion'])+'</li>'
    pre=plan['preflight']
    body+='</ul><p>CPU checks prepared 420 inputs, verified 210 recorded baseline/current-note prompt hashes, and passed seven behavior tests. Earlier evidence is restored for '+str(pre['history_adds_sources_to_questions'])+' questions within a 4,096-token quote budget. Mean Thinking input sizes are '+', '.join(c.replace('_',' ')+': '+f'{v:,.0f}' for c,v in pre['mean_input_tokens'].items())+' tokens. These are input-size measurements, not model-quality or latency results.</p>'
    body+='<details><summary>Scoring, cost, success criteria and GPU allocation</summary><p>The current evaluator can declare an answer wrong from a short key and bypass the full-source check. The revised evaluator must check every proposed incorrect fact and unsupported addition against the source, including equivalent percentages/counts and optional supported details. It must pass the source-reviewed cases and new controls before the diagnostic runs.</p><p>'+e(plan['common']['cost'])+'</p><p>'+e(plan['evaluation']['targets'])+'</p><p>Report all-case accuracy, mean and median thinking tokens, cap hits, missing answers, actual input/output tokens and cold serial first-answer/completion time; keep correct-in-both and cap-excluded slices secondary.</p><p>Current work uses 0 GPUs, with no GPU services or dependencies. Planned stages are sequential, maximum one GPU: evaluator and Instruct use one A100 80 GB each; Thinking uses one H100 80 GB; scoring uses one A100 80 GB. Model weights and 8 GiB KV cache share GPU 0 in each job. No S1, ASR, TTS or DuplexOmni service is shared. No new job has been submitted.</p></details><p><a href="../research/note-functions/followup.json">Complete follow-up protocol</a></p></section>'
    return body

