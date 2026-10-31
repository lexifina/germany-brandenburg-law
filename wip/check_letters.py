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


def number_lists(s):
    """Write out the numbers the browser shows for <ol> items, innermost lists first (tags in either case). A <ul>
    is unnumbered; it is resolved like any inner list, so an outer <ol> never numbers its bullets."""
    inner = re.compile(r'(?is)<(ol|ul)\b([^>]*)>((?:(?!<[ou]l\b).)*?)</\1>')
    while True:
        m = inner.search(s)
        if not m:
            return s
        kind, attrs, body = m.group(1).lower(), m.group(2), m.group(3)
        if kind == 'ul':
            s = s[:m.start()] + '<xul>' + re.sub(r'(?i)<li\b[^>]*>', '<xli>', body) + '</xul>' + s[m.end():]
            continue
        typ = re.search(r'(?i)type="(\w)"', attrs)
        st = re.search(r'(?i)start="(\d+)"', attrs)
        alpha = bool(typ and typ.group(1) == 'a') or 'lower-alpha' in attrs.lower()
        n = [int(st.group(1)) if st else 1]

        def mark(_):
            x = n[0]
            n[0] += 1
            return f"<xli> {chr(96 + x) if alpha else x} "
        s = s[:m.start()] + '<xol>' + re.sub(r'(?i)<li\b[^>]*>', mark, body) + '</xol>' + s[m.end():]


def source(raw):
    i = raw.index('class="reiterbox_innen_text"')
    j = raw.index('id="nachoben"', i)
    s = raw[raw.index('>', i) + 1:raw.rindex('<', i, j)]
    s = re.sub(r'(?s)<!--.*?-->', '', s)
    s = re.sub(r'(?s)<script.*?</script>', '', s)
    s = number_lists(s)
    return ld(html.unescape(re.sub(r'<[^>]+>', ' ', s)).replace('­', ''))


def main(paths):
    bad = total = 0
    for p in paths:
        for a in json.load(open(p, encoding='utf-8'))['acts']:
            vs = a['versions']
            for i, v in enumerate(vs):
                if 0 < i < len(vs) - 1 and vs[i + 1]['source_url'] == v['source_url']:
                    # A version composed from two Lesefassungen (an announced change and a later act's change, each
                    # in force on its own day): every file is the version before's or the next version's word for
                    # word, and the next one is checked against its page below.
                    prev, nxt = vs[i - 1]['units'], vs[i + 1]['units']
                    total += 1
                    odd = [k for k, u in v['units'].items()
                           if u != prev.get(k) and u != nxt.get(k)]
                    odd += [k for k in set(prev) & set(nxt) if k not in v['units']]
                    if odd:
                        bad += 1
                        print(f'MISMATCH {a["slug"]} {v["from"]}: composed version, files neither before nor after: {odd[:4]}')
                    continue
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
                    print(f'MISMATCH {a["slug"]} {v["from"]}: {pos}/{len(src)}; next {src[pos:pos+70]!r}; unplaced {list(rest)[:4]}; url={v["source_url"]}')
    print(f'{total} versions checked, {bad} mismatches')
    return bad


if __name__ == '__main__':
    sys.exit(1 if main(sys.argv[1:] or sorted(str(p) for p in (HERE / 'corpus.d').glob('*.json'))) else 0)
