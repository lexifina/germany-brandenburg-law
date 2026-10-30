# How this repository was made (Brandenburg)

This file is written by the build on 2026-10-30, the day the source data was retrieved.

## Sources

| Source | Address | Retrieved | Licence |
| --- | --- | --- | --- |
| BRAVORS - Brandenburgisches Vorschriftensystem (Landesregierung Brandenburg): current text, Änderungshistorie and the Lesefassung of each historical version | <https://bravors.brandenburg.de> | 2026-10-30 | § 5 Abs. 1 UrhG: Gesetze, Verordnungen and amtliche Erlasse enjoy no copyright protection. BRAVORS states no terms restricting reuse. |
| Gesetz- und Verordnungsblatt für das Land Brandenburg Teil I (PDF issues on BRAVORS) | <https://bravors.brandenburg.de/de/veroeffentlichungsblaetter_einfache_suche> | 2026-10-30 | § 5 Abs. 1 UrhG. |

Every word of law in this repository comes from these sources. Lexifina reads them and records each act's dated versions, and the laws that made each change, in one corpus file. This repository is built from that file.

## What is in it

| Act | Title | Versions | Span |
| --- | --- | ---: | --- |
| `verfassung` | Verfassung des Landes Brandenburg | 7 | 2004-06-18 to 2022-07-07 |

The build made 7 commits:

| Commits | Kind |
| ---: | --- |
| 1 | first version of an act |
| 6 | one law on its in-force day |
| 0 | changes no amendment note explains, credited to the publisher |

Other counts:
- 0 commits on the branch `zukunft`: laws not yet in force on 2026-10-30.
- 0 commits dated 1 January 1970: in force before 1970, with the real day in their `In-force` trailer.
- 12 laws in the record.
- 13 tags.

## Dates

Each commit is dated at noon (Europe/Berlin) on the day the change took effect. The other dates, enacted and published, are trailers.

When a law gives no date of its own, the default rule applies: Verfassung des Landes Brandenburg Art. 81 Abs. 3: "Jedes Gesetz und jede Rechtsverordnung soll den Tag des Inkrafttretens bestimmen. Fehlt eine solche Bestimmung, so treten sie mit dem vierzehnten Tag nach Ablauf des Tages in Kraft, an dem das Gesetzblatt ausgegeben worden ist." Each version here is dated by the Inkrafttreten clause of the amending act, applied to the issue date of the Gesetz- und Verordnungsblatt that printed it. https://bravors.brandenburg.de/de/gesetze-212792

## How the history is built

`tools/build.py` turns the corpus into this history in one pass: one commit per law, on the day it took effect. The same corpus always gives the same commit hashes. `tools/check_repo.py` reads every version back from git and compares it with the corpus. `tools/on.py` shows the law as it stood on any date. The corpus format is described in `tools/SCHEMA.md`.

- Corpus: sha256 `31836031ace083e785d2aebc15a49784b0c4a898e92e72b1de5713cdca4a86f1` (650729 bytes).
- Builder blob hashes (`git hash-object`): `build.py` `a97ff7ea62c3c7595c5668a297d533da0b74373c`, `check.py` `3e59cb6f05eccb94a9ec14431a7f6781221e83ef`, `on.py` `644a6c0857fbcc72562032b58d57aa113fee0641`.
- Python 3.12.10; git version 2.46.0.windows.1.

## Checks

Not yet run for this build.

No second build of this corpus has been compared yet.

## Decisions made by hand

- The versions are the rows of BRAVORS' "Änderungshistorie" that link a Lesefassung. Amending acts listed before the oldest linked row have no Lesefassung; the oldest one is the oldest version available, credited to the publisher and naming those acts.
- Each later version is credited, for every provision that differs from the version before, to the amending act its history row names.
- Each version is dated by its amending act's Inkrafttreten clause in the Gesetz- und Verordnungsblatt issue the row cites: "am Tag nach der Verkündung" is the day after the issue date; a stated day is that day. A version whose clause is not one of these is left out (listed below).
- One file per Artikel or Paragraph; the Inhaltsübersicht is its own file. Headings of Hauptteile and Abschnitte stand above the first provision under them.
- Left out: Verfassung des Landes Brandenburg: version /de/gesetze-213018 (Präambel, Artikel 22, 62, 65, 74, 77, 78, 81, 87, 94, 96, 97, 109, 112, 114 geändert durch Artikel 1 des Gesetzes vom 7. April 1999) left out: GVBl issue not retrieved

## What AI did and did not do

The scripts that read the sources and build this repository were written by Claude Code running Claude Opus 5.5 (`claude-opus-5-5`) under Lexifina's direction.

No model wrote, translated or corrected legal text. No model runs at build time. Every word of law in this repository comes from the official sources above.

The commit messages are written by `build.py` from the source data.

Model use at data-build time:
- Claude Code (claude-opus-5-5) wrote Lexifina's code and chose the sources. No model output is used as legal text, dates or credits: words come from BRAVORS, dates from the Gesetz- und Verordnungsblatt, credits from BRAVORS' history.
