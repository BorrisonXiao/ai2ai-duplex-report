#!/usr/bin/env bash
# One L40S 48 GB: ASR then speaker encoder sequentially share GPU 0.
# Runs only after all TTS jobs finish; no generation job overlaps it.
#SBATCH --job-name=ami-tts-eval
#SBATCH --partition=l40s
#SBATCH --account=lgarci27_omnienc
#SBATCH --qos=jhu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gres=gpu:l40s:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=00:15:00
#SBATCH --chdir=/weka/scratch/jhu/lgarci27/omnienc/users/cxiao/duplex
#SBATCH --output=/weka/scratch/jhu/lgarci27/omnienc/users/cxiao/duplex/logs/%x-%j.out
#SBATCH --error=/weka/scratch/jhu/lgarci27/omnienc/users/cxiao/duplex/logs/%x-%j.err
set -euo pipefail
source scripts/cluster_runtime.sh
export HF_HOME="$PWD/cache/hf" XDG_CACHE_HOME="$PWD/cache" TORCH_HOME="$PWD/cache/torch"
export PYTHONPYCACHEPREFIX="$PWD/cache/pycache" TMPDIR="$PWD/cache/tmp" NUMBA_CACHE_DIR="$PWD/cache/numba" MPLCONFIGDIR="$PWD/cache/matplotlib"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 TOKENIZERS_PARALLELISM=false
envs/duplexomni/bin/python -u scripts/with_gpu_runtime.py --out "exp/ami_question_audio/eval_runtime_$SLURM_JOB_ID" -- envs/mpbench_asr/bin/python -u scripts/ami_tts_evaluate.py --stage asr
exec envs/duplexomni/bin/python -u scripts/with_gpu_runtime.py --out "exp/ami_question_audio/speaker_runtime_$SLURM_JOB_ID" -- envs/ami_chatterbox/bin/python -u scripts/ami_tts_evaluate.py --stage speaker
