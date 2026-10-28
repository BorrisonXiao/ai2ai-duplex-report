"""Concise current pressure experiment, with actual cases in expandable details."""
import json
from pathlib import Path
from html import escape as e
ROOT=Path(__file__).resolve().parents[1]
def load():
    p=ROOT/'research/s1-context-pressure/progress.json'
    return json.loads(p.read_text()) if p.exists() else None
def summary(d):
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
    body+='<p><strong>Recognition criterion:</strong> word error rate (WER) at most 0.25, the “Assistant” cue present, and both “shared folder” and “conceptual design” recognized; lower WER is better. Question ASR includes the request packets and four following packets (1.92 seconds); the full recorded response is reviewed separately. A missed transcript criterion can still preserve the question’s meaning, which is reviewed separately.</p><p><strong>Answer criterion:</strong> a grounded answer recalls that the files were reported in the shared folder and that a components-design PowerPoint was identified; this does not establish a folder outage. Score those facts only when their source passages are included. Text and independently transcribed speech are reviewed separately.</p>'
    if (ROOT/'research/s1-context-pressure/recognition.svg').exists():
        body+='<figure style="margin:1rem 0"><div style="overflow-x:auto" tabindex="0" role="region" aria-label="Recognition plot"><img src="research/s1-context-pressure/recognition.svg" alt="Question word error rate against earlier audio duration; points are colored by the stated recognition rule" style="width:100%;min-width:640px;background:white"></div><figcaption>Figure 1. Request recognition versus earlier audio duration; only completed levels are plotted, and the dashed vertical line marks when all listed answer evidence is included. <a href="research/s1-context-pressure/recognition.svg">Open full-size plot</a>.</figcaption></figure>'
    else:body+='<p>The ASR curve will appear after actual pressure outputs are saved. These sentence groups are separate from the 10–40 second amortized-thinking chunks.</p>'
    if d['completed_levels']:
        if d['first_failure_index'] is None:body+='<p>No strict ASR-check failure observed in the completed levels.</p>'
        else:
            first=next(l for l in d['levels'] if l['index']==d['first_failure_index'])
            body+='<p>First completed miss of the strict ASR criterion: level '+str(first['index'])+', with '+format(first['context_seconds'],'.2f')+' seconds of earlier audio; '+str(len(d['later_recognized_indices']))+' later completed levels recover.</p>'
    body+='</section><section class="section" id="matched-controls"><h2>Match the working short-request recipe</h2><p>The reference is the earlier DailyTalk outlet question, using its original native helper, short prompt, 480 ms packets, 4,096-token engine and greedy decoding. New-runner controls change listening rules and sampling in separate rows; the pressure sweep uses a larger engine and retains every selected packet.</p>'
    names={'M0-original-native':'Original native helper · greedy','M1-new-native':'New runner · native, greedy','M2-constrained-greedy':'New runner · constrained, greedy','M3-clear-greedy':'New runner · decode and clear, greedy','M4-constrained-sampled':'New runner · constrained, sampled','P01-L00':'P01 request-only · greedy'}
    rows=[]
    for key,label in names.items():
        r=next((r for r in d['matched'] if r['id']==key),None)
        rows.append([e(label),e(r.get('question_asr','') if r else 'Pending'),e((r.get('speech_text','')[:160]+'…' if len(r.get('speech_text',''))>160 else r.get('speech_text','')) if r else 'Pending')])
    body+=t('Matched short controls; captured answer excerpts are shown here and independently transcribed recordings are expandable below.',['Condition','Recognized request','Native answer text'],rows)
    if d.get('matched_review'):body+='<p>'+e(d['matched_review']['summary'])+'</p>'
    body+='</section><details id="pressure-levels"><summary>All pressure levels, actual outputs and speech</summary>'
    body+=t('One fresh replay per level, ordered by increasing earlier context; capacity/format failures are distinct from recognition failures.',['Level','Earlier audio (s)','Request WER','Strict ASR check','Full answer evidence'],[[str(l['index']),format(l['context_seconds'],'.2f'),format(l['recognition']['WER'],'.3f') if l.get('recognition') else '—',('Pass' if l['recognition']['recognized'] else 'Miss') if l['status']=='completed_content_review_required' else e(l['status'].replace('_',' ')),'Included' if l['source_evidence_fully_available'] else 'Incomplete'] for l in d['levels']])
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
    body+='</details><section class="section" id="pressure-resources"><h2>Resources and progress</h2><p>The matched run and each current pressure worker request one H100 SXM 80 GB; Thinker, Talker, MTP and Code2Wav share GPU 0, then independent Parakeet ASR uses GPU 0 after S1 exits. The matched check precedes up to four independent pressure workers; S2 is disabled. Allocated now: '+str(d['active_gpus'])+' GPUs; maximum active so far: '+str(d['maximum_active_gpus'])+'; allocated cost: '+format(d['allocated_gpu_hours'],'.3f')+' GPU hours.</p><p>Every selected audio packet stays in history; capacity errors are logged without trimming. This unpaced sweep measures accuracy, with no real-time latency claim.</p><p><a href="research/s1-context-pressure/progress.json">Saved outputs and allocations</a> · <a href="research/s1-context-pressure/protocol.json">Frozen levels and scoring rules</a> · <a href="research/s1-context-pressure/README.md">Method details</a> · <a href="research/s1-context-pressure/manifest.json">Checksums</a></p></section>'
    return body
