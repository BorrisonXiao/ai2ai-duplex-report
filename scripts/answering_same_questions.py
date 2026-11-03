"""Align existing S1 and text S2 decisions by the six distinct question IDs."""
from html import escape as e

QUESTION_LABELS=['Notes volunteer','Audio work','Slogan choice','Presentation time','Outreach call','Shared folder']
TRANSCRIPTS=[('ground-truth','Ground truth'),('parakeet-automatic','Parakeet · automatic speakers'),('parakeet-oracle_identity','Parakeet · annotation-mapped speakers'),('whisper-automatic','Whisper · automatic speakers'),('whisper-oracle_identity','Whisper · annotation-mapped speakers')]

def build_data(results):
    questions=results['questions'];assert len(questions)==6 and len({q['id'] for q in questions})==6
    columns=[dict(key='s1-duplex',label='S1 · DuplexOmni',short='DuplexOmni',family='S1',model='DuplexOmni'),dict(key='s1-moshi',label='S1 · Moshi',short='Moshi',family='S1',model='Moshi'),dict(key='s1-minicpm',label='S1 · MiniCPM',short='MiniCPM',family='S1',model='MiniCPM'),dict(key='s2-instruct',label='S2 · Instruct',short='Instruct',family='S2',model='instruct'),dict(key='s2-thinking',label='S2 · Thinking',short='Thinking',family='S2',model='thinking')]
    rows=[]
    for number,(q,label) in enumerate(zip(questions,QUESTION_LABELS),1):
        case=next(c for c in results['pilot'] if c['question_id']==q['id'] and c['variant']=='full')
        assert case['question']==q['question'] and case['meeting']==q['meeting'] and case['original_recording_question_time']==q['at']
        outcomes=[]
        for col in columns:
            if col['family']=='S1':
                r=next(o for o in case['outputs'] if o['model']==col['model'])
                status='input_failed' if not r['complete_input'] else 'complete' if r['correct'] else 'incomplete'
                outcomes.append(dict(key=col['key'],status=status,answer=r['native_text'],review=r.get('failure',r['criterion']),source_url='#pilot-'+case['id']))
            else:
                r=next(r for r in results['s2_answers'] if r['dataset']=='ground-truth' and r['model']==col['model'] and r['condition']=='reactive' and r['question_id']==q['id'])
                outcomes.append(dict(key=col['key'],status='complete' if r['complete'] else 'incomplete',answer=r['answer'],review=r['reason'],source_url='#all-s2-answers',request_thinking_tokens=r['native_thinking_tokens']))
        rows.append(dict(number=number,question_id=q['id'],label=label,question=q['question'],meeting=q['meeting'],request_time_seconds=q['at'],reference_answer=q['reference_answer'],S1_case_id=case['id'],outcomes=outcomes))
    totals={col['key']:dict(complete=sum(next(o for o in r['outcomes'] if o['key']==col['key'])['status']=='complete' for r in rows),input_failed=sum(next(o for o in r['outcomes'] if o['key']==col['key'])['status']=='input_failed' for r in rows),scheduled=6) for col in columns}
    assert [totals[c['key']]['complete'] for c in columns]==[0,0,2,4,6]
    extended=[]
    for ds,description in TRANSCRIPTS:
        for model in ['instruct','thinking']:
            conditions={c:next(r for r in results['s2_summary'] if r['dataset']==ds and r['model']==model and r['condition']==c)['correct'] for c in ['reactive','amortized_summary','amortized_structured_notes']}
            extended.append(dict(dataset=ds,transcript=description,model=model,correct=conditions,scheduled=6))
    support={model:sum(o['correct'] is True for c in results['pilot'] if c['variant']=='support' for o in c['outputs'] if o['model']==model) for model in ['DuplexOmni','Moshi','MiniCPM']}
    assert list(support.values())==[1,1,1]
    return dict(scope='Six distinct questions at their original insertion times; one full-history S1 run per question and reactive ground-truth text S2 as the primary comparison.',columns=columns,questions=rows,totals=totals,S2_extensions=extended,supporting_audio_diagnostic_correct=support,excluded_from_primary=['Short retail control','Repeated time-and-microphone ablation positions','Supporting-audio edits','Selected-source S2 controls'],score='Source-based Codex completeness review of native S1 text or final S2 answer text; input failures are reported separately within six scheduled cases.',new_inference=False,GPU_count=0,maximum_active_GPUs=0)

