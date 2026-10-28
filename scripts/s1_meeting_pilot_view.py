"""Render actual GPU pilot evidence separately from earlier CPU software checks."""
import json
from pathlib import Path
from html import escape as e
ROOT=Path(__file__).resolve().parents[1]
def load():
 path=ROOT/'research/s1-meeting-pilot/progress.json'
 return json.loads(path.read_text()) if path.exists() else None

def player(path,label):
 return '<audio controls preload="none" src="'+e(path,quote=True)+'" aria-label="'+e(label,quote=True)+'"></audio>' if path else '<p>No speech recording was produced.</p>'

def render(t):
 d=load()
 if not d:return ''
 audit=d.get('content_audit');u=d.get('native_ungated_diagnostic',{})
 body='<section class="section" id="fresh-pilot"><h2>Fresh S1 pilot: three meeting questions</h2><p>Compare complete buffered input with a check that supplies the request in native audio packets; both retain all earlier meeting audio.</p><p><a href="#pilot-audio">Review the requests and responses</a> · <a href="#pilot-methods">Input methods and controls</a> · <a href="#pilot-resources">GPU accounting</a></p>'
 body+=t('Buffered full-history results: the entire earlier meeting and question are supplied before generation. A score of 1 requires a complete spoken answer supported by the source transcript.',['Case / meeting','Question time','S1 output','Spoken-answer result'],[[e(x['id']+' / '+x['meeting']),f"{int(x['source_cutoff_seconds']//60)}:{x['source_cutoff_seconds']%60:05.2f}",e('Correct plain text; rejected by speech interface.' if x.get('raw_text_output') else x['native_text'] or 'Empty native speech text; independent ASR is also empty.'),e('Pending quiet-audio review' if x['score'] is None else '0: no usable spoken answer' if x.get('raw_text_output') else '0: unrelated reply' if x['score']==0 else str(x['score']))] for x in d['cases']])
 body+='<p>The quiet first response remains unscored; empty text and ASR alone do not settle whether any quiet speech is audible. The correct text in P02 is a useful diagnostic, but it is not a successful spoken response.</p>'
 if u:
  body+='<h3>Check with native request packets</h3><p>'+e(u['method'])+'</p>'
  body+=t('Full-history check with the noise gate disabled; these are the same three questions, not additional evaluation questions.',['Case','Actual model speech, transcribed independently','Result'],[[e(x['id'].split('-')[0]),e(x['spoken_transcript'] if x['spoken_transcript'] is not None else 'Transcription pending'),e('0: required answer facts missing' if x['score']==0 else 'Review pending' if x['score'] is None else str(x['score']))] for x in u['cases']])
 if audit:body+='<p>'+e(audit['interpretation'])+'</p><p><strong>Scoring check:</strong> '+e(audit['judge_finding'])+'</p>'
 body+='<h3 id="pilot-audio">Review the actual audio</h3>'
 for x in d['cases']:
  body+='<details id="pilot-'+x['id']+'"><summary>'+e(x['id']+': '+x['question'])+'</summary><p><strong>Recent original speech and recorded question:</strong></p>'+player(x['input_preview'],x['id']+' recent context and question')+'<p>This player includes the last 18 seconds before the question; the model receives the full earlier meeting.</p><p><strong>Reference answer:</strong> '+e(x['reference']['answer'])+'</p><details><summary>Source passages available before this request</summary><ul>'+''.join('<li>'+e(str(p.get('source',''))+': '+p['text'])+'</li>' for p in x['reference']['evidence'])+'</ul></details>'
  body+='<p><strong>Buffered-input S1 response:</strong></p>'+player(x['response_audio'],x['id']+' buffered-input S1 response')+'<p><strong>Independent response transcript:</strong> '+e(x['spoken_transcript'] or '(empty)')+'</p>'
  if x.get('raw_text_output'):body+='<p><strong>Raw S1 text rejected by the speech interface:</strong> '+e(x['raw_text_output'])+'</p>'
  if x.get('raw_text_output'):body+='<p>The complete audio input was processed; generation returned plain text instead of the four fields required by the speech backend.</p>'
  else:body+='<p><strong>Score explanation:</strong> '+e(x['score_reason'])+'</p>'
  n=next((c for c in u.get('cases',[]) if c['question_id']==x['question_id']),None)
  if n:
   body+='<p><strong>Native-packet S1 response, noise gate disabled:</strong></p>'+player(n['response_audio'],x['id']+' native-packet S1 response without noise gate')+'<p><strong>Independent response transcript:</strong> '+e(n['spoken_transcript'] or '(empty)')+'</p><p><strong>Independent transcript of the consumed request:</strong> '+e(n.get('request_transcript') or '(empty)')+'</p><p><strong>S1’s own request transcript:</strong> '+e(n['model_asr'] or '(empty)')+'</p>'
  body+='</details>'
 body+='<details id="pilot-methods"><summary>Inputs, output formats and caller controls</summary><ul><li>'+e(d['method'])+'</li><li>Native-packet controls retain the earlier meeting as an audio user turn, then process the request in 480 ms packets; they do not simulate listening throughout the meeting.</li><li>'+e(d['input_integrity'])+'</li><li>Ground-truth transcripts, reference answers and later meeting audio are never S1 inputs; S2 is disabled in every case.</li><li>The actual processor input lengths are 4,141, 7,394 and 17,044 tokens, within the declared 49,152-token context.</li><li>The native prompt and greedy decoding are fixed across input checks; no question text or voice is changed.</li><li>S1 exposes no separate thinking channel, so thinking tokens are N/A; its output-token totals include transcription and control text.</li><li>Audio players contain actual model playback, including gaps and interruptions, rather than concatenated discarded synthesis.</li></ul>'
 c=d.get('calibration')
 if c:body+='<p><strong>Short speech control:</strong> “'+e(c['question'])+'”</p>'+player(c['audio'],'Fresh S1 sky calibration output')+'<p>'+e(c['spoken_transcript'])+'</p><p>This successful short request verifies the speech path; it does not verify long-history question answering.</p>'
 n=d.get('native_packet_diagnostic')
 if n:
  body+='<h3 id="native-packet-controls">Stock microphone noise gate</h3><p>The stock gate zeroes each quiet sample below an amplitude of 500 in 16-bit PCM. Only about 4% of samples in P02 and P03 remain nonzero after this gate, so it is disabled for the final prerecorded-input check.</p><p>The native-packet check still fails to produce complete answers after disabling the gate; the gate alone does not explain the failures.</p>'
  body+=t('Stock-gate diagnostic; question-only controls have no meeting facts and are not accuracy cases.',['Case / condition','S1 request transcript','Independent response transcript'],[[e(x['id']),e(x['model_asr'] or '(empty)'),e(x['spoken_transcript'] or '(empty)')] for x in n['cases']])
 body+='<p><strong>Initial startup correction:</strong> '+e(d['initial_attempt']['finding'])+'</p></details>'
 body+='<details id="pilot-resources"><summary>GPU roles, dependencies and cost</summary><ul><li>Each job uses 1 A100 SXM 80 GB: Thinker, Talker, MTP and Code2Wav share GPU 0.</li><li>After all S1 services exit, Parakeet ASR and then the offline Qwen3-30B Instruct judge run on GPU 0; language models use vLLM.</li><li>The offline judge does not help S1 answer, and no S2 service runs.</li><li>Jobs run sequentially, with a maximum of one GPU active; currently '+str(d['active_gpus'])+' GPU is allocated.</li><li>All attempts, startup, transcription and offline judging total '+format(d['allocated_gpu_hours'],'.5f')+' GPU hours'+(' (all jobs finished).' if d['all_jobs_complete'] else ' so far.')+'</li><li>No CUDA out-of-memory error occurred, and no two-GPU fallback was used.</li></ul>'
 body+=t('Actual allocation time includes every stage within each job.',['Job','Purpose','State','Allocated seconds'],[[e(r['job']),e({'1317618':'Initial cache-limit rejection and speech control','1317667':'Buffered full-history generation','1317837':'Native packets with the stock noise gate','1317930':'Native packets with the noise gate disabled'}.get(r['job'],'S1 pilot')),e(r['state']),str(r['elapsed_seconds'])] for r in d['allocations']])+'</details><p>Snapshot: '+e(d['updated_at'])+'. The worker saves a heartbeat every 30 seconds; this public page is a dated checkpoint.</p><p>Source: AMI Meeting Corpus and the <a href="experiments/question-audio.html">existing question recordings</a>; no new TTS was generated. <a href="research/s1-meeting-pilot/progress.json">Pilot evidence</a> · <a href="research/s1-meeting-pilot/README.md">Protocol, code and 46 software checks</a>.</p></section>'
 return body
