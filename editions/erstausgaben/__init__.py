"""Erstausgaben nach dem Deutschen Textarchiv: Bd. 1 (1867), Bd. 2 (1885), Bd. 3
(1894, zwei Theile)."""

import re
from pathlib import Path

from lxml import etree

from . import errata, notes, sperrsatz

TEI = '{http://www.tei-c.org/ns/1.0}'
HERE = Path(__file__).parent


def _head(div):
    h = div.find(TEI + 'head')
    return ' '.join(''.join(h.itertext()).split()) if h is not None else ''


# ---------------------------------------------------------------- Band 1 (1867)


def k1_raw(s):
    m = re.search(
        r'<note place="foot" n="137\)"><hi rendition="#sup">147</hi>\)'
        r' (.*?)</note>',
        s,
        re.S,
    )
    s = s[: m.start()] + s[m.end() :]
    anchor = '<hi rendition="#sup">147</hi>)'
    assert s.count(anchor) == 1
    return s.replace(anchor, f'<note place="foot" n="147)">{m.group(1)}</note>')


def k1_struct(root):
    for div in root.iter(TEI + 'div'):
        if div.get('n') == '4' and _head(div).startswith('4) Der Arbeitstag'):
            parent = div.getparent()
            parent.remove(div)
            parent.addnext(div)
            div.set('n', '3')
            return
    raise SystemExit('k1_struct: Arbeitstag not found')


