"""Supply the missing reference-length callback in vLLM-Omni 0.16's example.

Uses the same frame-count rule as its official serving_speech.py: ceil(duration
times codec frame rate). No model weights or generation settings are changed.
The initial offline helper instead falls back to a 2048-token padded prompt.
"""
import json
import math
from pathlib import Path
import runpy
import soundfile as sf

ROOT=Path(__file__).resolve().parents[1]

def install():
 from vllm_omni.model_executor.models.qwen3_tts.qwen3_tts_talker import Qwen3TTSTalkerForConditionalGeneration as Talker
 cfg=json.loads((ROOT/'models/ami-qwen3-tts/speech_tokenizer/config.json').read_text());rate=cfg['output_sample_rate']/cfg['encode_downsample_rate']
 original=Talker.estimate_prompt_len_from_additional_information
 def estimate(ref):
  while isinstance(ref,list) and len(ref)==1:ref=ref[0]
  if isinstance(ref,str):
   info=sf.info(ref);return math.ceil(info.frames/info.samplerate*rate)
  if isinstance(ref,(tuple,list)) and len(ref)==2:return math.ceil(len(ref[0])/int(ref[1])*rate)
  raise ValueError('Unrecognized reference type; no fallback padding permitted')
 def exact(**kwargs):
  if kwargs.get('estimate_ref_code_len') is None:kwargs['estimate_ref_code_len']=estimate
  length=original(**kwargs)
  print(json.dumps(dict(exact_prompt_tokens=length,reference_codec_frames=estimate(kwargs['additional_information']['ref_audio']),codec_frame_rate=rate)),flush=True)
  return length
 Talker.estimate_prompt_len_from_additional_information=staticmethod(exact)

if __name__=='__main__':
 install();runpy.run_path(str(ROOT/'scripts/ami_tts_generate.py'),run_name='__main__')
