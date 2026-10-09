#!/usr/bin/env bash
# One 80 GB GPU, all S1 modules share GPU 0. No S2. Baseline gates interruption.
#SBATCH --job-name=duplex-natural-interrupt
#SBATCH --partition=a100,h100
#SBATCH --account=YOUR_SLURM_ACCOUNT
#SBATCH --qos=jhu
#SBATCH --constraint=a100_sxm|h100_sxm
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=16
#SBATCH --mem=96000M
#SBATCH --time=00:08:00
#SBATCH --chdir=/path/to/duplex
#SBATCH --output=/path/to/duplex/logs/%x-%j.out
#SBATCH --error=/path/to/duplex/logs/%x-%j.err
set -euo pipefail
snapshot_dir="$1"
envs/data/bin/python - "$snapshot_dir" <<'PY'
import hashlib,json,sys
from pathlib import Path
directory=Path(sys.argv[1]);manifest=json.loads((directory/'prepared.json').read_text())
assert manifest['preflight_status']=='cpu_preflight_pass'
for name,digest in manifest['files'].items():
    assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==digest,name
print('Frozen source/config/input hashes match CPU validation.',flush=True)
PY
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 NUMEXPR_NUM_THREADS=4
bash jobs/duplexomni_smoke.sbatch --config "$snapshot_dir/config.json"