K1 = {
    'tei': HERE / 'sources' / 'marx_kapital01_1867.xml',
    'key': 'k1',
    'dir': 'marx_kapital01_1867',
    'prefix': '',
    'idp': '',
    'br_levels': 2,
    'table_dir': HERE / 'tables' / 'k1',
    'toc_contents': 'Inhalt des ersten Bandes (Erstausgabe)',
    'marks_after_stop': True,
    'raw_fixes': [
        ('Unzahljetzt', 'Unzahl jetzt'),
        ("C'ver-", "C' ver-"),
        (
            '<hi rendition="#g">Engels</hi>den',
            '<hi rendition="#g">Engels</hi> den',
        ),
        (
            '<hi rendition="#g">Geist</hi>der',
            '<hi rendition="#g">Geist</hi> der',
        ),
        ('noth wendigen', 'nothwendigen'),
        (
            '&#x03F0;&#x03B1;&#x03C0;&#x03B7;&#x03BB;&#x03B9;&#x03C0;&#x1F74;',
            'ϰαπηλιϰὴ',
        ),
        (
            '&#x1F00;&#x03B4;&#x03C5;&#x03BD;&#x03B1;&#x03C4;&#x03BF;&#x03BD;',
            'ἀδύνατον',
        ),
        ('Linie a--------------b', 'Linie <seg type="line">a6 b0</seg>'),
        ('a-------------b---c', '<seg type="line">a6 b1 c0</seg>'),
        (
            "a-------------b'--b----c",
            '<seg type="line">a6 b&#x2032;1 b2 c0</seg>',
        ),
        (
            '<p>I)<lb/>\n<formula/>.<lb/>\n',
            '<p><formula rend="display" n="I)" suffix="."/>',
        ),
        (
            '<p>II)<lb/>\n<formula/>. Eine',
            '<p><formula rend="display" n="II)" suffix="."/>Eine',
        ),
        (
            'Proportionen: <formula/><lb/>\n<formula/>. Nach',
            'Proportionen: <formula rend="display" suffix="."/>Nach',
        ),
        (
            'dagegen: <formula/><lb/>\n= 50 %.</p>',
            'dagegen: <formula rend="display" suffix=" = 50 %."/></p>',
        ),
        # Tabellen, die der Druck mitten im Satz an den Kopf der Folgeseite
        # gesetzt hat, an ihre Verweisstelle
        (
            (
                '<table><row><cell/></row></table>'
                ' <table><row><cell/></row></table>'
                ' <table><row><cell/></row></table> überhaupt'
            ),
            'überhaupt',
        ),
        (
            (
                '<hi rendition="#c">(Siehe nebenstehende Tabelle.)</hi>        '
                '       </p>'
            ),
            (
                '<hi rendition="#c">(Siehe nebenstehende'
                ' Tabelle.)</hi><lb/>\n<table _page="665"'
                ' _facs="684"><row><cell/></row></table> <table _page="665"'
                ' _facs="684"><row><cell/></row></table> <table _page="665"'
                ' _facs="684"><row><cell/></row></table></p>'
            ),
        ),
        (
            (
                '<hi rendition="#c"><hi rendition="#b">Tabelle'
                ' E.</hi><lb/>\nRubrik D. Einkommen aus Profiten (über 60 Pfd.'
                ' St.) in Irland.</hi><lb/>\n<table><row><cell/></row></table>'
                ' Bodenprodukt'
            ),
            'Bodenprodukt',
        ),
        (
            '<hi rendition="#c">Siehe nebenstehende Tabelle E.</hi></p>',
            (
                '<hi rendition="#c">Siehe nebenstehende Tabelle'
                ' E.</hi><lb/>\n<hi rendition="#c"><hi rendition="#b">Tabelle'
                ' E.</hi><lb/>\nRubrik D. Einkommen aus Profiten (über 60 Pfd.'
                ' St.) in Irland.</hi><lb/>\n<table _page="693"'
                ' _facs="712"><row><cell/></row></table></p>'
            ),
        ),
    ],
    'raw_hook': k1_raw,
    'struct_hook': k1_struct,
    'formulas': [
        r'\lab{c}{410}',
        r'\lab{v}{90}',
        r'\ov{c + v}',
        r'\ov{\lab{c}{410 l.} + \lab{v}{90 l.}} + \lab{m}{90 l}',
        r'\ov{c + v}',
        r'\ov{c + v}',
        r'\ov{\lab{c}{410 l.} + \lab{v}{90 l.}} + \lab{m}{90}',
        r'\ov{\lab{v}{90 l.} + \lab{m}{90 l.}}',
        r'\ov{0 + v}',
        r'\ov{c + v}',
        r'\lab{v}{90 l.}',
        r'\ov{c + v}',
        r'\ov{v + m}',
        r'\ov{\lab{c}{410 l.} + \lab{v}{90 l.}}',
        r'\lab{m}{90}',
        r'\ov{3 l. 10 sh. + 3 l. 11 sh.}',
        r'\frac{Mehrwerth}{Variables Kapital} (\frac{m}{v}) ='
        r' \frac{Mehrwerth}{Werth der Arbeitskraft}'
        r' = \frac{Mehrarbeit}{Nothwendige Arbeit}',
        (
            r'\frac{Mehrarbeit}{Arbeitstag} = \frac{Mehrwerth}{Werth des'
            r' Produkts} = \frac{Mehrprodukt}{Gesammtprodukt}'
        ),
        r'\frac{6 Stunden Mehrarbeit}{6 Stunden nothwendige Arbeit} ='
        r' \frac{Mehrwerth von 3 sh.}'
        r'{Variables Kapital von 3 sh.} = 100 %',
        (
            r'\frac{6 Stunden Mehrarbeit}{Arbeitstag von 12 Stunden} ='
            r' \frac{Mehrwerth von 3 sh.}{Werthprodukt von 6 sh.}'
        ),
        (
            r'\frac{Tageswerth der Arbeitskraft}{Arbeitstag von gegebner'
            r' Stundenzahl}'
        ),
        r'\frac{Tageswerth der Arbeitskraft}{Arbeitstag}',
        (
            r'\frac{Tageswerth der Arbeitskraft}{Arbeitstag von gegebner'
            r' Stundenzahl}'
        ),
        (
            r'\frac{Tageswerth der Arbeitskraft}{Arbeitstag von gegebner'
            r' Stundenzahl}'
        ),
    ],
    'tables': [
        '101',
        '189',
        '208',
        '271',
        '409',
        '456',
        '635',
        '636',
        '637',
        '643',
        '651a',
        '651b',
        '665',
        '668',
        '669',
        '680',
        '689a',
        '689b',
        '690',
        '691',
        '692',
        '693',
        '698',
        '759',
    ],
    'table_notes': notes.K1,
    'text_table_note': (
        ' Wo eine Tabelle für die Zeile zu breit ist, ist sie geteilt: die'
        ' Tabellen B, C und D (S. 690–692) und die Übersicht der'
        ' Getreideeinfuhr (S. 759) nach Spaltengruppen. Die Statistik der zwölf'
        ' Häuser (S. 680) steht in einer Folge statt in zwei Hälften'
        ' nebeneinander, die Übersicht der Pachten (S. 698) zeilenweise statt'
        ' in Spalten. Einheiten, die der Druck in jeder Spalte oder Zeile'
        ' wiederholt, stehen einmal (S. 409, 637, 668).'
    ),
}

