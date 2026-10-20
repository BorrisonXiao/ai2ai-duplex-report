#!/usr/bin/env bash
# Apply the measured Chatterbox runtime after the original isolated setup.
set -euo pipefail
cd "$(dirname "$0")/.."
export UV_CACHE_DIR="$PWD/cache/uv" TMPDIR="$PWD/cache/tmp"
.migration/bin/uv pip install --python envs/ami_chatterbox/bin/python 'torch==2.9.1' 'torchaudio==2.9.1' 'setuptools<81' --override requirements/ami_chatterbox_override.txt
.migration/bin/uv pip freeze --python envs/ami_chatterbox/bin/python > research/ami_question_audio/ami_chatterbox-lock.txt
