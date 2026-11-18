# Marx, Das Kapital – EPUB und PDF aus den DTA-Transkriptionen

Baut EPUB-3-Dateien der drei Bände des *Kapital* aus den TEI-P5-Transkriptionen
des [Deutschen Textarchivs](https://www.deutschestextarchiv.de/) (DTA). Ziel ist
eine sorgfältige Leseausgabe für E-Reader:

- Wortlaut und Orthographie wie in der Vorlage, Silbentrennungen aufgelöst.
- Sperrsatz als Kursive.
- Verlinkte Fußnoten, gesammelt in „Anmerkungen“ am Bandende; über Seitengrenzen
  fortgesetzte Fußnoten zusammengeführt.
- Seitenzählung der Vorlage als Seitenmarker und EPUB-Seitenliste.
- Das ursprüngliche Inhaltsverzeichnis, mit diesen Seiten verlinkt.
- Formeln als Text (Brüche, Indizes).
- Was das DTA leer gelassen hat (Formeln, Tabellen, Schemata), nach dem
  Faksimile ergänzt und als Text gesetzt; außer den Umschlägen enthalten die
  Ausgaben keine Bilder.
- Die Druckfehlerlisten der Erstausgaben (Bd. 1 und 3), offensichtliche
  Druckfehler im Griechischen und die Ergebnisse eines Abgleichs aller Bände mit
  der MEGA² (II/5, II/13, II/15) sind eingearbeitet
  (`editions/erstausgaben/errata.py`).
- In jedem Band eine editorische Notiz, die alle Eingriffe auflistet.

Aus demselben Zwischenstand entstehen PDFs im Buchformat 13,5 × 21 cm (LuaLaTeX,
KOMA-Script, Crimson Pro, Griechisch in Gentium Book): Fußnoten am Seitenende,
die Seitenzahlen der Erstausgabe am Rand, das ursprüngliche Inhaltsverzeichnis
mit den Seiten der neuen Ausgabe. Bd. 3 ergibt wie die Erstausgabe zwei Bände;
Bd. 1 ist für den Druck nach dem dritten Kapitel in zwei Teile mit
durchlaufender Seitenzählung geteilt.

## Quellen

Textgrundlage (Edition `erstausgaben`) sind die DTA-Transkriptionen der
Erstausgaben in der TEI-Fassung vom 28.02.2025. Sie liegen unverändert unter
`editions/erstausgaben/sources/`, Prüfsummen in `SHA256SUMS`.

| Band | Ausgabe                                   | DTA                       |
|------|-------------------------------------------|---------------------------|
| 1    | Hamburg: Meissner 1867                    | [marx_kapital01_1867][]   |
| 2    | Hamburg: Meissner 1885, hg. von F. Engels | [marx_kapital02_1885][]   |
| 3/I  | Hamburg: Meissner 1894, Kapitel I–XXVIII  | [marx_kapital0301_1894][] |
| 3/II | Hamburg: Meissner 1894, Kapitel XXIX–LII  | [marx_kapital0302_1894][] |

[marx_kapital01_1867]: https://www.deutschestextarchiv.de/book/show/marx_kapital01_1867
[marx_kapital02_1885]: https://www.deutschestextarchiv.de/book/show/marx_kapital02_1885
[marx_kapital0301_1894]: https://www.deutschestextarchiv.de/book/show/marx_kapital0301_1894
[marx_kapital0302_1894]: https://www.deutschestextarchiv.de/book/show/marx_kapital0302_1894

- **XML:** `https://www.deutschestextarchiv.de/book/download_xml/<id>`. Die
  Seite verlangt JavaScript, also im Browser laden. Wer die Quellen
  aktualisiert, sollte danach `SHA256SUMS` erneuern und den Build prüfen:
  `raw_fixes` brechen absichtlich ab, wenn ihr Suchtext nicht mehr genau einmal
  vorkommt.
- **Faksimiles:**
  `https://www.deutschestextarchiv.de/media/images/<id>/<id>_<NNNN>_1600px.jpg`.
  Die Exemplare stammen aus der Staatsbibliothek zu Berlin – Preußischer
  Kulturbesitz.
- **Lizenz:** siehe [unten](#lizenz).

## Nutzung

Voraussetzungen: Python 3 mit `lxml` (`pip install -r requirements.txt`). Für
`make check` zusätzlich [EPUBCheck](https://www.w3.org/publishing/epubcheck/),
z. B. `pip install epubcheck` (braucht Java). Ein anderer Aufruf geht über
`EPUBCHECK`, etwa mit dem Debian-Paket:
`make check EPUBCHECK='java -jar /usr/share/java/epubcheck.jar'`.

GitHub Actions bauen und prüfen bei jedem Push alle EPUBs und bauen die PDFs
(`ci.yml`). Ein Tag der Form `X.Y.Z` erzeugt ein Release mit den EPUBs als
`marx-kapital-<band>-<jahr>[-modern].epub` und den PDFs als
`marx-kapital-<band>[.<teil>]-<jahr>[-modern].pdf` (`release.yml`).

```sh
make                 # build/erstausgaben/kapital-{1,2,3}.epub
make VARIANT=modern  # build/erstausgaben-modern/…: heutige Rechtschreibung
make BANDS=3         # nur Band 3
make check           # EPUBCheck über alle Bände
```

PDFs:

```sh
make pdf                 # build/erstausgaben/kapital-{1-1,1-2,2,3-1,3-2}.pdf
make pdf VARIANT=modern
```

Dafür braucht es LuaLaTeX mit KOMA-Script, `realscripts` und den deutschen und
griechischen Trennmustern; die Schriften Crimson Pro und Gentium Book liegen
unter `latex/fonts/` (SIL OFL). Unter Debian/Ubuntu:

```sh
apt install texlive-luatex texlive-latex-recommended texlive-xetex \
    texlive-lang-german texlive-lang-greek
```

`tei2tex.py` schreibt die LaTeX-Quelle nach `build/<edition>/tex/`; die Präambel
liegt in `latex/praeambel.tex`.

Direkt aufgerufen:

```sh
python3 tei2epub.py 1 "Marx - Das Kapital I (1867).epub"
python3 tei2epub.py -e erstausgaben -v <variante> 2 out.epub
```

Die eingecheckten Umschläge neu erzeugen:

```sh
make covers
```

Das braucht Node.js und einmalig `cd tools && npm ci && npx playwright install
chromium`.

### Reproduzierbarkeit

Mit gesetztem `SOURCE_DATE_EPOCH` sind die EPUBs bitgenau reproduzierbar:
Erstelldatum in der Notiz, `dcterms:modified` und Zeitstempel im ZIP. Das
Makefile setzt die Variable in einem Git-Checkout auf die Zeit des letzten
Commits. Die Buch-ID ist eine UUIDv5 aus Edition, Band und Varianten.

## Aufbau

```
tei2epub.py              Konverter TEI → EPUB (allgemein, ohne Banddaten)
tei2tex.py               LaTeX aus dem XHTML-Zwischenstand von tei2epub.py
tables.py                abgeschriebene Tabellen: Textnotation → TEI
kapital.css              Stylesheet aller Bände
latex/praeambel.tex      Präambel der PDFs
latex/fonts/             Crimson Pro (variabel) und Gentium Book, SIL OFL
editions/<edition>/      eine Textgrundlage
  __init__.py            Bände und Teile (VOLUMES): Quellen, Korrekturen,
                         Formeln, Tabellen, Texte der Notiz
  sources/               TEI-Dateien + SHA256SUMS
  tables/<teil>/         abgeschriebene Tabellen (tab-*.txt)
  covers/, covers.json   Umschläge und ihre Texte
  errata.py              Textkorrekturen (Druckfehler, Erfassungsfehler)
  sperrsatz.py           Erfassungsfehler im Sperrsatz
  notes.py               nicht transkribierte Fußnoten aus Tabellen
variants/                optionale Textbearbeitungen (Orthographie), s. unten
tools/                   Umschläge, Wortliste der Variante modern
experiments/             abgebrochener Pilot: Bd. 1 nach der 4. Auflage aus
  vierte-auflage/        Scan + OCR (siehe dortige README)
```

### Konfiguration eines Teils (Auszug)

- `raw_fixes`: Ersetzungen im XML-Text vor dem Parsen. Jeder Suchtext muss genau
  einmal vorkommen.
- `raw_hook`, `struct_hook`: Funktionen für größere Eingriffe am Text bzw. Baum,
  z. B. falsch verschachtelte Kapitel.
- `formulas`: Ersatz für die leeren `<formula/>`, in Dokumentreihenfolge.
  - Ein TeX-Teilmenge-String (`\frac`, `_`/`^`, `{A \atop B}`, `\nt{1}{W}`
    usw.).
  - `!` am Anfang setzt die Formel abgesetzt, nachfolgende Satzzeichen wandern
    mit.
  - `\braced{^tu _ab _c}{G – W …~ :a | P :ta | …}` setzt Text unter
    übereinandergreifende Klammern: die erste Angabe nennt die Klammern je Zeile
    über (`^`) und unter (`_`) dem Text, die nächste zuerst; jedes durch `|`
    getrennte Stück nennt nach `:` die Klammern, die es überspannen. Im PDF
    stehen geschweifte Klammern, im EPUB eckige.
- `tables`: IDs der leeren `<table>`, in Dokumentreihenfolge. Zu jeder ID gehört
  die Abschrift `tables/<teil>/tab-<ID>.txt` (siehe unten); fehlt sie, steht ein
  Hinweis mit Link auf das Faksimile.
- `table_notes`: Fußnoten, deren Marken in einer leeren Tabelle stehen und die
  das DTA deshalb nicht erfasst hat; Schlüssel ist die Tabellen-ID (Bd. 1:
  `notes.py`).
- `prefix`, `idp`: Präfix der Seitenzahlen und Seiten-IDs, wenn ein Band aus
  mehreren Teilen besteht (Bd. 3: `I/`, `II/`).
- `toc_fixes`, `toc_skip`, `toc_title`: Korrekturen fürs Inhaltsverzeichnis.
- `marks_after_stop`: Fußnotenzeichen, die der Druck vor Satzzeichen und
  schließende Anführungszeichen setzt, dahinter stellen.
- `formula_note` (dazu `formula_note_epub`), `text_table_note`: Ergänzungen der
  editorischen Notiz zu Formeln und Tabellen.

Auf Bandebene:

- `corrections`, `structure` (dazu `structure_epub`, `structure_pdf`),
  `factual_note`, `emphasis_note` und `pages_note` (dazu `pages_note_pdf`),
  `footnote_note` für die Abschnitte der Notiz.
- `print_split`: teilt einen Band für den Druck in zwei PDFs mit durchlaufender
  Seitenzählung. `at` nennt die erste Datei des zweiten Teils, `move` einen
  Abschnitt, der ans Ende des ersten Teils vorgezogen wird, `front` den
  Vorspann, den der zweite Teil wiederholt.

### Satzdetails

Was die editorische Notiz nur zusammenfasst:

- **Silbentrennung:** Ein Trennstrich am Zeilenende bleibt als Bindestrich
  stehen, wenn das Folgewort groß beginnt, eine Konjunktion folgt („Lohn- und
  Preisbewegung“) oder die verbundene Form im Band sonst mit Bindestrich
  vorkommt. Alle anderen Trennungen werden aufgelöst. Die Zählung steht in der
  Ausgabe von `tei2epub.py`.
- **Leerzeichen:** Innerhalb von Abkürzungen (z. B., u. s. w.) und zwischen Zahl
  und £, ℔ oder % stehen schmale geschützte Leerzeichen (U+2009 in `span.nobr`,
  weil manche Reader U+202F nicht kennen), zwischen Zahl und Einheit sowie vor
  Seitenzahlen geschützte Leerzeichen.
- **Auslassungspunkte:** Folgen von drei bis sechs gesperrten Punkten werden
  „…“, mit geschütztem Leerzeichen am vorigen Wort; ein Punkt dicht am Wort
  bleibt als Satzpunkt („ausbieten. … Wir“). Längere Folgen und solche vor einer
  Zahl sind Füllpunkte in Aufstellungen und bleiben, nur ohne Umbruch.
- **Griechisch** steht aufrecht, auch wo der Druck es kursiv setzt.
- **Formeln** (Bd. 1): Bögen über zusammengehörigen Gliedern wie im Druck statt
  Klammern, die Buchstaben c, v, m mit Klammer über den Beträgen.
- **PDF:** 11 pt auf 13 pt Zeilenabstand, Fußnoten mit sieben Zeilen auf sechs
  Textzeilen; Satzspiegel nach KOMA-Script (`DIV=12`, `BCOR=8mm`). Der Einzug
  der Fußnoten richtet sich nach der längsten Nummer des Bandes. Zu breite
  Tabellen ragen bis 3 mm in den Bundsteg und sonst nach außen, notfalls
  verkleinert.
- **Abgeschriebene Tabellen:** eine Textdatei je Tabelle, aus der EPUB und PDF
  gesetzt werden.

  ```
  @ l n n u              Spaltenarten (optional): l links, c mittig, r rechts,
                         t Fließtext (umbricht), n Zahlen, an der Einerstelle
                         ausgerichtet, u Einheit zur Spalte davor, m Beträge
                         wie „1 sh. 6 d.“, an der ersten Zahl ausgerichtet
  Bodenart | Rente | <   Zellen; „<“ verbindet mit der Zelle links, „^“ mit
  ^ | qrs. | £           der Zelle darüber
  ===                    Ende des Kopfs
  :: Erstes Dorf.        Zeile über alle Spalten
  A | 1 1/3 | £
  B | 25 5/7 {25 2/7} | „
                         berichtigte Angabe, die Lesart des Drucks in Klammern
  ---                    Linie
  Total | 27 | £<note/>  Marke der Fußnote aus `table_notes`
  ```

Zellen enthalten TEI-Auszeichnung (`<lb/>` für den Umbruch im Kopf); `1 1/3` und
`2/9` werden Brüche, `80_c` ein Index, `9 317 629` eine Zahl in Dreiergruppen.
Eine Leerzeile beginnt eine weitere Tabelle an derselben Stelle; so sind
Tabellen geteilt, die für die Zeile eines Lesegeräts zu breit sind. Ohne
`@`-Zeile ergeben sich die Spaltenarten aus dem Inhalt. Linien stehen nur
waagerecht, gestürzte Köpfe des Drucks sind waagerecht gesetzt. Das EPUB wählt
die Schriftgröße nach der geschätzten Breite der Tabelle (`TABLE_SIZES`,
`TABLE_LINE` in `tei2epub.py`); der Bau meldet Tabellen, die auch im kleinsten
Grad zu breit bleiben. Berichtigt ist nur, was der Rechengang oder die
Schreibweise der Tabelle selbst als Druckfehler ausweist; die editorische Notiz
listet diese Stellen aus den Dateien auf.

## Erweitern

**Weitere Textgrundlage**, z. B. die Ausgaben letzter Hand (Bd. 1: 4. Aufl.
1890, Bd. 2: 2. Aufl. 1893, Bd. 3: 1894):

- Neues Verzeichnis `editions/<name>/` mit eigenem `__init__.py` (`VOLUMES`),
  `sources/` und Umschlägen.
- Aufruf mit `make EDITION=<name>`.
- Der Konverter erwartet TEI im DTA-Basisformat. Eine Grundlage, die nicht als
  TEI vorliegt (etwa eine OCR), muss zuerst in diese Form gebracht werden.

**Variante** einer Textgrundlage: ein Modul `variants/<name>.py` mit

```python
# geht in Buch-ID und Ausgabeverzeichnis ein
NAME = 'modern'
# Abschnitt „Rechtschreibung“ der editorischen Notiz
NOTICE = 'Orthographie …'


# TEI-Baum nach Notenzusammenführung und Silbentrennung
def transform(root, part):
    ...


# optional: Titel, Beschreibung, 'principle' der Notiz anpassen
def adjust(vol):
    vol['principle'] = '…'
```

Aufruf mit `make VARIANT=<name>` oder `tei2epub.py -v <name>`. `transform` sieht
den Text nach dem Auflösen der Silbentrennungen, aber vor der Umwandlung in
XHTML.

### Variante `modern`: heutige Rechtschreibung

Orthographie sowie Getrennt- und Zusammenschreibung folgen den heutigen Regeln.
Im Zweifel gilt die heute geläufigste Form. Marx' Wortformen und Satzbau bleiben
(„andren“, „verschiedne“, „geschehn“).

- **Wortliste:** `variants/modern_map.json`, erzeugt aus allen Wortformen der
  drei Bände (braucht `pip install wordfreq`):

  ```sh
  python3 tools/dump_vocab.py build/vocab.json
  python3 tools/mk_modern_map.py build/vocab.json
  ```

  - Regeln wie th→t, aa→a, c→k/z, -iren→-ieren, -niss→-nis, Ae→Ä erzeugen
    Kandidaten. Ein Kandidat gewinnt, wenn er im heutigen Deutsch deutlich
    häufiger ist.
  - Zusammensetzungen werden stückweise umgeschrieben.
  - ß/ss nach festen Stammregeln (groß, Größe, äußer-, -mäßig, schließen …).
  - Einzelentscheidungen stehen in `variants/modern_overrides.py`.
- **Kontextregeln** in `variants/modern.py`:
  - Masse oder Maße (nach „dem“, „im“, „gleichem“ …).
  - Wortgruppen: usw., zugrunde, imstande, aufeinander, stattfinden, solange
    (als Konjunktion) …
  - Kleinschreibung von Pronomen (jeder, alles, andre) außerhalb des
    Satzanfangs.
  - Apostrophe: ins, aufs, Smiths.
- **Nicht angetastet:**
  - Fremdsprachiges. Ein Wort gilt als fremdsprachig, wenn die Mehrzahl der
    Wörter um es herum auf der Fremdwortliste steht.
  - Frühneuhochdeutsche Zitate (Luther), erkannt an typischen Wortformen
    innerhalb von „…“.
- **Protokoll:** Jeder Build schreibt alle Änderungen nach
  `build/modern-changes-<teil>.tsv`.

## Werkzeuge

- `tools/render_covers.js`: Umschläge aus `tools/cover.html` und `covers.json`
  rendern.
- `tools/dump_vocab.py`: alle Wortformen der Bände mit Häufigkeit →
  `build/vocab.json`.
- `tools/mk_modern_map.py`: Wortliste für die Variante `modern` (alt → heute)
  aus `build/vocab.json`.

## Lizenz

- **Code** (Konverter, Stylesheet, Makefile, `latex/praeambel.tex`, `tools/`,
  `variants/`, `experiments/`, die `*.py` unter `editions/`): [MIT](LICENSE),
  © Holger Weiß. Textauszüge aus den Transkriptionen in diesen Dateien
  (Korrekturen, ergänzte Fußnoten) stehen wie diese unter CC BY-SA 4.0.
- **Texte und Bilder** unter `editions/` (Quellen, Tabellen, Umschläge) und die
  erzeugten EPUBs und PDFs:
  [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/deed.de), wie
  die DTA-Transkriptionen. Namensnennung: Textgrundlage
  [Deutsches Textarchiv](https://www.deutschestextarchiv.de/),
  Berlin-Brandenburgische Akademie der Wissenschaften; Bearbeitung Holger Weiß.
  Die editorische Notiz jedes Bandes nennt die Quelle und alle Eingriffe.
- **Schriften** unter `latex/fonts/`:
  [SIL Open Font License 1.1](https://openfontlicense.org), Copyright der
  jeweiligen Projekte, siehe `OFL-CrimsonPro.txt` und `OFL-Gentium.txt` dort.
  Die PDFs betten die Schriften ein; die OFL gilt nicht für Dokumente, die mit
  ihnen gesetzt sind. Die EPUBs betten keine Schriften ein. Die Umschläge sind
  in [Crimson Pro](https://fonts.google.com/specimen/Crimson+Pro) gesetzt
  (`@fontsource/crimson-pro`).