VOL1 = {
    'footnote_note': (
        ' Die Fußnotenzeichen stehen, wie heute üblich und wie in den beiden'
        ' anderen Bänden, hinter Satzschlusszeichen und schließenden'
        ' Anführungszeichen; die Erstausgabe setzt sie davor.'
    ),
    'index': 1,
    'year': '1867',
    'cover': HERE / 'covers' / 'cover1.png',
    'uid_key': 'dta:marx_kapital01_1867:epub',
    'title': (
        'Das Kapital. Kritik der politischen Oekonomie. Erster Band (1867)'
    ),
    'description': (
        'Erstausgabe des ersten Bandes (Hamburg: Meissner 1867) nach der'
        ' TEI-Transkription des Deutschen Textarchivs; Orthographie des'
        ' Originals, verlinkte Fußnoten, Seitenzählung der Erstausgabe.'
    ),
    'parts': [K1],
    'corrections': [
        (
            'Die Korrekturen der Liste „Störende Druckfehler“ am Ende des'
            ' Bandes sind eingearbeitet, bis auf die Angabe zu S. 534 („lies 8'
            ' statt 11“), die sich keiner Stelle zuordnen lässt. Die Liste'
            ' selbst ist wiedergegeben.'
        ),
    ],
    'print_split': {
        'at': '16.xhtml',
        'move': '28.xhtml',
        'front': ['01-titel.xhtml', '03-inhalt.xhtml'],
    },
    'structure_pdf': [
        (
            'Für den Druck ist der Band in zwei Teile geteilt, mit'
            ' durchlaufender Seitenzählung. Der erste Teil reicht bis zum Ende'
            ' des dritten Kapitels und enthält auch den „Anhang zu Kapitel I,'
            ' 1“, den das Vorwort an Stelle eines Teils des ersten Kapitels zu'
            ' lesen empfiehlt. Der zweite Teil beginnt mit dem vierten Kapitel'
            ' und enthält den „Nachtrag zu den Noten“ und die „Störenden'
            ' Druckfehler“. Beide Teile geben das vollständige'
            ' Inhaltsverzeichnis wieder.'
        ),
    ],
    'structure': [
        (
            'Die Fußnote zur Drainirung im sechsten Kapitel (im Druck „147)“)'
            ' steht an ihrer Stelle; das DTA hatte sie als „137)“ einer'
            ' späteren Seite zugeordnet.'
        ),
        (
            'Die Überschrift „4) Der Arbeitstag“ war im DTA als Unterabschnitt'
            ' von „3) Die Rate des Mehrwerths“ kodiert und ist gleichrangig'
            ' eingeordnet.'
        ),
        (
            'Die Liste der schwindsüchtigen Spitzenmacherinnen 1852–1861, die'
            ' der Druck in zwei Spalten setzt, steht in der Folge der Jahre.'
        ),
        (
            'Zwei Tabellen, die der Druck mitten in einem Satz an den Kopf der'
            ' folgenden Seite gesetzt hat (S. 665 und 693), stehen hinter der'
            ' Zeile, die auf sie verweist („Siehe nebenstehende Tabelle“).'
        ),
    ],
}


# ---------------------------------------------------------------- Band 2 (1885)


def k2_struct(root):
    for div in root.iter(TEI + 'div'):
        if div.get('n') == '3' and _head(div).startswith(
            'III. Der Umsatz zwischen den beiden Abtheilungen'
        ):
            prev, lead = div.getprevious(), []
            while prev is not None and not (
                isinstance(prev.tag, str) and prev.tag == TEI + 'div'
            ):
                lead.insert(0, prev)
                prev = prev.getprevious()
            assert _head(prev).startswith('Zwanzigstes Kapitel'), _head(prev)
            first = div.find(TEI + 'div')
            rest = [first, *first.itersiblings()]
            for e in lead + [div] + rest:
                prev.append(e)
            div.set('n', '4')
            return
    raise SystemExit('k2_struct: chapter 20 section III not found')


