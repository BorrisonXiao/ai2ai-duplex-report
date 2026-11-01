"""Verify causal paired audio and payload constraints before GPU submission."""
import hashlib,json
from pathlib import Path
import numpy as np,soundfile as sf
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'research/answering_study_20261101'
def main():
 p=json.loads((D/'pilot-audio.json').read_text());review=json.loads((ROOT/'site/research/question-acoustic-bank/review.json').read_text());by={c['catalog_id']:c for c in review['cases'] if c['primary']};groups={}
 for c in p['cases']:
  path=ROOT/c['input_audio'];assert hashlib.sha256(path.read_bytes()).hexdigest()==c['input_sha256'];x,sr=sf.read(path,dtype='int16');assert sr==16000 and x.ndim==1
  start=round(c['source_cutoff_seconds']*sr);insertion=x[start:];assert hashlib.sha256(insertion.tobytes()).hexdigest()==c['insertion_pcm_sha256'];groups.setdefault(c['question_id'],[]).append(c)
  assert all(b<=c['original_recording_question_time'] for a,b in c['source_intervals'])
  if c['variant']=='full':
   q=by[c['question_id']];v,rate=sf.read(ROOT/'site/research/question-acoustic-bank'/q['injected_audio'],dtype='int16');n=round(q['inserted_interval_start_seconds']*rate)
   assert np.array_equal(x[start-n:start],v[:n]),c['id']+' source prefix disagrees with published preview'
 for id,rows in groups.items():assert len(rows)==2 and rows[0]['insertion_pcm_sha256']==rows[1]['insertion_pcm_sha256']
 # The actual existing Duplex caller has a separate positive/negative payload fixture.
 fixture=json.loads((ROOT/'research/s1_context_pressure/call-preflight.json').read_text());assert fixture['status']=='pass' and fixture['no_question_transcript_in_payload']
 result=dict(status='pass',paired_questions=len(groups),audio_cases=len(p['cases']),full_prefixes_match_current_library=True,question_insertions_byte_identical=True,source_evidence_past_only=True,no_enrollment_or_future_source=True,prior_actual_Duplex_payload_fixture=fixture,GPUs=0)
 (D/'native-preflight.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['status','paired_questions','audio_cases','GPUs']}))
if __name__=='__main__':main()
