"""Concise current pressure experiment, with actual cases in expandable details."""
import json
from pathlib import Path
from html import escape as e
ROOT=Path(__file__).resolve().parents[1]
def load():
    p=ROOT/'research/s1-context-pressure/progress.json'
    return json.loads(p.read_text()) if p.exists() else None
def summary(d):
    if d.get('review'):
        r=d['review']
        return ['The original DailyTalk helper and new native runner match on all 40 response-field records and produce the same spoken answer content.',
                'All 41 P01 context lengths produce speech, but only 20 preserve the core question in their ASR text.',
                'The first clear ASR failure occurs with 61.11 seconds of earlier audio; recognition later recovers, including at 206.11 seconds.',
                'None of the 11 contexts containing all answer evidence produces a complete source-grounded answer within the 19.2-second response window.']
    lines=['Reproduce the working DailyTalk recipe, then compare the current runner under matched settings.','Test P01 with request-only audio and all 40 backward additions, keeping the request audio fixed.']
    if d.get('matched_review'):
        lines=['The original helper and new native runner give identical response fields on all 40 DailyTalk packets under greedy decoding.','P01 request-only recognition passes (WER 0.063), but its folder-status answer is unsupported without earlier evidence.']
    if d['completed_levels']:lines.append(str(d['completed_levels'])+'/41 pressure levels completed; '+str(d['recognized_levels'])+' pass the strict ASR check, with question meaning and answer correctness reviewed separately.')
    else:lines.append('Pressure outputs are pending; the matched check is '+d['state']+' and uses '+str(d['active_gpus'])+' allocated GPUs now.')
    return lines
