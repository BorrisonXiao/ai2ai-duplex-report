"""Opt-in bounded Code2Wav context across live six-frame speech calls.

The first call retains the decoder's startup delay. Later calls return the
new frame increment from the end of a bounded context window. They do not
repeat the convolution warmup loss or stretch the audio to hide it.
"""
import os
import torch


def install(server, context_frames=25):
    if context_frames < 1:
        raise ValueError('Streaming decoder requires at least one context frame')
    original_process = server.TalkerEngine.process_chunk
    states = {}

    @torch.inference_mode()
    def decode(self, rvq):
        if rvq.numel() == 0:
            return None
        key = self._streaming_code2wav_session
        current = rvq.to(device=self.device, dtype=torch.long)
        if current.ndim == 2:
            current = current.unsqueeze(0)
        previous = states.get(key)
        window = current if previous is None else torch.cat([previous, current], dim=-1)
        waveform = self.code2wav(window).reshape(-1)
        increment = current.shape[-1] * int(self.code2wav.total_upsample)
        if previous is not None:
            if waveform.numel() < increment:
                raise RuntimeError('Context decoder output is shorter than the new frame increment')
            waveform = waveform[-increment:]
        states[key] = window[..., -context_frames:].detach().clone()
        self._streaming_code2wav_meta = {
            'mode': 'bounded_context', 'new_codec_frames': current.shape[-1],
            'window_codec_frames': window.shape[-1], 'context_limit_frames': context_frames,
            'returned_samples': waveform.numel(), 'nominal_new_samples': increment,
            'startup': previous is None,
        }
        return server.float_audio_to_wav_bytes(waveform.detach().cpu(), self.cfg.sample_rate)

    def process(self, session, *args, cache_salt, **kwargs):
        self._streaming_code2wav_session = cache_salt
        self._streaming_code2wav_meta = None
        wave, meta = original_process(self, session, *args, cache_salt=cache_salt, **kwargs)
        if self._streaming_code2wav_meta:
            meta['streaming_decoder'] = self._streaming_code2wav_meta
        return wave, meta

    server.TalkerEngine.decode_wav = decode
    server.TalkerEngine.process_chunk = process
