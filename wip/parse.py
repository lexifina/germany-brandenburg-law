"""Brandenburg law from BRAVORS pages (.cache/pages) into corpus.d/ parts.

    python -X utf8 parse.py

Reads only the cache; the same cache gives the same bytes. For each act: the "Änderungshistorie" tab lists the
amending acts; the rows that link a "Lesefassung" are the versions here. Each version is dated by the in-force day of
the amending act, read from the Gesetz- und Verordnungsblatt issue the row links (its issue date and the act's
Inkrafttreten clause). Parts:
  10-verfassung.json   the Verfassung des Landes Brandenburg
  20-gesetze-NN.json   other Gesetze, about 50 acts a part
"""
from __future__ import annotations

import datetime as dt
import hashlib
import html
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

HERE = Path(__file__).resolve().parent
CACHE = HERE / '.cache' / 'pages'
BASE = 'https://bravors.brandenburg.de'
RETRIEVED = '2026-10-30'
MONTHS = {m: i + 1 for i, m in enumerate(['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August',
                                           'September', 'Oktober', 'November', 'Dezember'])}
DATE = r'(\d{1,2})\.\s*(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s+(\d{4})'

COUNTRY = {
    'code': 'DE-BB', 'name': 'Brandenburg', 'slug': 'germany-brandenburg', 'lang': 'de', 'tz': 'Europe/Berlin',
    'future_branch': 'zukunft',
    'publisher': {'name': 'Landesregierung Brandenburg (BRAVORS)', 'email': 'bravors@bravors.brandenburg.de.invalid'},
    'default_in_force_rule': {
        'text': 'Verfassung des Landes Brandenburg Art. 81 Abs. 3: "Jedes Gesetz und jede Rechtsverordnung soll den '
                'Tag des Inkrafttretens bestimmen. Fehlt eine solche Bestimmung, so treten sie mit dem vierzehnten Tag '
                'nach Ablauf des Tages in Kraft, an dem das Gesetzblatt ausgegeben worden ist." Each version here is '
                'dated by the Inkrafttreten clause of the amending act, applied to the issue date of the Gesetz- und '
                'Verordnungsblatt that printed it.',
        'source': 'https://bravors.brandenburg.de/de/gesetze-212792'},
    'licence_note': 'Texts: BRAVORS - Brandenburgisches Vorschriftensystem, Landesregierung Brandenburg, '
                    'bravors.brandenburg.de; Gesetz- und Verordnungsblatt für das Land Brandenburg Teil I. Gesetze and '
                    'Verordnungen are not protected by copyright (§ 5 Abs. 1 UrhG). Non-official reading text: only '
                    'the Gesetz- und Verordnungsblatt is authoritative.',
}


# Versions whose words, as parsed, differ from what the page shows (the letters-and-digits check): left out rather
# than published with a difference. Malformed nested lists (<ol start> inside <ol> with no <li>) whose numbers the
# parser drops, and pages whose footnote or Inhaltsübersicht the parser places elsewhere.
_LISTS = 'the page\'s nested list numbering is malformed and the parsed text differs from the page (letters check)'
_ORDER = 'the parsed text order differs from the page around its Inhaltsübersicht (letters check)'
LETTERS_DIFFER = {
    '/gesetze/bbgpolg_2013_1/12': _ORDER, '/gesetze/bbgsvvollzg/3': _ORDER, '/gesetze/bbgsvvollzg': _ORDER,
    '/gesetze/bbgrig/2': _LISTS, '/de/gesetze-213730': _LISTS, '/gesetze/bbguvpg/6': _LISTS, '/gesetze/bbguvpg/7': _LISTS,
    '/gesetze/bbguvpg': _LISTS, '/de/gesetze-212545': _LISTS,
}

