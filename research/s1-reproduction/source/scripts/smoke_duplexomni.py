"""Run local Thinker -> Talker audio inference on one or two allocated A100s.

The default tests one audio-conditioned turn. The System-2 configuration adds
a local reasoning service and a controlled feedback test. Neither is a latency
benchmark of the full realtime conversation stack.
"""
import argparse
import base64
import csv
import io
import json
import os
import signal
import subprocess
import time
from pathlib import Path

import requests
import soundfile as sf
import torch
from trajectory import Trajectory, export_trace

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--config", type=Path, default=root / "configs/duplexomni_single_gpu.json")
args = parser.parse_args()
config = json.loads(args.config.read_text())
assert config["gpus"] in (1, 2, 3), config
thinker_tp = int(config.get("thinker_tp", 1))
assert thinker_tp >= 1 and (thinker_tp == 1 if config["gpus"] == 1 else thinker_tp < config["gpus"])
speech_gpu = 0 if config["gpus"] == 1 else thinker_tp
s2_gpu = int(config.get("s2_gpu", speech_gpu))
assert 0 <= s2_gpu < config["gpus"]
if config["gpus"] == 1:
    assert config["sequential_startup"], "Shared-device memory profiling must be serialized"
    assert config["thinker_gpu_memory_utilization"] + config["talker_gpu_memory_utilization"] < 1
if "system2" in config:
    assert config["sequential_startup"]
    if config["gpus"] == 1:
        assert "continuous_system2" in config or "native_loop" in config
        assert config["thinker_gpu_memory_utilization"] + config["talker_gpu_memory_utilization"] + config["system2"]["gpu_memory_utilization"] < 1
    if s2_gpu == speech_gpu:
        assert config["talker_gpu_memory_utilization"] + config["system2"]["gpu_memory_utilization"] < 1
job = os.environ.get("SLURM_JOB_ID", str(os.getpid()))
suffix = "_system2" if "system2" in config else ("" if config["gpus"] == 2 else "_single_gpu")
out = root / "exp/inference/duplexomni" / (f"native_loop_{job}" if "native_loop" in config else f"audio_turn{suffix}_{job}")
out.mkdir(parents=True, exist_ok=True)
devices = os.environ["CUDA_VISIBLE_DEVICES"].split(",")
assert len(devices) == config["gpus"], devices
model = str(root / "models/duplexomni")
source = root / "external/duplexomni/inference_framework/realtime_serving/serving_core"
base = os.environ.copy()
base.update(PYTHONPATH=os.pathsep.join(filter(None, [str(root / "scripts/runtime_shims"), str(source), base.get("PYTHONPATH")])), THINKER_MODEL=model, TALKER_MODEL=model,
            VLLM_ROOT=str(root / "envs/duplexomni/lib/python3.11/site-packages"),
            THINKER_HOST="127.0.0.1", TALKER_HOST="127.0.0.1",
            THINKER_PORT="21991", TALKER_PORT="21992", THINKER_TP=str(thinker_tp),
            THINKER_MAX_MODEL_LEN=str(config["max_model_len"]),
            THINKER_GPU_MEM_UTIL=str(config["thinker_gpu_memory_utilization"]),
            DUPLEX_SMOKE_AUDIO_LIMIT=str(config.get("audio_limit", 1)),
            THINKER_HIDDEN_STORE_DIR="0", TALKER_TP="1",
            TALKER_GPU_MEM_UTIL=str(config["talker_gpu_memory_utilization"]),
            DUPLEX_SMOKE_MAX_MODEL_LEN=str(config["max_model_len"]),
            TALKER_MTP_SPLIT_ENGINE="0", TALKER_MTP_CUDAGRAPH_MODE="NONE",
            TALKER_MTP_PROFILE="0", TALKER_MTP_VERBOSE_LOG="0")
if "max_num_batched_tokens" in config:
    base["DUPLEX_SMOKE_MAX_BATCHED_TOKENS"] = str(config["max_num_batched_tokens"])
for component in ("thinker", "talker"):
    if f"{component}_kv_cache_memory_bytes" in config:
        base[f"DUPLEX_SMOKE_{component.upper()}_KV_CACHE_BYTES"] = str(config[f"{component}_kv_cache_memory_bytes"])
