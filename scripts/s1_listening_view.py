"""Focused progress: current method, current outputs and links to earlier failures."""
import json
from pathlib import Path
from html import escape as e
ROOT=Path(__file__).resolve().parents[1]
def load():
    p=ROOT/'research/s1-listening/progress.json';return json.loads(p.read_text()) if p.exists() else None
def render(t):
    d=load()
    if not d:return '<p>The controlled listening comparison has not started.</p>'
    completed=sum(c['status']=='completed_content_review_required' for c in d['cases'])
    body='<section class="section" id="s1-empty"><span id="s1-listening"></span><h2>Keep S1 listening until the question ends</h2><ul><li>Compare decode-and-clear with constrained decoding on the same '+str(d.get('planned_meeting_questions',3))+' meeting questions.</li><li>Use native 480 ms audio packets and retain the generated ASR after each packet.</li><li>Start the answer on the first silence packet after the complete question, with S2 disabled.</li></ul>'
    body+='<p><strong>System:</strong> DuplexOmni S1, released BF16 checkpoint; its Thinker is the S1 language model, separate from S2.</p>'
    body+='<p><code>asr</code> contains recognized speech, <code>tts</code> contains the next words to speak, and the two control fields manage speech and S2 requests; Talker converts the response text into audio.</p>'
    body+=t('The methods differ only in how background-listening responses are generated; both save empty speech and control fields.',['Method','During listening','After the question'],[['Decode and clear','Keep generated ASR, clear any generated controls and skip the unused speech suffix.','Start with a nonempty speech fragment; later speech is free and S2 stays disabled.'],['Constrained decoding','Restrict generation so only ASR is free and the other fields stay empty.','Use the same answer rules as decode-and-clear.']])
    body+='<p>Both methods preserve the checkpoint’s observed field orders and use its original short prompt. At the known question end, both must produce an initial speech fragment containing a letter or digit; the model chooses every word and later continuation. No question transcript, answer facts, text cue or new beginning-of-sequence token is supplied.</p><p>Listening silence and answer start are set by the test; automatic wake-word detection and turn taking are not scored.</p>'
    body+='<p><strong>Progress:</strong> '+str(completed)+' / '+str(d.get('planned_meeting_outputs',6))+' meeting outputs completed; '+('the GPU runs are active.' if d['active_gpus'] else 'no experiment GPU is active.')+' Completion alone does not establish a correct answer.</p>'
    rows=[]
    for c in d['cases']:
        if c['status']=='deferred':continue
        label=c['case']+' · '+('decode and clear' if c['method']=='decode_clear' else 'constrained')
        status={'not_started':'Not started','running':'Listening / answering','completed_content_review_required':'Output saved; review pending','failed':'Failed; see execution records'}.get(c['status'],c['status'])
        if c['status']=='running' and c.get('phase')=='listening':status='Listening: '+format(c.get('frames_completed',0)*.48/60,'.1f')+' / '+format(c['request_minutes'],'.1f')+' min'
        if c['status']=='failed' and c.get('frames_completed',0)<c.get('listening_frames',0):status='Replay stopped before the question'
        review=c.get('source_review')
        if review:status=review['short_result']
        context=c.get('answer_context') or {};history=('All earlier packets' if context and not context.get('trimmed_frames') else 'Recent history from '+format(context.get('oldest_retained_seconds',0)/60,'.1f')+' min' if context else 'To record')
        rows.append([e(label)+'<p><small>Asked at '+format(c['request_minutes'],'.1f')+' min; '+e(history.lower())+'.</small></p>',e((c.get('speech_text') or 'No answer text yet')[:400]),e(status)])
    body+=t('Current meeting outputs; full texts, independent speech transcripts, recordings and required facts are expandable below.',['Question / method','S1 answer text','Source review'],rows)
    body+='<p>A complete text answer must cover the listed facts without inventing a status or action; uncertain speech transcription stays pending listening review.</p>'
    if d.get('source_reviewed_outputs')==d.get('planned_meeting_outputs'):
        body+='<p>All four runs preserved the generated ASR text and saved empty speech/control fields during listening; clearing those fields did not resolve meeting-question recognition or answer accuracy.</p>'
    body+='<p>The full 105-question evaluation remains unvalidated; these four pilot outputs are separate from its result counts.</p></section>'
    body+='<section class="section" id="listening-examples"><h2>Questions and actual outputs</h2>'
    for case in ['P01','P02','P03']:
        items=[c for c in d['cases'] if c['case']==case]
        if all(c['status']=='deferred' for c in items):continue
        body+='<details id="listening-'+case+'"><summary>'+case+': '+e(items[0]['question'])+'</summary>'
        body+='<p><strong>Required facts:</strong></p><ul>'+''.join('<li>'+e(f)+'</li>' for f in items[0].get('required_facts',[]))+'</ul>'
        for c in items:
            method='Decode and clear' if c['method']=='decode_clear' else 'Constrained decoding'
            body+='<h3>'+method+'</h3><p><strong>S1 recognized request:</strong> '+e(c.get('question_asr') or '(empty)' if c['status']=='completed_content_review_required' else c.get('question_asr') or '(not available yet)')+'</p><p><strong>S1 response text:</strong> '+e(c.get('speech_text') or '(empty or not generated yet)')+'</p>'
            if c.get('audio'):body+='<audio controls preload="none" src="'+e(c['audio'],quote=True)+'" aria-label="'+e(case+' '+method+' actual response',quote=True)+'"></audio>'
            body+='<p><strong>Independent speech transcript:</strong> '+e(c.get('spoken_transcript') or '(not available yet)')+'</p>'
            if c.get('source_review'):body+='<p>'+e(c['source_review']['reason'])+'</p>'
            if c.get('listening_rule_violations') is not None:body+='<p>Saved listening responses with nonempty speech/control fields: '+str(c['listening_rule_violations'])+'.</p>'
        body+='</details>'
    body+='</section><section class="section" id="listening-notes"><h2>Scope</h2><ul><li>Compare request recognition and model answer text while preserving the actual response recordings.</li><li>Use all native history while it fits, with a shared context-limit fallback whose exact retained times are recorded.</li><li>Keep a shortened-history case separate from a full-meeting retention result.</li></ul></section>'
    if d.get('recognition_probes'):
        body+='<details id="recognition-check"><summary>Why the first meeting question still failed</summary><p>Neither meeting run transcribed the inserted folder question, and both replies missed its required facts. Replaying the same question packets without the preceding meeting recovered the question with both methods, using the same allocated model services and no extra GPU.</p><p>This establishes an effect of earlier history; it does not yet separate audio-history length from errors in the saved ASR.</p>'
        for probe in d['recognition_probes']:body+='<p><strong>'+e(probe['method'].replace('_',' '))+' question-only ASR:</strong> '+e(probe['request_ASR'])+'</p>'
        body+='</details>'
    if d.get('deferred_case'):body+='<p>The 21:40 case is deferred: its native full prefix exceeds 65,536 tokens even with empty ASR fields, and the recent-history fallback would discard its listed older evidence.</p>'
    if d.get('controls'):
        body+='<details id="listening-control"><summary>Why answer start is forced in this test</summary><p>With the same sky question and identical saved history, allowing an empty first speech fragment produced no answer text with either method; requiring a first speech fragment produced correct blue-sky answer text with both.</p><p>The model still chooses every answer word; this separates answer content from deciding when to speak. Independent speech transcripts contain pronunciation errors, and no human speech-quality rating is claimed.</p>'
        for c in d['controls']:
            body+='<p><strong>'+e(c['method'].replace('_',' '))+':</strong> '+e(c['speech_text'] or '(no text yet)')+'</p><p>Speech transcript: '+e(c.get('spoken_transcript') or '(pending)')+'</p>'
            if c.get('audio'):body+='<audio controls preload="none" src="'+e(c['audio'],quote=True)+'" aria-label="'+e(c['method']+' short control',quote=True)+'"></audio>'
        body+='</details>'
    body+='<section class="section" id="resources"><h2>Resources</h2><p>Each paired job requests one RTX PRO 6000 Blackwell 96 GB: Thinker, Talker, MTP and Code2Wav share GPU 0, then independent Parakeet ASR uses GPU 0 after S1 exits; S2 is disabled. The two jobs use separate services and may overlap; stages within each job are sequential. Maximum active so far: '+str(d['maximum_active_gpus'])+' GPUs; currently active: '+str(d['active_gpus'])+'.</p><p>Allocated cost so far: '+format(d['allocated_gpu_hours'],'.3f')+' GPU hours, including earlier calibration attempts; this unpaced replay does not measure real-time latency.</p><p><a href="research/s1-listening/progress.json">Execution records and per-job allocations</a> · <a href="research/s1-listening/README.md">Method details and context-limit rule</a> · <a href="research/s1-listening/manifest.json">File checksums</a></p></section>'
    return body
