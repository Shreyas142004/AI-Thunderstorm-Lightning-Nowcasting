import json
import re

with open('scratch/full_papers_catalog.json', encoding='utf-8') as f:
    d = json.load(f)

# Also load existing bibitems from AeroCast_AI_Report.tex
with open('report/AeroCast_AI_Report.tex', encoding='utf-8') as f:
    tex = f.read()

bib_pattern = r'\\bibitem\{([^}]+)\}\s*(.*?)(?=\\bibitem|\s*\\end\{thebibliography\})'
matches = list(re.finditer(bib_pattern, tex, re.DOTALL))

bib_dict = {}
for m in matches:
    key = m.group(1).strip()
    raw = m.group(2).strip()
    bib_dict[key] = raw

print(f"Loaded {len(bib_dict)} bibitems.")

# Let's map each bibitem to its year, title, authors, journal, doi
paper_records = []
for key, raw in bib_dict.items():
    # Extract year: search for , 20XX, or . 20XX, or 20XX.
    # Note: in bibitems, year is usually at the end before doi or after pp.
    # e.g., vol. 109, art. no. 101566, 2025, doi:
    # e.g., pp. 620--628, 2022, doi:
    y_match = re.search(r'(20\d\d)', key)
    year = int(y_match.group(1)) if y_match else 2020

    t_match = re.search(r'`+(.*?)\'+', raw)
    title = t_match.group(1).strip() if t_match else "Unknown"

    author_part = raw.split('`')[0].strip().rstrip(',')

    doi_m = re.search(r'doi:\s*([^\s,]+)', raw)
    doi = doi_m.group(1).rstrip('.') if doi_m else ""

    journal_m = re.search(r'\\emph\{([^}]+)\}', raw)
    journal = journal_m.group(1).strip() if journal_m else ""

    paper_records.append({
        'key': key,
        'year': year,
        'title': title,
        'authors': author_part,
        'journal': journal,
        'doi': doi,
        'raw': raw
    })

# Sort by year descending. If years are equal, sort alphabetically by title or author
paper_records.sort(key=lambda x: (-x['year'], x['title']))

print("\n--- ALL 25 PAPERS SORTED BY YEAR (LATEST FIRST) ---")
for i, p in enumerate(paper_records, 1):
    print(f"[{i:2d}] Year {p['year']} | Key: {p['key']}")
    print(f"     Title: {p['title']}")
    print(f"     Authors: {p['authors']}")
