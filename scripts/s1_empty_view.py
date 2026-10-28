"""Readable current S1 empty-response investigation."""
import json
from pathlib import Path
from html import escape as e
ROOT=Path(__file__).resolve().parents[1]
def load():
 p=ROOT/'research/s1-empty-diagnosis/progress.json';return json.loads(p.read_text()) if p.exists() else None
def condition_name(c):
 kind='question only' if c['history_mode']=='none' else 'full meeting'
 prompt='direct-answer prompt' if c['prompt_changed'] else 'native prompt'
 level='higher question level' if c['request_level_adjusted'] else 'original level'
 return c['id'][:3]+': '+kind+', '+prompt+', '+level

def render(t):
 d=load()
 if not d:return ''
 body='<section class="section" id="s1-empty"><h2>Why did S1 give no usable answer?</h2><p><strong>System:</strong> <a href="https://huggingface.co/MuyeHuang/DuplexOmni">DuplexOmni</a>, released checkpoint '+e(d['model_revision'][:12])+', with S2 disabled; Moshi and MiniCPM have not run in this pilot.</p>'
 body+='<p>In the native response, <code>asr</code> holds recognized speech and <code>tts</code> holds the next words to say.</p>'
 body+=t('Different causes in the original three-question pilot; an empty speech recording does not identify the cause by itself.',['Case / condition','What the raw output shows','Consequence'],[['P01, buffered full history','All 17 language-model calls contain empty asr and tts fields.','The language model supplied no words to speak; the failure starts before speech synthesis.'],['P02, buffered full history','The model gives a correct choose-one answer as ordinary text.','The caller rejects the format before invoking speech synthesis.'],['P01, native request packets','The model says it will check the folder and emits [THINK].','S2 is disabled, so the requested reasoning never runs; this is not a completed lookup.'],['P02/P03, native request packets','The model misses the request in its own ASR and gives a greeting.','Request recognition and long-history conditioning need separate controls.']])
 body+='<p>Thinker is the name of DuplexOmni’s S1 language-model component; it is separate from the external S2 reasoning model.</p>'
 if d.get('audit'):body+='<details><summary>What the controlled comparisons establish</summary><ul>'+''.join('<li>'+e(x)+'</li>' for x in d['audit']['findings'])+'</ul></details>'
 body+='<p><strong>Controlled diagnostic:</strong> job '+e(d['job'])+' is '+e(d['state'].lower())+' on one '+e(d['gpu_type_vram'])+'; '+str(d['active_gpus'])+' GPU is allocated, and '+str(d['conditions_recorded'])+' of '+str(d['conditions_planned'])+' conditions have saved outputs.</p><p>GPU 0 holds only the S1 audio encoder and language model, using vLLM; no Talker, MTP, Code2Wav, independent ASR or S2 service is loaded. All conditions run sequentially, with a maximum of one GPU active. Text output in this diagnostic does not establish successful speech.</p>'
 body+='<details id="s1-empty-method"><summary>What the controlled comparisons test</summary><ul><li>Question-only native packets isolate request recognition from missing meeting facts.</li><li>Original audio versus a louder copy tests audio level; normalization targets an RMS amplitude of 0.05 (about −26 dBFS), capped at a peak of 0.95 for waveform samples scaled to ±1, and changes only the request.</li><li>Full earlier audio with the native prompt reproduces the buffered input condition.</li><li>Generic format and task instructions are varied separately and together, without supplying transcripts, reference answers or question-specific hints.</li><li>These are diagnostic conditions on the same three questions, not additional evaluation questions or a full-bank accuracy result.</li><li>The unallocated A100 request was cancelled before using any GPU; the same diagnostics moved to one available H200 to avoid the queue.</li></ul></details>'
 if d['cases']:
  body+='<details id="s1-empty-outputs"><summary>Inspect the actual language-model outputs</summary>'
  body+=t('Actual S1 text from the controlled conditions; recognition-only controls are not scored for unavailable meeting facts.',['Condition','Status','S1 ASR','S1 speech text or unstructured text'],[[e(c['id']),e(c['status'] or 'running'),e(c.get('asr') or '(empty)'),e(c.get('raw_unstructured_text') or c.get('tts') or '(empty)')] for c in d['cases']])+'</details>'
 b=d.get('speech_validation')
 if b:
  body+='<h3 id="s1-speech-repair">Actual speech validation</h3><p>Job '+e(b['job'])+' is '+e(b['state'].lower())+' on one H200 141 GB; '+str(b['active_gpus'])+' GPU is allocated. Thinker, Talker, MTP and Code2Wav share GPU 0, then independent Parakeet ASR uses GPU 0 after S1 exits; S2 is disabled.</p><p>'+e(b['method'])+'</p>'
  combined=[c for c in b['cases'] if c['history_mode']=='full' and c['prompt_changed'] and c['request_level_adjusted']]
  body+=t('Combined candidate: a higher question level and direct-answer prompt produce recognized speech in all three cases, with zero complete answers supported by the source facts.',['Question','Independent response transcript','Source review'],[[e(c['id'][:3]),e(c['spoken_transcript'] or '(empty)'),e(c['review_reason'] or 'Pending source review')] for c in combined])
  body+='<details id="s1-all-speech-conditions"><summary>All sixteen speech conditions and recognition controls</summary>'
  body+=t('Actual speech from candidate repairs; question-only controls cannot answer facts from an absent meeting.',['Condition / history','Independent response transcript','Source review'],[[e(condition_name(c)),e(c['spoken_transcript'] if c['spoken_transcript'] is not None else 'Pending ASR'),e('Not scored: question-only control' if c['history_mode']=='none' else c['review_reason'] or 'Pending source review')] for c in b['cases']])
  body+='</details>'
  body+='<p>The speech run sampled a peak of '+str(b.get('sampled_peak_memory_mib'))+' MiB on its H200; this extended configuration has not been capacity-qualified on an A100 80 GB.</p>'
  body+='<details id="s1-repair-audio"><summary>Listen to the actual candidate responses</summary><p>Compare the louder questions with the <a href="#pilot-audio">original question recordings</a>; their text and voice are unchanged.</p>'
  for tag in ['P01','P02','P03']:body+='<p>'+tag+': louder input question</p><audio controls preload="none" src="research/s1-empty-diagnosis/audio/'+tag+'-adjusted-request.wav" aria-label="'+tag+' louder input question"></audio>'
  for c in b['cases']:
   if c['response_audio']:body+='<p><strong>'+e(condition_name(c))+'</strong></p><audio controls preload="none" src="'+e(c['response_audio'],quote=True)+'" aria-label="'+e(c['id']+' actual S1 response',quote=True)+'"></audio><p>'+e(c['spoken_transcript'] or '(empty independent transcript)')+'</p>'
  body+='</details>'
 native=d.get('native_history_controls',[])
 if native:
  body+='<h3 id="s1-native-history">Check the native input path</h3><p>The original whole-WAV pilot was an unvalidated input path: it differs from the released 480 ms message loop. These controls process the earlier audio through native messages before the question, retaining every actual S1 response without trimming; input advances without real-time pacing and speech synthesis is disabled. Each native-history job uses one H200 NVL 141 GB for S1 Thinker on GPU 0, with no separate ASR or S2 service.</p>'
  if d.get('audit',{}).get('upstream_history_policy'):
   h=d['audit']['upstream_history_policy'];body+='<p>The <a href="'+e(h['source'],quote=True)+'">pinned released bridge</a> keeps 150 turns by default, about 72 seconds. These full-history controls deliberately extend that policy; token capacity alone does not establish understanding.</p>'
  if d.get('audit',{}).get('native_history_findings'):body+='<ul>'+''.join('<li>'+e(x)+'</li>' for x in d['audit']['native_history_findings'][2:-1])+'</ul>'
  body+=t('Native-history controls for P01 at 5:09; 643 earlier frames end at 308.64 seconds, and the branch includes the remaining original audio plus the question.',['Job / decoding','Earlier frames processed','Largest prompt / limit','Calls at output limit / job state'],[[e(n['job']+' / '+n['prompt_mode']+', temperature '+str(n['temperature'])+', max '+str(n['max_tokens_per_turn'])),str(n['prefill_frames_completed'])+' / '+str(n['prefill_frames_planned']),str(n['max_prompt_tokens'])+' / 65,536',str(n['length_stopped_calls'])+' / '+e(n['state'])] for n in native])
  body+='<p>An output-limit stop means the model used its full per-turn token budget without ending; the response object can be left unfinished. The context guard reserves space for the next call, so it can stop below the model’s full token limit.</p>'
  for n in native:
   body+='<details><summary>Native history '+e(n['job'])+': actual output</summary><p>'+e(n['scope'])+'</p><p>Model ASR emitted while the input clock covers about 101–156 seconds: '+e(n['early_file_discussion_model_asr'] or '(empty)')+'. This is model output, not a verified transcript.</p>'
   if n['branches']:
    body+=t('Native S1 response text after the preserved history; speech synthesis is disabled in these controls.',['Question input','S1 recognized request','S1 speech text','S2 request / oracle flag'],[[e(b['id']),e(b['model_asr'] or '(empty)'),e(b['native_text'] or '(empty)'),e((', '.join(b['S2_requests']) or 'None')+(' / written question supplied' if b.get('oracle_question_text') else ''))] for b in n['branches']])
   else:body+='<p>No question branch completed; this is not an answer-accuracy result.</p>'
   body+='</details>'
 o=d.get('oracle_controls')
 if o:
  body+='<details id="s1-oracle-controls"><summary>Can the same S1 model answer with the question or transcript supplied as text?</summary><p>Job '+e(o['job'])+' is '+e(o['state'].lower())+' on one H200 141 GB, Thinker only using vLLM; no speech, ASR or S2 service. These ordinary answer-text controls are separate from native duplex speech scores.</p><p>All three conditions use the same generic question-answering instruction: original audio and spoken question; original audio plus the written question; or the manual speaker-attributed transcript plus the written question.</p>'
  body+=t('Same-checkpoint content controls; oracle means supplying correct text that would be unavailable in an audio-only S1 baseline.',['Case / input','Actual answer text','Source review'],[[e(c['id']),e(c['answer_text']),e(c.get('source_review',{}).get('reason','Pending source review'))] for c in o['cases']])+'</details>'
 if d.get('audit'):body+='<p><strong>Speech delivery:</strong> '+e(d['audit']['speech_delivery_finding'])+'</p><p><strong>What remains:</strong></p><ul>'+''.join('<li>'+e(x)+'</li>' for x in d['audit']['remaining'])+'</ul>'
 body+='<details id="s1-diagnosis-cost"><summary>All attempts and GPU cost</summary><p>New investigation total: '+format(d['allocated_gpu_hours'],'.5f')+' GPU hours; maximum one GPU active, including the cancelled partial speech run. The unallocated A100 request costs zero GPU hours. No CUDA OOM or two-GPU fallback occurred.</p><p>The first speech diagnostic had a progress-counter bug after its first returned fragment; it was stopped, preserved and excluded from complete-answer results. A CPU check verified the repaired wrapper before the retry.</p>'+t('All new allocations, including cancelled attempts; older pilot cost is recorded separately below.',['Job','State','GPU type / count','Allocated seconds'],[[e(r['job']),e(r['state']),e(r['gpu_type_vram'])+' / '+str(r['gpus']),str(r['elapsed_seconds'])] for r in d['allocations']])+'</details>'
 body+='<p>The <a href="https://huggingface.co/MuyeHuang/DuplexOmni#known-issues">official model card</a> lists unexpected silence as a known issue; that statement does not identify the cause of these particular failures.</p><p>Snapshot: '+e(d['updated_at'])+'. <a href="research/s1-empty-diagnosis/progress.json">Actual diagnostic records</a> · <a href="#fresh-pilot">Original pilot audio and source facts</a>.</p></section>'
 return body