K2 = {
    'tei': HERE / 'sources' / 'marx_kapital02_1885.xml',
    'key': 'k2',
    'dir': 'marx_kapital02_1885',
    'prefix': '',
    'idp': '',
    'br_levels': 3,
    'marks_after_stop': True,
    'table_dir': HERE / 'tables' / 'k2',
    'toc_contents': 'Inhaltsverzeichniss (Erstausgabe)',
    'raw_fixes': [
        ('n="4)" xml:id="seg2pn_6_1"', 'n="38)" xml:id="seg2pn_6_1"'),
        ('n="4)" xml:id="seg2pn_6_2"', 'n="38)" xml:id="seg2pn_6_2"'),
        (
            "<formula>G' &#x2014; W'&lt;A Pm</formula>",
            (
                "<formula notation=\"TeX\">\\mathrm{G' - W' &lt; {A \\atop"
                " Pm}}</formula>"
            ),
        ),
        # Schemazeilen, die das DTA in den Fließtext gezogen hat (S. 451, 454,
        # 462), als eigene Zeilen
        (
            (
                'I. 4000<hi rendition="#sub">c</hi> + 1000<hi'
                ' rendition="#sub">v</hi> + 1000<hi'
                ' rendition="#sub">m</hi><lb/>\nII. . . . . . <formula/> +'
                ' 500<hi rendition="#sub">v</hi> + 500<hi'
                ' rendition="#sub">m</hi>,<lb/>'
            ),
            (
                '<hi rendition="#et">I. 4000<hi rendition="#sub">c</hi> +'
                ' 1000<hi rendition="#sub">v</hi> + 1000<hi'
                ' rendition="#sub">m</hi></hi>\n<hi rendition="#et">II. . . . .'
                ' . <formula/> + 500<hi rendition="#sub">v</hi> + 500<hi'
                ' rendition="#sub">m</hi>,</hi>'
            ),
        ),
        (
            (
                'I. 1000<hi rendition="#sub">v</hi> + 1000<hi'
                ' rendition="#sub">m</hi>, wurde reducirt auf die Schwierigkeit'
                ' bei Um-<lb/>\nII. <formula/><lb/>\nsetzung der'
                ' Reste:<lb/>\nI. . . . . . 400<hi'
                ' rendition="#sub">m</hi><lb/>\nII. (1) 200 Geld + 200<hi'
                ' rendition="#sub">c</hi> Waare + (2) 200<hi'
                ' rendition="#sub">c</hi> Waare, oder, um die<lb/>\nSache noch'
                ' klarer zu machen:<lb/>\n. 200<hi rendition="#sub">m</hi> +'
                ' 200<hi rendition="#sub">m</hi>.<lb/>\nII. (1) 200 Geld +'
                ' 200<hi rendition="#sub">c</hi> Waare + (2) 200<hi'
                ' rendition="#sub">c</hi> Waare.</p>'
            ),
            (
                '<hi rendition="#et">I. 1000<hi rendition="#sub">v</hi> +'
                ' 1000<hi rendition="#sub">m</hi></hi>\n<hi rendition="#et">II.'
                ' <formula/>,</hi> wurde reducirt auf die Schwierigkeit bei'
                ' Umsetzung der Reste:\n<hi rendition="#et">I. . . . . . 400<hi'
                ' rendition="#sub">m</hi></hi>\n<hi rendition="#et">II. (1) 200'
                ' Geld + 200<hi rendition="#sub">c</hi> Waare + (2) 200<hi'
                ' rendition="#sub">c</hi> Waare,</hi> oder, um die Sache noch'
                ' klarer zu machen:\n<hi rendition="#et">. 200<hi'
                ' rendition="#sub">m</hi> + 200<hi'
                ' rendition="#sub">m</hi>.</hi>\n<hi rendition="#et">II. (1)'
                ' 200 Geld + 200<hi rendition="#sub">c</hi> Waare + (2) 200<hi'
                ' rendition="#sub">c</hi> Waare.</hi></p>'
            ),
        ),
        (
            (
                'den Umsatz I. 1000<hi rendition="#sub">v</hi> + 1000<hi'
                ' rendition="#sub">m</hi><lb/>'
            ),
            (
                'den Umsatz<lb/>\n<hi rendition="#et">I. 1000<hi'
                ' rendition="#sub">v</hi> + 1000<hi'
                ' rendition="#sub">m</hi></hi>'
            ),
        ),
    ],
    'struct_hook': k2_struct,
    'formulas': [
        r"!\mathrm{\braced{^tu _ab _c}{G – W …~ :a | P :ta | ~…~ :ta | W' :tac"
        r" | ~– G'. :tac | ~G – W …~ :tbc | "
        r"P :tubc | ~…~ :ubc | W' :ubc | ~– G'. :ub | ~G – W …~ :u | P :u | ~…"
        r" etc.}}",
        r"!\mathrm{W' \bcases{W \\ + \\ w} \rows{– – \\ – G' \\ – –} \bcases{G"
        r" \\ + \\ g} "
        r"\rows{– W < {A \atop Pm} \\ ~ \\ – w}}",
        r"!\mathrm{P … W' \bcases{W \\ + \\ w} \rows{– \\ ~ \\ –} \bcases{G \\"
        r" + \\ g} "
        r"\rows{– W < {A \atop Pm} … P \\ ~ \\ – w}}",
        (
            r"!\mathrm{P … \nt{1}{\ov{W' – G'}}. \nt{2}{\ov{G – W}} < {A \atop"
            r" Pm} … P (P')}"
        ),
        r"!\mathrm{W' \begin{cases} W – \\ – G' \\ w – \end{cases} "
        r"\begin{cases} G – W < {A \atop Pm} … P … W' \\ ~ \\ g – w"
        r" \end{cases}}",
        r"\mathrm{P … W' \begin{cases} W – \\ – G' \\ w – \end{cases} "
        r"\begin{cases} G \\ – W < {A \atop Pm} … P (P') \\ g – w \end{cases}}",
        r"\mathrm{W' \begin{cases} W – \\ – G' \\ w – \end{cases} "
        r"\begin{cases} G – W < {A \atop Pm} … P … W' \\ ~ \\ g – w"
        r" \end{cases}}",
        (
            r'\frac{Rate des Mehrwerths von Kapital B}{Rate des Mehrwerths von'
            r' Kapital A} = \frac{10 %}{100 %}'
        ),
        (
            r'!\frac{Jahresrate des Mehrwerths von Kapital B}{Jahresrate des'
            r' Mehrwerths von Kapital A} = \frac{100 %}{1000 %}'
        ),
        (
            r'!\frac{Jährlich producirte Masse Mehrwerth}{Jährlich'
            r' umgeschlagnes variables Kapital}'
        ),
        r'!\frac{Jährlich umgeschlagnes Kapital}{Vorgeschossnes Kapital}',
        (
            r'!\frac{5000 £ jährlich umgeschlagnes Kapital}{500 £'
            r' vorgeschossnes Kapital}'
        ),
        (
            r'!\frac{5000 £ jährlich umgeschlagnes Kapital}{5000 £'
            r' vorgeschossnes Kapital}'
        ),
        (
            r'!\frac{Masse des während des Jahres producirten'
            r' Mehrwerths}{Vorgeschossnes variables Kapital}'
        ),
        (
            r'!\frac{Wirkliche Rate des Mehrwerths × dem vorgeschossnen'
            r' variablen Kapital × n}{Vorgeschossnes variables Kapital}'
        ),
        (
            r"!M' = \frac{100 % × 5500 × \frac{10}{11}}{5500} = 100 ×"
            r" \frac{10}{11} = \frac{1000}{11} = 90\frac{10}{11} %"
        ),
        (
            r'!\frac{Während einer Umschlagsperiode erzeugte Masse von'
            r' Mehrwerth}{Während einer Umschlagsperiode angewandtes variables'
            r' Kapital}'
        ),
        (
            r'\frac{v}{400_{v} (a)} + \frac{m}{240_{m} (a) + 100_{v} (b) +'
            r' 60_{m} (b)} = 800'
        ),
        (
            r'\frac{v}{100_{m} (a)} + \frac{m}{60_{m} (a) + 40_{m} (b)} . . . .'
            r' . . = \frac{200}{1000}'
        ),
        r'\nt{1}{W}',
        r'\nt{2}{G}',
        r'\nt{3}{W}',
        r'2000_{c}',
        r'1800_{c}',
        r'2000_{c}',
    ],
    'formula_note': (
        ' Die Kreislaufschemata (S. 37, 40, 50, 61, 71, 90) sind Text.'
    ),
    'formula_note_epub': (
        ' Eckige Klammern und gerade Linien stehen dabei für die geschweiften'
        ' Klammern des Drucks.'
    ),
    'tables': [f'{i:02d}' for i in range(1, 11)],
    'table_notes': notes.K2,
}

