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


if __name__ == '__main__':
    if sys.argv[1] == 'get':
        for x in sys.argv[2:]:
            print(x, get(x), flush=True)
    elif sys.argv[1] == 'list':  # paths one per line from a file
        for x in Path(sys.argv[2]).read_text(encoding='utf-8').split():
            print(x, get(x), flush=True)
