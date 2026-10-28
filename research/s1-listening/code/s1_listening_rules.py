"""Per-call listening rules; preserve the four native fields and ASR text."""
import json

FIELDS = ('tts_control', 'system2_control', 'asr', 'tts')
PY_STRING = r'''(?:'(?:[^'\\\x00-\x1f]|\\[^\r\n])*'|"(?:[^"\\\x00-\x1f]|\\[^\r\n])*")'''
PY_SPEECH_STRING = r'''(?:'(?:[^'\\\x00-\x1f]|\\[^\r\n])*[A-Za-z0-9](?:[^'\\\x00-\x1f]|\\[^\r\n])*'|"(?:[^"\\\x00-\x1f]|\\[^\r\n])*[A-Za-z0-9](?:[^"\\\x00-\x1f]|\\[^\r\n])*")'''
LISTEN_REGEX = (r"(?:\{'tts_control': '', 'system2_control': '', 'asr': " + PY_STRING + r", 'tts': ''\}|\{'asr': " + PY_STRING + r", 'tts': '', 'tts_control': '', 'system2_control': ''\})")
ANSWER_REGEX = (r"(?:\{'tts_control': " + PY_STRING + r", 'system2_control': '', 'asr': " + PY_STRING + r", 'tts': " + PY_STRING + r"\}|\{'asr': " + PY_STRING + r", 'tts': " + PY_STRING + r", 'tts_control': " + PY_STRING + r", 'system2_control': ''\})")
NATIVE_REGEX = (r"(?:\{'tts_control': " + PY_STRING + r", 'system2_control': " + PY_STRING + r", 'asr': " + PY_STRING + r", 'tts': " + PY_STRING + r"\}|\{'asr': " + PY_STRING + r", 'tts': " + PY_STRING + r", 'tts_control': " + PY_STRING + r", 'system2_control': " + PY_STRING + r"\})")
ANSWER_START_REGEX = (r"(?:\{'tts_control': " + PY_STRING + r", 'system2_control': '', 'asr': " + PY_STRING + r", 'tts': " + PY_SPEECH_STRING + r"\}|\{'asr': " + PY_STRING + r", 'tts': " + PY_SPEECH_STRING + r", 'tts_control': " + PY_STRING + r", 'system2_control': ''\})")

def saved_listening_response(fields):
    """Retain exactly generated ASR, including mistakes, without unexecuted actions."""
    assert all(isinstance(fields[k], str) for k in FIELDS)
    assert set(fields)==set(FIELDS)
    return repr({k: fields[k] if k == 'asr' else '' for k in fields})

def install_sampling_rules(server):
    from vllm.sampling_params import StructuredOutputsParams
    original = server.build_sampling_params
    def sampling(payload):
        params = original(payload)
        mode = payload.get('listening_rule')
        if mode not in (None, 'unconstrained', 'native_format', 'listening', 'answering','answer_start'):
            raise ValueError('Unknown listening rule')
        if mode in ('native_format', 'listening', 'answering','answer_start'):
            params.structured_outputs = StructuredOutputsParams(regex={'native_format':NATIVE_REGEX,'listening':LISTEN_REGEX,'answering':ANSWER_REGEX,'answer_start':ANSWER_START_REGEX}[mode])
        params.seed = int(payload.get('seed', 17))
        return params
    server.build_sampling_params = sampling
