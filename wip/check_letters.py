"""Independent letters-and-digits check of every version against its raw BRAVORS page (regex only).

    python -X utf8 check_letters.py [part.json ...]

Private. The text of the reading-version box (from "reiterbox_innen_text" to "nachoben", HTML comments removed),
reduced to letters and digits, must equal the version's files (the title line of 000-eingang left out) placed one
after another in source order.
"""
import html, json, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def ld(s):
    return ''.join(ch for ch in s if ch.isalnum())


def cpath(path):
    name = re.sub(r'[^A-Za-z0-9._-]+', '_', path.strip('/')) or 'root'
    return HERE / '.cache' / 'pages' / (name[:150] + '.html')


def source(raw):
    i = raw.index('class="reiterbox_innen_text"')
    s = raw[raw.index('>', i) + 1:raw.index('id="nachoben"', i)]
    s = re.sub(r'(?s)<!--.*?-->', '', s)
    s = re.sub(r'(?s)<script.*?</script>', '', s)
    return ld(html.unescape(re.sub(r'<[^>]+>', ' ', s)).replace('­', ''))


def main(paths):
    bad = total = 0
    for p in paths:
        for a in json.load(open(p, encoding='utf-8'))['acts']:
            for v in a['versions']:
                src = source(cpath(v['source_url'].split('brandenburg.de', 1)[1]).read_text(encoding='utf-8', errors='replace'))
                rest = {}
                for k, u in v['units'].items():
                    t = u['text'].split('\n', 1)[1] if k == '000-eingang' else u['text']
                    rest[k] = ld(t)
                pos = 0
                while rest:
                    hit = max((k for k, t in rest.items() if src.startswith(t, pos)), key=lambda k: len(rest[k]), default=None)
                    if hit is None:
                        break
                    pos += len(rest.pop(hit))
                total += 1
                if rest or pos != len(src):
                    bad += 1
                    print(f'MISMATCH {a["slug"]} {v["from"]}: {pos}/{len(src)}; next {src[pos:pos+70]!r}; unplaced {list(rest)[:4]}')
    print(f'{total} versions checked, {bad} mismatches')
    return bad


if __name__ == '__main__':
    sys.exit(1 if main(sys.argv[1:] or sorted(str(p) for p in (HERE / 'corpus.d').glob('*.json'))) else 0)
