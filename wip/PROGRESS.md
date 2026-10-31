# Brandenburg (germany-brandenburg-law) - private

State 2026-10-31 06:45 UTC (gitlaw-scraper-dell, CLAIMED): BbgVerfSchG fix verified and handed to autopush; Verordnungen
fetching.
- BbgVerfSchG: /14 (Art. 9 Gesetz vom 14. Mai 2024, in force 2024-09-01) is an announcement Lesefassung: the /13 text
  plus "Hinweis: Artikel 9 ... tritt am 1. September 2024 in Kraft". The current Lesefassung holds Art. 9 (§ 25) AND
  the Gesetz vom 27. Juni 2024 (Inhaltsübersicht, § 14a, § 30; in force 2024-06-28). BRAVORS orders rows by
  Ausfertigung, not by in-force day. parse.py now: an announcement-only Lesefassung is not a version; the next one is
  split by the history rows' own provision lists (desc_units) into 2024-06-28 (June act's provisions) and 2024-09-01
  (full current text, § 25 credited to Art. 9). Final BbgVerfSchG files = the current text the repo held before
  05:36 (a5cf0f7), all provision files identical.
- Same family fixed: Lesefassungen taking effect the same day as the version before are kept as "same_day" versions
  (BbgPolG/23, LBG/23, OBG/23, BbgBKG/6; this also corrects the next version's credits), BbgBeamtVG/15 (announcement
  only, was dated 2024-09-01 with the pre-change text) removed. Guards: a row recording "außer Kraft" is never dated by
  an Inkrafttreten clause (BbgSGG/BbgVwGG/BbgFGG current: Art. 4 Satz 2, expiry 31 July 2016 - left out); same-day
  and split versions need an unstaggered Inkrafttreten Artikel (staggered()). HG 2023/2024 current (retroactive
  "mit Wirkung vom 1. Januar 2024", enacted 25 July 2024) stays left out, reason reworded.
- Verified (.tmp/): parse into a staging corpus.d; per-act JSON: 6 acts changed, 264 identical; check_letters 563
  versions 0 mismatches (composed version checked file by file); local build before/after: check.py 0/0/0, audit [];
  local "before" build == published main 54237b1 in all 270 act folders; after: 264 act trees identical, 258 commit
  lists identical (the other 6: multi-act commits whose message named the corrected BbgBKG/BbgVerfSchG/BbgBeamtVG
  lines; their own files, dates and authors unchanged). 559 -> 563 versions, 569 -> 574 commits.
- FINDING, not fixed (would change published acts): in_force() reads only the first "Dieses Gesetz tritt ... in Kraft"
  sentence; when the amending act's Inkrafttreten Artikel staggers parts (e.g. AbgG/7: Art. 2 Nr. 1-4 from 2019-01-01,
  Nr. 5 retroactive 2014-10-08, published as 2018-03-09) the version can be misdated. .tmp/stagger.py lists 117 dated
  versions whose amending act has more than one in/außer-Kraft sentence (many harmless: repeal of other acts, or the
  staggered part is another Artikel). Needs a decision + a verified rebuild.
- Verordnungen: fetch.py verordnungen (PID 7104, BelowNormal, restarted 05:49 UTC; 13412 stopped by me), 1,250 index
  entries, each in full in index order, >= 21 s per request (about 1.5 min an act, ~31 h). Parts 30-verordnungen-NN of
  50 index entries: `PARSE_OUT=<stage>/corpus.d python -X utf8 parse.py 30-verordnungen-NN` (never written unless
  named; written once every act in it is fully fetched: ready_full via requests.jsonl), check_letters, verify, then
  copy into corpus.d + .PUBLISH. Verordnungen dated like the Gesetze ("Diese Verordnung tritt ..."; GVBl Teil II).

Earlier state (superseded):

