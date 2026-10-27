import re

with open('report/AeroCast_AI_Report.tex', 'r', encoding='utf-8') as f:
    text = f.read()

bib_pattern = r'\\bibitem\{([^}]+)\}\s*(.*?)(?=\\bibitem|\s*\\end\{thebibliography\})'
matches = list(re.finditer(bib_pattern, text, re.DOTALL))

print(f"Total bibitems found: {len(matches)}")

papers = []
for m in matches:
    key = m.group(1).strip()
    content = m.group(2).strip()
    
    # Year
    years = re.findall(r'\b(20[12]\d)\b', content)
    year = int(years[-1]) if years else 0
    
    # Title
    t_match = re.search(r'`+(.*?)\'+', content)
    title = t_match.group(1).strip() if t_match else "Unknown"
    
    # Author
    author_part = content.split('`')[0].strip().rstrip(',')
    
    papers.append({
        'key': key,
        'year': year,
        'title': title,
        'authors': author_part,
        'raw': content
    })

# Sort by year descending. If years match, sort alphabetically by key or author
papers.sort(key=lambda x: (-x['year'], x['authors']))

for i, p in enumerate(papers, 1):
    print(f"{i:2d}. [{p['year']}] {p['key']}: {p['authors'][:30]} | {p['title'][:50]}")