# Versions whose amending act's Inkrafttreten clause names no calendar day: the day, read by hand, and why.
OVERRIDES = {
    '/de/gesetze-247329': ('2019-09-25', '"Dieses Gesetz tritt mit dem Beginn der 7. Wahlperiode des Landtages '
                                         'Brandenburg in Kraft" (GVBl. I 2015 Nr. 6); the 7. Wahlperiode began with '
                                         'the first sitting of the newly elected Landtag on 25 September 2019'),
}


def cache_path(path: str) -> Path:
    name = re.sub(r'[^A-Za-z0-9._-]+', '_', path.strip('/')) or 'root'
    return CACHE / (name[:150] + '.html')


def text(s: str) -> str:
    s = re.sub(r'(?s)<br\s*/?>', ' ', s)
    s = html.unescape(re.sub(r'(?s)<[^>]+>', '', s))
    s = s.replace(' ', ' ').replace('­', '').replace(' ', ' ').replace(' ', ' ')
    s = s.replace(',,', '„').replace('”', '“')
    s = re.sub(r'([(\[„]) +', r'\1', s)
    return re.sub(r'\s+', ' ', s).strip()


def de_date(m) -> str:
    d, mon, y = m.groups()
    return f'{y}-{MONTHS[mon]:02d}-{int(d):02d}'


def body_of(raw: str) -> str:
    i = raw.index('class="reiterbox_innen_text"')
    j = raw.index('id="nachoben"', i)
    s = raw[raw.index('>', i) + 1:j]
    return re.sub(r'(?s)<!--.*?-->', '', s)


VOID = {'br', 'img', 'hr', 'input', 'meta', 'link', 'col', 'wbr'}


class Node:
    __slots__ = ('tag', 'attrs', 'kids', 'parent')

    def __init__(self, tag, attrs, parent):
        self.tag, self.attrs, self.kids, self.parent = tag, dict(attrs), [], parent


