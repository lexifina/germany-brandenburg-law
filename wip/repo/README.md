# Brandenburg: law history in git

The law of the Land Brandenburg as a git history: one file per Artikel or Paragraph, one paragraph per line, one
commit per amending act on the day it came into force. `git blame` names the act behind each change; `git log`
lists every change; picking a date gives the text in force that day. The text is German.

It follows the shared design of [lexifina/global-law](https://github.com/lexifina/global-law).

## What this repository holds

Each reading version (Lesefassung) that BRAVORS keeps in an act's "Änderungshistorie", from the oldest to the
current one. Amending acts older than the oldest kept Lesefassung are named in the first commit, which is credited
to the publisher as "oldest version available".

| Folder | Act | History |
| --- | --- | --- |
| `verfassung/` | Verfassung des Landes Brandenburg vom 20. August 1992 | each Lesefassung since the amendment of 7 April 1999 |
| other folders | Brandenburg Gesetze, one folder per act (named by its abbreviation) | each Lesefassung BRAVORS holds |

269 of the 445 Gesetze in BRAVORS' list are here, with 552 versions. A version is left out when its date cannot be read
from the Gesetz- und Verordnungsblatt without guessing (no issue on BRAVORS, no Inkrafttreten clause, a split or
conditional clause, or several acts signed the same day), or when its text as parsed differs from the page; an act
with no version left is left out. Each one is listed under "Decisions made by hand" in REPRODUCE.md. Verordnungen and
Verwaltungsvorschriften are not included yet.

## Source

[BRAVORS - Brandenburgisches Vorschriftensystem](https://bravors.brandenburg.de) of the Landesregierung
Brandenburg: the current text, the change history and the historical reading versions of each act. The in-force day
of each version is read from the issue of the Gesetz- und Verordnungsblatt für das Land Brandenburg Teil I that the
history cites. The sha256 of each page a version was read from is in `data/versions.json`.

## Dates

Each version is dated by the Inkrafttreten clause of the act that made it, applied to the issue date of the Gesetz-
und Verordnungsblatt: "am Tag nach der Verkündung" is the day after the issue date, a stated day is that day. A
version whose clause is more complicated is left out and listed in `REPRODUCE.md`. Commits are at noon in Potsdam.
Versions in force only after the retrieval date (30 October 2026) are on the `zukunft` branch.

## What "author" means

Every provision that differs from the version before is credited to the amending act the history row names; that act
is the commit's author, with an e-mail address that cannot exist. The committer is always Lexifina.

## How it is built

Each Lesefassung becomes one file per provision; the Inhaltsübersicht is its own file. Headings of Hauptteile,
Abschnitte and Teile stand above the first provision under them. Tables are one line per row, cells separated by
` | `.

## How it is checked

Every version is read back from git on the day it took effect and on the day before (`tools/check_repo.py`) and must
match the corpus; an independent letters-and-digits comparison of every version against its source page must show
no difference. Results are in `REPRODUCE.md`.

## Limits

History only as far back as BRAVORS keeps Lesefassungen. Anlagen are not included. The text is not the official
version: only the Gesetz- und Verordnungsblatt is authoritative.

## Licence

See [LICENSE](LICENSE): the law texts are free of copyright (§ 5 Abs. 1 UrhG). Quelle: BRAVORS -
Brandenburgisches Vorschriftensystem, Landesregierung Brandenburg.
