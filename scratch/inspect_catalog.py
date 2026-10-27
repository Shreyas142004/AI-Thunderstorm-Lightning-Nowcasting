import json
import re

with open('scratch/full_papers_catalog.json', encoding='utf-8') as f:
    d = json.load(f)

print("Excel papers:")
for p in d.get('excel_papers', []):
    print(p['date'], "|", p['doi'], "|", p['title'][:70])