class Tree(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.root = Node('root', {}, None)
        self.cur = self.root

    def handle_starttag(self, tag, attrs):
        n = Node(tag, attrs, self.cur)
        self.cur.kids.append(n)
        if tag not in VOID:
            self.cur = n

    def handle_startendtag(self, tag, attrs):
        self.cur.kids.append(Node(tag, attrs, self.cur))

    def handle_endtag(self, tag):
        x = self.cur
        while x is not self.root and x.tag != tag:
            x = x.parent
        if x is not self.root:
            self.cur = x.parent

    def handle_data(self, data):
        self.cur.kids.append(data)

    def handle_entityref(self, name):
        self.cur.kids.append(f'&{name};')

    def handle_charref(self, name):
        self.cur.kids.append(f'&#{name};')


def raw_of(n) -> str:
    """Inline content as text (tags dropped, <br> read as a space)."""
    if isinstance(n, str):
        return n
    if n.tag == 'br':
        return ' '
    return ''.join(raw_of(k) for k in n.kids)


BLOCKS = ('h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'table', 'ul', 'ol', 'dl', 'div', 'blockquote', 'center')


def blocks(s: str) -> list:
    """Block elements in order; a <p> or <div> holding other blocks is read as those blocks."""
    t = Tree()
    t.feed(s)
    out = []

    def walk(n):
        loose = []

        def flush():
            if any(text(raw_of(x)) for x in loose):
                q = Node('p', {}, None)
                q.kids = list(loose)
                out.append(('p', q))
            loose.clear()
        for k in n.kids:
            if isinstance(k, Node) and k.tag in BLOCKS:
                flush()
                if k.tag in ('p', 'div', 'blockquote', 'center') and any(isinstance(x, Node) and x.tag in BLOCKS for x in k.kids):
                    walk(k)
                else:
                    out.append((k.tag, k))
            else:
                loose.append(k)
        flush()
    walk(t.root)
    return out


def list_lines(n) -> list:
    """A list: one line per item; the numbers the browser shows (1., 2., ... or a), b), ...) are written out."""
    out = []
    typ = n.attrs.get('type') or ('a' if 'lower-alpha' in (n.attrs.get('style') or '') else '1')
    num = int(n.attrs.get('start') or 1)
    for li in n.kids:
        if not (isinstance(li, Node) and li.tag == 'li'):
            # Text standing in the list outside any item (the closing words of an enumeration): its own line.
            loose = text(raw_of(li))
            if loose:
                out.append(loose)
            continue
        mark = (f'{chr(96 + num)})' if typ == 'a' else f'{num}.') if n.tag == 'ol' else ''
        num += 1
        # The item's own words, its nested lists and paragraphs, and any words after them, in source order.
        ls, run = [], []
        for k in li.kids:
            if isinstance(k, Node) and k.tag in ('ol', 'ul', 'p', 'div'):
                if text(''.join(run)):
                    ls.append(text(''.join(run)))
                run = []
                ls += list_lines(k) if k.tag in ('ol', 'ul') else [text(raw_of(k))]
            else:
                run.append(raw_of(k))
        if text(''.join(run)):
            ls.append(text(''.join(run)))
        ls = [x for x in ls if x]
        if mark:
            ls = [f'{mark} {ls[0]}' if ls else mark] + ls[1:]
        out += ls
    return out


def block_lines(tag: str, node) -> list:
    if tag == 'table':
        rows = []

        def walk(x):
            for k in x.kids:
                if isinstance(k, Node):
                    if k.tag == 'tr':
                        cells = [text(raw_of(c)) for c in k.kids if isinstance(c, Node) and c.tag in ('td', 'th')]
                        if any(cells):
                            rows.append(' | '.join(cells))
                    else:
                        walk(k)
        walk(node)
        return rows
    if tag in ('ul', 'ol'):
        return list_lines(node)
    if tag == 'dl':
        return [t for t in (text(raw_of(k)) for k in node.kids if isinstance(k, Node)) if t]
    t = text(raw_of(node))
    return [t] if t else []


def inner(node) -> str:
    """The element as text with its anchors kept, for the table-of-contents test."""
    def r(n):
        if isinstance(n, str):
            return n
        if n.tag == 'a':
            return f'<a href="{n.attrs.get("href", "")}">' + ''.join(r(k) for k in n.kids) + '</a>'
        if n.tag == 'br':
            return '<br />'
        return ''.join(r(k) for k in n.kids)
    return ''.join(r(k) for k in node.kids)


def is_toc(tag: str, inner: str) -> bool:
    return tag == 'p' and bool(re.search(r'<a href="#', inner)) and not text(re.sub(r'(?s)<a href="#[^"]*">.*?</a>', '', inner))


def unit_key(head: str, seen: set) -> tuple[str, str]:
    m = re.match(r'^(Artikel|Art\.|§§?)\s*(\d+)\s*([a-z]?)\b', head)
    if m:
        pre = 'art' if m.group(1).startswith('Art') else 'par'
        k, kind = f'{pre}-{int(m.group(2)):03d}{m.group(3)}', pre
    elif re.match(r'(?i)pr(ä|ae)ambel', head):
        k, kind = '001-praeambel', 'preamble'
    elif re.match(r'^(Anlage|Anhang)', head):
        mm = re.match(r'^(\w+)\s*(\d*)', head)
        k, kind = 'z-' + mm.group(1).lower() + (f'-{int(mm.group(2)):02d}' if mm.group(2) else ''), 'annex'
    else:
        k = 'y-' + (re.sub(r'[^a-z0-9]+', '-', head.lower().translate(str.maketrans('äöüß', 'aous'))).strip('-')[:40] or 'teil')
        kind = 'other'
    base, n = k, 2
    while k in seen:
        k = f'{base}-{n}'
        n += 1
    seen.add(k)
    return k, kind


def parse_version(raw: str, title: str) -> dict:
    bl = [(t, inner(n), n) for t, n in blocks(body_of(raw))]
    toc_idx = [i for i, (t, x, _) in enumerate(bl) if is_toc(t, x)]
    units: dict[str, dict] = {}
    seen = {'000-eingang'}
    if toc_idx:
        start_toc = next((i for i, (t, x, _) in enumerate(bl[:toc_idx[0] + 1]) if t.startswith('h') and 'Inhalts' in text(x)), toc_idx[0])
        intro, toc, body = bl[:start_toc], bl[start_toc:toc_idx[-1] + 1], bl[toc_idx[-1] + 1:]
    else:
        first = next((i for i, (t, x, _) in enumerate(bl) if t.startswith('h')), len(bl))
        intro, toc, body = bl[:first], [], bl[first:]
    eingang = ['# ' + title]
    for t, x, nd in intro:
        eingang += block_lines(t, nd)
    units['000-eingang'] = {'label': 'Eingang', 'kind': 'title', 'text': '\n'.join(eingang) + '\n'}
    if toc:
        ls = []
        for t, x, nd in toc:
            if t == 'p' and is_toc(t, x):
                ls += [text(a) for a in re.findall(r'(?s)<a href="#[^"]*">(.*?)</a>', x) if text(a)]
            else:
                ls += [('## ' if t.startswith('h') else '') + l for l in block_lines(t, nd)]
        units['000-inhalt'] = {'label': 'Inhaltsübersicht', 'kind': 'other', 'text': '\n'.join(ls) + '\n'}
        seen.add('000-inhalt')
    pending: list[str] = []
    cur = None
    for t, x, nd in body:
        if t.startswith('h'):
            head = text(x)
            starts_unit = '<a name=' in x or re.match(r'(?i)^(pr(ä|ae)ambel|anlage|anhang)', head) or \
                re.match(r'^(Artikel|§)\s*\d', head)
            if starts_unit:
                key, kind = unit_key(head, seen)
                label = re.sub(r'\s*\(.*$', '', head) or head
                units[key] = {'label': label, 'kind': kind, 'lines': pending + ['# ' + head]}
                pending = []
                cur = key
            else:
                level = int(t[1])
                pending.append('#' * max(2, min(level - 1, 6)) + ' ' + head)
            continue
        ls = block_lines(t, nd)
        if not ls:
            continue  # an empty block (a bare anchor): the headings before it stay with what follows
        if cur is None:
            units['000-eingang']['text'] += '\n'.join(pending + ls) + ('\n' if pending or ls else '')
            pending = []
        else:
            units[cur]['lines'] += pending + ls
            pending = []
    if pending and cur:
        units[cur]['lines'] += pending
    for k, u in units.items():
        if 'lines' in u:
            u['text'] = '\n'.join(u.pop('lines')) + '\n'
    return units


def history(raw: str) -> list[dict]:
    rows = []
    tb = raw[raw.index('class="historie"'):]
    tb = tb[:tb.index('</table>')]
    tb = re.sub(r'(?s)<!--.*?-->', '', tb)
    for r in re.findall(r'(?s)<tr>(.*?)</tr>', tb)[1:]:
        tds = re.findall(r'(?s)<td[^>]*>(.*?)</td>', r)
        if len(tds) < 2:
            continue
        link = re.search(r'href="(/(?:de/gesetze-\d+|gesetze/[^"?#]+))"', tds[0])
        pdf = re.search(r'href="(/fm/[^"]+\.pdf)"', tds[1])
        desc, fund = text(tds[0]), text(tds[1])
        m = re.search(r'vom ' + DATE, desc)
        rows.append({'desc': desc, 'fundstelle': fund, 'link': link.group(1) if link else None,
                     'pdf': pdf.group(1) if pdf else None, 'enacted': de_date(m) if m else None})
    return rows


def guess_pdf(fund: str) -> str | None:
    m = re.match(r'GVBl\.I/(\d{2}), \[Nr\. (\d+)\]', fund)
    if not m:
        return None
    y = int(m.group(1))
    y += 1900 if y > 50 else 2000
    return f'/fm/76/GVBl_I_{int(m.group(2)):02d}_{y}.pdf'


def in_force(pdf_path: Path, enacted: str, act_title: str) -> tuple:
    """(day, how) from the GVBl issue: its issue date and the amending act's Inkrafttreten clause.

    The issue is cut into acts at each signature line ("Potsdam, den <date>"); the amending act is the one signed on
    its Ausfertigung day, and if several were, the one that names the amended act's title."""
    import pypdf
    r = pypdf.PdfReader(str(pdf_path))
    full = '\n'.join(pg.extract_text() or '' for pg in r.pages)
    flat = re.sub(r'(\w)[-\u00ad]\s*\n\s*(\w)', r'\1\2', full)
    flat = re.sub(r'[\u00ad]', '', flat)
    flat = re.sub(r'\s+', ' ', flat)
    m = re.search(r'Teil I\W+Nr\. \d+ vom ' + DATE, flat) or re.search(r'Potsdam, den ' + DATE, flat[:600])
    if not m:
        return None, 'no issue date'
    issued = de_date(m)
    sigs = [(x.start(), de_date(x)) for x in re.finditer(r'Potsdam, den ' + DATE, flat)]
    segs, prev = [], 0
    for pos, d in sigs:
        if pos < 600 and not segs and prev == 0:  # the issue's own date line
            prev = pos + 20
            continue
        segs.append((flat[prev:pos], d))
        prev = pos + 20
    cand = [sg for sg, d in segs if d == enacted]
    if len(cand) > 1:
        names = {v: k for k, v in MONTHS.items()}
        y, mo, d = enacted.split('-')
        vom = f'Vom {int(d)}. {names[int(mo)]} {y}'
        titled = [sg for sg in cand if re.search(r'Änderung (der|des) ' + re.escape(act_title[:60]) + r'\W*' + vom, sg)]
        cand = titled or cand
    if len(cand) > 1:
        words = act_title[:60]
        cand = [sg for sg in cand if words in sg]
        if len(cand) > 1:
            amend = [sg for sg in cand if re.search(re.escape(words) + r'.{0,300}?(wird|werden) wie folgt geändert', sg)]
            cand = amend or cand
        if len(cand) > 1:
            named = [sg for sg in cand if ('Änderung der ' + words) in sg[:400]]
            cand = named or cand
    if len(cand) != 1:
        return None, f'{len(cand)} acts signed on {enacted} in the issue'
    cl = re.findall(r'(Dieses Gesetz tritt (?:(?!Dieses Gesetz).){0,200}? in Kraft)', cand[0])
    if len(cl) != 1:
        return None, f'{len(cl)} Inkrafttreten clauses'
    c = cl[0]
    if re.fullmatch(r'DiesesGesetztrittamTage?nach(der|seiner)Verkünd(?:ung|igung)inKraft', c.replace(' ', '')):
        day = (dt.date.fromisoformat(issued) + dt.timedelta(days=1)).isoformat()
        return day, f'"{c}"; GVBl. I issued {issued}'
    mm = re.fullmatch(r'Dieses Gesetz tritt (?:am|mit Wirkung vom) ' + DATE + r' in Kraft', re.sub(r'\s+', ' ', c))
    if mm:
        return de_date(mm), f'"{c}"'
    return None, f'clause not simple: "{c[:200]}"'


def act_of(doc: str, overrides: dict) -> tuple[dict | None, dict, list[str]]:
    cur = cache_path(doc)
    hist = cache_path(doc + '?history')
    raw_cur = cur.read_text(encoding='utf-8', errors='replace')
    title = text(re.search(r'(?s)<h2 id="norm_title">(.*?)</h2>', raw_cur).group(1))
    rows = history(hist.read_text(encoding='utf-8', errors='replace'))
    laws, problems, versions = {}, [], []
    linked = [r for r in rows if r['link']]
    if not linked:  # no Lesefassung of any version: current text only
        linked = [{'link': doc, 'desc': None, 'enacted': None, 'pdf': None, 'fundstelle': None}]
    earlier = []
    skipped: list = []
    first = True
    for n, r in enumerate(linked):
        page = cache_path(r['link'])
        if n == len(linked) - 1 and not page.exists():
            page = cur  # the newest Lesefassung is the act's own page
        if not page.exists():
            if versions:
                problems.append(f'{title}: version {r["link"]} not retrieved; later versions left out')
                break
            continue  # older Lesefassungen not retrieved yet: the history starts at the oldest one retrieved
        raw = page.read_text(encoding='utf-8', errors='replace')
        units = parse_version(raw, title)
        if r['link'] in LETTERS_DIFFER:
            problems.append(f'{title}: version {r["link"]} ({r["desc"]}) left out: {LETTERS_DIFFER[r["link"]]}')
            if versions:
                skipped.append(units)
            continue
        if first:
            # Oldest version available: dated by its amending act's in-force day if known, else its own date.
            pass
        day, how = None, ''
        if r['enacted']:
            if r['link'] in overrides:
                day, how = overrides[r['link']]
            else:
                pdf = r['pdf'] or guess_pdf(r['fundstelle'] or '')
                pp = cache_path(pdf) if pdf else None
                if pp and pp.exists():
                    day, how = in_force(pp, r['enacted'], title)
                else:
                    how = 'GVBl issue not retrieved'
        elif n == 0 and rows and rows[0]['desc'] and rows[0]['desc'].startswith('Ursprüngliche Fassung'):
            pass
        if not day:
            problems.append(f'{title}: version {r["link"]} ({r["desc"]}) left out: {how}')
            if versions:
                skipped.append(units)
            continue
        key = f'gvbl-{day[:4]}-{r["enacted"].replace("-", "")}'
        law = {'label': f'{re.sub(r"^.*?durch ", "", r["desc"])} ({r["fundstelle"]})', 'title': None, 'kind': 'law',
               'enacted': r['enacted'], 'published': None, 'url': BASE + (r['pdf'] or guess_pdf(r['fundstelle']) or ''),
               'temporary_until': None, 'restores': None, 'note': None}
        key = 'bb-' + re.sub(r'[^a-z0-9]+', '-', (r['fundstelle'] or '').lower()).strip('-') + '-' + r['enacted'].replace('-', '')
        v = {'from': day, 'source_url': BASE + r['link'], 'sha256': hashlib.sha256(page.read_bytes()).hexdigest(),
             'units': units, 'credits': {}, 'note': f'In force from {day}: {how}.'}
        if versions and day <= versions[-1]['from']:
            problems.append(f'{title}: version {r["link"]} dated {day}, not after {versions[-1]["from"]}; left out')
            continue
        if versions:
            prev = versions[-1]['units']
            for k in sorted(set(prev) | set(units)):
                if prev.get(k, {}).get('text') != units.get(k, {}).get('text'):
                    # A change that a left-out version between them already shows is not this act's: unexplained.
                    if not any(sk.get(k, {}).get('text') != prev.get(k, {}).get('text') for sk in skipped):
                        v['credits'][k] = [key]
            skipped = []
            laws[key] = law
        else:
            for e in rows[:rows.index(r) + 1]:
                if e['enacted']:
                    ek = 'bb-' + re.sub(r'[^a-z0-9]+', '-', (e['fundstelle'] or '').lower()).strip('-') + '-' + e['enacted'].replace('-', '')
                    laws[ek] = {'label': f'{re.sub(r"^.*?durch ", "", e["desc"])} ({e["fundstelle"]})', 'title': None,
                                'kind': 'law', 'enacted': e['enacted'], 'published': None, 'url': None,
                                'temporary_until': None, 'restores': None, 'note': None}
                    earlier.append(ek)
        versions.append(v)
    if not versions:
        return None, laws, problems
    m = re.search(r'[–-]\s*([A-Za-zÄÖÜäöüß][\wÄÖÜäöüß./-]*)\)\s*$', title) or re.search(r'\(([A-Za-zÄÖÜäöüß][\wÄÖÜäöüß./-]*)\)\s*$', title)
    abk = m.group(1) if m else None
    slug = re.sub(r'[^a-z0-9]+', '-', doc.rsplit('/', 1)[1].lower()).strip('-')
    act = {'slug': 'verfassung' if doc == '/de/gesetze-212792' else (re.sub(r'[^a-z0-9]+', '-', abk.lower().translate(str.maketrans('äöüß', 'aous'))).strip('-') if abk else slug),
           'short': 'BbgVerf' if doc == '/de/gesetze-212792' else (abk or title[:60]), 'title': title,
           'url': BASE + doc, 'first_law': None, 'earlier_laws': sorted(set(earlier)), 'versions': versions}
    return act, laws, problems


def write_part(name: str, docs: list[str], country: bool, overrides: dict) -> None:
    acts, laws, problems = [], {}, []
    for d in docs:
        a, lw, pr = act_of(d, overrides)
        problems += pr
        if a:
            acts.append(a)
            laws.update(lw)
    nv = sum(len(a['versions']) for a in acts)
    # One amending law, one entry: the label names the law, not the Artikel that touched this act; a law an earlier
    # published part already holds keeps that part's entry word for word (published parts are never rewritten).
    for k, lw in laws.items():
        lw['label'] = re.sub(r'^(?:Artikel|Art\.)\s*\d+\w*(?:\s+(?:Absatz|Abs\.)\s*\d+\w*)?\s+des\s+Gesetzes\b',
                             'Gesetz', lw['label'])
    for other in sorted((HERE / 'corpus.d').glob('*.PUBLISH')):
        if other.stem != name and other.with_suffix('.json').exists():
            for k, lw in json.loads(other.with_suffix('.json').read_text(encoding='utf-8'))['laws'].items():
                if k in laws:
                    laws[k] = lw
    out = {'acts': acts, 'laws': dict(sorted(laws.items())), 'applies': [],
           'sources': [{'name': 'BRAVORS - Brandenburgisches Vorschriftensystem (Landesregierung Brandenburg): current '
                                'text, Änderungshistorie and the Lesefassung of each historical version',
                        'url': BASE, 'retrieved': RETRIEVED,
                        'licence': '§ 5 Abs. 1 UrhG: Gesetze, Verordnungen and amtliche Erlasse enjoy no copyright '
                                   'protection. BRAVORS states no terms restricting reuse.',
                        'notes': f'{len(acts)} acts, {nv} versions in this part.'},
                       {'name': 'Gesetz- und Verordnungsblatt für das Land Brandenburg Teil I (PDF issues on BRAVORS)',
                        'url': BASE + '/de/veroeffentlichungsblaetter_einfache_suche', 'retrieved': RETRIEVED,
                        'licence': '§ 5 Abs. 1 UrhG.', 'notes': 'Read only for each issue date and each amending act\'s '
                                                                 'Inkrafttreten clause.'}],
           'decisions': [
               'The versions are the rows of BRAVORS\' "Änderungshistorie" that link a Lesefassung. Amending acts '
               'listed before the oldest linked row have no Lesefassung; the oldest one is the oldest version '
               'available, credited to the publisher and naming those acts.',
               'Each later version is credited, for every provision that differs from the version before, to the '
               'amending act its history row names.',
               'Each version is dated by its amending act\'s Inkrafttreten clause in the Gesetz- und Verordnungsblatt '
               'issue the row cites: "am Tag nach der Verkündung" is the day after the issue date; a stated day is '
               'that day. A version whose clause is not one of these is left out (listed below).',
               'One file per Artikel or Paragraph; the Inhaltsübersicht is its own file. Headings of Hauptteile and '
               'Abschnitte stand above the first provision under them.'] + [f'Left out: {p}' for p in problems],
           'ai_use': ['Claude Code (claude-opus-5-5) wrote Lexifina\'s code and chose the sources. No model output is '
                      'used as legal text, dates or credits: words come from BRAVORS, dates from the Gesetz- und '
                      'Verordnungsblatt, credits from BRAVORS\' history.']}
    if country:
        out['country'] = COUNTRY
    d = HERE / 'corpus.d'
    tmp = d / (name + '.json.tmp')
    tmp.write_text(json.dumps(out, ensure_ascii=False, indent=1) + '\n', encoding='utf-8', newline='\n')
    tmp.replace(d / (name + '.json'))
    print(name, len(acts), 'acts', nv, 'versions', len(problems), 'problems')
    for p in problems:
        print('  ', p)


PART_SIZE = 50


def ready(doc: str) -> bool:
    return cache_path(doc).exists() and cache_path(doc + '?history').exists()


def harmonise(written: list[str]) -> None:
    """One entry per law key across all parts (the builder refuses two). An entry in a part not written in this run
    wins; otherwise the one that names the GVBl issue and the law ("Gesetz vom ..."), not the act's own
    "Ursprüngliche Fassung" row."""
    d = HERE / 'corpus.d'
    parts = {p.stem: json.loads(p.read_text(encoding='utf-8')) for p in sorted(d.glob('*.json'))}
    best: dict = {}
    for name, part in parts.items():
        for k, lw in part['laws'].items():
            rank = (name not in written, bool(lw.get('url')), not lw['label'].startswith('Ursprüngliche Fassung'))
            if k not in best or rank > best[k][0]:
                best[k] = (rank, lw)
    # A slug two acts share (a generic abbreviation such as "Staatsvertrag"): each such act in a part written now takes
    # its BRAVORS document name instead.
    uses: dict = {}
    for part in parts.values():
        for a in part['acts']:
            uses[a['slug']] = uses.get(a['slug'], 0) + 1
    for name in written:
        part = parts[name]
        changed = False
        for a in part['acts']:
            if uses[a['slug']] > 1:
                a['slug'] = re.sub(r'[^a-z0-9]+', '-', a['url'].rsplit('/', 1)[1].lower()).strip('-')
                changed = True
        new = {k: best[k][1] for k in part['laws']}
        if new != part['laws'] or changed:
            part['laws'] = new
            tmp = d / (name + '.json.tmp')
            tmp.write_text(json.dumps(part, ensure_ascii=False, indent=1) + '\n', encoding='utf-8', newline='\n')
            tmp.replace(d / (name + '.json'))
            print(name, 'law entries harmonised')


if __name__ == '__main__':
    # python -X utf8 parse.py [<part> ...]: write only the named parts (a published part is never rewritten unless
    # named). --harmonise <part> ...: only make the named parts' law entries agree with the others.
    if sys.argv[1:2] == ['--harmonise']:
        harmonise(sys.argv[2:])
        sys.exit()
    only = set(sys.argv[1:])
    written = []
    if not only or '10-verfassung' in only:
        write_part('10-verfassung', ['/de/gesetze-212792'], country=True, overrides=OVERRIDES)
        written.append('10-verfassung')
    lst = HERE / '.cache' / 'gesetze.txt'
    docs = lst.read_text(encoding='utf-8').split() if lst.exists() else []
    for n in range(0, len(docs), PART_SIZE):
        chunk = docs[n:n + PART_SIZE]
        name = f'20-gesetze-{n // PART_SIZE + 1:02d}'
        if not all(ready(d) for d in chunk):
            break
        if not only or name in only:
            write_part(name, chunk, country=False, overrides=OVERRIDES)
            written.append(name)
    harmonise(written)
