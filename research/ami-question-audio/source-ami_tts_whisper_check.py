"""Second independent CPU transcription after acoustic processing, raw versus matched."""
import json
import math
from pathlib import Path
import time
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly
import torch
from transformers import WhisperForConditionalGeneration,WhisperProcessor

ROOT=Path(__file__).resolve().parents[1]

def main():
 torch.set_num_threads(4);start=time.monotonic();path=ROOT/'models/validation/whisper-base'
 processor=WhisperProcessor.from_pretrained(path,local_files_only=True);model=WhisperForConditionalGeneration.from_pretrained(path,local_files_only=True).float().cpu().eval()
 base=ROOT/'exp/ami_question_audio/review';data=json.loads((base/'manifest.json').read_text());records=[]
 for clip in data['clips']:
  row=dict(id=clip['id'],question=clip['question'])
  for key in ['raw_path','matched_path']:
   y,sr=sf.read(ROOT/clip[key],dtype='float32')
   if sr!=16000:y=resample_poly(y,16000//math.gcd(sr,16000),sr//math.gcd(sr,16000))
   inputs=processor(y,sampling_rate=16000,return_tensors='pt',return_attention_mask=True)
   with torch.inference_mode():ids=model.generate(inputs.input_features,attention_mask=inputs.attention_mask,max_new_tokens=128,language='en',task='transcribe')
   row[key]=processor.batch_decode(ids,skip_special_tokens=True)[0].strip()
  records.append(row);print(json.dumps(row),flush=True)
 (base/'whisper-check.json').write_text(json.dumps(dict(model='openai/whisper-base',gpus=0,seconds=time.monotonic()-start,records=records,scope='Independent ASR proxy; small-model errors require comparison with Parakeet, not automatic rejection.'),indent=2)+'\n')

if __name__=='__main__':main()
