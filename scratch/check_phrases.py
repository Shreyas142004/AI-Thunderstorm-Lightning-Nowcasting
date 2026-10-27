import re

with open('report/AeroCast_AI_Report.tex', 'r', encoding='utf-8') as f:
    text = f.read()

patterns = [
    r'\bthis\s+chapter\b',
    r'\bthis\s+project\b',
    r'\bthis\s+report\b',
    r'\bin\s+this\s+chapter\b',
    r'\bin\s+this\s+project\b',
    r'\bof\s+this\s+project\b'
]

for p in patterns:
    matches = list(re.finditer(p, text, re.I))
    print(f'Pattern "{p}": {len(matches)} matches')
    for m in matches:
        start = max(0, m.start() - 30)
        end = min(len(text), m.end() + 30)
        print('  ...', text[start:end].replace('\n', ' '), '...')