VOL2 = {
    'footnote_note': (
        ' Zwei Fußnotenzeichen, die der Druck vor das Satzschlusszeichen setzt,'
        ' stehen wie sonst dahinter.'
    ),
    'index': 2,
    'year': '1885',
    'cover': HERE / 'covers' / 'cover2.png',
    'uid_key': 'dta:marx_kapital02_1885:epub',
    'title': (
        'Das Kapital. Kritik der politischen Oekonomie. Zweiter Band (1885)'
    ),
    'description': (
        'Erstausgabe des zweiten Bandes (Hamburg: Meissner 1885, hrsg. von'
        ' Friedrich Engels) nach der TEI-Transkription des Deutschen'
        ' Textarchivs; Orthographie des Originals, verlinkte Fußnoten,'
        ' Seitenzählung der Erstausgabe.'
    ),
    'parts': [K2],
    'emphasis_note': (
        ' Kursiv gesetzt sind im Druck nur die Zeichen £ und ℔ (hier aufrecht)'
        ' sowie Griechisches.'
    ),
    'structure': [
        (
            'Der Unterabschnitt „III. Der Umsatz zwischen den beiden'
            ' Abtheilungen“ des zwanzigsten Kapitels und die folgenden'
            ' Unterabschnitte IV–XIII waren im DTA eine Ebene zu hoch kodiert'
            ' und sind in das Kapitel eingeordnet.'
        ),
        (
            'Zeilenweise gesetzte Umsatzschemata, die das DTA in den Fließtext'
            ' gezogen hat (S. 451, 454, 462), stehen wie im Druck auf eigenen'
            ' Zeilen.'
        ),
        (
            'Die Fußnote 38) im neunzehnten Kapitel (S. 353) ist im Druck'
            ' versehentlich als „4)“ beziffert.'
        ),
    ],
}


# ---------------------------------------------------------------- Band 3 (1894)

