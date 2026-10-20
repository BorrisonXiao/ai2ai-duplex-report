"""Use lossless SoundFile WAV reads with F5, avoiding a CUDA-13 TorchCodec wheel.

This replaces file decoding only. It preserves sample rate, channels and floating
PCM values; the frozen F5 model, vocoder and inference sweep remain unchanged.
"""
from pathlib import Path
import runpy
import soundfile as sf
import torch
import torchaudio

def load_pcm(uri,frame_offset=0,num_frames=-1,normalize=True,channels_first=True,**kwargs):
 if Path(uri).suffix.lower()!='.wav':raise ValueError('Pilot adapter accepts PCM WAV only')
 if not normalize:raise ValueError('Pilot requires normalized floating PCM')
 with sf.SoundFile(uri) as f:
  f.seek(frame_offset);a=f.read(frames=num_frames,dtype='float32',always_2d=True);sr=f.samplerate
 return torch.from_numpy(a.T.copy() if channels_first else a),sr

torchaudio.load=load_pcm
print('F5 PCM-only SoundFile decoder adapter enabled; synthesis unchanged',flush=True)
runpy.run_path(str(Path(__file__).with_name('ami_tts_generate.py')),run_name='__main__')
