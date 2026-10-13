#!/usr/bin/env bash
# One A100-SXM4 80 GB: teacher alone on GPU 0, cases sequential; no fallback.
#SBATCH --job-name=prethink-completion
#SBATCH --partition=a100
#SBATCH --account=lgarci27_omnienc
#SBATCH --qos=jhu
#SBATCH --constraint=a100_sxm
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=12
#SBATCH --mem=64G
#SBATCH --time=00:45:00
#SBATCH --chdir=/weka/scratch/jhu/lgarci27/omnienc/users/cxiao/duplex
#SBATCH --output=/weka/scratch/jhu/lgarci27/omnienc/users/cxiao/duplex/logs/%x-%j.out
#SBATCH --error=/weka/scratch/jhu/lgarci27/omnienc/users/cxiao/duplex/logs/%x-%j.err
set -euo pipefail
source scripts/cluster_runtime.sh
export HF_HOME="$PWD/cache/hf" XDG_CACHE_HOME="$PWD/cache" TORCH_HOME="$PWD/cache/torch"
export PYTHONPYCACHEPREFIX="$PWD/cache/pycache" TMPDIR="$PWD/cache/tmp" VLLM_CACHE_ROOT="$PWD/cache/vllm" TRITON_CACHE_DIR="$PWD/cache/triton"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 NUMEXPR_NUM_THREADS=4
envs/duplexomni/bin/python -u scripts/with_gpu_runtime.py --out "exp/prethinking_pilot/completion_runtime_$SLURM_JOB_ID" -- \
  envs/duplexomni/bin/python -u scripts/run_prethinking_completion.py --config "$1"