if "native_loop" in config:
    base["DUPLEX_DECODER_ABLATION_DIR"] = str(out / "decoder_ablation")
if config.get("streaming_decoder"):
    base["DUPLEX_STREAM_DECODER"] = config["streaming_decoder"]
    base["DUPLEX_DECODER_CONTEXT_FRAMES"] = str(config.get("decoder_context_frames", 25))
if config.get("thinker_cuda_graphs"):
    base["DUPLEX_THINKER_CUDA_GRAPHS"] = "1"
processes = []
handles = []
summary = {"model": "MuyeHuang/DuplexOmni", "job_id": job, "gpus": config["gpus"],
           "config": config,
           "cuda_visible_devices": devices,
           "revision": "b8a5ff6395ae51460d0402424fbd3359614a901a",
           "layout": f"Thinker TP{thinker_tp} on GPU(s) {list(range(thinker_tp))}; Talker TP1/MTP/Code2Wav on GPU {speech_gpu}",
           "mode": "audio_conditioned_turn_with_local_system2" if "system2" in config else "audio_conditioned_turn"}
if config["gpus"] == 1:
    summary["layout"] += "; Thinker and the full speech pipeline share allocation GPU 0"
if "system2" in config:
    summary["layout"] += f"; System-2 TP1 on GPU {s2_gpu}" + (" shared with Talker" if s2_gpu == speech_gpu else " dedicated")
if os.environ.get("DUPLEX_BASELINE_JOB_ID"):
    summary["prerequisite_job_id"] = os.environ["DUPLEX_BASELINE_JOB_ID"]
summary["gpu_runtime"] = {
    "mps_enabled": bool(os.environ.get("CUDA_MPS_PIPE_DIRECTORY")),
    "uuid_mapping_enabled": os.environ.get("DUPLEX_GPU_UUID_MAPPING") == "1",
    "visible_devices": devices,
}
start = time.monotonic()
trace = Trajectory(out, origin=start)

def wait_healthy(servers, deadline):
    pending = list(servers)
    while pending:
        if time.monotonic() > deadline:
            raise TimeoutError("serving startup exceeded one hour")
        for item in list(pending):
            component, proc, port = item
            if proc.poll() is not None:
                raise RuntimeError(f"{component} exited {proc.returncode}; see {component}.log")
            try:
                response = requests.get(f"http://127.0.0.1:{port}/health", timeout=2)
                if response.ok:
                    pending.remove(item)
                    trace.end("startup", f"startup-{component}", f"{component} ready")
                    print(f"{component} healthy after {time.monotonic()-start:.1f}s", flush=True)
            except requests.RequestException:
                pass
        if pending:
            time.sleep(5)

