# Selbst bauen und erweitern

## Bauen

Voraussetzungen: Python 3 mit `lxml` (`pip install -r requirements.txt`). Für
`make check` zusätzlich [EPUBCheck](https://www.w3.org/publishing/epubcheck/),
z. B. `pip install epubcheck` (braucht Java). Ein anderer Aufruf geht über
`EPUBCHECK`, etwa mit dem Debian-Paket:
`make check EPUBCHECK='java -jar /usr/share/java/epubcheck.jar'`.

GitHub Actions bauen und prüfen bei jedem Push alle EPUBs und bauen die PDFs
(`ci.yml`). Ein Tag der Form `X.Y.Z` erzeugt ein Release mit den EPUBs als
`marx-kapital-<band>-<jahr>[-modern].epub` und den PDFs als
`marx-kapital-<band>[.<teil>]-<jahr>[-modern].pdf` (`release.yml`).

Die Version kommt aus `git describe --tags --dirty` (oder `VERSION=…`) und
steht mit dem Datum im Impressum der PDFs, unter der editorischen Notiz und in
den EPUB-Metadaten (`schema:version`). Versionen 0.Y.Z sind Vorabfassungen. Ab
1.0.0 zählt Z reine Korrekturen, Y weitergehende Überarbeitungen; ein neues X
steht für eine wesentlich geänderte Edition.

```sh
make                 # build/erstausgaben/kapital-{1,2,3}.epub
make VARIANT=modern  # build/erstausgaben-modern/…: heutige Rechtschreibung
make BANDS=3         # nur Band 3
make check           # EPUBCheck über alle Bände, auch Warnungen sind Fehler
```

PDFs:

```sh
make pdf                 # build/erstausgaben/kapital-{1-1,1-2,2,3-1,3-2}.pdf
make pdf VARIANT=modern
```

Dafür braucht es LuaLaTeX; die Schriften liegen in `latex/fonts/`. Unter
Debian/Ubuntu (`texlive-xetex` nur für das Paket `realscripts`):

```sh
apt install texlive-luatex texlive-latex-recommended texlive-xetex \
    texlive-lang-german texlive-lang-greek
```

`make pdf` bricht ab, wenn einer Schrift eine Glyphe fehlt, und schlägt fehl,
wenn das Log eine zu breite Zeile (`Overfull \hbox`) oder eine Warnung von
LaTeX, Klasse oder Paket enthält (`tools/check_tex_log.py`). Ausgenommen sind
zwei Hinweise neuerer babel-Versionen auf `polutonikogreek` und `german`: Beide
Namen sind gewollt, sie laden polytones Griechisch und die Schreibung von 1901
über die `ldf`-Dateien, ohne Trennung und Satz zu ändern.

Direkt aufgerufen:

```sh
python3 tei2epub.py 1 "Marx - Das Kapital I (1867).epub"
python3 tei2epub.py -e erstausgaben -v <variante> 2 out.epub
```

Die eingecheckten Umschläge erzeugt `make covers` neu; das braucht Node.js und
einmalig `cd tools && npm ci && npx playwright install chromium`.

### Reproduzierbarkeit

Mit gesetztem `SOURCE_DATE_EPOCH` sind die EPUBs bitgenau reproduzierbar:
Erstelldatum in der Notiz, `dcterms:modified` und Zeitstempel im ZIP. Das
Makefile setzt die Variable in einem Git-Checkout auf die Zeit des letzten
Commits. Die Buch-ID ist eine UUIDv5 aus Edition, Band und Varianten.

### Quellen

Die DTA-Transkriptionen (Edition `erstausgaben`) liegen unverändert unter
`editions/erstausgaben/sources/`, Prüfsummen in `SHA256SUMS`. Textkorrekturen
(Druckfehlerlisten, MEGA-Abgleich, Erfassungsfehler) stehen in
`editions/erstausgaben/errata.py` und `sperrsatz.py`.

- **Faksimiles:**
  `https://www.deutschestextarchiv.de/media/images/<id>/<id>_<NNNN>_1600px.jpg`.
- **XML:** `https://www.deutschestextarchiv.de/book/download_xml/<id>`. Die
  Seite verlangt JavaScript, also im Browser laden. Wer die Quellen
  aktualisiert, sollte danach `SHA256SUMS` erneuern und den Build prüfen:
  `raw_fixes` brechen absichtlich ab, wenn ihr Suchtext nicht mehr genau einmal
  vorkommt.

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
  Textzeilen; Format 14 × 21,6 cm („Digest“), Satzspiegel nach KOMA-Script
  (`DIV=calc`, `BCOR=16mm`). Der Einzug der Fußnoten richtet sich nach der
  längsten Nummer des Bandes. Zu breite Tabellen ragen bis 3 mm in den Bundsteg
  und sonst nach außen, notfalls verkleinert.
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
  drei Bände (braucht `pip install wordfreq spylls` und das deutsche
  Wörterbuch `de_DE_frami.dic`/`.aff` aus
  [LibreOffice/dictionaries](https://github.com/LibreOffice/dictionaries/tree/master/de)
  in `build/`):

  ```sh
  python3 tools/dump_vocab.py build/vocab.json
  python3 tools/mk_modern_map.py build/vocab.json
  ```

  - Regeln wie th→t, aa→a, c→k/z, -iren→-ieren, -niss→-nis, Ae→Ä erzeugen
    Kandidaten. Ein Kandidat gewinnt, wenn er im heutigen Deutsch deutlich
    häufiger ist; kennt wordfreq keine der Formen, entscheidet das
    Wörterbuch (die alte Form darf es nicht kennen, die neue muss es).
  - Zusammensetzungen werden stückweise umgeschrieben.
  - ß/ss nach festen Stammregeln (groß, Größe, äußer-, -mäßig, schließen …).
  - Einzelentscheidungen stehen in `variants/modern_overrides.py`, dazu
    Ersetzungsmuster für Wortfamilien, die die Regeln nicht erfassen (Brod,
    Frohn, allmälig, selbständig).
- **Kontextregeln** in `variants/modern.py`:
  - Masse oder Maße (nach „dem“, „im“, „gleichem“ …).
  - Wortgruppen: usw., zugrunde, imstande, aufeinander, stattfinden, solange
    und soweit (als Konjunktion), so viel, ebenso wenig, jedes Mal, umso,
    infolge, sozusagen, aufrechterhalten, wiederherstellen, glücklicherweise
    … – Duden-Empfehlung, wo beides erlaubt ist.
  - Substantivierungen: etwas Neues, das Doppelte, im Allgemeinen, aufs
    Höchste.
  - Kommas vor Nebensätzen (dass, ob, wenn, weil, wo, worin …), vor
    Infinitivgruppen mit um/ohne … zu, vor „sondern“ und „d. h.“; nicht nach
    Konjunktionen und Partikeln (und dass, ohne dass, je nachdem).
  - Adjektive aus Personennamen: hegelsche, ricardoschen.
  - Kleinschreibung von Pronomen und Zahlwörtern (jeder, alles, andre,
    viele, wenige) außerhalb des Satzanfangs, von Tageszeiten (nachts,
    morgens).
  - Apostrophe: ins, aufs, Smiths.
  - Die Regeln sehen eine Zeile der Vorlage und, über Zeilen- und
    Seitenumbrüche hinweg, die folgende; über Auszeichnungen (Sperrung,
    Indizes) sehen sie nicht hinweg.
- **Einzelstellen** in `variants/modern_spots.py`, jede einzeln geprüft:
  `SPELLINGS` (Schreibungen, die keine Regel trifft), `COMMAS`
  (Kommas vor Nebensätzen und Infinitivgruppen) als genaue Ersetzungen,
  `EDGES` als reguläre Ausdrücke für Stellen an einer Auszeichnung. Ob jede
  Ersetzung greift, zeigt das Protokoll.
- **Nicht angetastet:**
  - Fremdsprachiges. Ein Wort gilt als fremdsprachig, wenn die Mehrzahl der
    Wörter um es herum auf der Fremdwortliste steht.
  - Frühneuhochdeutsche Zitate (Luther), erkannt an typischen Wortformen
    innerhalb von „…“.
- **Protokoll:** Jeder Build schreibt alle Änderungen nach
  `build/modern-changes-<teil>.tsv`.
