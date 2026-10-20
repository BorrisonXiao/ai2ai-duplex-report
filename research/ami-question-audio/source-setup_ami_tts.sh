#!/usr/bin/env bash
# Isolated runtimes; existing model environments are never modified.
set -euo pipefail
cd "$(dirname "$0")/.."
export UV_CACHE_DIR="$PWD/cache/uv" UV_PYTHON_INSTALL_DIR="$PWD/cache/uv-python"
export UV_LOCK_TIMEOUT=1800 TMPDIR="$PWD/cache/tmp" HF_HOME="$PWD/cache/hf"
export PYTHONPYCACHEPREFIX="$PWD/cache/pycache"
UV="$PWD/.migration/bin/uv"
for name in ami_qwen_tts ami_chatterbox ami_f5; do
  if [ ! -x "envs/$name/bin/python" ]; then "$UV" venv --python envs/data/bin/python "envs/$name"; fi
done
"$UV" pip install --python envs/ami_qwen_tts/bin/python 'vllm==0.16.0' 'vllm-omni==0.16.0' 'transformers==4.57.6' 'librosa==0.11.0' 'soundfile==0.14.0' 'qwen-tts==0.1.1' --override requirements/ami_qwen_override.txt
"$UV" pip install --python envs/ami_chatterbox/bin/python 'chatterbox-tts==0.1.7' 'speechbrain==1.0.3' 'imageio-ffmpeg' 'jiwer'
"$UV" pip install --python envs/ami_f5/bin/python 'torch==2.9.1' 'torchaudio==2.9.1' 'transformers==4.57.6' 'f5-tts==1.1.22' 'soundfile==0.14.0' 'imageio-ffmpeg'
for name in ami_qwen_tts ami_chatterbox ami_f5; do
  "$UV" pip freeze --python "envs/$name/bin/python" > "research/ami_question_audio/$name-lock.txt"
done