State 2026-10-31 05:37 UTC (gitlaw-scraper-dell): Gesetze PUBLISHED, claim deleted. Fetch 33368 finished pass 1 and
pass 2 (all 445 Gesetze, older Lesefassungen and their GVBl issues). All nine parts 20-gesetze-01..09 parsed together
(01-03 rebuilt with the older versions under the verified-rebuild standing yes), check_letters 0 differences, local
build 270 acts / 559 versions (269 Gesetze, 552 versions + Verfassung 7), check.py 0/0/0, audit_push [] -> main
54237b1 (verified rebuild a5cf0f7 -> 54237b1, old tip archived, 789 tags). Verfassung part kept as published.
Changes 2026-10-31: check_letters.py numbers <ol> inside-out with <ul> bullets resolved first (an outer <ol type=a>
had numbered nested bullets: 8 false mismatches); parse.py LETTERS_DIFFER leaves out 9 versions whose parsed text
differs from the page (malformed nested <ol start> lists: bbgrig/2, bbguvpg 213730,/6,/7,current, Haushaltsgesetz
212545; text order at the Inhaltsübersicht: bbgpolg_2013_1/12, bbgsvvollzg/3 and current); harmonise() gives one law
entry per key across parts and renames shared slugs ("staatsvertrag" x3 -> BRAVORS document names).
Known: BbgVerfSchG's current Lesefassung (in force 2024-06-28) is not after /14 (2024-09-01) and is left out, so that
act ends at the 2024-09-01 version. README updated (269 of 445; left-out rules).
Next (not claimed): Verordnungen.

Earlier state (superseded):

State 2026-10-30 (gitlaw-scraper-dell):
- Source BRAVORS (bravors.brandenburg.de), robots Crawl-delay 20 -> fetch.py keeps >= 21 s between requests.
- Fetch PID 33368: `python -X utf8 fetch.py gesetze > fetch-gesetze.log` (started 10:36 UTC, cache .cache/pages).
  445 Gesetze (.cache/gesetze.txt). Pass 1: each act's page, ?history and the newest GVBl issue (about 1 act a
  minute); pass 2 (after all 445): the older Lesefassungen and their GVBl issues. Restart with the same command if it
  dies (cached pages are skipped).
- Parts: `python -X utf8 parse.py 20-gesetze-NN` writes only that part (published parts are never rewritten), then
  `python -X utf8 check_letters.py corpus.d/20-gesetze-NN.json`, local build + check.py, audit_push, then
  corpus.d/20-gesetze-NN.PUBLISH (autopush_dell publishes main).
- Published: 10-verfassung (7 versions); 20-gesetze-01 (acts 1-50: 28 acts, current Lesefassung only, 22 left out),
  main 045d291; 20-gesetze-02 (acts 51-100: 15 acts, 35 left out, 22 of them because the 1990s GVBl issue is not on
  BRAVORS, 404), main f54d83c; 20-gesetze-03 (acts 101-150: 29 acts, 21 left out), main 6b0ce6b (12:59 UTC). Next: 20-gesetze-04 once
  `pass1 199` is in fetch-gesetze.log (about 1 act a minute), then 05-09 the same way.
- check_letters.py fix 2026-10-30: lists written <OL>/<LI> (upper case) are numbered too (one false mismatch,
  GräbVersammlG, in part 03; parts 01-02 and the Verfassung unchanged, 0 mismatches).
- Left-out reasons are conservative on purpose: split or conditional Inkrafttreten clauses ("vorbehaltlich",
  treaty-dependent days) and Mantelgesetze with several acts signed the same day are not guessed.
- Append-only rule: parts from pass 1 hold only each act's newest version, and later parts interleave older dates,
  so each new part is a law-history rewrite of main. That falls under Alan's standing yes for verified rebuilds of
  repos we own (autopush: "main verified rebuild ... lease, old tip archived"). Older versions from pass 2 for acts
  already in a published part would need that part rewritten: not done; decide when pass 2 has run.
- parse.py fixes 2026-10-30 (no change to the published Verfassung, verified): words inside an <ol> outside any <li>
  kept; text after a nested list kept in order; lists styled lower-alpha numbered a), b); an empty anchor block no
  longer moves the headings before it into the Eingang; one label per amending law ("Gesetz vom ...", not
  "Artikel N des Gesetzes"), and a law an earlier published part holds keeps that part's entry.
- 2015 amendment of the Verfassung, "mit dem Beginn der 7. Wahlperiode": 2019-09-25 is right. Verfassung Art. 62
  Abs. 4: the new Landtag meets within 30 days of its election and with that the previous Wahlperiode ends; the 7.
  Landtag (elected 1 September 2019) held its constituent sitting on 25 September 2019 (Landtag Brandenburg agenda
  and press releases).
