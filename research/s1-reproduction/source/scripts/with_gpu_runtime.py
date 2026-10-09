"""Run a command using only allocated GPUs, with job-local MPS when required.

Do not change GPU compute mode or the cluster's shared MPS service. Runtime
logs stay in the requested experiment directory; the private IPC socket uses
a short temporary path. UUID selection avoids MPS ordinal remapping.
"""
import argparse
import csv
import io
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
import time

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--out", type=Path, required=True)
parser.add_argument("command", nargs=argparse.REMAINDER)
args = parser.parse_args()
command = args.command[1:] if args.command[:1] == ["--"] else args.command
if not command:
    parser.error("Specify the command after --")
if "SLURM_JOB_ID" not in os.environ or not os.environ.get("CUDA_VISIBLE_DEVICES"):
    raise RuntimeError("A Slurm GPU allocation with CUDA_VISIBLE_DEVICES is required")
args.out.mkdir(parents=True, exist_ok=True)
job = os.environ["SLURM_JOB_ID"]
started = time.monotonic()
env = os.environ.copy()
original = env["CUDA_VISIBLE_DEVICES"].split(",")
raw = subprocess.check_output(["nvidia-smi", "--query-gpu=index,uuid,name,compute_mode,memory.total",
                               "--format=csv,nounits"], text=True)
inventory = list(csv.DictReader(io.StringIO(raw), skipinitialspace=True))
# ConstrainDevices may renumber CUDA_VISIBLE_DEVICES inside a job cgroup.
# Slurm's allocation IDs remain global; prefer step IDs for narrower steps.
# https://slurm.schedmd.com/gres.html#GPU_Management
allocation_ids = env.get("SLURM_STEP_GPUS") or env.get("SLURM_JOB_GPUS")
identities = original
mapping_basis = "visible_devices"
if allocation_ids and all(entry.strip().isdigit() for entry in original):
    allocation = allocation_ids.split(",")
    if len(allocation) != len(original):
        raise RuntimeError("Global allocation IDs do not match the visible step; refuse ambiguous GPU mapping")
    indices = {row['index'] for row in inventory}
    if len(inventory) == len(original) and {entry.strip() for entry in original} == indices:
        # Some job containers filter and renumber NVML as well as CUDA. In
        # that case the complete visible inventory is already job-local.
        identities = original
        mapping_basis = "complete_job_local_nvml_inventory"
    else:
        identities = allocation
        mapping_basis = "global_slurm_allocation_ids"
env["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
selected = []
for entry in identities:
    matches = [row for row in inventory if row["index"] == entry.strip() or row["uuid"] == entry.strip()]
    if len(matches) != 1:
        raise RuntimeError(f"Allocated GPU {entry!r} does not map uniquely to the NVML inventory")
    selected.append(matches[0])
if len({row["uuid"] for row in selected}) != len(original):
    raise RuntimeError("Duplicate allocated GPU mapping")
env["CUDA_VISIBLE_DEVICES"] = ",".join(row["uuid"] for row in selected)
env["DUPLEX_GPU_UUID_MAPPING"] = "1"
env["VLLM_WORKER_MULTIPROC_METHOD"] = "spawn"
shims = str(Path(__file__).resolve().parent / "runtime_shims")
env["PYTHONPATH"] = shims + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
modes = [row["compute_mode"].lower() for row in selected]
if any("prohibited" in mode for mode in modes):
    raise RuntimeError("An allocated GPU is in prohibited compute mode")
needs_mps = any("exclusive" in mode for mode in modes)
summary = {"job_id": job, "node": env.get("SLURMD_NODENAME"), "status": "starting",
           "original_visible_devices": original, "global_allocation_ids": allocation_ids, "mapping_basis": mapping_basis, "selected_gpus": selected,
           "visible_devices": env["CUDA_VISIBLE_DEVICES"], "mps_required": needs_mps}
pipe = None
control = None
child = None
mps_started = False
interrupted = None


def forward_signal(signum, _frame):
    global interrupted
    interrupted = signum
    if child is not None and child.poll() is None:
        os.killpg(child.pid, signum)


signal.signal(signal.SIGTERM, forward_signal)
signal.signal(signal.SIGINT, forward_signal)
try:
    if needs_mps:
        control = shutil.which("nvidia-cuda-mps-control")
        if not control:
            raise RuntimeError("Exclusive-process GPUs require nvidia-cuda-mps-control on this node")
        pipe = tempfile.mkdtemp(prefix=f"duplex-mps-{os.getuid()}-{job}-", dir="/tmp")
        logdir = args.out.resolve() / "mps"
        logdir.mkdir(exist_ok=True)
        env.update(CUDA_MPS_PIPE_DIRECTORY=pipe, CUDA_MPS_LOG_DIRECTORY=str(logdir))
        summary.update(mps_pipe=pipe, mps_log_directory=str(logdir))
        subprocess.run([control, "-d"], env=env, check=True, timeout=30)
        mps_started = True
        summary["mps_control_status"] = subprocess.check_output(
            [control], input="get_server_list\n", env=env, text=True, timeout=30).strip()
    summary["status"] = "running"
    (args.out / "runtime.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({"gpu_runtime": summary}), flush=True)
    if interrupted is not None:
        raise RuntimeError("Interrupted before client command started")
    child = subprocess.Popen(command, env=env, start_new_session=True)
    code = child.wait()
    summary.update(status="pass" if code == 0 else "failed", command_exit_code=code)
except BaseException as exc:
    summary.update(status="failed", error=f"{type(exc).__name__}: {exc}")
    raise
finally:
    if child is not None and child.poll() is None:
        os.killpg(child.pid, signal.SIGTERM)
        try:
            child.wait(timeout=30)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL)
            child.wait()
    if mps_started:
        try:
            shutdown = subprocess.run([control], input="quit\n", env=env,
                                      text=True, capture_output=True, timeout=30)
            summary["mps_shutdown_exit_code"] = shutdown.returncode
            if shutdown.returncode:
                summary["mps_shutdown_error"] = shutdown.stderr[-2000:]
        except Exception as exc:
            summary["mps_shutdown_error"] = f"{type(exc).__name__}: {exc}"
    if pipe is not None:
        shutil.rmtree(pipe, ignore_errors=True)
    summary["wall_seconds"] = time.monotonic() - started
    (args.out / "runtime.json").write_text(json.dumps(summary, indent=2) + "\n")
raise SystemExit(code if code >= 0 else 128 - code)
