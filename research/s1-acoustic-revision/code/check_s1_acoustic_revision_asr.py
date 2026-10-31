"""Independently transcribe the saved revised inputs; no S1, TTS or judge."""
import hashlib,json,os,sys,time
from pathlib import Path
import soundfile as sf
import torch
import jiwer
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'external/mp-bench/scripts'))
from transcribe import transcribe_paths
import nemo.collections.asr as nemo_asr

def words(s):
 import re
 return re.findall(r'[a-z0-9]+',s.lower().replace("'",'').replace('’',''))
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
def main():
 snap=ROOT/os.environ['ACOUSTIC_SNAPSHOT'];job=os.environ['SLURM_JOB_ID'];out=ROOT/'exp/s1_acoustic_revision'/job;out.mkdir(parents=True,exist_ok=True)
 for name,digest in json.loads((snap/'hashes.json').read_text()).items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
 spec=json.loads((snap/'protocol.json').read_text());tasks=[dict(id=r['id'],path=r['question_audio'],expected=spec['question'],kind='question') for r in spec['cases']]
 tasks+=[dict(id='original-shared',path='exp/s1_acoustic_revision/assets/original-shared-question.wav',expected=spec['question'],kind='question')]
 tasks+=[dict(id=c+'-background',path=f'exp/s1_acoustic_revision/assets/{c}-background-control.wav',expected='',kind='background') for c in ['headset_mix','distant_01','beamformed_mdm8']]
 started=time.monotonic();model=nemo_asr.models.ASRModel.restore_from(str(next((ROOT/'models/mpbench-parakeet').glob('*.nemo'))),map_location=torch.device('cuda')).eval();rows=[]
 for task in tasks:
  result=transcribe_paths(model,[str(ROOT/task['path'])],batch_size=1)[0];text=result['text'];normalized=' '.join(words(text));expected=' '.join(words(task['expected']));info=sf.info(ROOT/task['path'])
  row=dict(**task,text=text,asr=result,audio_sha256=hashlib.sha256((ROOT/task['path']).read_bytes()).hexdigest(),audio_seconds=info.duration,word_count=len(words(text)))
  if task['kind']=='question':row.update(WER=jiwer.wer(expected,normalized),exact_wording=expected==normalized,cue_first=bool(words(text) and words(text)[0]=='assistant'))
  rows.append(row);save(out/'asr.json',rows);print(json.dumps({k:row.get(k) for k in ['id','text','WER','word_count','exact_wording','cue_first']}),flush=True)
 save(out/'summary.json',dict(status='ASR_completed_listening_review_required',cases=rows,wall_seconds=time.monotonic()-started,total_audio_seconds=sum(r['audio_seconds'] for r in rows),gpus=1,gpu_type_vram='L40S 48 GB',role='Independent Parakeet ASR on GPU 0; no S1/TTS/S2/judge'))
if __name__=='__main__':main()
