#!/usr/bin/env bash
# One H100 SXM 80 GB per model; acoustic decoder shares GPU 0 with TTS.
# Three independent model jobs may overlap: maximum three GPUs. No answer model.
#SBATCH --job-name=ami-tts
#SBATCH --partition=h100
#SBATCH --account=lgarci27_omnienc
#SBATCH --qos=jhu
#SBATCH --constraint=h100_sxm
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gres=gpu:h100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=00:30:00
#SBATCH --chdir=/weka/scratch/jhu/lgarci27/omnienc/users/cxiao/duplex
#SBATCH --output=/weka/scratch/jhu/lgarci27/omnienc/users/cxiao/duplex/logs/%x-%j.out
#SBATCH --error=/weka/scratch/jhu/lgarci27/omnienc/users/cxiao/duplex/logs/%x-%j.err
set -euo pipefail
source scripts/cluster_runtime.sh
export HF_HOME="$PWD/cache/hf" XDG_CACHE_HOME="$PWD/cache" TORCH_HOME="$PWD/cache/torch"
export PYTHONPYCACHEPREFIX="$PWD/cache/pycache" TMPDIR="$PWD/cache/tmp" VLLM_CACHE_ROOT="$PWD/cache/vllm" TRITON_CACHE_DIR="$PWD/cache/triton"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 TOKENIZERS_PARALLELISM=false
export PATH="$PWD/cache/ami-tools:$PATH"
mkdir -p "$TMPDIR" "$VLLM_CACHE_ROOT" "$TRITON_CACHE_DIR"
model=$1
case "$model" in
 qwen) runtime=ami_qwen_tts;;
 chatterbox) runtime=ami_chatterbox;;
 f5) runtime=ami_f5;;
 *) exit 2;;
esac
envs/data/bin/python scripts/verify_ami_tts_launch.py
exec envs/duplexomni/bin/python -u scripts/with_gpu_runtime.py --out "exp/ami_question_audio/runtime_$SLURM_JOB_ID" -- "envs/$runtime/bin/python" -u scripts/ami_tts_generate.py --model "$model"
