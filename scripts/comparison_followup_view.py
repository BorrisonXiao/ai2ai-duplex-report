"""Concise status for the requested follow-up, with exact saved native strings."""
import json
from html import escape as e
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / 'research/comparison-followup'


def render(t):
    d = json.loads((P / 'progress.json').read_text())
    native = json.loads((P / 'native-strings.json').read_text())
    disagreements = json.loads((P / 'scorer-disagreements.json').read_text())
    quality = d['pipeline_quality']
    finished = all(r['completed'] + r['failed'] == 123 for r in d['native_models'])
    body = '<header class="hero"><h1>Experiment progress</h1></header><section class="section" id="summary"><ul class="brief">'
    body += '<li>'+('Finished' if finished else 'Running')+' the matched Moshi and MiniCPM sweeps: 41 history lengths and three recording signals for one question.</li>'
    body += '<li>Use each S1 model’s native text; no response ASR is required for these comparisons.</li>'
    body += '<li>'+('Prepared Parakeet and Whisper transcripts with both speaker-identity conditions.' if quality['whisper_final_inputs_ready'] else 'Parakeet inputs are ready; Whisper readers await a repair for hallucinations during silence.')+'</li>'
    body += '<li>Saved '+str(d['request_outputs'])+'/192 generated-transcript S2 answers and recorded '+str(d['reviewed_outputs'])+' source reviews.</li>'
    body += '<li>The generic scorer disagrees with earlier Codex labels on 13/68 answers and remains unqualified.</li></ul>'
    body += '<p><a href="#comparison-followup">Native time sweeps</a> · <a href="#generated-transcript-pipeline">Generated transcript inputs</a> · <a href="#generated-transcript-outputs">S2 outputs</a> · <a href="#scorer-examples">Scorer examples</a> · <a href="todo.html">Project TODO</a> · <a href="daily-log.html">Daily log</a></p>'
    body += '<p>Saved snapshot: '+e(d['updated_utc'])+'. This page shows recorded progress, not a live cluster monitor; all 105 questions remain in the planned evaluation.</p></section>'
    body += '<section class="section" id="comparison-followup"><h2>Native time sweeps</h2><p>Each model receives the same 123 waveforms as the revised DuplexOmni study: the request alone, then progressively earlier sentences, for headset mix, one distant microphone and the beamformed microphone array. All histories end at the same question. The answer window is 19.2 seconds of input time; this is an accuracy diagnostic, not a latency test.</p>'
    body += t('Saved native response strings for one question; completed inference does not establish a correct answer.', ['Model','Completed / 123','Failed','Remaining'], [[e(r['model']),str(r['completed'])+'/123',str(r['failed']),str(123-r['completed']-r['failed'])] for r in d['native_models']])
    body += '<p><a href="research/comparison-followup/native-strings.csv">Download every native string (CSV)</a> · <a href="research/comparison-followup/native-strings.json">Native strings, exact history lengths and output-window definitions (JSON)</a></p><p>DuplexOmni listens under constrained decoding and starts answering at the known question end. Moshi and MiniCPM keep their native speaking decisions and generated state. Their 80 ms and 1 s frames differ from DuplexOmni’s 480 ms frames; full request-onward text and the matched post-input window are both retained. These caller differences limit causal comparisons between model architectures.</p>'
    body += '<details id="native-time-strings"><summary>Read the actual native strings for each history</summary>'
    groups = {}
    for r in native['rows']:
        groups.setdefault(r['case_id'], []).append(r)
    for key, rows in groups.items():
        body += '<details><summary>'+e(key)+' · '+format(rows[0]['history_seconds'],'.2f')+' seconds of earlier meeting audio</summary>'
        for r in rows:
            body += '<p><strong>'+e(r['model'])+' · '+e(r['status'].replace('_',' '))+'</strong></p><p>'+e(r['native_text'] or '(empty or not yet saved)')+'</p>'
        body += '</details>'
    body += '</details></section>'
    body += '<section class="section" id="generated-transcript-pipeline"><h2>Generated speaker-attributed transcripts</h2><ul class="brief"><li>Decode only audio available before each shared chunk boundary or user request.</li><li>Run Parakeet TDT or Whisper-large-v3 for words, with the same four-speaker Sortformer diarizer for speaker boundaries.</li><li>Use generated word times to assign words to predicted speakers; align Whisper’s recognized words back to the same audio because its native times drifted into silence.</li><li>Compare automatic requester-voice matching with annotation-based A–D naming, while retaining exactly the same predicted words and boundaries.</li></ul>'
    alignment_note = (str(quality['unaligned_whisper_tasks'])+' clips could not be aligned and retain recognized text with an unknown speaker.') if quality['unaligned_whisper_tasks'] else 'All clips in the latest saved Whisper output passed the alignment procedure; this does not certify word correctness.'
    body += '<p>Both methods produced 61 chunk/request transcripts over five meetings. Parakeet supplies native word times. Whisper uses the existing Wav2Vec2 CTC aligner with recognized words only; no reference words enter alignment. '+e(alignment_note)+' Automatic voice matching identifies '+str(quality['automatic_requesters_matched'])+' requesters and leaves '+str(quality['automatic_requesters_unknown'])+' unknown. Annotation-based naming uses only the source annotations available at that cutoff; it does not repair recognition errors, merged speakers or swapped turns.</p>'
    if not quality['whisper_final_inputs_ready']:
        body += '<p><strong>Whisper inputs are still being repaired.</strong> A source-free repetition check stopped reader launch; the next run decodes predicted speech regions with short margins. Word and speaker accuracy remain separate checks.</p>'
    elif quality['whisper_native_fallback_complete']:
        body += '<p>A first greedy Whisper run repeated a thank-you sentence many times in one segment. The final inputs use predicted speech regions plus Whisper’s native temperature fallback, repetition, log-probability and silence checks; original outputs remain preserved. Alignment follows recognition and cannot repair invented words.</p>'

    body += '<p>The fixed schedule comes from the original ground-truth pilot and is shared across transcript conditions; online boundary estimation is not tested. The six questions, thinking goals, note limits, reader prompts and decoding settings are unchanged. The question text is kept as ground truth to isolate errors in the earlier meeting history; request recognition is not tested here. Earlier notes finish before the worker opens the request file. These are past-only offline replays: actual ASR/note completion times have not been tested for real-time use. Sortformer was trained partly on AMI, so this is not an unseen-corpus test.</p><p><a href="research/comparison-followup/input-checks.json">Matched-input and cutoff checks</a> · <a href="research/comparison-followup/protocol.json">Methods, model sources and unchanged reader settings</a> · <a href="research/comparison-followup/ASR-quality.json">Prefix word-error diagnostics and normalization</a></p></section>'
    body += '<section class="section" id="generated-transcript-outputs"><h2>Generated-transcript S2 runs</h2><p>Each input variant runs Qwen3-30B Instruct and Thinking in separate vLLM processes. Per reader there are 104 earlier calls and 24 final answers: six questions in each of reactive reading, amortized summaries, structured notes and an extra source-excerpt diagnostic. Only the first three conditions are the main comparison.</p>'
    body += t('Completion and source review are separate; valid note formats and source IDs do not establish correct notes.', ['Input / identities','Reader','Earlier calls / 104','Answers / 24','Source reviews / 24'], [[e(r['dataset'].replace('oracle_identity','annotation-mapped')),e(r['model']),str(r['note_calls'])+'/104',str(r['request_outputs'])+'/24',str(r['reviewed_outputs'])+'/24'] for r in d['readers']])
    body += '<p>A complete answer must give the required source facts without a material unsupported claim; correct facts mixed with a wrong deadline, owner or decision remain incomplete. <a href="research/comparison-followup/scoring-policy.json">Source-based scoring criteria</a>. Request-time thinking tokens and ordinary output tokens are saved separately. Thinking is N/A for Instruct. All earlier generated tokens count toward amortized-thinking cost, including truncated or unusable outputs. <a href="research/comparison-followup/text-answers.json">Actual answers and token counts</a> · <a href="research/comparison-followup/saved-notes.json">Saved notes</a> · <a href="research/comparison-followup/generated-transcripts.json">Exact generated histories</a></p></section>'
    answers=json.loads((P/'text-answers.json').read_text())['readers']
    transcripts=json.loads((P/'generated-transcripts.json').read_text())['datasets']
    questions=transcripts[0]['cases'] if transcripts else []
    body+='<details id="generated-answer-examples"><summary>Read the actual S2 answers and source reviews</summary>'
    for index,q in enumerate(questions):
        body+='<details id="generated-question-'+str(index)+'"><summary>'+e(q['question'])+'</summary>'
        for reader in answers:
            for answer in reader['answers']:
                qid,condition=answer['id'].split('|',1)
                if qid!=q['id']:continue
                label=reader['dataset'].replace('oracle_identity','annotation-mapped')+' · '+reader['model']+' · '+condition.replace('_',' ')
                review=answer.get('source_review')
                result=e(review['grade']+': '+review['reason']) if review else 'Pending; saved output alone is not an accuracy result.'
                thinking=str(answer['native_thinking_tokens']) if answer['native_thinking_tokens'] is not None else 'N/A'
                body+='<details><summary>'+e(label)+'</summary><p>'+e(answer['answer'] or '(no complete final answer extracted)')+'</p><p><strong>Codex source review:</strong> '+result+'</p><p>Request-time thinking tokens: '+thinking+'; ordinary output tokens: '+str(answer['ordinary_output_tokens'])+'.</p></details>'
        body+='</details>'
    body+='</details>'
    body += '<section class="section" id="scorer-examples"><h2>What a scorer disagreement means</h2><p>The local automatic judge and an earlier Codex source review assigned different completeness labels to the same saved answer. They agree on 55/68 answers; the judge marks 11 additional answers complete and marks two earlier complete answers incomplete. Neither set is independent human ground truth, so disagreement calls for source inspection.</p>'
    for c in disagreements['cases']:
        body += '<details><summary>'+e(c['question'])+'</summary><p><strong>Actual answer:</strong> '+e(c['native_reader_answer'])+'</p><p><strong>Earlier Codex label:</strong> '+e(c['earlier_Codex_grade'])+'. <strong>Automatic judge:</strong> '+e(c['judge_grade'])+'.</p><p>'+e(c['explanation'])+'</p></details>'
    body += '<p>The capitalization example contains a correct main fact plus an incorrect extra rule; the judge accepted both. The backlight example shows the reverse issue: the judge demanded a detail Codex treated as optional. The scoring rules and earlier labels both need review. <a href="research/comparison-followup/scorer-disagreements.json">Verbatim answers, reasons and source passages</a></p></section>'
    body += '<section class="section" id="followup-next"><h2>Next steps and goals</h2><ul class="brief">'
    for step in d['next_steps']:
        body += '<li>'+e(step['action'])+' '+e(step['goal'])+'</li>'
    body += '</ul></section><details id="followup-resources"><summary>Resources and dependencies</summary><p>Allocated at this snapshot: '+str(d['active_GPUs'])+' GPUs; observed maximum '+str(d['maximum_active_GPUs_observed'])+'; allowed maximum four. Every allocated job uses one H100 SXM 80 GB. Total allocated cost, including the failed history-completion stage and repairs: '+format(d['allocated_GPU_hours'],'.3f')+' GPU hours.</p>'
    body += t('Per-job GPU roles, sharing and dependencies; cancelled pending submissions have zero allocation.', ['Stage / job','State','GPUs / type / VRAM','Roles and dependencies'], [[e(j['stage']+' / '+j['job']),e(j['state']),str(j['gpu_count'])+' / '+e(j['gpu_type_vram']),e(j['roles']['0']+'; '+j['dependencies'])] for j in d['jobs']])
    body += '<p>Zero-GPU CPU follow-ups launch readers only after input construction and repetition checks. Parakeet readers use two lanes released by history construction; Whisper readers reuse the completed MiniCPM/repair and Parakeet-automatic lanes, keeping the maximum at four. Native components share GPU 0 within each model job. ASR, diarization, voice matching and alignment run sequentially on GPU 0; no live S1 or ASR service shares a reader GPU. <a href="research/comparison-followup/progress.json">Saved progress and accounting</a></p></details>'
    return body
