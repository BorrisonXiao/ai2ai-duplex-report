"""Read complete native ASR/control fields when unused TTS decoding is stopped."""
import re
from s1_listening_rules import PY_STRING
from s1_response_parser import parse_s1_with_audit
PREFIX_REGEX = r"\{'tts_control': " + PY_STRING + r", 'system2_control': " + PY_STRING + r", 'asr': " + PY_STRING
ASR_FIRST_PREFIX_REGEX = r"\{'asr': " + PY_STRING
STOP_BEFORE_TTS = ", 'tts': "
def fields_from_prefix(raw):
    clean=raw.strip()
    if re.fullmatch(ASR_FIRST_PREFIX_REGEX,clean):
        completed=clean+", 'tts': '', 'tts_control': '', 'system2_control': ''}"
    elif re.fullmatch(PREFIX_REGEX,clean):
        completed=clean+", 'tts': ''}"
    else:
        raise ValueError('The complete ASR/control prefix was not returned; do not invent ASR')
    fields,audit=parse_s1_with_audit(completed)
    audit.update(method='complete_asr_prefix_unused_tts_skipped',tts_value_generated=False)
    return fields,audit
