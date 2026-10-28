"""Verify candidate caller repairs using the actual S1 speech pipeline."""
import copy,json,os,time,inspect
from pathlib import Path
from unittest.mock import patch
import s1_meeting_pilot_adapter as pilot
ROOT=Path(__file__).resolve().parents[1]
REPAIR=pilot.NATIVE+"\nThe audio contains the earlier meeting followed by a request addressed to you. Answer the final request using only the meeting audio. System 2 is unavailable, so answer yourself rather than delegating or offering to check. Use the normal four-field object with tts_control, system2_control, asr and tts. Put only the next short spoken fragment in tts; later turns will continue it. The asr field may be empty. Do not greet or invent facts. State uncertainty when the audio does not establish an answer."
# This generic instruction supplies no question text, transcript or reference answer.
def make_buffered_case(prompt,progress):
 source=inspect.getsource(pilot.buffered_case);needle="int(case['id'][1:])-1";assert source.count(needle)==1
 source=source.replace(needle,"case.get('progress_index', 0)")
 scope=vars(pilot).copy();scope.update(NATIVE=prompt,progress=progress)
 exec(compile(source,__file__+' [diagnostic condition IDs]','exec'),scope)
 return scope['buffered_case']

def run_pilot(root,out,config,trace):
 target=root/'exp/s1_empty_speech'/os.environ['SLURM_JOB_ID'];target.mkdir(parents=True,exist_ok=True)
 rows=json.loads((root/'research/s1_meeting_pilot/inputs.json').read_text())['cases'];conditions=[]
 # Native P01 reproduces the empty-field control with the full speech stack.
 conditions.append((rows[0],False,False,False))
 for row in rows:
  conditions.extend([(row,False,True,False),(row,True,False,False),(row,True,True,False),(row,False,False,True),(row,False,True,True)])
 results=[];case_records=[]
 def update(phase,**extra):pilot.save(root/'research/s1_empty_diagnosis/speech-progress.json',{'job':os.environ['SLURM_JOB_ID'],'phase':phase,'updated_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),**extra})
 for row,use_prompt,use_gain,question_only in conditions:
  name=row['id']+('-request-only' if question_only else '')+('-repair' if use_prompt else '-native')+('-request-adjusted' if use_gain else '-original')
  case=copy.deepcopy(row);case['id']=name
  if question_only:
   path=root/'research/s1_empty_diagnosis/audio'/(row['id']+('-rms_adjusted-request.wav' if use_gain else '-original-request.wav'));case['input_audio']=str(path.relative_to(root));case['input_sha256']=pilot.sha(path);case['input_method']='Question-only buffered diagnostic; meeting history absent.'
  elif use_gain:
   path=root/'research/s1_empty_diagnosis/audio'/(row['id']+'-full-request-adjusted.wav');case['input_audio']=str(path.relative_to(root));case['input_sha256']=pilot.sha(path)
  case_records.append({**case,'system_prompt':REPAIR if use_prompt else pilot.NATIVE,'prompt_changed':use_prompt,'request_level_adjusted':use_gain,'history_mode':'none' if question_only else 'full'})
  update('speech_inference',current_case=name,completed_conditions=len(results))
  case['progress_index']=len(results)
  r=make_buffered_case(REPAIR if use_prompt else pilot.NATIVE,update)(root,target,case,config)
  if question_only:r['context_mode']='no_history';pilot.save(target/name/'run.json',r)
  results.append(r);pilot.save(target/'cases.json',case_records);pilot.save(target/'runs.json',results)
  print(json.dumps({'case':name,'status':r['status'],'model_asr':r.get('model_asr'),'tts':r['native_text']}),flush=True)
 return [{'name':r['pilot_id'],'turns':json.loads((target/r['pilot_id']/'turns.json').read_text()),'wall_seconds':r['wall_seconds']} for r in results]
def main():
 source=(ROOT/'scripts/smoke_duplexomni.py').read_text().replace('from native_interaction import run_native_interaction','from s1_empty_speech_adapter import run_pilot as run_native_interaction').replace('str(root / "scripts/duplex_server_smoke.py")','str(root / "scripts/s1_meeting_pilot_server.py")')
 exec(compile(source,str(ROOT/'scripts/smoke_duplexomni.py')+' [S1 empty-response speech controls]','exec'),{'__name__':'__main__','__file__':str(ROOT/'scripts/smoke_duplexomni.py')})
if __name__=='__main__':main()
