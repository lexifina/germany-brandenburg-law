"""Fetch BRAVORS (bravors.brandenburg.de) into .cache/.

    python -X utf8 fetch.py get <path> [<path> ...]      # any page, cached under .cache/pages
Private (never published). One process, one request at a time, at least 21 s apart (robots.txt Crawl-delay: 20),
curl with a browser User-Agent, cached by path; stops on 403/429 or a challenge page.
"""
import hashlib, json, re, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
CACHE = HERE / '.cache'
BASE = 'https://bravors.brandenburg.de'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'
STAMP = CACHE / 'last-request'


def cache_path(path: str) -> Path:
    name = re.sub(r'[^A-Za-z0-9._-]+', '_', path.strip('/')) or 'root'
    return CACHE / 'pages' / (name[:150] + '.html')


def get(path: str) -> Path | None:
    out = cache_path(path)
    if out.exists() and out.stat().st_size:
        return out
    last = float(STAMP.read_text()) if STAMP.exists() else 0.0
    wait = 21 - (time.time() - last)
    if wait > 0:
        time.sleep(wait)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix('.part')
    url = BASE + path
    p = subprocess.run(['curl', '-s', '--compressed', '--max-time', '90', '-A', UA, '-o', str(tmp),
                        '-w', '%{http_code} %{redirect_url}', url], capture_output=True, text=True)
    STAMP.write_text(str(time.time()))
    code, _, redir = p.stdout.strip().partition(' ')
    code = int(code or 0)
    body = tmp.read_bytes() if tmp.exists() else b''
    with open(CACHE / 'requests.jsonl', 'a', encoding='utf-8') as f:
        f.write(json.dumps({'t': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'url': url, 'code': code,
                            'redirect': redir, 'bytes': len(body), 'sha256': hashlib.sha256(body).hexdigest()}) + '\n')
    if code in (403, 429) or b'Just a moment' in body[:5000] or b'captcha' in body[:5000].lower():
        tmp.unlink(missing_ok=True)
        raise SystemExit(f'stop: {code} on {url}')
    if code == 200 and body:
        tmp.replace(out)
        return out
    tmp.unlink(missing_ok=True)
    return None


SACH = '/de/vorschriften_fundstellennachweis_gesetzte_und_verordnungen_sachgebietlich/sachgebiet/'


def gesetze() -> list[str]:
    """Act pages of the Gesetze on the subject index (not Verordnungen, Geschäftsordnungen or Staatsverträge alone),
    in index order."""
    import html as h
    out = []
    for n in range(1, 10):
        f = cache_path(SACH + str(n))
        if not f.exists():
            continue
        s = f.read_text(encoding='utf-8', errors='replace')
        for href, t in re.findall(r'<a[^>]*href="(/(?:de/gesetze-\d+|gesetze/[^"]+))"[^>]*>(.*?)</a>', s, re.S):
            t = h.unescape(re.sub('<[^>]+>', '', t)).strip()
            if re.match(r'^(Gesetz|[A-ZÄÖÜ][\wäöüß-]*gesetz\b)', t) and href not in out and href != '/de/gesetze-212792':
                out.append(href)
    return out


def history_rows(path: str) -> list[tuple[str, str | None]]:
    """(version page, GVBl pdf) for each history row that links a Lesefassung, oldest first."""
    f = cache_path(path + '?history')
    s = f.read_text(encoding='utf-8', errors='replace')
    s = re.sub(r'(?s)<!--.*?-->', '', s)
    out = []
    for r in re.findall(r'(?s)<tr>(.*?)</tr>', s):
        link = re.search(r'href="(/(?:de/gesetze-\d+|gesetze/[^"?#]+))"', r)
        if not link:
            continue
        pdf = re.search(r'href="(/fm/[^"]+\.pdf)"', r)
        fund = re.search(r'GVBl\.I/(\d{2}), \[Nr\. (\d+)\]', re.sub(r'<[^>]+>', '', r))
        if not pdf and fund:
            y = int(fund.group(1))
            y += 1900 if y > 50 else 2000
            pdf_path = f'/fm/76/GVBl_I_{int(fund.group(2)):02d}_{y}.pdf'
        else:
            pdf_path = pdf.group(1) if pdf else None
        out.append((link.group(1), pdf_path))
    return out


