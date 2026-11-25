<!-- lawwatch: written from data/checks by the check trail; edit the records, not this page -->

# Beobachtung: was gelesen wird und was daraus folgte

[English](README.en.md)

Wie global-law jedes Land beobachtet: [global-law monitoring/](https://github.com/lexifina/global-law/tree/main/monitoring). Diese Seite zeigt dasselbe nur für Brandenburg: jedes Lesen einer amtlichen Quelle, wann, und was daraus folgte (Vorschriften hinzugefügt, geändert und entfernt). Maschinenlesbar in [data/checks/](../data/checks/) (JSON Lines, Schema `lexifina-check/1`), in `git log` als Commits mit `Kind: check` und Monat für Monat in [checks/](checks/).

**Letzte Prüfung:** 2026-11-25 07:38 UTC, BRAVORS (Landesregierung Brandenburg): 67 Adressen gelesen; 1 hinzugefügt, 38 geändert, 1 entfernt; Änderungen gefunden; 573 nicht veröffentlicht, davon 0 ohne Grund.

## Quellen

| Quelle | Ordner | Wie oft | Letzte erfolgreiche Prüfung | Letztes Ergebnis | Stand |
| --- | --- | --- | --- | --- | --- |
| [BRAVORS (Landesregierung Brandenburg)](https://bravors.brandenburg.de) | `<act>/` | täglich | 2026-11-25 07:38 UTC | Änderungen gefunden | beobachtet |

## Die letzten 30 Tage

| Beginn (UTC) | Quelle | Gelesen | Hinzugefügt | Geändert | Entfernt | Nicht veröffentlicht (ohne Grund) | Ergebnis | Commits |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| [2026-11-25 07:15](checks/2026-11.md#de-bravors-20261125t071559z) | bravors | 67 | 1 | 38 | 1 | 573 (0) | Änderungen gefunden | — |
| [2026-11-23 23:49](checks/2026-11.md#de-bravors-20261123t234959z) | bravors | 67 | 0 | 0 | 0 | 573 (0) | keine Änderung | — |
| [2026-11-23 21:12](checks/2026-11.md#de-bravors-20261123t211258z) | bravors | 8 | 0 | 0 | 0 | 0 (0) | die Quelle hat nicht geantwortet | — |

## Selbst prüfen

```
python tools/checktrail.py                      # die letzte Prüfung jeder Quelle
python tools/checktrail.py --day 2026-11-23     # jede Prüfung eines Tages
python tools/checktrail.py --act <id>           # wann eine Vorschrift gesehen und veröffentlicht wurde
git log --grep='^Kind: check' --format='%ci %s'  # die Prüfungen in der Historie
```

Rechtskraft hat nur die amtliche Verkündung; die Texte hier sind Kopien zum Lesen und Suchen.
