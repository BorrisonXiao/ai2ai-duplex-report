"""Bound the official serving stack to short audio-only feasibility requests."""
import dataclasses
import os
import sys

import uvicorn

component = sys.argv[1]
max_model_len = int(os.environ.get("DUPLEX_SMOKE_MAX_MODEL_LEN", "4096"))
engine_overrides = {"enforce_eager": True, "max_num_seqs": 1}
if component == "thinker" and os.environ.get("DUPLEX_THINKER_CUDA_GRAPHS") == "1":
    engine_overrides["enforce_eager"] = False
if component == "thinker" and int(os.environ.get("THINKER_TP", "1")) > 1:
    # vLLM 0.16 custom all-reduce parses CVD as integers. NCCL supports the
    # allocation-scoped UUID selection used by our GPU runtime wrapper.
    engine_overrides["disable_custom_all_reduce"] = True
cache_key = f"DUPLEX_SMOKE_{component.upper()}_KV_CACHE_BYTES"
if cache_key in os.environ:
    cache_bytes = int(os.environ[cache_key])
    if cache_bytes <= 0:
        raise ValueError("KV cache byte limit must be positive")
    engine_overrides["kv_cache_memory_bytes"] = cache_bytes
if "DUPLEX_SMOKE_MAX_BATCHED_TOKENS" in os.environ:
    engine_overrides["max_num_batched_tokens"] = int(os.environ["DUPLEX_SMOKE_MAX_BATCHED_TOKENS"])
if component == "thinker":
    import server_thinker as server
    audio_limit = int(os.environ.get("DUPLEX_SMOKE_AUDIO_LIMIT", "1"))
    if audio_limit <= 0:
        raise ValueError("Audio input limit must be positive")
    server.CONFIG = dataclasses.replace(server.CONFIG, limit_mm_per_prompt={"audio": audio_limit, "image": 0, "video": 0})
    original_args = server.AsyncEngineArgs
    def smoke_args(*args, **kwargs):
        kwargs.update(engine_overrides)
        return original_args(*args, **kwargs)
    server.AsyncEngineArgs = smoke_args
    port = server.CONFIG.port
else:
    import server_talker as server
    original_llm = server.LLM
    def smoke_llm(*args, **kwargs):
        kwargs.update(engine_overrides, max_model_len=max_model_len)
        return original_llm(*args, **kwargs)
    server.LLM = smoke_llm
    original_config = server._server_config_from_env
    server._server_config_from_env = lambda: dataclasses.replace(original_config(), max_model_len=max_model_len)
    port = server._server_config_from_env().port
    if os.environ.get("DUPLEX_STREAM_DECODER") == "bounded_context":
        from streaming_code2wav import install as install_streaming_decoder
        install_streaming_decoder(server, int(os.environ.get("DUPLEX_DECODER_CONTEXT_FRAMES", "25")))
    if os.environ.get("DUPLEX_DECODER_ABLATION_DIR"):
        from decoder_ablation import install
        install(server, os.environ["DUPLEX_DECODER_ABLATION_DIR"])

if __name__ == "__main__":
    uvicorn.run(server.app, host="127.0.0.1", port=port)
