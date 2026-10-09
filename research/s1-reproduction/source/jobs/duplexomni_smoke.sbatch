#!/usr/bin/env bash
#SBATCH --job-name=duplex-omni-smoke
#SBATCH --partition=a100
#SBATCH --account=YOUR_SLURM_ACCOUNT
#SBATCH --qos=jhu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=16
#SBATCH --mem=192G
#SBATCH --time=01:30:00
#SBATCH --chdir=/path/to/duplex
#SBATCH --output=/path/to/duplex/logs/%x-%j.out
#SBATCH --error=/path/to/duplex/logs/%x-%j.err
set -euo pipefail
source scripts/cluster_runtime.sh
export HF_HOME="$PWD/cache/hf"
export XDG_CACHE_HOME="$PWD/cache"
export TORCH_HOME="$PWD/cache/torch"
export PYTHONPYCACHEPREFIX="$PWD/cache/pycache"
export TMPDIR="$PWD/cache/tmp"
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export VLLM_CACHE_ROOT="$PWD/cache/vllm"
export TRITON_CACHE_DIR="$PWD/cache/triton"
export OMP_NUM_THREADS=4
mkdir -p "$TMPDIR" "$VLLM_CACHE_ROOT" "$TRITON_CACHE_DIR"
nvidia-smi --query-gpu=index,uuid,name,compute_mode,memory.total,memory.free --format=csv
envs/duplexomni/bin/python -u scripts/with_gpu_runtime.py \
  --out "exp/diagnostics/gpu_runtime_$SLURM_JOB_ID" -- \
  envs/duplexomni/bin/python -u scripts/smoke_duplexomni.py "$@"
