import json

with open("scratch/full_papers_catalog.json", "r", encoding="utf-8") as f:
    catalog = json.load(f)

with open("scratch/pdf_summary.txt", "w", encoding="utf-8") as out:
    out.write("="*80 + "\n")
    out.write("EXCEL PAPERS (8 total):\n")
    for i, p in enumerate(catalog["excel_papers"]):
        out.write(f"[{i+1}] Title: {p['title']}\n")
        out.write(f"    DOI:   {p['doi']}\n")
        out.write(f"    Date:  {p['date']}\n\n")

    out.write("="*80 + "\n")
    out.write(f"PDF PAPERS ({len(catalog['pdf_papers'])} total):\n")
    for i, p in enumerate(catalog["pdf_papers"]):
        out.write(f"\n--- PDF {i+1}: {p['filename']} ---\n")
        out.write(f"DOI: {p['doi']}\n")
        for line in p["lines"][:20]:
            out.write(f"  | {line}\n")

print("Wrote scratch/pdf_summary.txt successfully!")