K31 = {
    'tei': HERE / 'sources' / 'marx_kapital0301_1894.xml',
    'key': 'k31',
    'dir': 'marx_kapital0301_1894',
    'prefix': 'I/',
    'idp': '1-',
    'br_levels': 3,
    'marks_after_stop': True,
    'table_dir': HERE / 'tables' / 'k31',
    'part_label': ' im ersten Theil',
    'toc_contents': 'Inhaltsverzeichniss des ersten Theils (Erstausgabe)',
    'raw_fixes': [
        # Titelangabe im TEI-Kopf: Punkt wie auf dem Titelblatt
        (
            (
                '<title type="volume" n="3">Dritter Band, erster Theil. Buch'
                ' III: Der Gesammtprocess der kapitalistischen Produktion'
                ' Kapitel'
            ),
            (
                '<title type="volume" n="3">Dritter Band, erster Theil. Buch'
                ' III: Der Gesammtprocess der kapitalistischen Produktion.'
                ' Kapitel'
            ),
        ),
        (
            (
                '<title level="m" type="volume" n="3">Dritter Band, erster'
                ' Theil. Buch III: Der Gesammtprocess der kapitalistischen'
                ' Produktion Kapitel'
            ),
            (
                '<title level="m" type="volume" n="3">Dritter Band, erster'
                ' Theil. Buch III: Der Gesammtprocess der kapitalistischen'
                ' Produktion. Kapitel'
            ),
        ),
        (
            (
                '<hi rendition="#g">Im ersten Theil</hi>.</hi>         </p>    '
                '     <lb/>\n<list>'
            ),
            (
                '<hi rendition="#g">Im ersten Theil</hi>.</hi>         </p>    '
                '     <lb/>\n<list type="corrigenda" n="I/">'
            ),
        ),
        (
            (
                '<hi rendition="#g">Im zweiten Theil</hi>:</hi>         </p>   '
                '      <lb/>\n<list>'
            ),
            (
                '<hi rendition="#g">Im zweiten Theil</hi>:</hi>         </p>   '
                '      <lb/>\n<list type="corrigenda" n="II/">'
            ),
        ),
        (
            (
                '&#x201E; x <hi rendition="#i">£</hi>, &#x201E; 12 x <hi'
                ' rendition="#i">£</hi>.'
            ),
            (
                '&#x201E; x <hi rendition="#i">&#x2114;</hi>, &#x201E; 12 x <hi'
                ' rendition="#i">&#x2114;</hi>.'
            ),
        ),
    ],
    'formulas': [
        r"!p' = \frac{m}{C} = \frac{m}{c + v}",
        r"!p' = m' \frac{v}{C} = m' \frac{v}{c + v}",
        r"!p' : m' = v : C",
        r"!80_{c} + 20_{v} + 20_{m}; m' = 100 %, p' = 20 %",
        r"!80_{c} + 20_{v} + 40_{m}; m' = 200 %, p' = 40 %",
        (
            r"!80_{c} + 12_{v} + 28_{m}; m' = 233⅓ %, p' = \frac{28}{92} ="
            r" 30\frac{10}{23} %"
        ),
        r"!p' = m' \frac{v}{C}; p'_{1} = m' \frac{v_1}{C_1}",
        r"!p'_{1} = m' \frac{ev}{EC}",
        (
            r"!p' : p'_{1} = m' \frac{v}{C} : m' \frac{v_1}{C_1} = \frac{v}{C}"
            r" : \frac{v_1}{C_1}"
        ),
        r"!15000 C = 12000_{c} + 3000_{v} (+ 3000_{m})",
        r"!100 C = 80_{c} + 20_{v} (+ 20_{m})",
        r"!12000 C = 10800_{c} + 1200_{v} (+ 1200_{m})",
        r"!100 C = 90_{c} + 10_{v} (+ 10_{m})",
        r"!80_{c} + 20_{v} + 20_{m}",
        r"!90_{c} + 10_{v} + 10_{m}",
        r"!p' = m' \frac{v}{C}",
        r"!p'_{1} = m' \frac{v_1}{C}",
        r"!p' : p'_{1} = m' \frac{v}{C} : m' \frac{v_1}{C} = v : v_1",
        r"!p' = m' \frac{v}{C} in: p'_{1} = m' \frac{v}{C_1}",
        r"!p'_{1} : p' = C : C_1",
        r"!p'_{1} = m' \frac{ev}{EC}",
        r"!p' = m' \frac{v}{C}",
        r"!p'_{1} = m'_{1} \frac{v_1}{C_1}",
        r"!p' : p'_{1} = m' \frac{v}{C} : m'_{1} \frac{v_1}{C_1}",
        r"!p'_{1} = \frac{m'_1}{m'} × \frac{v_1}{v} × \frac{C}{C_1} × p'",
        r"!p' = m' \frac{v}{C}",
        r"!p'_{1} = m'_{1} \frac{v}{C}",
        r"!p' : p'_{1} = m' : m'_{1}",
        r"!p' : p'_{1} = m'v : m'_{1} v = m : m_{1}",
    ],
    'tables': [f'{i:02d}' for i in range(1, 6)],
}

