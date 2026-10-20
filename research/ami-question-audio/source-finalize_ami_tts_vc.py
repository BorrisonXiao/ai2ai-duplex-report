"""Record the VC control outcome and prepare level-matched comparison audio."""
import json
import math
from pathlib import Path
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly
from mix_ami_question_audio import process,tone_before

ROOT=Path(__file__).resolve().parents[1]

def main():
 base=ROOT/'exp/ami_question_audio';data=json.loads((base/'review/manifest.json').read_text());asr={r['path']:r for r in json.loads((base/'evaluation/asr.json').read_text())};speaker={r['path']:r for r in json.loads((base/'evaluation/speaker.json').read_text())}
 original=next(c for c in data['clips'] if c['model']=='f5' and c['short_id']=='deadlines');ref=next(r for r in data['protocol']['references'] if r['id']=='C-primary');reference,sr=sf.read(ROOT/ref['mix'])
 mix,_=sf.read(ROOT/'data/prethinking_pilot/ami_EN2003a/EN2003a.Mix-Headset.wav',dtype='int16');words=[w for c in json.loads((ROOT/'exp/prethinking_pilot/data/chunks.json').read_text()) for w in c['words']];tone,tone_info=tone_before(words,mix,original['source_time_seconds'])
 records=[]
 for row in json.loads((base/'vc/generations.json').read_text()):
  y,rate=sf.read(ROOT/row['path'])
  if rate!=16000:y=resample_poly(y,16000//math.gcd(rate,16000),rate//math.gcd(rate,16000))
  y,acoustics=process(y,reference,tone);path=(base/'vc')/(Path(row['path']).stem+'--matched.wav');sf.write(path,y,16000,subtype='PCM_16')
  records.append(dict(**row,matched_path=str(path.relative_to(ROOT)),asr=asr[row['path']],speaker_check=speaker[row['path']],acoustics=acoustics,delta_cosine_vs_direct_f5=speaker[row['path']]['target_cosine']-original['speaker_check']['target_cosine']))
 result=dict(condition='F5-TTS question converted with Chatterbox S3',records=records,direct_f5_cosine=original['speaker_check']['target_cosine'],decision='Retain direct F5. Both VC controls preserve wording under Parakeet but reduce held-out C speaker similarity; do not use VC for the main replay.',listening_review_pending=True,additional_tts_architectures=0)
 (ROOT/'research/ami_question_audio/vc-controls.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='records'},indent=2))

if __name__=='__main__':main()
