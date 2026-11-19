# Das Kapital – Erstausgaben als EPUB und PDF

Die drei Bände des *Kapital* im Text ihrer Erstausgaben (1867, 1885, 1894), nach
den Transkriptionen des
[Deutschen Textarchivs](https://www.deutschestextarchiv.de/) (DTA): als EPUB für
E-Reader und als PDF im Buchformat 13,5 × 21 cm, jeweils in der Schreibung der
Vorlage und in heutiger Rechtschreibung.

## Herunterladen

In der Schreibung der Vorlage:

- Band I (1867): [EPUB][o1e], [PDF Teil 1][o1.1p], [PDF Teil 2][o1.2p]
- Band II (1885): [EPUB][o2e], [PDF][o2p]
- Band III (1894): [EPUB][o3e], [PDF Teil 1][o3.1p], [PDF Teil 2][o3.2p]

In heutiger Rechtschreibung:

- Band I (1867): [EPUB][m1e], [PDF Teil 1][m1.1p], [PDF Teil 2][m1.2p]
- Band II (1885): [EPUB][m2e], [PDF][m2p]
- Band III (1894): [EPUB][m3e], [PDF Teil 1][m3.1p], [PDF Teil 2][m3.2p]

[o1e]: https://github.com/weiss/kapital/releases/latest/download/marx-kapital-1-1867.epub
[o1.1p]: https://github.com/weiss/kapital/releases/latest/download/marx-kapital-1.1-1867.pdf
[o1.2p]: https://github.com/weiss/kapital/releases/latest/download/marx-kapital-1.2-1867.pdf
[o2e]: https://github.com/weiss/kapital/releases/latest/download/marx-kapital-2-1885.epub
[o2p]: https://github.com/weiss/kapital/releases/latest/download/marx-kapital-2-1885.pdf
[o3e]: https://github.com/weiss/kapital/releases/latest/download/marx-kapital-3-1894.epub
[o3.1p]: https://github.com/weiss/kapital/releases/latest/download/marx-kapital-3.1-1894.pdf
[o3.2p]: https://github.com/weiss/kapital/releases/latest/download/marx-kapital-3.2-1894.pdf
[m1e]: https://github.com/weiss/kapital/releases/latest/download/marx-kapital-1-1867-modern.epub
[m1.1p]: https://github.com/weiss/kapital/releases/latest/download/marx-kapital-1.1-1867-modern.pdf
[m1.2p]: https://github.com/weiss/kapital/releases/latest/download/marx-kapital-1.2-1867-modern.pdf
[m2e]: https://github.com/weiss/kapital/releases/latest/download/marx-kapital-2-1885-modern.epub
[m2p]: https://github.com/weiss/kapital/releases/latest/download/marx-kapital-2-1885-modern.pdf
[m3e]: https://github.com/weiss/kapital/releases/latest/download/marx-kapital-3-1894-modern.epub
[m3.1p]: https://github.com/weiss/kapital/releases/latest/download/marx-kapital-3.1-1894-modern.pdf
[m3.2p]: https://github.com/weiss/kapital/releases/latest/download/marx-kapital-3.2-1894-modern.pdf

## Die Ausgabe

- **Text:** Wortlaut und Zeichensetzung wie in der Vorlage. Die
  Druckfehlerlisten der Erstausgaben (Bd. 1 und 3) und die Ergebnisse eines
  Abgleichs aller Bände mit der MEGA² (II/5, II/13, II/15) sind eingearbeitet.
- **Zwei Fassungen:** in der Orthographie der Vorlage und in heutiger
  Rechtschreibung. Diese folgt in Orthographie sowie Getrennt- und
  Zusammenschreibung den heutigen Regeln, im Zweifel der heute geläufigsten
  Form; Marx' Wortformen und Satzbau bleiben („andren“, „verschiedne“,
  „geschehn“).
- **Lücken der Transkription:** Was das DTA leer gelassen hat (Formeln,
  Tabellen, Schemata), ist nach dem Faksimile ergänzt und als Text gesetzt.
- **Fußnoten** sind verlinkt (im EPUB) bzw. stehen am Seitenende (im PDF), mit
  der Zählung der Vorlage.
- **Seitenzahlen der Erstausgabe** stehen am Rand; das ursprüngliche
  Inhaltsverzeichnis ist erhalten und verweist auf die Seiten dieser Ausgabe.
- **Editorische Notiz:** Jeder Band nennt am Ende seine Quelle und alle
  Eingriffe.
- **PDF:** gesetzt mit LuaLaTeX in Crimson Pro, Griechisch in Gentium Book.
  Band I ist nach dem dritten Kapitel in zwei Teile mit durchlaufender
  Seitenzählung geteilt, Band III wie in der Erstausgabe.

## Quellen

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

Grundlage ist die TEI-Fassung der Transkriptionen vom 28.02.2025. Die
gedruckten Exemplare stammen aus der Staatsbibliothek zu Berlin – Preußischer
Kulturbesitz.

## Fehler melden

Hinweise auf Fehler im Text oder im Satz gern als
[Issue](https://github.com/weiss/kapital/issues) oder an
holger+kapital@weiss-berlin.de.

## Selbst bauen

Wie die Dateien entstehen und wie sie sich selbst bauen oder erweitern lassen,
beschreibt [DEVELOPMENT.md](DEVELOPMENT.md).

## Lizenz

- **Code** (Konverter, Stylesheet, Makefile, `latex/praeambel.tex`, `tools/`,
  `variants/`, `experiments/`, die `*.py` unter `editions/`): [MIT](LICENSE).
  Textauszüge aus den Transkriptionen in diesen Dateien (Korrekturen, ergänzte
  Fußnoten) stehen wie diese unter CC BY-SA 4.0.
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
  ihnen gesetzt sind. Die EPUBs betten keine Schriften ein.