try:
    monitor_handle = (out / "gpu_monitor.log").open("w")
    handles.append(monitor_handle)
    monitor = subprocess.Popen([str(root / "envs/duplexomni/bin/python"),
        str(root / "scripts/monitor_gpu.py"), ",".join(devices), str(out / "gpu.csv")],
        stdout=monitor_handle, stderr=subprocess.STDOUT, start_new_session=True)
    processes.append(monitor)
    servers = []
    deadline = time.monotonic() + 3600
    talker_devices = devices[speech_gpu:speech_gpu+1]
    for component, gpu_ids, port in (("thinker", devices[:thinker_tp], 21991), ("talker", talker_devices, 21992)):
        env = base | {"CUDA_VISIBLE_DEVICES": ",".join(gpu_ids)}
        if component == "talker":
            env['DUPLEX_SMOKE_MAX_MODEL_LEN'] = str(config.get('talker_max_model_len', config['max_model_len']))
        handle = (out / f"{component}.log").open("w")
        handles.append(handle)
        trace.begin("startup", f"startup-{component}", f"Load {component}", {"allocation_gpu": list(range(thinker_tp)) if component == "thinker" else speech_gpu})
        proc = subprocess.Popen([str(root / "envs/duplexomni/bin/python"), "-u",
                                 str(root / "scripts/duplex_server_smoke.py"), component],
                                cwd=root, env=env, stdout=handle, stderr=subprocess.STDOUT, start_new_session=True)
        processes.append(proc)
        servers.append((component, proc, port))
        if config["sequential_startup"]:
            wait_healthy(servers[-1:], deadline)
    if not config["sequential_startup"]:
        wait_healthy(servers, deadline)
    if "system2" in config:
        s2 = config["system2"]
        model_s2 = root / s2["model"]
        assert (model_s2 / "model.safetensors.index.json").is_file(), model_s2
        env = base | {"CUDA_VISIBLE_DEVICES": devices[s2_gpu]}
        handle = (out / "system2.log").open("w")
        handles.append(handle)
        command = [str(root / "envs/duplexomni/bin/vllm"), "serve", str(model_s2),
                   "--served-model-name", s2["served_model_name"], "--host", "127.0.0.1",
                   "--port", str(s2["port"]), "--dtype", "bfloat16", "--tensor-parallel-size", "1",
                   "--gpu-memory-utilization", str(s2["gpu_memory_utilization"]),
                   "--max-model-len", str(s2["max_model_len"]), "--max-num-seqs", "1",
                   "--max-num-batched-tokens", str(s2["max_num_batched_tokens"])]
        if not s2.get("cuda_graphs", False):
            command += ["--enforce-eager"]
        if s2.get('reasoning_parser'):
            command += ['--reasoning-parser', s2['reasoning_parser']]
        if "kv_cache_memory_bytes" in s2:
            command += ["--kv-cache-memory-bytes", str(s2["kv_cache_memory_bytes"])]
        (out / "system2_command.json").write_text(json.dumps(command, indent=2) + "\n")
        trace.begin("startup", "startup-system2", "Load System-2", {"allocation_gpu": s2_gpu, "model": s2["repo"]})
        proc = subprocess.Popen(command, cwd=root, env=env, stdout=handle,
                                stderr=subprocess.STDOUT, start_new_session=True)
        processes.append(proc)
        servers.append(("system2", proc, s2["port"]))
        wait_healthy(servers[-1:], deadline)
    summary["startup_seconds"] = time.monotonic() - start
    if "author_reference" in config:
        from run_s1_author_reference import run_s1_author_reference
        summary["mode"] = "authors_s1_only_simulation"
        summary["native_cases"] = run_s1_author_reference(root, out, config, trace)
        summary["status"] = "completed_content_review_required"
    elif "native_loop" in config:
        from native_interaction import run_native_interaction
        summary["mode"] = "native_audio_control_replay"
        summary["native_cases"] = run_native_interaction(root, out, config, trace)
        summary["status"] = "completed_content_review_required"
        if (out / "runtime_qualification.json").exists():
            summary["runtime_qualification"] = json.loads((out / "runtime_qualification.json").read_text())
            if not summary["runtime_qualification"]["qualified"]:
                summary["status"] = "blocked_infrastructure_qualification"
        if (out / "initial_response_gate.json").exists():
            summary["initial_response_gate"] = json.loads((out / "initial_response_gate.json").read_text())
            if not summary["initial_response_gate"]["qualified"]:
                summary["status"] = "blocked_initial_s1_response"
    else:
        audio_path = root / "data/benchmarks/functional_smoke/dailytalk_user_10s.wav"
        payload = {"model": model, "session_id": f"smoke_{job}", "max_tokens": config.get("initial_max_tokens", 32), "temperature": 0,
                   "messages": [{"role": "system", "content": "You are a helpful assistant. Respond briefly to the audio."},
                                {"role": "user", "content": [{"type": "input_audio", "input_audio": {
                                    "data": base64.b64encode(audio_path.read_bytes()).decode(), "format": "wav"}}]}]}
        if "system2" in config:
            payload["messages"][0]["content"] = (
                "You are a helpful voice assistant. Return the usual JSON object with asr, tts, "
                "tts_control and system2_control. Transcribe the user audio into asr and reply briefly "
                "in English in tts. Use [THINK] in system2_control if background assistance is needed."
            )
            parts = payload["messages"][1]["content"]
            payload["messages"][1]["content"] = [
                {"type": "text", "text": "{'audio_input': '"}, *parts,
                {"type": "text", "text": "', 'from_s2': ''}"},
            ]
        t = time.monotonic()
        trace.media("user", audio_path, "User recording submitted (whole file)", role="input", duration=10)
        trace.begin("thinker", "thinker-initial", "S1 audio-conditioned turn", {"input_media": "user"})
        response = requests.post("http://127.0.0.1:21991/internal/chat_turn", json=payload, timeout=600)
        response.raise_for_status()
        internal = torch.load(io.BytesIO(response.content), map_location="cpu", weights_only=False)
        summary["thinker_seconds"] = time.monotonic() - t
        summary["response"] = internal["response"]
        trace.end("thinker", "thinker-initial", "S1 response received", {"response": internal["response"]})
        if "system2" in config:
            if "continuous_system2" in config:
                from system2_continuous import run_continuous_system2 as run_system2
                summary["mode"] = "continuous_s1_s2_audio"
            else:
                from system2_smoke import run_system2_smoke as run_system2
                summary["mode"] = "audio_conditioned_turn_with_local_system2"
            summary["system2"] = run_system2(root, out, config, payload, response.content, trace=trace)
            summary.update(status=summary["system2"]["status"], output_seconds=summary["system2"]["final_audio"]["seconds"],
                           sample_rate=summary["system2"]["final_audio"]["sample_rate"], input_seconds=10)
        else:
            t = time.monotonic()
            trace.begin("talker", "talker-initial", "Talker / codec synthesis", {"allocation_gpu": 1 if config["gpus"] == 2 else 0})
            speech = requests.post(f"http://127.0.0.1:21992/internal/talker/turn/smoke_{job}", data=response.content,
                                   headers={"content-type": "application/octet-stream"}, timeout=600)
            speech.raise_for_status()
            summary["talker_seconds"] = time.monotonic() - t
            if not speech.content:
                raise RuntimeError("Talker returned empty audio")
            (out / "response.wav").write_bytes(speech.content)
            audio, sr = sf.read(out / "response.wav")
            trace.end("talker", "talker-initial", "Waveform received", {"output_seconds": len(audio)/sr})
            trace.media("response", out / "response.wav", "Response available", duration=len(audio)/sr)
            summary.update(status="pass", output_seconds=len(audio)/sr, sample_rate=sr, input_seconds=10)

