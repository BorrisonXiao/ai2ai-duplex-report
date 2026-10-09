"""Repair skipped-vision buffers and audio-only budgeting in the pinned Thinker.

vLLM builds disabled vision components on the meta device. The fork also makes
a Python list of vision DeepStack buffers inside that meta-device context;
those survive even though the tower is disabled. Audio-only warmup then adds
these meta tensors to real language hidden states. Remove only that unused list
when both image/video limits are zero. Model weights and audio paths are intact.
"""
from functools import wraps


def disable_skipped_visual_buffers(model):
    mm = model.multimodal_config
    if mm.get_limit_per_prompt("image") != 0 or mm.get_limit_per_prompt("video") != 0:
        return False
    model.deepstack_input_embeds = []
    model.use_deepstack = False
    model.deepstack_num_level = 0
    model.multiscale_dim = 0
    model.duplex_audio_only_buffers_disabled = True
    return True


def patch_thinker(module):
    info = getattr(module, "Qwen3OmniMoeThinkerProcessingInfo", None)
    if info is not None and not getattr(info, "duplex_audio_budget_patch", False):
        original_budget = info.get_mm_max_tokens_per_item

        @wraps(original_budget)
        def audio_budget(self, seq_len, mm_counts):
            if mm_counts.get("audio", 0) and not mm_counts.get("image", 0) and not mm_counts.get("video", 0):
                # The inherited VL estimator lists image/video only. Returning
                # None asks vLLM to measure the real dummy audio placeholders.
                return None
            return original_budget(self, seq_len, mm_counts)

        info.get_mm_max_tokens_per_item = audio_budget
        info.duplex_audio_budget_patch = True
    cls = module.Qwen3OmniMoeThinkerForConditionalGeneration
    if getattr(cls, "duplex_audio_only_init_patch", False):
        return
    original = cls.__init__

    @wraps(original)
    def initialize(self, *args, **kwargs):
        original(self, *args, **kwargs)
        disable_skipped_visual_buffers(self)

    cls.__init__ = initialize
    cls.duplex_audio_only_init_patch = True
