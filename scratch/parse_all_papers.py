import json
import re
from pathlib import Path
# pyrefly: ignore[missing-import]
from pypdf import PdfReader
import pandas as pd

excel_path = Path("Research-Paper/Research-Paper.xlsx")
excel_papers = []
if excel_path.exists():
    df = pd.read_excel(excel_path)
    for _, row in df.iterrows():
        excel_papers.append({
            "title": str(row.get("Research Paper Name", "")).strip(),
            "doi": str(row.get("DOI", "")).strip(),
            "date": str(row.get("Date", "")).split()[0].strip(),
            "link": str(row.get("Link", "")).strip()
        })

print(f"Loaded {len(excel_papers)} papers from Excel.")

# Now parse all 17 PDFs
pdf_files = sorted(list(Path("Research-Paper").glob("*.pdf")))
pdf_details = []

for p in pdf_files:
    reader = PdfReader(str(p))
    t1 = reader.pages[0].extract_text() or ""
    t2 = reader.pages[1].extract_text() if len(reader.pages) > 1 else ""
    full_first_pages = t1 + "\n" + t2

    # Clean lines
    lines = [l.strip() for l in full_first_pages.split("\n") if l.strip()]

    # Extract DOI
    doi_m = re.search(r'(10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)', full_first_pages)
    doi = doi_m.group(1).rstrip('.,)') if doi_m else "N/A"

    pdf_details.append({
        "filename": p.name,
        "doi": doi,
        "lines": lines[:25],
        "full_text": full_first_pages[:2000]
    })

out_data = {
    "excel_papers": excel_papers,
    "pdf_papers": pdf_details
}

with open("scratch/full_papers_catalog.json", "w", encoding="utf-8") as f:
    json.dump(out_data, f, indent=2, ensure_ascii=False)

print("Saved full catalog to scratch/full_papers_catalog.json")
