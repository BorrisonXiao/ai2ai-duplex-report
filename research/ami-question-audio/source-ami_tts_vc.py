"""Two VC controls for the harder requester C, reusing Chatterbox's S3 generator."""
import hashlib
import json
import os
from pathlib import Path
import time
import numpy as np
import soundfile as sf
import torch
from chatterbox.vc import ChatterboxVC

ROOT=Path(__file__).resolve().parents[1]

def main():
 start=time.monotonic();base=ROOT/'exp/ami_question_audio';data=json.loads((base/'review/manifest.json').read_text());c=next(c for c in data['clips'] if c['short_id']=='deadlines' and c['model']=='f5');out=base/'vc';out.mkdir(exist_ok=True)
 model=ChatterboxVC.from_local(ROOT/'models/ami-chatterbox','cuda');rows=[]
 for kind in ['primary','alternate']:
  ref=next(r for r in data['protocol']['references'] if r['id']=='C-'+kind);torch.manual_seed(17);np.random.seed(17);t=time.monotonic()
  y=model.generate(str(ROOT/c['raw_path']),target_voice_path=str(ROOT/ref['headset'])).detach().cpu().numpy().flatten();path=out/('deadlines--f5-vc-'+kind+'.wav');sf.write(path,y,model.sr,subtype='PCM_16')
  rows.append(dict(model='f5_chatterbox_vc',job=os.environ['SLURM_JOB_ID'],path=str(path.relative_to(ROOT)),text=c['question'],requester='C',short_id='deadlines',reference_id=ref['id'],reference_path=ref['headset'],source_tts_path=c['raw_path'],source_tts_job=c['job'],reference_end_seconds=ref['source_end_seconds'],source_time_seconds=c['source_time_seconds'],is_vc=True,status='generated_content_and_voice_review_required',duration_seconds=len(y)/model.sr,wall_seconds=time.monotonic()-t,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),watermark='Standard Perth watermark applied'))
  (out/'generations.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows[-1]),flush=True)
 (out/'runtime.json').write_text(json.dumps(dict(job=os.environ['SLURM_JOB_ID'],gpus=1,gpu_name=torch.cuda.get_device_name(0),seconds=time.monotonic()-start,scope='F5 waveform converted with Chatterbox S3 only; no new TTS architecture'),indent=2)+'\n')

if __name__=='__main__':main()
