#!/usr/bin/env bash
# One L40S 48 GB. VC, Parakeet and ECAPA run sequentially on GPU 0.
#SBATCH --job-name=ami-tts-vc
#SBATCH --partition=l40s
#SBATCH --account=lgarci27_omnienc
#SBATCH --qos=jhu
#SBATCH --gres=gpu:l40s:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=00:10:00
#SBATCH --chdir=/weka/scratch/jhu/lgarci27/omnienc/users/cxiao/duplex
#SBATCH --output=/weka/scratch/jhu/lgarci27/omnienc/users/cxiao/duplex/logs/%x-%j.out
#SBATCH --error=/weka/scratch/jhu/lgarci27/omnienc/users/cxiao/duplex/logs/%x-%j.err
set -euo pipefail
source scripts/cluster_runtime.sh
export HF_HOME="$PWD/cache/hf" XDG_CACHE_HOME="$PWD/cache" TORCH_HOME="$PWD/cache/torch" TMPDIR="$PWD/cache/tmp"
export PYTHONPYCACHEPREFIX="$PWD/cache/pycache" NUMBA_CACHE_DIR="$PWD/cache/numba" MPLCONFIGDIR="$PWD/cache/matplotlib"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 TOKENIZERS_PARALLELISM=false
envs/duplexomni/bin/python scripts/with_gpu_runtime.py --out "exp/ami_question_audio/vc_runtime_$SLURM_JOB_ID" -- envs/ami_chatterbox/bin/python -u scripts/ami_tts_vc.py
envs/duplexomni/bin/python scripts/with_gpu_runtime.py --out "exp/ami_question_audio/vc_asr_runtime_$SLURM_JOB_ID" -- envs/mpbench_asr/bin/python -u scripts/ami_tts_evaluate.py --stage asr
exec envs/duplexomni/bin/python scripts/with_gpu_runtime.py --out "exp/ami_question_audio/vc_speaker_runtime_$SLURM_JOB_ID" -- envs/ami_chatterbox/bin/python -u scripts/ami_tts_evaluate.py --stage speaker
