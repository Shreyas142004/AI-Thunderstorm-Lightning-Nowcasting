import urllib.request, json, sys

sys.stdout.reconfigure(encoding='utf-8')

dois = [
    ('10.1029/2022GL101626', 'leinonen2023multihazard'),
    ('10.1002/qj.4623', 'prasad2023impact'),
    ('10.1175/AIES-D-22-0043.1', 'leinonen2022seamless'),
    ('10.5194/nhess-22-577-2022', 'leinonen2022nowcasting'),
    ('10.1109/JSTARS.2020.3040648', 'luo2021pfst'),
    ('10.1038/s41612-023-00451-x', 'song2023lightning'),
    ('10.1007/s41651-020-00070-7', 'sibolla2021determining'),
    ('10.1016/j.atmosres.2023.107098', 'lu2023mcgln'),
    ('10.1007/s12040-017-0859-2', 'goyal2017satellite'),
    ('10.1016/j.cageo.2024.105539', 'le2024autocorrelated')
]

for doi, key in dois:
    url = f'https://api.crossref.org/works/{doi}'
    req = urllib.request.Request(url, headers={'User-Agent': 'Thesis/1.0 (mailto:test@univ.edu)'})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            d = json.loads(r.read().decode('utf-8'))['message']
            title = d.get('title', [''])[0].replace('‐', '-').replace('&', r'\&')
            authors = []
            for a in d.get('author', []):
                given = a.get('given', '')
                family = a.get('family', '')
                initials = '.~'.join([p[0] for p in given.split() if p]) + '.' if given else ''
                authors.append(f"{initials}~{family}" if initials else family)
            if len(authors) > 2:
                auth_str = ', '.join(authors[:-1]) + ', and ' + authors[-1]
            elif len(authors) == 2:
                auth_str = f"{authors[0]} and {authors[1]}"
            elif len(authors) == 1:
                auth_str = authors[0]
            else:
                auth_str = 'Unknown'
            jrnl = d.get('container-title', [''])[0].replace('&', r'\&')
            vol = d.get('volume', '')
            issue = d.get('issue', '')
            page = d.get('page', '')
            art = d.get('article-number', '')
            year = d.get('issued', {}).get('date-parts', [[0]])[0][0]
            
            vol_str = f"vol. {vol}" if vol else ""
            no_str = f"no. {issue}" if issue else ""
            if page:
                pp_str = f"pp. {page}"
            elif art:
                pp_str = f"art. no. {art}"
            else:
                pp_str = ""
            
            parts = [p for p in [vol_str, no_str, pp_str, str(year)] if p]
            meta = ', '.join(parts)
            
            print(f"\\bibitem{{{key}}}")
            print(f"{auth_str}, ``{title},'' \\emph{{{jrnl}}}, {meta}, doi: {doi}.\n")
    except Exception as e:
        print(f"Error {key} ({doi}): {e}")