except Exception as exc:
    summary.update(status="failed", error=f"{type(exc).__name__}: {exc}")
    trace.mark("control", "error", "Run failed", {"error": summary["error"]})
    raise
finally:
    summary["wall_seconds"] = time.monotonic() - start
    if (out / "gpu.csv").exists():
        peaks = {}
        with (out / "gpu.csv").open() as handle:
            for row in csv.DictReader(handle, skipinitialspace=True):
                try:
                    key = next(k for k in row if k.startswith("memory.used"))
                    uid, mem = row["uuid"], float(row[key])
                    peaks[uid] = max(peaks.get(uid, 0), mem)
                except (StopIteration, KeyError, TypeError, ValueError):
                    continue
        summary["sampled_peak_memory_mib_by_uuid"] = peaks
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    trace.mark("control", "run_end", "Run finished", {"status": summary.get("status", "unknown")})
    trace.close()
    display = {k: v for k, v in summary.items() if k != "native_cases"}
    if "native_cases" in summary:
        display["native_cases"] = [{"name": c["name"], "status": c.get("status"),
                                    "turns": len(c["turns"]), "wall_seconds": c["wall_seconds"]}
                                   for c in summary["native_cases"]]
    print(json.dumps(display), flush=True)
    for proc in reversed(processes):
        if proc.poll() is None:
            try:
                os.killpg(proc.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
    # Let CUDA clients exit before the outer wrapper stops this job's MPS.
    for proc in reversed(processes):
        try:
            proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            proc.wait(timeout=10)
    for handle in handles:
        handle.close()
    try:
        export_trace(out)
    except Exception as exc:
        print(f"Trajectory export failed; events.jsonl retained: {type(exc).__name__}: {exc}", flush=True)
