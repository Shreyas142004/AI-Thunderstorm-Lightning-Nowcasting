import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

dois = [
    '10.1109/JSTARS.2020.3040648',
    '10.1038/s41612-023-00451-x',
    '10.1007/s41651-020-00070-7',
    '10.1007/s12040-017-0859-2',
    '10.2139/ssrn.4510991'
]

for doi in dois:
    url = f'https://api.crossref.org/works/{doi}'
    req = urllib.request.Request(url, headers={'User-Agent': 'MajorProjectThesis/1.0 (mailto:student@university.edu)'})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))['message']
            title = data.get('title', [''])[0]
            authors = [f"{a.get('given', '')} {a.get('family', '')}".strip() for a in data.get('author', [])]
            container = data.get('container-title', [''])[0]
            year = data.get('issued', {}).get('date-parts', [[0]])[0][0]
            vol = data.get('volume', '')
            issue = data.get('issue', '')
            page = data.get('page', '')
            art = data.get('article-number', '')
            print(f'DOI: {doi}')
            print(f'  Title: {title}')
            print(f'  Authors: {", ".join(authors)}')
            print(f'  Journal: {container}, vol. {vol}, no. {issue}, pp. {page or art}, {year}\n')
    except Exception as e:
        print(f'Error for {doi}: {e}')
