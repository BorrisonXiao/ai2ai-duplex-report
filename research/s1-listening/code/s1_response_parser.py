"""Parse S1 fields, with audited recovery of mismatched known-key quotes.

The repair grammar is deliberately flat: four known keys and four valid string
values. Only the delimiter around a key may be mismatched. Speech/control values
are parsed without alteration; incomplete values, extra fields and duplicate
keys cannot enter through the repair path. No eval or arbitrary text repair.
"""
import ast
import json

FIELDS = ('asr', 'tts', 'tts_control', 'system2_control')


def _validate(result):
    if not isinstance(result, dict) or not any(key in result for key in FIELDS):
        raise ValueError('S1 response is not a field object')
    for key in FIELDS:
        if key in result and not isinstance(result[key], str):
            raise ValueError(f'S1 {key} must be a string')
    return result


def _repair_key_quotes(text):
    i, result, repaired = 1, {}, []
    def whitespace(position):
        while position < len(text) and text[position].isspace():position += 1
        return position
    while True:
        i = whitespace(i)
        if i >= len(text) or text[i] not in "\"'":
            raise ValueError('Expected quoted S1 field name')
        opening = text[i];i += 1;start = i
        while i < len(text) and text[i] not in "\"'":i += 1
        if i >= len(text):raise ValueError('Incomplete S1 field name')
        key, closing = text[start:i], text[i];i = whitespace(i+1)
        if key not in FIELDS or key in result or i >= len(text) or text[i] != ':':
            raise ValueError('Unknown, duplicate or malformed S1 field')
        if opening != closing:repaired.append(key)
        i = whitespace(i+1)
        if i >= len(text) or text[i] not in "\"'":raise ValueError('Expected complete string value')
        quote, start = text[i], i;i += 1
        while i < len(text):
            if text[i] == '\\':i += 2;continue
            if text[i] == quote:break
            i += 1
        if i >= len(text):raise ValueError('Incomplete S1 string value')
        token = text[start:i+1]
        try:value = json.loads(token) if quote == '"' else ast.literal_eval(token)
        except (ValueError, SyntaxError):raise ValueError('Invalid S1 string value') from None
        if not isinstance(value,str):raise ValueError('Non-string S1 value')
        result[key] = value;i = whitespace(i+1)
        if i < len(text) and text[i] == '}':
            if whitespace(i+1) != len(text):raise ValueError('Trailing S1 object content')
            break
        if i >= len(text) or text[i] != ',':raise ValueError('Expected S1 field separator')
        i += 1
    if set(result) != set(FIELDS) or not repaired:
        raise ValueError('Key-quote repair requires all four known string fields')
    return result,repaired


def parse_s1_with_audit(text):
    clean = text.replace('```json','').replace('```','').strip()
    first,last = clean.find('{'),clean.rfind('}')
    if first < 0 or last < first:raise ValueError('S1 did not return a structured response')
    clean = clean[first:last+1]
    try:
        result = json.loads(clean)
        return _validate(result),{'method':'json','repaired_keys':[]}
    except json.JSONDecodeError:
        pass
    try:
        result = ast.literal_eval(clean)
        return _validate(result),{'method':'python_literal','repaired_keys':[]}
    except (ValueError,SyntaxError):
        pass
    try:
        result,repaired = _repair_key_quotes(clean)
    except ValueError as exc:
        raise ValueError(f'Unrecoverable S1 field response: {exc}') from None
    return _validate(result),{'method':'repaired_key_quotes','repaired_keys':repaired}


def parse_s1(text):
    return parse_s1_with_audit(text)[0]
