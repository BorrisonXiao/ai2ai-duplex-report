"""Independent ASR after all S1 services have exited; no automatic accuracy claim."""
import argparse,json,math,sys
from pathlib import Path
import numpy as np,soundfile as sf,torch
from scipy.signal import resample_poly
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'external/mp-bench/scripts'))
from transcribe import transcribe_paths
import nemo.collections.asr as nemo_asr

def main():
    p=argparse.ArgumentParser();p.add_argument('--job',required=True);a=p.parse_args();base=ROOT/'exp/s1_listening'/a.job
    model=nemo_asr.models.ASRModel.restore_from(str(next((ROOT/'models/mpbench-parakeet').glob('*.nemo'))),map_location=torch.device('cuda')).eval()
    for folder in sorted(base.iterdir()):
        if not folder.is_dir() or not (folder/'response.wav').exists():continue
        x,sr=sf.read(folder/'response.wav',dtype='float32');g=math.gcd(sr,16000);y=resample_poly(x,16000//g,sr//g) if sr!=16000 else x
        path=folder/'response-for-asr.wav';sf.write(path,y,16000,subtype='PCM_16')
        result=transcribe_paths(model,[str(path)],batch_size=1)[0] if np.max(abs(y))>0 else {'text':'','chunks':[]}
        (folder/'asr.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({'case':folder.name,'spoken_transcript':result['text']}),flush=True)

if __name__=='__main__':main()
