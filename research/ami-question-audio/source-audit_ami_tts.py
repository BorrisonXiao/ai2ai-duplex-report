"""Audit actual audio, copied source samples and independently decoded wording."""
import hashlib
import json
from pathlib import Path
import numpy as np
import soundfile as sf

ROOT=Path(__file__).resolve().parents[1]

def main():
 base=ROOT/'exp/ami_question_audio';manifest=json.loads((base/'review/manifest.json').read_text());replay=json.loads((base/'review/replay.json').read_text());whisper=json.loads((base/'review/whisper-check.json').read_text())
 asr_all={r['path']:r for r in json.loads((base/'evaluation/asr.json').read_text())}
 speaker_all={r['path']:r for r in json.loads((base/'evaluation/speaker.json').read_text())}
 failures=[];checks=[]
 def check(condition,note):
  checks.append(note)
  if not condition:failures.append(note)
 mix,sr=sf.read(ROOT/'data/prethinking_pilot/ami_EN2003a/EN2003a.Mix-Headset.wav',dtype='int16')
 check(len(manifest['clips'])==9,'Three questions times three model comparisons')
 check(len(manifest['candidates'])==36,'All 36 generated tuning variants evaluated')
 for q in manifest['protocol']['questions']:
  check(not q['answer_generated'],'Answer generation deferred: '+q['id'])
  check(q['mode']=='pause_insert_question_resume','Question-only pause mode: '+q['id'])
 for c in manifest['clips']:
  y,rate=sf.read(ROOT/c['injected_path'],dtype='int16');a=round(c['context_start_seconds']*sr);t=round(c['source_time_seconds']*sr);b=round(c['context_end_seconds']*sr)
  check(np.array_equal(y[:t-a],mix[a:t]),'Original prefix exact: '+c['id'])
  check(np.array_equal(y[-(b-t):],mix[t:b]),'Original suffix exact: '+c['id'])
  z,zsr=sf.read(ROOT/c['matched_path'],dtype='float32')
  check(rate==zsr==16000 and np.isfinite(z).all(),'16 kHz finite mono matched audio: '+c['id'])
  check(np.max(abs(z))<.999,'No clipped matched samples: '+c['id'])
  check(c['asr']['wer']==0,'Exact normalized independent ASR: '+c['id'])
  check(asr_all.get(c['matched_path'],{}).get('wer')==0,'Exact normalized ASR on actual matched WAV: '+c['id'])
  c['processed_asr']=asr_all.get(c['matched_path'])
  c['processed_speaker_check']=speaker_all.get(c['matched_path'])
  check(c['speaker_check']['target_minus_other']>0,'Closer to held-out requester than other requester: '+c['id'])
  check(c['room_tone']['source_end_seconds']<=c['source_time_seconds'],'Room tone comes from past source: '+c['id'])
  check(abs(c['acoustics']['matched_active_rms_dbfs']-c['acoustics']['reference_active_rms_dbfs'])<2,'Active level within 2 dB of original reference: '+c['id'])
 check(replay['source_pcm_exact_after_removing_insertions'],'Complete replay recovers original PCM after removing insertions')
 packets=replay['packets'];check(packets[0]['playback_start_sample']==0 and packets[-1]['playback_end_sample']==replay['replay_samples'],'Packet replay covers full audio')
 check(all(a['playback_end_sample']==b['playback_start_sample'] and a['source_end_sample']==b['source_start_sample'] for a,b in zip(packets,packets[1:])),'Playback/source packet clocks are contiguous')
 check(packets[-1]['source_end_sample']==replay['source_samples'],'Packet replay consumes original source exactly once')
 content=[]
 for model in ['qwen','chatterbox','f5']:
  rows=[r for r in manifest['candidates'] if r['model']==model];content.append(dict(model=model,total=len(rows),exact_asr=sum(r['asr']['wer']==0 for r in rows),requester_closer_than_other=sum(r['speaker_check']['target_minus_other']>0 for r in rows),mean_wer=float(np.mean([r['asr']['wer'] for r in rows]))))
 original_baselines=[s for s in json.loads((base/'evaluation/speaker.json').read_text()) if s.get('is_reference')]
 vc=json.loads((ROOT/'research/ami_question_audio/vc-controls.json').read_text())
 room_asr=[s for s in json.loads((base/'evaluation/asr.json').read_text()) if s.get('is_room_tone')]
 check(all(not r['text'].strip() for r in room_asr) and len(room_asr)==3,'Captured room tone has no recognized words in three ASR checks')
 (base/'review/manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 result=dict(status='automated_checks_pass_listening_review_pending' if not failures else 'audit_failure',failures=failures,checks=checks,content_summary=content,original_speaker_baselines=original_baselines,room_tone_asr=room_asr,whisper_after_matching=whisper,vc_controls=vc,selected=[dict(id=c['id'],setting=c['setting']['id'],asr=c['asr']['text'],speaker_cosine=c['speaker_check']['target_cosine'],speaker_margin=c['speaker_check']['target_minus_other']) for c in manifest['clips']],overview='Thirty-six question-only outputs compare three architectures and four settings per question, followed by two voice-conversion controls. Model and setting selection uses independently decoded wording, followed by voice similarity to a separate original utterance. All nine selected processed WAVs have zero normalized Parakeet WER. The chosen examples preserve all original context PCM samples; a full local replay injects three F5 questions on a 480 ms packet timeline. F5 has the highest held-out cosine among wording-qualified variants for each question. VC lowers speaker C similarity from 0.571 to 0.496/0.403 and is excluded from the main replay.',limitations='This is a development pilot with three questions and two speakers from one meeting. ASR and speaker embeddings are proxies: they do not prove natural prosody, exact accent, perceived identity or a physical room match. The assistant inspected transcripts, timing and audio measurements; listening review is still requested from the user. Whisper-base hears Remami instead of remind me in the Chatterbox C clip while Parakeet recovers the intended words, so pronunciation remains uncertain there. Speaker C is comparatively harder. Tuning covers reference, inference and acoustic settings; model weights were not trained. No live synthesis or answer-generation result is claimed.',gpus_for_audit=0)
 (ROOT/'research/ami_question_audio/review.json').write_text(json.dumps(result,indent=2)+'\n');(ROOT/'reports/ami_tts_review.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'failures':failures,'content':content,'selected':result['selected']},indent=2))
 if failures:raise SystemExit(1)

if __name__=='__main__':main()
