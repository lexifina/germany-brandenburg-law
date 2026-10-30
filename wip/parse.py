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


BLOCK = re.compile(r'(?s)<(h[1-6]|p|table|ul|ol|dl)\b[^>]*>(.*?)</\1>')


def blocks(s: str) -> list[tuple[str, str]]:
    """Top-level blocks in order. Nested <p><p>..</p></p> is read as its inner paragraphs."""
    out = []
    for m in BLOCK.finditer(s):
        tag, inner = m.group(1), m.group(2)
        out.append((tag, inner))
    return out


def block_lines(tag: str, inner: str) -> list[str]:
    if tag == 'table':
        rows = []
        for r in re.findall(r'(?s)<tr\b[^>]*>(.*?)</tr>', inner):
            cells = [text(c) for c in re.findall(r'(?s)<t[dh]\b[^>]*>(.*?)</t[dh]>', r)]
            if any(cells):
                rows.append(' | '.join(cells))
        return rows
    if tag in ('ul', 'ol', 'dl'):
        items = re.findall(r'(?s)<(?:li|dd|dt)\b[^>]*>(.*?)</(?:li|dd|dt)>', inner)
        return [t for t in (text(x) for x in items) if t]
    t = text(inner)
    return [t] if t else []


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
    bl = blocks(body_of(raw))
    toc_idx = [i for i, (t, x) in enumerate(bl) if is_toc(t, x)]
    units: dict[str, dict] = {}
    seen = {'000-eingang'}
    if toc_idx:
        start_toc = next(i for i, (t, x) in enumerate(bl) if t.startswith('h') and 'Inhalts' in text(x)) \
            if any(t.startswith('h') and 'Inhalts' in text(x) for t, x in bl[:toc_idx[0] + 1]) else toc_idx[0]
        intro, toc, body = bl[:start_toc], bl[start_toc:toc_idx[-1] + 1], bl[toc_idx[-1] + 1:]
    else:
        first = next((i for i, (t, x) in enumerate(bl) if t.startswith('h')), len(bl))
        intro, toc, body = bl[:first], [], bl[first:]
    eingang = ['# ' + title]
    for t, x in intro:
        eingang += block_lines(t, x)
    units['000-eingang'] = {'label': 'Eingang', 'kind': 'title', 'text': '\n'.join(eingang) + '\n'}
    if toc:
        ls = []
        for t, x in toc:
            if t == 'p' and is_toc(t, x):
                ls += [text(a) for a in re.findall(r'(?s)<a href="#[^"]*">(.*?)</a>', x) if text(a)]
            else:
                ls += [('## ' if t.startswith('h') else '') + l for l in block_lines(t, x)]
        units['000-inhalt'] = {'label': 'Inhaltsübersicht', 'kind': 'other', 'text': '\n'.join(ls) + '\n'}
        seen.add('000-inhalt')
    pending: list[str] = []
    cur = None
    for t, x in body:
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
        ls = block_lines(t, x)
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
        link = re.search(r'href="(/de/gesetze-\d+)"', tds[0])
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


def in_force(pdf_path: Path, enacted: str) -> tuple[str | None, str]:
    """(day, how) from the GVBl issue: its issue date and the act's Inkrafttreten clause."""
    import pypdf
    r = pypdf.PdfReader(str(pdf_path))
    full = '\n'.join(p.extract_text() or '' for p in r.pages)
    flat = re.sub(r'-\s*\n\s*', '', full)
    flat = re.sub(r'\s+', ' ', flat)
    m = re.search(r'Potsdam, den ' + DATE + r' Nummer', flat) or re.search(r'Nr\. \d+ vom ' + DATE, flat)
    if not m:
        return None, 'no issue date'
    issued = de_date(m)
    y, mo, d = enacted.split('-')
    names = {v: k for k, v in MONTHS.items()}
    vom = f'Vom {int(d)}. {names[int(mo)]} {y}'
    i = flat.find(vom)
    if i < 0:
        return None, f'act "{vom}" not found in the issue'
    nxt = flat.find(' Vom ', i + len(vom))
    seg = flat[i:nxt if nxt > 0 else len(flat)]
    cl = [c for c in re.findall(r'(Dieses Gesetz tritt[^.]*?in Kraft)', seg)]
    if len(cl) != 1:
        return None, f'{len(cl)} Inkrafttreten clauses'
    c = cl[0]
    if re.fullmatch(r'Dieses Gesetz tritt am Tag(e)? nach (der|seiner) Verkündung in Kraft', c) or \
            re.fullmatch(r'Dieses Gesetz tritt am Tag(e)? nach (der|seiner) Verkündigung in Kraft', c):
        day = (dt.date.fromisoformat(issued) + dt.timedelta(days=1)).isoformat()
        return day, f'"{c}"; GVBl. I issued {issued}'
    mm = re.fullmatch(r'Dieses Gesetz tritt (?:am|mit Wirkung vom) ' + DATE + r' in Kraft', c)
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
    first = True
    for n, r in enumerate(linked):
        page = cache_path(r['link'])
        raw = page.read_text(encoding='utf-8', errors='replace')
        units = parse_version(raw, title)
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
                    day, how = in_force(pp, r['enacted'])
                else:
                    how = 'GVBl issue not retrieved'
        elif n == 0 and rows and rows[0]['desc'] and rows[0]['desc'].startswith('Ursprüngliche Fassung'):
            pass
        if not day:
            problems.append(f'{title}: version {r["link"]} ({r["desc"]}) left out: {how}')
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
                    v['credits'][k] = [key]
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


if __name__ == '__main__':
    write_part('10-verfassung', ['/de/gesetze-212792'], country=True, overrides={})
