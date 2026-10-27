"""Use the project term in prose while preserving recorded prompts and outputs."""
import re


def prethinking_prose(source):
    def replace(text):
        text = re.sub(r'\bpre-thinking\b', lambda m: 'Amortized thinking' if m[0][0].isupper() else 'amortized thinking', text, flags=re.I)
        text = re.sub(r'\b([Aa]) (?=[Aa]mortized thinking\b)', lambda m: 'An ' if m[1]=='A' else 'an ', text)
        return text
    pieces = []
    cursor = 0
    for match in re.finditer(r'<(?P<tag>script|style|pre|code|blockquote)\b[^>]*>.*?</(?P=tag)>|“[^”]*”|<[^>]+>', source, flags=re.S | re.I):
        pieces.extend([replace(source[cursor:match.start()]), match[0]])
        cursor = match.end()
    pieces.append(replace(source[cursor:]))
    return ''.join(pieces)
