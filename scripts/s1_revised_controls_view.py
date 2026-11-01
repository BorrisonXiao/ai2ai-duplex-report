"""Fresh paired listening controls with actual speech and source comparisons."""
from html import escape as e
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def render(t):
 p=ROOT/'research/s1-revised-controls/review.json'
 if not p.exists():return ''
 d=json.loads(p.read_text());body='<section class="section" id="revised-pilot-controls"><h2>Earlier pilot questions rerun with revised audio</h2><p>Two existing listening methods are repeated for P01 at 5:09 and P02 at 9:21 using their original native prompt, sampling and history policy. Decode and clear generates a native recognition field, then discards speech/action fields during listening. Constrained decoding prevents those fields during listening. Both retain their original controlled first response after the known question end. These pilot controls use temperature 0.8 and a 65,536-token context, so they are separate from the greedy 49,152-token pressure curves above. All acoustic changes are baked into the input, with no runtime question amplification.</p>'
 body+=t('Actual generated responses, transcribed independently and reviewed against the earlier source.',['Question / method','Independent response ASR','Source review'],[[e(c['id']),e(c.get('spoken_transcript') or '(empty)'),e(c.get('source_audit',{}).get('reason',c.get('error',c['status'])))] for c in d['cases']])
 for c in d['cases']:
  body+='<details id="revised-control-'+e(c['id'])+'"><summary>'+e(c['id'])+' · question, actual speech and source facts</summary><p><strong>Question:</strong> '+e(c['question'])+'</p><p><strong>S1 question-ASR field:</strong> '+e(c.get('question_asr') or '(empty)')+'</p>'
  if c.get('audio'):body+='<audio controls preload="none" src="'+e(c['audio'])+'" aria-label="'+e(c['id'])+' revised pilot response"></audio>'
  body+='<details><summary>Show response ASR</summary><blockquote>'+e(c.get('spoken_transcript') or '(empty)')+'</blockquote></details><p><strong>Source-based reference facts:</strong> '+e(' '.join(c['required_facts']))+'</p>'
  if c.get('source_audit'):body+='<p>'+e(c['source_audit']['reason'])+'</p>'
  body+='<p>Retained source begins at '+format(c.get('oldest_source_at_answer_end_seconds',0),'.2f')+' seconds by the end of the answer. '+('All listed source evidence remains available.' if c.get('source_evidence_fully_retained') else 'Do not treat this replay as retaining all listed evidence.')+'</p><p><strong>Native intended response:</strong> '+e(c.get('speech_text') or '(empty)')+'</p></details>'
 deferred=d['deferred'];body+='<p><strong>P03 remains excluded:</strong> the question follows 21:40 of meeting audio, and the source plus question requires '+str(deferred['full_prefix_frames'])+' native packets and an estimated '+format(deferred['empty_ASR_prompt_estimate_tokens'],',')+' prompt tokens even with empty recognized-text fields, beyond the 65,536-token context. The acoustic revision preserves that duration; no shortened-history response is counted as full-history retention. This capacity check uses zero GPUs.</p><details><summary>Short native controls and GPU roles</summary><p>Each method first qualifies the same short sky question, followed by its original allow-empty response control. These are runtime checks, not meeting-answer accuracy.</p>'
 for c in d['controls']:
  body+='<p><strong>'+e(c['case']+' '+c['method'])+'</strong>: '+e(c['spoken_transcript'] or '(empty)')+'</p><audio controls preload="none" src="'+e(c['audio'])+'" aria-label="'+e(c['case']+' '+c['method'])+' current calibration response"></audio>'
 body+='<p>Each control job uses one RTX PRO 6000 Blackwell 96 GB, with Thinker, Talker, MTP and Code2Wav on GPU 0, followed by Parakeet on the same GPU after S1 exits. The two jobs have private services and each depends on a different sweep worker ending; the overall maximum stays four GPUs. No S2 runs.</p></details><p><a href="research/s1-revised-controls/review.json">All current control responses and source reviews</a> · <a href="research/s1-revised-controls/manifest.json">Checksums</a></p></section>'
 return body
