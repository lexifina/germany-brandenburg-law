# Brandenburg (germany-brandenburg-law) - private

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
  BRAVORS, 404), main f54d83c. Next: 20-gesetze-03 once `pass1 149` is in fetch-gesetze.log (about 1 act a minute).
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