K32 = {
    'tei': HERE / 'sources' / 'marx_kapital0302_1894.xml',
    'key': 'k32',
    'dir': 'marx_kapital0302_1894',
    'prefix': 'II/',
    'idp': '2-',
    'br_levels': 3,
    'marks_after_stop': True,
    'table_dir': HERE / 'tables' / 'k32',
    'part_label': ' im zweiten Theil',
    'toc_title': 'Titel des zweiten Theils (Erstausgabe)',
    'toc_contents': 'Inhaltsverzeichniss des zweiten Theils (Erstausgabe)',
    'toc_skip': ('Drittes Buch', 'Fünfter Abschnitt'),
    'raw_fixes': [
        # Titelangabe im TEI-Kopf: Schreibung wie auf dem Titelblatt
        # (Gesammtprocess)
        (
            (
                '<title type="volume" n="4">Dritter Band, zweiter Theil. Buch'
                ' III: Der Gesamtprocess'
            ),
            (
                '<title type="volume" n="4">Dritter Band, zweiter Theil. Buch'
                ' III: Der Gesammtprocess'
            ),
        ),
        (
            (
                '<title level="m" type="volume" n="4">Dritter Band, zweiter'
                ' Theil. Buch III: Der Gesamtprocess'
            ),
            (
                '<title level="m" type="volume" n="4">Dritter Band, zweiter'
                ' Theil. Buch III: Der Gesammtprocess'
            ),
        ),
        (
            (
                'Bank von'
                ' Eng-<lb/>\n<choice><sic>fand</sic><corr>land</corr></choice>'
            ),
            (
                'Bank von'
                ' <choice><sic>Engfand</sic><corr>England</corr></choice><lb/>'
            ),
        ),
    ],
    'formulas': [],
    'tables': [f'{i:02d}' for i in range(1, 55)],
}

VOL3 = {
    'footnote_note': (
        ' Ein Fußnotenzeichen, das der Druck vor das Satzschlusszeichen setzt,'
        ' steht wie sonst dahinter.'
    ),
    'index': 3,
    'year': '1894',
    'cover': HERE / 'covers' / 'cover3.png',
    'uid_key': 'dta:marx_kapital03_1894:epub',
    'title': (
        'Das Kapital. Kritik der politischen Oekonomie. Dritter Band (1894)'
    ),
    'description': (
        'Erstausgabe des dritten Bandes in zwei Theilen (Hamburg: Meissner'
        ' 1894, hrsg. von Friedrich Engels) in einem EPUB, nach der'
        ' TEI-Transkription des Deutschen Textarchivs; Orthographie des'
        ' Originals, verlinkte Fußnoten, Seitenzählung der Erstausgabe.'
    ),
    'parts': [K31, K32],
    'emphasis_note': (
        ' Kursiv gesetzt sind im Druck nur die Zeichen £ und ℔ (hier aufrecht)'
        ' sowie Griechisches.'
    ),
    'pages_note': (
        ' Da beide Theile eigene Seitenzählungen haben, tragen die Seitenzahlen'
        ' die Präfixe „I/“ und „II/“.'
    ),
    'pages_note_pdf': (
        ' In dieser Notiz bezeichnen „I/“ und „II/“ vor einer Seitenzahl den'
        ' ersten und zweiten Theil.'
    ),
    'corrections': [
        (
            'Die Korrekturen der Liste „Druckfehler“ vor dem'
            ' Inhaltsverzeichniss des ersten Theils sind eingearbeitet,'
            ' darunter die Überschrift des sechsundvierzigsten Kapitels (im'
            ' Druck „Achtundvierzigstes“) und der von Engels gestrichene Satz'
            ' auf S. I/182. Die Liste selbst ist wiedergegeben; die Angabe zu'
            ' S. I/115 stand schon richtig in der Transkription.'
        ),
        (
            'Druckfehler im Aristoteles-Zitat im dreiundzwanzigsten Kapitel (S.'
            ' I/371) sind berichtigt: „αὕτη“ (im Druck „αὐτῆ“), „ἐπίστασθαι“'
            ' und „ἐπιτάττειν“ (ohne Spiritus gedruckt), „ταύτην“ („ταυτὴν“).'
        ),
    ],
    'structure_epub': [
        (
            'Die beiden Theile der Erstausgabe sind in einem Band vereinigt.'
            ' Der fünfte Abschnitt, den die Theilung nach Kapitel XXVIII'
            ' durchschneidet, erscheint im Inhaltsverzeichnis als ein'
            ' Abschnitt; Titelblatt und Inhaltsverzeichniss des zweiten Theils'
            ' stehen an ihrer Stelle im Text.'
        ),
    ],
}

VOLUMES = {'1': VOL1, '2': VOL2, '3': VOL3}
for _vol in VOLUMES.values():
    _vol['editor'] = (
        'Holger Weiß',
        'Weiß, Holger',
        'holger+kapital@weiss-berlin.de',
    )
    _vol['publisher'] = 'Selbstverlag Holger Weiß, Berlin'
    _vol['homepage'] = 'https://holger.weiss-berlin.de/kapital.html'
    _vol['printer'] = 'Lulu Press, Inc., Morrisville\u00a0(USA)'
    _vol['factual_note'] = (
        ', auch wo die MEGA² sie nach den Quellen verbessert.'
    )

