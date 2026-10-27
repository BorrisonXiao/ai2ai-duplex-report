"""Use the project term in prose while preserving recorded prompts and outputs."""
import re


def prethinking_prose(source):
    def replace(text):
        # These phrases describe data processing, rather than private reasoning.
        text = text.replace('CPU preparation', 'CPU data work').replace('Prompt preparation', 'Prompt tokenization').replace('that preparation time', 'that tokenization time')
        text = re.sub(r'\bpreparation\b', lambda m: 'Pre-thinking' if m[0][0].isupper() else 'pre-thinking', text, flags=re.I)
        return text
    pieces = []
    cursor = 0
    for match in re.finditer(r'<(?P<tag>script|style|pre|code|blockquote)\b[^>]*>.*?</(?P=tag)>|“[^”]*”', source, flags=re.S | re.I):
        pieces.extend([replace(source[cursor:match.start()]), match[0]])
        cursor = match.end()
    pieces.append(replace(source[cursor:]))
    return ''.join(pieces)
