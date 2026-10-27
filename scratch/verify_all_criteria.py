import re

def verify_report():
    with open('report/AeroCast_AI_Report.tex', 'r', encoding='utf-8') as f:
        text = f.read()

    print("=== COMPREHENSIVE REPORT AUDIT FOR ALL 7 SUGGESTIONS ===\n")
    
    # -------------------------------------------------------------
    # Suggestion 1: Abstract title is missing; no project title in paragraphs; avoid starting paragraphs with project title.
    # -------------------------------------------------------------
    print("[1] Abstract Title & Project Title in Paragraphs:")
    abstract_match = re.search(r'\\begin\{center\}(.*?)\\textbf\{ABSTRACT\}(.*?)\\end\{center\}', text, re.DOTALL)
    if abstract_match:
        print("  - Abstract header block found:")
        for line in abstract_match.group(0).strip().split('\n'):
            print(f"    {line.strip()}")
    else:
        print("  - [WARNING] Abstract block not found!")

    # Check paragraph starts
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
    p_starting_with_project_title = []
    p_starting_with_fig_tab = []
    aerocast_in_paragraphs = []

    for idx, p in enumerate(paragraphs):
        lines = [l.strip() for l in p.split('\n') if l.strip() and not l.strip().startswith('%')]
        if not lines:
            continue
        first_line = lines[0]
        # Ignore commands and environments
        if first_line.startswith('\\chapter') or first_line.startswith('\\section') or first_line.startswith('\\subsection') or first_line.startswith('\\begin') or first_line.startswith('\\end') or first_line.startswith('\\titleformat') or first_line.startswith('\\usepackage') or first_line.startswith('\\fancy') or first_line.startswith('\\renewcommand') or first_line.startswith('\\newcommand') or first_line.startswith('\\titlespacing') or first_line.startswith('\\captionsetup') or first_line.startswith('\\setlength') or first_line.startswith('\\newcolumntype') or first_line.startswith('\\pagestyle') or first_line.startswith('\\fancypagestyle') or first_line.startswith('\\documentclass') or first_line.startswith('\\newpage') or first_line.startswith('\\pagenumbering') or first_line.startswith('\\setcounter') or first_line.startswith('\\vspace'):
            continue
        
        # Check starting with project title
        if re.match(r'^(AeroCast|The AeroCast|AI-Driven)', first_line, re.IGNORECASE):
            p_starting_with_project_title.append((idx, first_line[:80]))
            
        # Check starting with Figure / Table (Suggestion 7)
        if re.match(r'^(Figure|Fig\.|Table|Tab\.|As shown in|As illustrated in|In Figure|In Table)', first_line, re.IGNORECASE):
            p_starting_with_fig_tab.append((idx, first_line[:80]))
            
        # Check if "AeroCast" is mentioned inside standard text paragraphs
        if 'aerocast' in p.lower() and not p.startswith('\\bibitem') and not p.startswith('\\fancy') and not p.startswith('\\begin{center}'):
            # Ignore table rows or captions
            if '\\caption' not in p and '\\begin{xltabular}' not in p and '\\begin{tabularx}' not in p:
                aerocast_in_paragraphs.append((idx, first_line[:80]))

    print(f"  - Paragraphs starting with project title: {len(p_starting_with_project_title)} -> {p_starting_with_project_title}")
    print(f"  - Paragraphs mentioning AeroCast in body text: {len(aerocast_in_paragraphs)} -> {aerocast_in_paragraphs}")

    # -------------------------------------------------------------
    # Suggestion 2: Literature review numerical order 1 to 25, latest papers first.
    # -------------------------------------------------------------
    print("\n[2] Literature Review Organization (1 to 25, latest first):")
    # Find all \cite{...} in Section 2.1
    sec2_match = re.search(r'\\section\{Existing Studies\}(.*?)\\section\{Comparative Summary\}', text, re.DOTALL)
    if sec2_match:
        sec2_text = sec2_match.group(1)
        cites_in_sec2 = re.findall(r'\\cite\{([^}]+)\}', sec2_text)
        print(f"  - Total citations in Section 2.1: {len(cites_in_sec2)}")
        
        # Check order against bibitems
        bibitems = re.findall(r'\\bibitem\{([^}]+)\}', text)
        print(f"  - Total bibitems: {len(bibitems)}")
        
        is_exact_match = (cites_in_sec2 == bibitems)
        print(f"  - Are Section 2.1 citations in exact 1:1 numerical order with bibitems? {is_exact_match}")
        
        # Extract years of bibitems
        bib_years = []
        for b in bibitems:
            m = re.search(r'\\bibitem\{' + b + r'\}.*?(\b20\d\d\b)', text, re.DOTALL)
            if m:
                bib_years.append(int(m.group(1)))
        print(f"  - Years of papers (first 6): {bib_years[:6]}")
        print(f"  - Years of papers (last 6): {bib_years[-6:]}")
        is_sorted_desc = all(bib_years[i] >= bib_years[i+1] for i in range(len(bib_years)-1))
        print(f"  - Are papers sorted in descending chronological order (latest first)? {is_sorted_desc}")
    else:
        print("  - [WARNING] Section 2.1 not found!")

    # -------------------------------------------------------------
    # Suggestion 3: Comparative table has paper titles and same order 1 to 25.
    # -------------------------------------------------------------
    print("\n[3] Comparative Table Titles and Ordering:")
    tbl_match = re.search(r'\\begin\{xltabular\}\{\\textwidth\}\{\|L\{4\.2cm\}\|C\{1\.1cm\}\|L\{4\.2cm\}\|Y\|\}(.*?)\\end\{xltabular\}', text, re.DOTALL)
    if tbl_match:
        tbl_text = tbl_match.group(1)
        rows = [r.strip() for r in tbl_text.split(r'\hline') if r.strip() and not r.strip().startswith('\\caption') and not r.strip().startswith('\\hdrrow') and not r.strip().startswith('\\endfirsthead') and not r.strip().startswith('\\endhead') and not r.strip().startswith('\\endfoot') and not r.strip().startswith('\\endlastfoot')]
        print(f"  - Total data rows in comparative table: {len(rows)}")
        tbl_cites = re.findall(r'\\cite\{([^}]+)\}', tbl_text)
        print(f"  - Total citations in table: {len(tbl_cites)}")
        print(f"  - Does table citations match bibitems order? {tbl_cites == bibitems}")
        # Check first 3 row titles
        for r in rows[:3]:
            title = r.split('&')[0].strip()
            print(f"    Sample Row Title: {title}")
        last_row = rows[-1].split('&')[0].strip()
        print(f"    Final Row Title: {last_row}")
    else:
        print("  - [WARNING] Comparative table not found!")

    # -------------------------------------------------------------
    # Suggestion 4 & 5: Proposed and Existing System Diagrams
    # -------------------------------------------------------------
    print("\n[4 & 5] Existing & Proposed System Diagrams:")
    figs = re.findall(r'\\begin\{figure\}.*?\\includegraphics.*?\{([^}]+)\}.*?\\caption\{([^}]+)\}.*?\\label\{([^}]+)\}.*?\\end\{figure\}', text, re.DOTALL)
    for f in figs:
        print(f"  - File: {f[0]} | Label: {f[2]} | Caption: {f[1][:60]}...")

    # -------------------------------------------------------------
    # Suggestion 6: All table captions placed ABOVE respective tables
    # -------------------------------------------------------------
    print("\n[6] Table Captions Above Tables:")
    table_env_matches = re.findall(r'(\\begin\{(table|xltabular)\}.*?\\end\{\2\})', text, re.DOTALL)
    for env_text, env_type in table_env_matches:
        cap_pos = env_text.find(r'\caption')
        tabular_pos = -1
        if env_type == 'table':
            tabular_pos = env_text.find(r'\begin{tabular')
        elif env_type == 'xltabular':
            tabular_pos = env_text.find(r'\hdrrow')
        label_match = re.search(r'\\label\{([^}]+)\}', env_text)
        lbl = label_match.group(1) if label_match else "unknown"
        if cap_pos != -1 and tabular_pos != -1:
            is_above = cap_pos < tabular_pos
            print(f"  - Table [{lbl}]: Caption is placed ABOVE table body? {is_above}")
        else:
            print(f"  - Table [{lbl}]: [WARNING] Check positions cap_pos={cap_pos}, tabular_pos={tabular_pos}")

    # -------------------------------------------------------------
    # Suggestion 7: Paragraphs never begin with Figure or Table references
    # -------------------------------------------------------------
    print("\n[7] Paragraphs Never Starting with Figure / Table:")
    print(f"  - Paragraphs starting with Figure / Table: {len(p_starting_with_fig_tab)} -> {p_starting_with_fig_tab}")

    print("\n=== AUDIT COMPLETE ===")

if __name__ == '__main__':
    verify_report()
