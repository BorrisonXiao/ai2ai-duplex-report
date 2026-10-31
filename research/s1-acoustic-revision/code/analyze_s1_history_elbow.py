"""Describe saved recognition changes without claiming a response-quality threshold."""
import json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
def main():
 d=json.loads((ROOT/'research/s1_array_sweep/review.json').read_text());out=[]
 for condition in ['headset_mix','distant_01','beamformed_mdm8']:
  rows=[r for r in d['cases'] if r['condition']==condition];bins=[]
  for title,lo,hi in [('Below 60 seconds',0,60),('60 to below 180 seconds',60,180),('180 seconds and longer',180,float('inf'))]:
   all_rows=[r for r in rows if lo<=r['context_seconds']<hi];valid=[r for r in all_rows if r['WER_valid']]
   bins.append(dict(label=title,attempts=len(all_rows),WER_scored=len(valid),unscored=len(all_rows)-len(valid),strict_passes=sum(r['recognition']['recognized'] for r in valid),mean_WER=float(np.mean([r['recognition']['WER'] for r in valid])),median_WER=float(np.median([r['recognition']['WER'] for r in valid]))))
  valid=[r for r in rows if r['WER_valid']];fail=next(r for r in valid if not r['recognition']['recognized']);later=[r['index'] for r in valid if r['index']>fail['index'] and r['recognition']['recognized']];eligible=[r for r in rows if r.get('source_audit')]
  out.append(dict(condition=condition,bins=bins,first_strict_miss_level=fail['index'],first_strict_miss_seconds=fail['context_seconds'],later_strict_recoveries=later,eligible_responses=len(eligible),source_complete=sum(r['source_audit']['complete'] for r in eligible),partial_levels=[r['index'] for r in eligible if r['source_audit']['fact_score']>0]))
 pressure=json.loads((ROOT/'research/s1_context_pressure/review.json').read_text());bf40=next(r for r in d['cases'] if r['condition']=='beamformed_mdm8' and r['index']==40)
 result=dict(status='descriptive_saved_output_analysis',conditions=out,headset_first_core_question_loss_seconds=pressure['first_missing_core_context_seconds'],headset_later_core_recovery_levels=pressure['later_core_recovery_levels'],headset_latest_core_recovery_seconds=pressure['last_core_recovery_context_seconds'],all_evidence_first_available_seconds=198.91,facts_end_source_seconds=136.44,question_onset_source_seconds=309.21,fixed_gap_from_last_reference_fact_to_question_seconds=309.21-136.44,last_level_added_initial_silence_seconds=74.89,low_WER_strict_failure_example=dict(condition='beamformed_mdm8',level=40,WER=bf40['recognition']['WER'],question_ASR=bf40['question_asr']),conclusions=['The headset trace has a descriptive recognition change between 53.94 and 61.11 seconds, with later recoveries; it is not a universal cutoff.','Raw and beamformed recognition fluctuate and improve again at longer contexts.','No response-quality elbow can be estimated: prefixes below 198.91 seconds lack complete reference evidence, and all 33 eligible responses are incomplete.','Adding older audio before a fixed question does not vary the time elapsed from the answer evidence to the question.','The shared clean question, boundary microphone switch and limited automatic judge constrain interpretations; acoustic realism is a separate control.'],limitations=['One question and one greedy run per position; nested contexts are dependent.','Bins and the candidate recognition interval are descriptive, not a fitted or independently validated breakpoint.','A low-WER strict miss may only omit the Assistant cue, rather than lose the request meaning.'],gpus=0)
 p=ROOT/'research/s1_acoustic_revision/elbow-analysis.json';p.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