def render(t):
    d=load();p=json.loads((ROOT/'research/s1-context-pressure/protocol.json').read_text())
    body='<section class="section" id="s1-pressure"><h2>P01: add earlier context one sentence group at a time</h2><ul><li>Start with the recorded question alone and open a fresh model session at every level.</li><li>Prepend one continuous audio chunk at each step, merging overlapping sentences so no speaker’s sentence is cut.</li><li>Test every level and report any recovery after a failure.</li></ul><p><strong>Question:</strong> '+e(p['question']['question'])+'</p>'
    body+='<p>The 80 transcript sentences form 39 nonoverlapping groups; request-only, those 39 additions and a control that adds the original recording lead-in give 41 levels. The input stays audio-only: transcript words and speaker labels choose boundaries and score results, and never enter the model prompt.</p><p><strong>System:</strong> DuplexOmni S1 through vLLM, with S2 disabled. Use constrained listening at temperature zero, retaining generated ASR and empty speech/control fields. At the known question end, require a nonempty first reply fragment; the model chooses all answer words.</p>'
    body+='<p><strong>Two separate checks:</strong> first, does the model’s ASR retain the question; second, does its answer recover the meeting facts? Word error rate (WER) measures transcription errors; lower is better. Recognizing request-only audio cannot establish the earlier folder status, because that evidence is absent.</p>'
    if (ROOT/'research/s1-array-contrast/review.json').exists():body+='<p><a href="#ami-array-contrast">New: compare headset, distant-microphone and beamformed audio at level 30.</a></p>'
    r=d.get('review')
    if r:
        body+=t('Reviewed results for one distinct question at 41 context lengths; these are diagnostic replays, not 41 new evaluation questions.',['Check','Result','Meaning'],[
            ['Question meaning retained in ASR','20/41','Both the shared-folder request and missing conceptual-design files remain recognizable.'],
            ['First missing core question','61.11 s of earlier audio','Level 12 has empty question ASR; eight longer contexts later recover the question.'],
            ['Nonempty spoken response','41/41','Speech generation works, but nonempty speech does not establish relevance or accuracy.'],
            ['Complete reference answer','0/11 eligible contexts','Only the 11 contexts containing all listed evidence are scored; native text and independently transcribed speech both miss completeness.'],
            ['Partial reference answer','1/11 eligible contexts','Level 30 recalls the folder location but omits the identified components-design PowerPoint.'],
            ['Frozen strict ASR check','12/41','WER ≤ 0.25 and exact key terms; an understandable “share folder” fails this stricter text rule.'],
            ['Capacity / format failures','0/41','Maximum prompt: 37,626 tokens, below the 49,152-token limit; no history trimming or output-token-limit stops.']])
        body+='<p><strong>Interpretation:</strong> the matched short example works, while the longer meeting replay often loses the request or answers an earlier topic. This is a relevance and grounding failure under the tested listening rules, rather than empty speech or a reached token limit. The nonmonotonic results do not support a single context-length cutoff.</p>'
    body+='<details id="pressure-criteria"><summary>Recognition and answer criteria</summary><p><strong>Question ASR:</strong> concatenate recognition from the request packets and four following packets (1.92 seconds). The frozen strict check requires word error rate (WER) at most 0.25 and the exact words “Assistant,” “shared folder” and “conceptual design.” Lower WER is better.</p><p>After initial outputs showed that this strict rule rejects understandable word forms, Codex separately reviewed whether ASR preserves both the shared-folder status request and the missing conceptual-design files. This additional review leaves the original WER and strict scores unchanged; it measures ASR content, not internal comprehension. Later ASR was also checked: none of the 21 missing-core cases recovers the question later in the response window.</p><p><strong>Answer:</strong> recover both that C reported putting files in the shared folder and that C identified a components-design PowerPoint, without inventing a folder outage, upload failure or completed lookup. Score these facts only when all listed source passages are supplied, starting at level 30 with 198.91 seconds of earlier audio. Inspect native text and independent Parakeet transcripts of actual Talker speech separately.</p><p>The response window is 40 silent input packets, or 19.2 seconds on the input clock; this unpaced test makes no response-latency claim. Four levels still have speech text in their last packet, including one eligible context that is giving a wrong-topic PowerPoint tutorial. The reported 0/11 applies within this window, not unlimited generation. Codex reviewed text and independent transcripts; no human listening score is claimed.</p></details>'
    if (ROOT/'research/s1-context-pressure/recognition.svg').exists():
        body+='<figure style="margin:1rem 0"><div style="overflow-x:auto" tabindex="0" role="region" aria-label="Recognition plot"><img src="research/s1-context-pressure/recognition.svg" alt="Question word error rate against earlier audio duration; points are colored by the frozen strict recognition rule" style="width:100%;min-width:640px;background:white"></div><figcaption>Figure 1. Question WER against earlier audio duration; colors use the frozen strict ASR rule, not the additional meaning review. The dashed vertical line marks when all listed answer evidence is included. Empty ASR has WER 1. <a href="research/s1-context-pressure/recognition.svg">Open full-size plot</a>.</figcaption></figure>'
    else:body+='<p>The ASR curve will appear after actual pressure outputs are saved. These sentence groups are separate from the 10–40 second amortized-thinking chunks.</p>'
    if d['completed_levels'] and not r:
        if d['first_failure_index'] is None:body+='<p>No strict ASR-check failure observed in the completed levels.</p>'
        else:
            first=next(l for l in d['levels'] if l['index']==d['first_failure_index'])
            body+='<p>First completed miss of the strict ASR criterion: level '+str(first['index'])+', with '+format(first['context_seconds'],'.2f')+' seconds of earlier audio; '+str(len(d['later_recognized_indices']))+' later completed levels recover.</p>'
    if r:
        selected=[next(l for l in d['levels'] if l['index']==i) for i in [0,3,12,16,30,33,40]]
        body+=t('Examples showing why recognition and answer accuracy are separate; open each level below for its complete text and actual speech.',['Level / earlier audio','Question in ASR','Answer review'],[['<a href="#pressure-level-'+str(l['index'])+'">'+str(l['index'])+' / '+format(l['context_seconds'],'.2f')+' s</a>',e(l['source_review']['question_meaning_in_ASR']),e(l['source_review']['reason'])] for l in selected])
        body+='<p><strong>Limits:</strong> one question and one greedy replay per prefix, with controlled listening and answer start; these results do not test native wake-word timing or establish a general history limit. The sentence groups here are separate from the planned 10–40 second amortized-thinking chunks.</p>'
    body+='</section><section class="section" id="matched-controls"><h2>Match the working short-request recipe</h2><p>The reference is the earlier DailyTalk outlet question, using its original native helper, short prompt, 480 ms packets, 4,096-token engine and greedy decoding. New-runner controls change listening rules and sampling in separate rows; the pressure sweep uses a larger engine and retains every selected packet.</p>'
    names={'M0-original-native':'Original native helper · greedy','M1-new-native':'New runner · native, greedy','M2-constrained-greedy':'New runner · constrained, greedy','M3-clear-greedy':'New runner · decode and clear, greedy','M4-constrained-sampled':'New runner · constrained, sampled','P01-L00':'P01 request-only · greedy'}
    rows=[]
    for key,label in names.items():
        r=next((r for r in d['matched'] if r['id']==key),None)
        rows.append([e(label),e(r.get('question_asr','') if r else 'Pending'),e((r.get('speech_text','')[:160]+'…' if len(r.get('speech_text',''))>160 else r.get('speech_text','')) if r else 'Pending')])
    body+=t('Matched short controls; captured answer excerpts are shown here and independently transcribed recordings are expandable below.',['Condition','Recognized request','Native answer text'],rows)
    if d.get('matched_review'):body+='<p>'+e(d['matched_review']['summary'])+'</p>'
    body+='</section><details id="pressure-levels"><summary>All pressure levels, actual outputs and speech</summary>'
    body+=t('One fresh replay per level, ordered by increasing earlier context; the meaning column is the additional Codex ASR review.',['Level','Earlier audio (s)','Request WER','Strict ASR check','Meaning in ASR','Full answer evidence'],[[str(l['index']),format(l['context_seconds'],'.2f'),format(l['recognition']['WER'],'.3f') if l.get('recognition') else '—',('Pass' if l['recognition']['recognized'] else 'Miss') if l['status']=='completed_content_review_required' else e(l['status'].replace('_',' ')),e(l.get('source_review',{}).get('question_meaning_in_ASR','Pending')),'Included' if l['source_evidence_fully_available'] else 'Incomplete'] for l in d['levels']])
    for l in d['levels']:
        if l['status']=='not_started':continue
        body+='<details id="pressure-level-'+str(l['index'])+'"><summary>Level '+str(l['index'])+' · '+format(l['context_seconds'],'.2f')+' seconds of earlier audio</summary><p><strong>Recognized question:</strong> '+e(l.get('question_asr') or '(empty)')+'</p><p><strong>Native answer:</strong> '+e(l.get('speech_text') or '(empty)')+'</p>'
        if l.get('audio'):body+='<audio controls preload="none" src="'+e(l['audio'],quote=True)+'" aria-label="Pressure level '+str(l['index'])+' actual S1 response"></audio>'
        body+='<p><strong>Independent speech transcript:</strong> '+e(l.get('spoken_transcript') or '(pending)')+'</p>'
        if l.get('source_review'):body+='<p>'+e(l['source_review']['reason'])+'</p>'
        body+='</details>'
    body+='</details><details id="pressure-matched-audio"><summary>Matched-control speech recordings and independent transcripts</summary>'
    for r in d['matched']:
        body+='<details><summary>'+e(names.get(r['id'],r['id']))+'</summary><p><strong>Native answer:</strong> '+e(r.get('speech_text') or '(empty)')+'</p><p><strong>Speech transcript:</strong> '+e(r.get('spoken_transcript') or '(independent transcript pending)')+'</p>'
        if r.get('audio'):body+='<audio controls preload="none" src="'+e(r['audio'],quote=True)+'" aria-label="'+e(r['id'],quote=True)+' actual S1 response"></audio>'
        body+='</details>'
    body+='</details>'
    replay=d.get('frozen_replay')
    if replay:
        body+='<details id="frozen-feedback"><summary>Focused diagnostic: fresh model state and earlier ASR feedback</summary><p>The full-prefix replay saves an early mistranscription, “I’m a bit nervous. I need to translate a,” and later asks what needs translating instead of answering the folder question. This suggests earlier ASR feedback may matter, but the observation alone does not establish its cause.</p><p>Reconstruct the exact first-answer prompt, retaining every native audio packet and saved response; replay it twice in fresh sessions, then clear earlier ASR fields while retaining the same audio. Each condition generates 16 packets of text (7.68 seconds on the input clock). This uses one H100 SXM 80 GB, Thinker only on GPU 0, after the main sweep; it tests text behavior, with no Talker, external ASR or S2 and no spoken-answer score.</p>'
        body+=t('Fresh-session diagnostic; field agreement is against the first 16 recorded reply packets, and all answer words remain model-generated.',['Condition','Identical field records / 16','Native reply text'],[[e(c['condition'].replace('_',' ')),str(c['identical_recorded_field_turns'])+'/16',e(c['native_text'] or '(empty)')] for c in replay['cases']])
        if d.get('frozen_replay_review'):body+='<p>'+e(d['frozen_replay_review'])+'</p>'
        body+='</details>'
    body+='<section class="section" id="pressure-resources"><h2>Resources and progress</h2><p>Each matched or pressure job uses one H100 SXM 80 GB: Thinker, Talker, MTP and Code2Wav share GPU 0, followed by independent Parakeet ASR on GPU 0 after S1 exits. The matched check precedes four independent pressure workers; the later fresh-session diagnostic uses one H100 SXM 80 GB with Thinker only. Jobs share no model service, and S2 is disabled. Allocated now: '+str(d['active_gpus'])+' GPUs; maximum active: '+str(d['maximum_active_gpus'])+'; allocated cost including failed startup attempts: '+format(d['allocated_gpu_hours'],'.3f')+' GPU hours.</p><p>Every selected audio packet stays in history; capacity errors are logged without trimming. All 12 request-speech packets are byte-identical across the 41 captured inputs. This unpaced sweep measures accuracy, with no real-time latency claim.</p><p><a href="research/s1-context-pressure/progress.json">Saved outputs and allocations</a> · <a href="research/s1-context-pressure/review.json">Case-by-case source and speech review</a> · <a href="research/s1-context-pressure/protocol.json">Frozen levels and scoring rules</a> · <a href="research/s1-context-pressure/README.md">Method details</a> · <a href="research/s1-context-pressure/manifest.json">Checksums</a></p></section>'
    from s1_array_contrast_view import render as array_contrast
    return body+array_contrast(t)
