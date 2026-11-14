"""Full-set execution and measured statistics, separate from the development pilot."""
import html

NAMES={'reactive':'Reactive','current_notes':'Current notes','quotes_current':'Source quotes','quotes_history':'Quotes + earlier evidence','function_notes':'Function notes'}
MODELS={'instruct':'Qwen3-30B Instruct','thinking':'Qwen3-30B Thinking','minicpm':'MiniCPM-o 4.5','qwen-thinking':'Qwen3-Omni Thinking'}

def section(d,table):
    e=lambda x:html.escape(str(x))
    body='<section id="full-set"><h2>10. Full 105-question comparison</h2><ul><li>All 105 questions are retained across the text and audio comparisons.</li><li>'+f"Saved {d['outputs']:,} of 2,100 planned answers, including verified pilot reuse."+'</li><li>Answer accuracy remains separate from process completion and scoring progress.</li></ul>'
    body+='<p>Text compares reactive answering, current generated notes, source quotes, and source quotes plus earlier evidence. Audio compares reactive answering and function-call notes, each with audio alone or past-only labelled voices. These are 105 distinct questions from 26 meetings; the 2,100 outputs repeat the same questions under different settings.</p>'
    rows=[]
    for g in d['groups']:
        conditions='4 conditions × 2 seeds'if g['model']=='thinking'else'4 conditions × 1 seed'if g['branch']=='text'else'2 modes × 2 speaker inputs'
        rows.append([g['branch'].capitalize(),MODELS[g['model']],str(g['outputs'])+'/'+str(g['planned']),conditions])
    body+=table(13,'Full-set coverage by model; pilot outputs are reused only after matching prompts, audio views, note states and decoding settings.',['Input','Model','Saved / planned','Conditions and seeds'],rows)
    body+='<p><strong>Audio note generation:</strong> '+', '.join(e(MODELS[w['model']])+': '+str(w['updates'])+'/'+str(w['planned'])+' updates'for w in d['writer'])+'. One stream per meeting and speaker condition is reused for all questions in that meeting. Four independent note requests share a GPU; request-time answers run serially with cold prefix and audio caches.</p>'
    rows=[]
    for model in ['minicpm','qwen-thinking']:
        v=d['audio_views'][model]
        rows.append([MODELS[model],'40,960'if model=='minicpm'else'65,536',str(v['complete_history'])+'/105',str(len(v['trimmed_cases']))])
    body+=table(14,'Native audio context limits; both reserve 4,096 note tokens, and all four conditions use the same selected meeting audio for each model/question.',['Model','Native context tokens','Complete history','Recent-history cases'],rows)
    body+='<p>Qwen retains complete history for every question. For the two longest MiniCPM inputs, the oldest 303 or 219 seconds are removed to fit the native context; the retained histories are about 42 minutes. The same audio view is used with and without notes, while notes can preserve facts from earlier speech. These cases are identified in the download.</p>'
    body+='<p><strong>Scoring:</strong> '+e(d['scoring'])+' The source-judge check uses 315 reviewed examples; its raw agreement counts and any unresolved outputs remain visible rather than becoming a successful validation claim.</p>'
    q=d['qualification']
    if q:
        body+='<p>The latest automatic judge matches '+str(q.get('core_correct_agreements',0))+'/'+str(q.get('cases',315))+' required-fact labels and '+str(q.get('supported_correct_agreements',0))+'/'+str(q.get('cases',315))+' fully supported labels. '+str(q.get('valid',0))+' outputs pass the quotation and source-ID checks. These automatic scores require source review.</p>'
    for branch,number,title in [('text',15,'Text statistics'),('audio',16,'Audio statistics')]:
        rows=[]
        for r in d['summary']:
            if r['branch']!=branch:continue
            complete=r['complete'];m=r['metrics'];think=m['thinking_tokens']['mean'];lat=m['first_answer_seconds']['mean']
            status=str(r['source_reviewed_matches'])+' reviewed matches; '+str(r['missing_judgments'])+' pending'
            if r['scored']==r['planned']:
                status=str(r['supported_correct'])+'/'+str(r['planned'])+(' provisional'if r['provisional']else' judged')
            timing='Batched; excluded'if r['model']=='instruct'else f'{lat:.2f}'if complete and lat is not None else'Pending'
            rows.append([MODELS[r['model']],NAMES[r['condition']],r['identity'].replace('_',' '),str(r['outputs'])+'/'+str(r['planned']),
                'Not exposed'if r['model']in ['instruct','minicpm']else f'{think:,.0f}'if complete and think is not None else'Pending',
                timing,f"{m['generated_tokens']['mean']:,.0f}"if complete else'Pending',e(status)])
        body+=table(number,title+'; means appear after all planned outputs for that setting are available.',['Model','Condition','Speaker input','Outputs','Mean thinking tokens','Mean first-answer s','Mean generated tokens','Accuracy status'],rows)
    body+='<details><summary>Execution, cost and evaluation details</summary><p>Each allocated job uses one A100 SXM4 80 GB, with its model, audio encoder where needed, and 8 GiB KV cache on GPU 0. Model services are private to each job, and speech synthesis is disabled. Text generation/scoring stages run sequentially, as do audio stages; the study uses at most two GPUs at once.</p><p>Earlier note work is counted once per meeting and speaker condition, including unused updates and failed operations. The original text writer is charged to every saved-material condition; extracting source quotes adds no model generation. Native request-time thinking, ordinary output and earlier generation are reported separately. Instruct and MiniCPM expose no separate native thinking channel.</p><p>Audio is replayed offline in causal order, and final notes are selected only from boundaries before each question. This study measures the effect of saved content; a later real-time test can measure notes still pending when a request arrives.</p><p>Current allocated GPU-hours, including checks and stopped attempts: '+f"{d['GPU_hours_all_attempts']:.3f}"+'. Active GPUs: '+str(d['active_GPUs'])+'.</p></details>'
    body+='<p><a href="../research/note-functions/full-expansion.json">Full-set progress</a> · <a href="../research/note-functions/full-statistics.json">Paired statistics and token costs</a> · <a href="../research/note-functions/full-expansion-answers.json">All currently saved native answers and evaluation status</a></p></section>'
    return body
