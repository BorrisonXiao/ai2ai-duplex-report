"""Export short, explicitly synthetic AMI listening comparisons; no full prefix."""
import hashlib
import json
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'site/research/ami-question-audio'

def main():
 DEST.mkdir(parents=True,exist_ok=True);data=json.loads((ROOT/'exp/ami_question_audio/review/manifest.json').read_text());audio_map={}
 # Remove only this exporter's old flat WAV layout; source audio stays intact.
 for old in (DEST/'audio').glob('*.wav'):old.unlink()
 def audio(path):
  src=ROOT/path;relative='audio/'+src.parent.name+'/'+src.name;target=DEST/relative;target.parent.mkdir(parents=True,exist_ok=True)
  digest=hashlib.sha256(src.read_bytes()).hexdigest()
  if relative in audio_map and audio_map[relative]['sha256']!=digest:raise ValueError('Audio filename collision: '+relative)
  shutil.copyfile(src,target);assert hashlib.sha256(target.read_bytes()).hexdigest()==digest
  audio_map[relative]=dict(source=path,sha256=digest,bytes=src.stat().st_size)
  return relative
 for r in data['protocol']['references']:
  for channel in ['headset','mix']:r[channel]=audio(r[channel])
 for c in data['clips']:
  for key in ['raw_path','matched_path','injected_path']:c[key]=audio(c[key])
 for c in data['candidates']:c['path']=audio(c['path'])
 for c in data.get('excluded_attempt_outputs',[]):c['path']=audio(c['path'])
 data['publication_scope']='Short original voice references, short context-plus-synthetic-question clips, generated question-only tuning variants, metadata and scripts. Full meeting replay remains local.'
 (DEST/'manifest.json').write_text(json.dumps(data,indent=2)+'\n')
 vc=json.loads((ROOT/'research/ami_question_audio/vc-controls.json').read_text())
 for r in vc['records']:
  for key in ['path','matched_path']:r[key]=audio(r[key])
 (DEST/'vc-controls.json').write_text(json.dumps(vc,indent=2)+'\n')
 for name in ['model-provenance.json','source-revisions.json','protocol.json','accounting.json','review.json','literature.json','acoustic-tuning.json','ami_qwen_tts-lock.txt','ami_chatterbox-lock.txt','ami_f5-lock.txt']:
  p=ROOT/'research/ami_question_audio'/name
  if p.exists():shutil.copyfile(p,DEST/name)
 for name in ['configs/ami_qwen_tts_stages.yaml','jobs/ami_tts.sbatch','jobs/ami_tts_f5_retry.sbatch','jobs/ami_tts_qwen_retry.sbatch','jobs/ami_tts_evaluate.sbatch','jobs/ami_tts_vc.sbatch','scripts/setup_ami_tts.sh','scripts/repair_ami_tts_envs.sh']:
  shutil.copyfile(ROOT/name,DEST/('source-'+Path(name).name))
 for name in ['ami_tts_generate.py','prepare_ami_question_audio.py','ami_f5_pcm_launcher.py','ami_qwen_exact_prompt_launcher.py','ami_tts_evaluate.py','mix_ami_question_audio.py','export_ami_tts.py','replay_ami_question_injection.py','ami_tts_whisper_check.py','audit_ami_tts.py','ami_tts_vc.py','finalize_ami_tts_vc.py']:
  p=ROOT/'scripts'/name
  if p.exists():shutil.copyfile(p,DEST/('source-'+name))
 (DEST/'audio-provenance.json').write_text(json.dumps(audio_map,indent=2)+'\n')
 files={str(p.relative_to(DEST)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in DEST.rglob('*') if p.is_file() and p.name!='files.json'}
 (DEST/'files.json').write_text(json.dumps(files,indent=2)+'\n');print('Exported',len(files),'files',sum(f['bytes'] for f in files.values()),'bytes')

if __name__=='__main__':main()
