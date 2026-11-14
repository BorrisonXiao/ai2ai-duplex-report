"""Source-reviewed development results; historical full-bank figures stay intact."""
import html,json

NAMES={'reactive':'Reactive','current_notes':'Current notes','quotes_current':'Source quotes','quotes_history':'Quotes + earlier evidence'}

def section(d,table):
    e=lambda s:html.escape(str(s));body='<section id="diagnostic-results"><h2>9. Source-quote diagnostic results</h2>'
    body+='<ul><li>Source quotes improve several previously failing answers in this selected twelve-question pilot.</li><li>Thinking uses fewer request-time tokens with source quotes, while the small sample leaves the latency change uncertain.</li><li>Earlier note generation still dominates the complete generated-token cost.</li></ul>'
    body+='<p>Both thinkers retain the full transcript. The three saved-material conditions use the same original note writer: current generated notes, the source passages selected by those notes, or those passages plus earlier evidence for the same active notes. No new writer is trained or generated for this comparison.</p>'
    body+='<p><strong>Evaluation:</strong> Codex checked all 144 final outputs against past source speech and the frozen fact checklists. Fully supported means that the answer supplies the requested facts and contains no material unsupported claim. The automatic judge did not qualify and supplies none of these labels. This is a selected development set of 12 questions from eight meetings, with one Instruct seed and two Thinking seeds; it does not replace the 105-question results.</p>'
    rows=[]
    for r in d['summary']:
        m=r['metrics'];lat='Batched; excluded'
        if r['model']=='thinking':
            n=sum(x['first_answer_seconds']is not None for x in d['answers']if x['model']==r['model']and x['condition']==r['condition'])
            lat=f"{m['first_answer_seconds']:.2f} (n={n})"
        rows.append([r['model'].capitalize(),NAMES[r['condition']],f"{r['fully_supported']}/{r['outputs']}",f"{100*m['core_correct']:.1f}%",'Not exposed'if m['thinking_tokens']is None else f"{m['thinking_tokens']:,.0f}",lat])
    body+=table(12,'Selected development questions; each Thinking condition contains 24 outputs from 12 questions and two seeds.',['Thinker','Condition','Fully supported outputs','Required facts','Mean thinking tokens','Mean first-answer s'],rows)
    body+='<p>Source quotes change Thinking’s fully supported count from 18/24 to 21/24, with five improved and two worsened answers relative to reactive answering. Mean request-time thinking falls from 1,698 to 1,416 tokens (16.6%), and mean first-answer time falls from 16.51 to 14.60 seconds. The paired meeting-based 95% intervals cross zero for both changes (Figure 4); a reliable latency gain is not yet established. Adding earlier evidence gives 20/24 supported answers and 1,466 thinking tokens, showing no consistent improvement over current source quotes in this pilot.</p>'
    body+='<figure id="fig-diagnostic-paired"><img src="../research/note-functions/diagnostic-paired.svg" alt="Paired request-token and first-answer time changes with meeting-based uncertainty intervals" style="width:100%;height:auto"><figcaption><strong>Figure 4.</strong> Paired Thinking changes from reactive answering; negative values indicate less request-time work. Intervals resample meetings and retain both seeds. Current-note latency has 23 matched pairs because one native text answer lacked a measurable answer-start event; the quote conditions have 24. <a href="../research/note-functions/diagnostic-paired.pdf">PDF</a></figcaption></figure>'
    body+='<p><strong>Observed pattern:</strong> source quotes recover the spoken project-folder location and retain uncertainty about yellow as the company colour. They also recover the 36-to-30 talk-count revision. They still confuse initial document compilation with later final revisions, and the speech-implementation example remains sensitive to whether the answer distinguishes a proposed design from completed work. These examples support testing evidence-preserving notes; they do not establish that more historical evidence is always useful.</p>'
    body+='<figure id="fig-diagnostic-cost"><img src="../research/note-functions/diagnostic-total-cost.svg" alt="Earlier generation and request generation for each text condition" style="width:100%;height:auto"><figcaption><strong>Figure 5.</strong> Total generated-token cost for one seed-23 request set. The 91,144 earlier tokens include all writer and repair calls in the eight selected meetings up to their latest selected request, counted once per meeting. Quote extraction adds no generation. Input tokens, audio encoding and GPU time are separate costs; the earlier writer also consumed 3.18 million input tokens. <a href="../research/note-functions/diagnostic-total-cost.pdf">PDF</a></figcaption></figure>'
    body+='<p><strong>Timing:</strong> '+e(d['resource'])+' '+e(d['latency_protocol'])+' Instruct exposes no separate native thinking channel.</p>'
    body+='<details><summary>All 144 actual answers, reviewed labels and source evidence</summary>'
    grouped={}
    for r in d['answers']:grouped.setdefault(r['question_id'],[]).append(r)
    for qi,(qid,rows)in enumerate(grouped.items(),1):
        body+='<details id="diagnostic-case-'+str(qi)+'"><summary>'+e(rows[0]['question'])+'</summary><p>'+e(rows[0]['reason'])+'</p><details><summary>Source speech used for review</summary><pre class="native">'+e('\n'.join(s['id']+' · '+s['speaker']+' · '+str(s['start'])+' s: '+s['text']for s in rows[0]['source_speech']))+'</pre></details>'
        for r in rows:
            body+='<p><strong>'+e(r['model']+' · '+NAMES[r['condition']]+' · seed '+str(r['seed']))+'</strong> · fully supported: '+('yes'if r['supported_correct']else'no')+'</p><pre class="native">'+e(r['answer'])+'</pre>'
        body+='</details>'
    body+='</details><p><a href="../research/note-functions/diagnostic.json">Reviewed results, costs and paired comparisons</a></p></section>'
    return body
