import re

with open('report/AeroCast_AI_Report.tex', 'r', encoding='utf-8') as f:
    text = f.read()

bibitems = re.findall(r'\\bibitem\{([^}]+)\}', text)
years = []
for i, b in enumerate(bibitems, 1):
    # Find block for this bibitem
    start = text.find(f'\\bibitem{{{b}}}')
    next_start = text.find('\\bibitem{', start + 1)
    if next_start == -1:
        next_start = text.find('\\end{thebibliography}', start)
    entry = text[start:next_start]
    
    # Extract year: look for year like 2026, 2025, etc.
    # Usually year is at the end of the entry, or before doi
    y_matches = re.findall(r'\b(19\d\d|20\d\d)\b', entry)
    # The actual publication year is typically the last 4-digit number or explicitly after year/volume
    # Let's see all matches
    year = int(y_matches[-1]) if y_matches else 0
    # Also check doi year if any
    years.append((b, year, y_matches))
    print(f"{i:02d}. {b:30s} -> Extracted Year: {year} (all: {y_matches})")

is_desc = all(years[i][1] >= years[i+1][1] for i in range(len(years)-1))
print("\nIs strictly descending/non-increasing by year?", is_desc)