def render(data,details,table,figure,link,text):
    body='<section id="s1-s2-comparison"><h2>10. S1 and text S2 on the same six questions</h2><ul class="brief"><li>With full meeting audio, DuplexOmni and Moshi produce zero complete answers and MiniCPM produces two.</li><li>With the ground-truth transcript and no earlier notes, Qwen3-30B Instruct produces four complete answers and Thinking produces six.</li><li>All comparisons use the same six question IDs, meetings, insertion times and source-based answer requirements.</li></ul>'
    body+='<p>The primary comparison aligns one full-history audio run from each S1 system with the two reactive ground-truth text readers. Text S2 answers independently in these runs; its answer has not been passed back to S1 for speech generation. The six questions are evaluated once per configuration. The short retail control, supporting-audio edits, selected-source text controls and repeated time-ablation positions have separate roles in the report.</p>'
    body+=table(8,'Inputs, outputs and response allowances in the same-question comparison.', ['Configuration','History and request input','Scored output','Response allowance'],[
        ['S1 · three speech models','Continuous meeting audio from time zero to the insertion, followed by the participant-voice question.','Native response text; S1 audio and transcripts are linked in the paired-question gallery.','60 s of silent input after the request; model-specific native loops and context limits.'],
        ['S2 · reactive ground truth','All available ground-truth transcript segments, speaker labels, requester label and the question as text.','Final answer text from the reader; evidence IDs and missing information are recorded separately.','2,048 generated tokens for Instruct; 16,384 for Thinking, including its native reasoning.'],
        ['S2 · reactive generated transcript','Generated transcript and speaker labels from the same past audio; the question is supplied as text.','Final answer text under the same source criteria.','Same model-specific token caps as ground truth.'],
        ['S2 · earlier summaries or notes','The corresponding full transcript plus all valid earlier note snapshots and the text question.','Final answer text; earlier and request-time token costs are reported separately.','Same request-time caps; earlier thinking adds computation before the request.']])
    body+='<p>These rows compare complete system configurations: input representation, supplied speaker information, model and response allowance all differ. S1 must perceive the spoken request; S2 receives its text. Ground-truth S2 also receives reliable transcript words and speaker labels, while generated-transcript S2 receives predicted history. Speaker descriptions can satisfy S1 ownership questions; unspoken AMI letters are not required. Accuracy uses the existing source-based Codex reviews. The differing response allowances support an answer-content comparison; response latency is unmeasured here.</p>'
    body+=figure(7,'s1-s2-same-questions','Complete-answer outcomes on the six shared questions. S1 uses full preceding audio; S2 uses reactive reading of the ground-truth transcript. Gray marks the DuplexOmni input-processing failure before the slogan request. Column totals use all six scheduled cases; text labels identify every outcome.')
    labels={'complete':'Complete','incomplete':'Incomplete','input_failed':'Input failed'}
    matrix=[]
    for row in data['questions']:
        matrix.append([link('#comparison-question-'+str(row['number']),str(row['number'])+'. '+row['label'])]+[labels[o['status']] for o in row['outcomes']])
    total=[]
    for col in data['columns']:
        t=data['totals'][col['key']];total.append(str(t['complete'])+'/6'+(' · '+str(t['input_failed'])+' input failure' if t['input_failed'] else ''))
    matrix.append(['<strong>Complete / scheduled</strong>',*total])
    body+=table(9,'Question-level completeness; each column uses the same six distinct questions.', ['Question']+[c['label'] for c in data['columns']],matrix)
    body+='<p>Presentation-time retrieval is the clearest shared success: MiniCPM and both text readers recover seven minutes from the full history. On the audio-work question, MiniCPM and both readers recover a recorded reason for abandoning the work. The outreach and folder questions show a further distinction within text S2: the reactive Instruct reader misses required information, while the Thinking reader gives complete answers. S1 responses include offers to check, uncertain continuations and unsupported claims about who owns or has completed a task. These examples locate the observed gap in particular questions, rather than assuming one shared failure mechanism.</p>'
    examples=''
    for row in data['questions']:
        example='<p><strong>Question:</strong> '+e(row['question'])+'</p><p><strong>Reference:</strong> '+e(row['reference_answer'])+'</p><p class="small">'+e(row['meeting'])+f" · insertion at {row['request_time_seconds']:.2f} s · "+link('#pilot-'+row['S1_case_id'],'Original full-history audio and S1 records')+'</p>'
        for col,outcome in zip(data['columns'],row['outcomes']):
            placeholder='[No answer: input processing failed]' if outcome['status']=='input_failed' else '[Empty native response]'
            example+='<article class="model-card" data-comparison-key="'+col['key']+'"><h4>'+e(col['label'])+' · '+labels[outcome['status']]+'</h4>'+text(outcome['answer'] or placeholder)+'<p class="small">'+e(outcome['review'])+'</p></article>'
        examples+=details(str(row['number'])+'. '+row['question'],example,id='comparison-question-'+str(row['number']))
    body+=details('Read the five primary-system answers together for each question',examples,id='same-question-answers')
    extended=[]
    for r in data['S2_extensions']:
        extended.append([e(r['transcript']),r['model'].capitalize()]+[str(r['correct'][c])+'/6' for c in ['reactive','amortized_summary','amortized_structured_notes']])
    body+=details('Extend the comparison to generated transcripts and earlier thinking',table(10,'S2 completeness on the same six questions across all transcript inputs and note conditions.', ['Transcript input','Reader','Reactive','Summary','Structured notes'],extended)+'<p>The automatic-speaker reactive results are 4/6 for Instruct with either recognizer, 6/6 for Thinking with Parakeet, and 4/6 for Thinking with Whisper. Thus, the text-reader advantage in this sample also appears with generated history. Note-based changes and request-time reasoning costs are analyzed in '+link('#s2-tradeoff','the S2 accuracy and thinking section')+'. Annotation-mapped runs have the identity-consistency qualification described in '+link('#speaker-consistency-audit','the implementation audit')+'.</p>',id='same-question-extensions')
    body+='<p>The primary text S2 rows already achieve their results through reactive reading, without earlier thinking. The note-based conditions examine whether earlier work improves or preserves reader accuracy while changing its request-time reasoning budget. The supporting-audio diagnostic produces 1/6 complete answers for each S1 model. These edited inputs contain selected evidence and use the same six questions; they remain separate from the continuous-history comparison. Source references support all six questions, as the reactive ground-truth Thinking result demonstrates. The current measurements motivate using text S2 as an answering reference while isolating S1 request recognition, history access and response behavior. Six development questions and one generation per setting support descriptive comparisons; repeated held-out evaluation is needed for stable system rankings.</p>'
    body+='<p class="small">'+link('../research/answering-report/same-question-comparison.json','Download the aligned question-level decisions and exact answers')+' · This comparison reuses saved outputs and reviews; computation for analysis, plotting and rendering uses zero GPUs.</p></section>'
    return body
