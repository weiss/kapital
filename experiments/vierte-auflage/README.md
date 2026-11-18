# Experiment: Bd. 1 nach der 4. Auflage (1890)

Abgebrochener Pilot (November 2026). Er sollte klären, ob sich aus einem Scan
der 4. Auflage ein EPUB in derselben Qualität wie aus den DTA-Transkriptionen
bauen lässt. Ergebnis: technisch machbar, aber der Anteil an Sichtprüfung und
Handarbeit ist für den Nutzen zu groß. Der Code ist Versuchsstand, kein
Werkzeug.

## Quellen

- **Scan:**
  [archive.org `bub_gb_Tns7AAAAMAAJ`](https://archive.org/details/bub_gb_Tns7AAAAMAAJ).
  Das ist „Das Kapital. Erster Band. Vierte, durchgesehene Auflage“, Hamburg:
  Meissner 1890, Google-Scan eines Exemplars der University of Michigan, ca.
  2500 px breit. Einzelne Seiten tragen Bleistiftspuren eines Vorbesitzers.
  Druckseite = Leaf − 36, die Vorrede beginnt bei Leaf 9 = S. V.
- **ABBYY-OCR:** `…/bub_gb_Tns7AAAAMAAJ_djvu.xml` von archive.org.
- **Vergleichszeuge MEW 23:** die OCR eines MEW-23-Scans auf archive.org
  (`bwb_T5-CUS-871`, `_djvu.txt`). Sie dient nur dem lokalen Abgleich und gehört
  nicht ins Repo. mlwerke.de ist offline.
- **Lexikon:** die Wortformen der DTA-Erstausgaben aus
  `editions/erstausgaben/sources/`.

## Ablauf

Arbeitsverzeichnis `work/` (oder `$K4WORK`), darin `img/`, `tess/`, `hocr/`,
`djvu.xml`, `mew23.txt`.

1. `fetch_imgs.sh LEAF…`: Seitenbilder von archive.org laden.
2. Tesseract auf jede Seite, ohne Wörterbuch, damit es die alte Orthographie
   nicht „korrigiert“:

   ```sh
   tesseract img/leaf_NNNN.jpg tess/leaf_NNNN -l deu --oem 1 --psm 4 \
       -c load_system_dawg=0 -c load_freq_dawg=0 tsv
   ```

   Dasselbe mit `hocr` nach `hocr/` liefert die x-Höhe pro Zeile.
3. `build_models.py`: ABBYY-Seiten, DTA-Lexikon und das Modell der
   Buchstabenpaar-Abstände für die Sperrung.
4. `repage.py`: Seiten zerlegen (Kopf, Text, Fußnoten über die x-Höhe aus hOCR,
   Randnotizen und Bogensignaturen weg) und die Lesart je Wort wählen
   (`rec.choose`).
5. `assemble.py` / `notes_dp.py`: Absätze, Silbentrennung, Sperrung, Fußnoten zu
   TEI. `to_tei` ist ein unfertiger Entwurf.
6. `mewcheck.py`: Abgleich mit MEW 23 über normalisierte Tokens (th→t, aa→a,
   c/z→k, ss→s …). Übrig bleiben die Stellen für die Sichtprüfung.

## Was funktioniert

- **Lesarten:** Tesseract und ABBYY stimmen bei rund 98 % der Wörter überein.
  Die Lesart wird über Lexikon und Verwechslungspaare gewählt, etwa das
  „ſs“-Glyph als `ss` wie beim DTA, `li`→`h`, `rn`→`m`.
- **Sperrung:** Für jedes Buchstabenpaar wird der übliche Abstand gelernt. Ein
  Wort gilt als gesperrt, wenn seine Abstände im Median um mehr als etwa 0,085
  Zeilenhöhen darüber liegen (`rec.sperr_score`, `assemble.spaced`).
- **Fußnotenbereich:** Er lässt sich zuverlässig über die x-Höhe aus hOCR
  trennen, 34 px im Text gegen 29 px in den Fußnoten.

## Woran es hängt

- **Fußnotenziffern:** Es sind winzige Hochzahlen von etwa 15 px Höhe. Beide
  OCRs lesen sie meist falsch.
  - `notes_dp.py` nummeriert die Fußnotenanfänge per dynamischer Programmierung,
    weil die Nummern pro Abschnitt fortlaufen (Kap. 8 beginnt bei 35).
  - Auf etwa einem Viertel der Seiten bleiben Abweichungen zwischen Verweisen
    und Fußnoten.
- **Abgesetzte Formeln:** Wertform-Gleichungen, Klammerschemata, Tabellen und
  Liniengrafiken müssten wie bei den Tabellen der Erstausgaben von Hand gesetzt
  werden.
- **Sichtprüfung:** Nach dem MEW-Abgleich bleiben etwa 370 Stellen auf gut 120
  Seiten (Vorworte, Kap. 1, Kap. 8). Hochgerechnet auf den Band sind das rund
  2.500.
