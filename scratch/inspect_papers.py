import os
import glob
import pandas as pd
from pathlib import Path

# 1. Print Excel entries
excel_path = Path("Research-Paper/Research-Paper.xlsx")
if excel_path.exists():
    df = pd.read_excel(excel_path)
    print(f"=== Research-Paper.xlsx ({len(df)} entries) ===")
    for i, row in df.iterrows():
        print(f"[{i+1}] Title: {row.get('Research Paper Name')}")
        print(f"    DOI:   {row.get('DOI')}")
        print(f"    Date:  {row.get('Date')}")
        print(f"    Link:  {row.get('Link')}")
        print()

# 2. List all PDF files in Research-Paper
pdf_files = list(Path("Research-Paper").glob("*.pdf"))
print(f"\n=== Found {len(pdf_files)} PDF Files in Research-Paper ===")
for p in pdf_files:
    print(f" - {p.name} ({round(p.stat().st_size / (1024*1024), 2)} MB)")