for _part, _fixes in (
    (K1, sperrsatz.K1 + errata.K1 + errata.K1_GREEK + errata.K1_TEXT),
    (K2, sperrsatz.K2 + errata.K2_TEXT),
    (K31, sperrsatz.K31 + errata.K31_GREEK + errata.K31 + errata.K31_TEXT),
    (K32, sperrsatz.K32 + errata.K32 + errata.K32_TEXT),
):
    _part['raw_fixes'] = _part.get('raw_fixes', []) + _fixes
_n = lambda fixes: sum(f[2] if len(f) > 2 else 1 for f in fixes)
VOLUMES['1']['corrections'] += [
    (
        'Weitere offensichtliche Druckfehler und Erfassungsfehler der'
        ' Transkription sind berichtigt'
        f' ({_n(sperrsatz.K1) + _n(errata.K1_TEXT) + 5} Stellen):'
        ' Buchstabenverwechslungen („mensehlicher“, „Känfers“), falsche'
        ' Wortabstände („Unzahljetzt“, „unauf hörlich“, „welcheihren“),'
        ' grammatische Versehen („Eine bestimmtes jährliches Quantum“) und'
        ' Hervorhebungen, die in der Transkription einen Buchstaben zu früh'
        ' beginnen (gesperrt „hgrösse“ in „Werthgrösse“). Gefunden wurden sie'
        ' durch einen Abgleich mit der MEGA² (Bd. II/5, 1983), eine'
        ' Durchsicht der Sperrsatzstellen und beim Korrekturlesen;'
        ' Zweifelsfälle sind nach dem Faksimile entschieden.'
    ),
    (
        'Im Griechischen sind zwei Erfassungsfehler nach dem Faksimile und vier'
        ' Druckfehler berichtigt: „καπηλικὴ“, „ἀδύνατον“; „καλὸς“ (S. 202, im'
        ' Druck „καλος“), „αὐτάρκεια“ (S. 352, „αὐταρκεία“), „Κλῖναι“ und'
        ' „κλῖναι“ (S. 772, „Κλίναι“, „κλίναι“), „οὖν ἀληθείᾳ“ (S. 773, „οἶν'
        ' ἀληδείᾳ“).'
    ),
]
_SPERR = ' im Sperrsatz, wo Wortabstände schwer zu erkennen sind,'
_MEGA = (
    'Gefunden wurden sie durch einen Abgleich mit der MEGA² ({}) und beim'
    ' Korrekturlesen; Zweifelsfälle sind nach dem Faksimile entschieden.'
)
VOLUMES['2']['corrections'] = [
    f'Offensichtliche Druckfehler sind berichtigt ({len(errata.K2_TEXT)}'
    ' Stellen), darunter viele verdrehte Lettern („dnrch“, „indnstriellen“,'
    ' „Kreislänfe“), ausgefallene und verdoppelte Buchstaben („währen“ statt'
    ' „während“, „verrrichtet“) sowie verwechselte Wörter und Wortformen („das'
    ' fixe Kapitel“, „Geld, dass die industriellen Kapitalisten“, „von fremden'
    ' Geld“), am Zeilenwechsel verdoppelte Wörter („von fixem und und'
    ' flüssigem Kapital“) und unpaarige Klammern. Wo die Transkription das „ß“'
    ' des Drucks als „fs“ erfasst hat („Mafsstab“), ist es hergestellt. '
    + _MEGA.format('Bd. II/13, 2008'),
    (
        f'Erfassungsfehler der Transkription{_SPERR} sind berichtigt'
        f' ({_n(sperrsatz.K2)} Stellen): auseinandergeschriebene Wörter („fun'
        ' giren“) und Hervorhebungen, die einen Buchstaben zu früh beginnen'
        ' (gesperrt „szeit“ in „Umschlagszeit“).'
    ),
]
VOLUMES['3']['corrections'][1:1] = [
    'Weitere offensichtliche Druckfehler und Erfassungsfehler der'
    ' Transkription sind berichtigt'
    f' ({len(errata.K31_TEXT) + len(errata.K32_TEXT)} Stellen), etwa'
    ' „proportinal“, „Jahrhnnderts“, „Vorschusss“ oder „nichtüberihrem“, dazu'
    ' verwechselte Wörter und Wortformen („Realisirung der Werths“, „das'
    ' Kapitel verdoppeln“, „free heads“ statt „free hands“), verdoppelte'
    ' Wörter („Da da das Geschäft“) und unpaarige Klammern. '
    + _MEGA.format('Bd. II/15, 2004'),
    (
        f'Erfassungsfehler der Transkription{_SPERR} sind berichtigt'
        f' ({_n(sperrsatz.K31 + sperrsatz.K32)} Stellen), vor allem'
        ' Hervorhebungen, die einen Buchstaben zu früh beginnen (gesperrt'
        ' „trate“ in „Profitrate“).'
    ),
]
