<!-- lawwatch: written from data/checks by the check trail; edit the records, not this page -->

# Monitoring: what is read and what came of it

[Deutsch](README.md)

How global-law monitors every country: [global-law monitoring/](https://github.com/lexifina/global-law/tree/main/monitoring). This page is the same for Brandenburg only: every time an official source is read, when, and what came of it (acts added, changed and removed). The machine-readable form is [data/checks/](../data/checks/) (JSON Lines, schema `lexifina-check/1`), in `git log` as `Kind: check` commits, and month by month in [checks/](checks/).

**Last check:** 2026-11-25 07:38 UTC, BRAVORS (Brandenburg state government): 67 addresses read; 1 added, 38 changed, 1 removed; changes found; 573 not published, 0 of them with no reason.

## Sources

| Source | Folders | How often | Last successful check | Last result | State |
| --- | --- | --- | --- | --- | --- |
| [BRAVORS (Brandenburg state government)](https://bravors.brandenburg.de) | `<act>/` | daily | 2026-11-25 07:38 UTC | changes found | watched |

## The last 30 days

| Started (UTC) | Source | Read | Added | Changed | Removed | Not published (no reason) | Result | Commits |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| [2026-11-25 07:15](checks/2026-11.md#de-bravors-20261125t071559z) | bravors | 67 | 1 | 38 | 1 | 573 (0) | changes found | — |
| [2026-11-23 23:49](checks/2026-11.md#de-bravors-20261123t234959z) | bravors | 67 | 0 | 0 | 0 | 573 (0) | no change | — |
| [2026-11-23 21:12](checks/2026-11.md#de-bravors-20261123t211258z) | bravors | 8 | 0 | 0 | 0 | 0 (0) | the source did not answer | — |

## Check it yourself

```
python tools/checktrail.py                      # the latest check of every source
python tools/checktrail.py --day 2026-11-23     # every check of a day
python tools/checktrail.py --act <id>           # when an act was seen and published
git log --grep='^Kind: check' --format='%ci %s'  # the checks in the history
```

Only the official publication has legal force; the texts here are copies for reading and searching.