def run_gesetze():
    """Pass 1: every Gesetz's page, history and the GVBl issue of its newest version; pass 2: the older versions."""
    for n in range(1, 10):
        get(SACH + str(n))
    acts = gesetze()
    (CACHE / 'gesetze.txt').write_text('\n'.join(acts) + '\n', encoding='utf-8')
    print(len(acts), 'Gesetze', flush=True)
    for i, a in enumerate(acts):
        page = get(a)
        if page is None:
            continue
        real = re.search(r'<link rel="canonical" href="https://bravors\.brandenburg\.de(/de/gesetze-\d+)"', page.read_text(encoding='utf-8', errors='replace'))
        get(a + '?history')
        rows = history_rows(a)
        if rows and rows[-1][1]:
            get(rows[-1][1])
        print('pass1', i, a, len(rows), flush=True)
    for i, a in enumerate(acts):
        if not cache_path(a + '?history').exists():
            continue
        rows = history_rows(a)
        for link, pdf in reversed(rows[:-1]):
            get(link)
            if pdf:
                get(pdf)
        print('pass2', i, a, flush=True)


def verordnungen() -> list[str]:
    """Act pages of the Verordnungen on the subject index (not amending Verordnungen alone), in index order."""
    import html as h
    out = []
    for n in range(1, 10):
        f = cache_path(SACH + str(n))
        if not f.exists():
            continue
        s = f.read_text(encoding='utf-8', errors='replace')
        for href, t in re.findall(r'<a[^>]*href="(/(?:de/verordnungen-\d+|verordnungen/[^"]+))"[^>]*>(.*?)</a>', s, re.S):
            t = h.unescape(re.sub('<[^>]+>', '', t)).strip()
            if re.search(r'(?i)verordnung', t) and href not in out:
                out.append(href)
    return out


def history_links(path: str) -> list[tuple[str, str | None]]:
    """(Lesefassung page, GVBl pdf) of every history row of a Verordnung (Teil II issues), oldest first."""
    f = cache_path(path + '?history')
    s = re.sub(r'(?s)<!--.*?-->', '', f.read_text(encoding='utf-8', errors='replace'))
    out = []
    for r in re.findall(r'(?s)<tr>(.*?)</tr>', s):
        link = re.search(r'href="(/(?:de/verordnungen-\d+|verordnungen/[^"?#]+))"', r)
        pdf = re.search(r'href="(/fm/[^"]+\.pdf)"', r)
        fund = re.search(r'GVBl\.(I|II)/(\d{2}), \[Nr\. (\d+)\]', re.sub(r'<[^>]+>', '', r))
        pdf_path = pdf.group(1) if pdf else None
        if not pdf and fund:  # the issue named but not linked: its usual path on BRAVORS
            y = int(fund.group(2))
            y += 1900 if y > 50 else 2000
            pdf_path = f'/fm/76/GVBl_{fund.group(1)}_{int(fund.group(3)):02d}_{y}.pdf'
        if link or pdf_path:
            out.append((link.group(1) if link else None, pdf_path))
    return out


def run_verordnungen(start: int = 0):
    """Each Verordnung in full, in index order: its page, history, and every Lesefassung with its GVBl issue."""
    acts = verordnungen()
    (CACHE / 'verordnungen.txt').write_text('\n'.join(acts) + '\n', encoding='utf-8')
    print(len(acts), 'Verordnungen', flush=True)
    for i, a in enumerate(acts[start:], start=start):
        if get(a) is None or get(a + '?history') is None:
            print('missing', i, a, flush=True)
            continue
        rows = history_links(a)
        for link, pdf in reversed(rows):
            if link and link != a:
                get(link)
            if pdf:
                get(pdf)
        print('done', i, a, len(rows), flush=True)


if __name__ == '__main__':
    if sys.argv[1] == 'get':
        for x in sys.argv[2:]:
            print(x, get(x), flush=True)
    elif sys.argv[1] == 'gesetze':
        run_gesetze()
    elif sys.argv[1] == 'verordnungen':
        run_verordnungen(int(sys.argv[2]) if sys.argv[2:] else 0)
    elif sys.argv[1] == 'list':  # paths one per line from a file
        for x in Path(sys.argv[2]).read_text(encoding='utf-8').split():
            print(x, get(x), flush=True)

