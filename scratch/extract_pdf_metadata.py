import os
import re
import json
import sys
from pathlib import Path
# pyrefly: ignore[missing-import]
from pypdf import PdfReader

# Set UTF-8 output
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

pdf_dir = Path("Research-Paper")
pdf_files = sorted(list(pdf_dir.glob("*.pdf")))

results = []

for pdf_path in pdf_files:
    try:
        reader = PdfReader(str(pdf_path))
        text = ""
        for i in range(min(3, len(reader.pages))):
            text += (reader.pages[i].extract_text() or "") + "\n"
        
        # Clean text
        clean_text = " ".join(text.split())

        # Extract DOI
        doi_match = re.search(r'(10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)', text)
        doi = doi_match.group(1).rstrip('.,)') if doi_match else None
        if not doi:
            doi_match = re.search(r'doi[\s.:/]+(10\.\S+)', text, re.I)
            doi = doi_match.group(1).rstrip('.,)') if doi_match else "N/A"

        # Search for publication year/date
        date_patterns = [
            r'Received.*?(?:Published|Available online|Accepted)\s*:?\s*(\d{1,2}\s+[A-Za-z]+\s+\d{4}|\d{4})',
            r'(?:Published|Available online|Accepted|Publication Date)\s*:?\s*(\d{1,2}\s+[A-Za-z]+\s+\d{4}|\d{4})',
            r'(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})',
            r'\b(20[12]\d)\b'
        ]
        found_date = None
        for dp in date_patterns:
            m = re.search(dp, text, re.I)
            if m:
                found_date = m.group(1).strip()
                break

        results.append({
            "filename": pdf_path.name,
            "doi": doi,
            "detected_date": found_date,
            "intro_snippet": text[:1500]
        })
    except Exception as e:
        results.append({
            "filename": pdf_path.name,
            "error": str(e)
        })

out_json = Path("scratch/pdf_papers_metadata.json")
with open(out_json, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"Extracted metadata saved to {out_json} for {len(results)} PDFs.")
