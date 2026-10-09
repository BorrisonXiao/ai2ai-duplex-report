"""Enable UUID GPU selection for the pinned vLLM 0.16 runtime.

MPS remaps numeric device ordinals; NVIDIA recommends UUIDs for its server and
clients. vLLM 0.16's Platform mapper assumes integer CUDA_VISIBLE_DEVICES entries.
Patch that mapper and the fork's skipped-vision scratch buffers lazily in jobs
using our GPU runtime wrapper. No vLLM or CUDA modules load at Python startup.
"""
import os

if os.environ.get("DUPLEX_GPU_UUID_MAPPING") == "1":
    import importlib.abc
    from importlib.machinery import PathFinder
    import sys

    class PlatformLoader(importlib.abc.Loader):
        def __init__(self, original):
            self.original = original

        def create_module(self, spec):
            return self.original.create_module(spec)

        def exec_module(self, module):
            self.original.exec_module(module)
            if module.__name__ == "vllm.model_executor.models.qwen3_omni_moe_thinker":
                from audio_only_thinker import patch_thinker
                patch_thinker(module)
                return
            original = module.Platform.device_id_to_physical_device_id.__func__

            def physical_id(cls, device_id):
                visible = os.environ.get(cls.device_control_env_var, "")
                if cls.device_control_env_var == "CUDA_VISIBLE_DEVICES" and visible:
                    entry = visible.split(",")[device_id].strip()
                    if entry.startswith("GPU-"):
                        from vllm.third_party import pynvml
                        pynvml.nvmlInit()
                        try:
                            handle = pynvml.nvmlDeviceGetHandleByUUID(entry)
                            return pynvml.nvmlDeviceGetIndex(handle)
                        finally:
                            pynvml.nvmlShutdown()
                return original(cls, device_id)

            module.Platform.device_id_to_physical_device_id = classmethod(physical_id)
            module.Platform.duplex_uuid_mapping_enabled = True

    class PlatformFinder(importlib.abc.MetaPathFinder):
        def find_spec(self, fullname, path, target=None):
            if fullname not in {"vllm.platforms.interface", "vllm.model_executor.models.qwen3_omni_moe_thinker"}:
                return None
            spec = PathFinder.find_spec(fullname, path)
            if spec is not None and spec.loader is not None:
                spec.loader = PlatformLoader(spec.loader)
            return spec

    sys.meta_path.insert(0, PlatformFinder())
