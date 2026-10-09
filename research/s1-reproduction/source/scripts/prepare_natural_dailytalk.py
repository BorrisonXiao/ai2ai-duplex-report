"""Reproduce the selected same-speaker DailyTalk request/correction audio crops."""
from pathlib import Path
import argparse
import hashlib,json
import librosa
import soundfile as sf
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source',type=Path,default=ROOT/'data/benchmarks/natural_interruption_candidates/daily656.wav')
parser.add_argument('--folder',type=Path,default=ROOT/'data/benchmarks/natural_dailytalk_outlet')
args=parser.parse_args();SOURCE=args.source;DEST=args.folder
manifest=json.loads((DEST/'manifest.json').read_text())
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==manifest['source_sha256']
x,rate=sf.read(SOURCE,dtype='float32')
assert rate==manifest['source_sample_rate'] and x.shape[1]==2
for clip in manifest['clips']:
    wave=x[clip['source_sample_start']:clip['source_sample_end'],manifest['wave_channel']]
    wave=librosa.resample(wave,orig_sr=rate,target_sr=24000)
    path=ROOT/clip['file'];sf.write(path,wave,24000,subtype='PCM_16')
    assert hashlib.sha256(path.read_bytes()).hexdigest()==clip['sha256']
print('Original human crops reproduced byte for byte; no TTS or reference assistant audio.')
