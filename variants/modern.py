"""Variant 'modern': spelling and word division after the current German rules
(Marx' wording unchanged).

The word table (modern_map.json) comes from tools/mk_modern_map.py and
modern_overrides.py. Passages in other languages are left alone: a word counts
as foreign context when most of the words around it are foreign (list in
modern_map.json); a word also common in another language (Oct, Commission)
and an English possessive also when the words next to it are foreign. Words
whose ss becomes ß are always German. A few rewrites depend on context
(Masse/Maße, so lange/solange) or span several words (u. s. w. → usw.,
zu Grunde → zugrunde).
"""

import json
import re
from collections import Counter
from pathlib import Path

NAME = 'modern'
NOTICE = (
    'Orthographie, Getrennt- und Zusammenschreibung folgen den heutigen Regeln'
    ' (Wert statt Werth, Ware statt Waare, Prozess statt Process, Zirkulation'
    ' statt Cirkulation, produzieren statt produciren, groß statt gross, usw.'
    ' statt u. s. w., zugrunde statt zu Grunde, aufeinander statt auf einander,'
    ' jeder statt Jeder). Wortformen und Satzbau sind unverändert (z. B.'
    ' „andren“, „verschiedne“, „geschehn“, „ward“). Fremdsprachige Zitate,'
    ' Eigennamen und Titel bleiben in ihrer Schreibung, ebenso'
    ' frühneuhochdeutsche Zitate (Luther). Grundlage ist eine Wortliste aller'
    ' Formen der drei Bände mit Einzelentscheidungen.'
)

HERE = Path(__file__).resolve().parent
_DATA = json.load(open(HERE / 'modern_map.json', encoding='utf-8'))
MAP = {k: v[0] for k, v in _DATA['map'].items()}
FOREIGN = set(_DATA['foreign'])
AMBIGUOUS = {
    k for k, v in _DATA['map'].items() if v[1] == 'foreign?' or k in FOREIGN
}
GERMAN = {k for k, v in _DATA['map'].items() if v[1] == 'sz'} - FOREIGN
ORDINAL = {'st', 'nd', 'rd', 'th'}
TEI = '{http://www.tei-c.org/ns/1.0}'
BLOCKS = {
    TEI + t
    for t in (
        'p',
        'note',
        'head',
        'item',
        'cell',
        'l',
        'titlePart',
        'docImprint',
        'byline',
        'docAuthor',
        'trailer',
        'quote',
        'bibl',
        'fw',
        'label',
    )
}
WORD = re.compile(
    r"[A-Za-zÄÖÜäöüßàâçéèêëîïôûùœæ]+(?:[’']s(?![A-Za-zÄÖÜäöüß]))?"
)
MASS_DAT = re.compile(r'(?:em|im|^demselben|^denselben)$')
CONTRACT = {
    'in',
    'auf',
    'an',
    'für',
    'durch',
    'um',
    'über',
    'vor',
    'unter',
    'hinter',
}
# Early New High German quotations (Luther etc.) keep their spelling
ENHG = {
    'hie',
    'kauffen',
    'bezalen',
    'Las',
    'rhümen',
    'nimpt',
    'Nehesten',
    'Nehisten',
    'stelen',
    'geschicht',
    'wolgetan',
    'Vernunfft',
    'sey',
    'seyn',
    'vierfaltiger',
    'Edelleut',
    'Kaufleut',
    'Leut',
    'geschazt',
    'Leiptzischen',
    'obs',
    'Machest',
    'Schadewacht',
    'itzt',
    'jtzt',
    'umb',
    'Gelt',
    'gelt',
    'hanget',
    'dieweil',
    'Dieweil',
    'kündten',
    'thubar',
    'jm',
    'jn',
    'jr',
    'sölch',
    'solchs',
    'Wucherer',
    'wuchern',
    'Pfarrherrn',
    'darumb',
    'warumb',
    'nicht',
    'eitel',
    'Gulden',
    'jeglichen',
    'Heiden',
    'drüber',
    'freilich',
    'jtzund',
    'itzund',
    'sonderlich',
    'thun',
    'thut',
    'vnd',
    'vnnd',
    'auff',
    'Teuffel',
    'Teufel',
    'lasst',
    'leihet',
    'verleihen',
}
ENHG_STRONG = {
    'hie',
    'kauffen',
    'bezalen',
    'rhümen',
    'nimpt',
    'Nehesten',
    'Nehisten',
    'geschicht',
    'wolgetan',
    'Vernunfft',
    'vierfaltiger',
    'Edelleut',
    'Kaufleut',
    'geschazt',
    'Leiptzischen',
    'Machest',
    'Schadewacht',
    'itzt',
    'jtzt',
    'umb',
    'hanget',
    'kündten',
    'thubar',
    'jm',
    'jn',
    'solchs',
    'darumb',
    'warumb',
    'jtzund',
    'itzund',
    'vnd',
    'vnnd',
    'auff',
    'Teuffel',
    'Leut',
    'sey',
    'obs',
    'stelen',
}

PHRASES = [
    (r'\bu\.\s?s\.\s?w\.', 'usw.'),
    (r'\bu\.\s?s\.\s?f\.', 'usf.'),
    (r'\bU\.\s?s\.\s?w\.', 'Usw.'),
    (r'\bu\.(\s?)A\.', r'u.\1a.'),
    (r'\b([Zz])\.(\s?)Th\.', r'\1.\2T.'),
    (r'\b([Ee])ben so\b', r'\1benso'),
    (
        (
            r'\b([Ii])rgend'
            r' (ein|eine|einen|einem|einer|eines|welche[mnrs]?'
            r'|wie|wo|etwas|jemand)\b'
        ),
        r'\1rgend\2',
    ),
    (r'\bzu Grunde\b', 'zugrunde'),
    (r'\bzu Gunsten\b', 'zugunsten'),
    (r'\bzu Ungunsten\b', 'zuungunsten'),
    (r'\bim Stande\b', 'imstande'),
    (r'\bzu Stande\b', 'zustande'),
    (r'\bin Stand (?=setz|gesetz|zu setz)', 'instand '),
    (r'\bin Folge dessen\b', 'infolgedessen'),
    (
        (
            r'\b([Ii])n Folge'
            r' (?=(der|des|dieser|dieses|seiner|ihrer|eines|einer|von)\b)'
        ),
        r'\1nfolge ',
    ),
    (r'\bstatt finde(t|n)\b', r'stattfinde\1'),
    (r'\bstatt fand(en)?\b', r'stattfand\1'),
    (r'\bstatt gefunden\b', 'stattgefunden'),
    (r'\bstatt zu finden\b', 'stattzufinden'),
    (r'\bStatt finde(t|n)\b', r'stattfinde\1'),
    (r'\bStatt fand(en)?\b', r'stattfand\1'),
    (r'\bStatt gefunden\b', 'stattgefunden'),
    (r'\bzu Teil (?=werd|wird|ward|wurd|geword)', 'zuteil '),
    (r'\b([Ss])o gar\b', r'\1ogar'),
    (r'\b([Ii])n so fern\b', r'\1nsofern'),
    (r'\b([Ii])n so weit\b', r'\1nsoweit'),
    (r'\b([Ii])n wie fern\b', r'\1nwiefern'),
    (r'\b([Ii])n wie weit\b', r'\1nwieweit'),
    (r'\b([Ss])o fern\b', r'\1ofern'),
    (r'\b([Vv])or Allem\b', r'\1or allem'),
    (r'\bbei Seite\b', 'beiseite'),
    (r'\bzu Nutze\b', 'zunutze'),
    (r'\bzu Wege\b', 'zuwege'),
    (r'\bzu Tage\b', 'zutage'),
    (r'\bzu Statten\b', 'zustatten'),
    (r'\bvon Statten\b', 'vonstatten'),
    (r'\b([Aa])n Statt\b', r'\1nstatt'),
    (r'\bzu Schulden\b', 'zuschulden'),
    (r'\b([Hh])eut zu Tage\b', r'\1eutzutage'),
    (r'\b([Nn])ichts desto (weniger|minder|trotz)\b', r'\1ichtsdesto\2'),
    (r'\b([Ss])o wohl (?=.{1,80}\bals\b)', r'\1owohl '),
    (
        (
            r'\b(auf|an|unter|durch|neben|nach|mit|für|gegen|von|zu|über'
            r'|aus|bei|hinter|in|vor|um)('
            r' )einander\b'
        ),
        r'\1einander',
    ),
    (
        (
            r'\b(Auf|An|Unter|Durch|Neben|Nach|Mit|Für|Gegen|Von|Zu|Über'
            r'|Aus|Bei|Hinter|In|Vor|Um)('
            r' )einander\b'
        ),
        r'\1einander',
    ),
    (r'\b([Ss])tatt dessen\b', r'\1tattdessen'),
    (r'\baußer Stande\b', 'außerstande'),
    (r'\b([Ss])o dass\b', r'\1odass'),
    (r'(^|[,;:(]\s*|[.!?]\s+)([Ss])o lange\b', r'\1\2olange'),
    (r'(^|[,;:(]\s*|[.!?]\s+)([Ss])o bald\b', r'\1\2obald'),
]
PHRASES = [(re.compile(p), r) for p, r in PHRASES]
# pronouns written with a capital in the original, lower case today (not at the
# start of a sentence,
# not as a noun after an article: „das Nichts“, „ein Etwas“)
PRON = re.compile(
    r'(?<=[a-zäöüß0-9,;)–]\s)'
    r'(Jeder|Jede|Jedes|Jedem|Jeden|Alle|Alles|Allen|Aller|'
    r'Andre|Andrer|Andres|Andren|Andern|Andere|Anderer|Anderes|Anderen|'
    r'Einer|Keiner|Niemand|Jemand|'
    r'Nichts|Etwas|Beide|Beiden|Beides|Beider)\b'
)

_log = Counter()


def blocks(root):
    text = root.find(TEI + 'text')
    for e in text.iter():
        if isinstance(e.tag, str) and e.tag in BLOCKS:
            yield e


def segments(block):
    """(element, 'text'|'tail') pairs of a block in reading order, without
    nested blocks' content."""
    out = []

    def walk(e, top):
        if e.text:
            out.append((e, 'text'))
        for c in e:
            if isinstance(c.tag, str) and c.tag in BLOCKS:
                pass
            elif isinstance(c.tag, str):
                walk(c, False)
            if c.tail:
                out.append((c, 'tail'))

    walk(block, True)
    return out


def is_foreign(w):
    return w in FOREIGN or re.split("[’']", w)[0] in FOREIGN


def foreign_flags(words):
    flags = []
    for i, w in enumerate(words):
        win = [x for x in words[max(0, i - 3) : i + 4] if len(x) > 1]
        f = sum(1 for x in win if is_foreign(x))
        flags.append(f * 2 > len(win) and w not in GERMAN)
    for i, w in enumerate(words):
        if flags[i]:
            continue
        before, after = words[max(0, i - 2) : i], words[i + 1 : i + 3]
        if w in AMBIGUOUS:
            flags[i] = bool(
                before[-1:]
                and before[-1] in ORDINAL
                or any(
                    len(side) == 2 and all(is_foreign(x) for x in side)
                    for side in (before, after)
                )
                or w == 'that'
                and any(is_foreign(x) for x in after)
            )
        elif re.search("[’']s$", w) and is_foreign(w):
            flags[i] = any(is_foreign(x) for x in after)
    return flags


def map_word(w, prev, foreign):
    if foreign:
        return w
    if w in ('Masse', 'masse') and prev and MASS_DAT.search(prev.lower()):
        return w[0] + 'aße'
    m = re.fullmatch(r"(\w+)([’'])s", w)
    if m:
        base, apo = m.group(1), m.group(2)
        if base.lower() in CONTRACT:
            return base + 's'
        if base[0].isupper() and len(base) > 1:
            base = MAP.get(base, base)
            return base + apo if base[-1] in 'sxzß' else base + 's'
        return MAP.get(base, base) + apo + 's'
    return MAP.get(w, w)


def historic_quotes(text, offsets, flags):
    """Mark the words of „…“ quotations written in Early New High German."""
    for m in re.finditer(r'„[^“]{0,4000}?(?:“|$)', text):
        ws = WORD.findall(m.group(0))
        strong = sum(1 for w in ws if w in ENHG_STRONG)
        weak = sum(1 for w in ws if w in ENHG)
        if strong >= 2 or (strong and weak >= 4):
            for i, (a, b) in enumerate(offsets):
                if a >= m.start() and b <= m.end():
                    flags[i] = True


def modernize_text(s, foreign=None):
    """Plain string (formulas, headings in the config): word table + phrases,
    German context assumed."""
    words = WORD.findall(s)
    flags = foreign or [False] * len(words)
    it = iter(range(len(words)))
    prev = ['']

    def rep(m):
        i = next(it)
        w = m.group(0)
        new = map_word(w, prev[0], flags[i])
        prev[0] = w
        if new != w:
            _log[(w, new)] += 1
        return new

    s = WORD.sub(rep, s)
    if not any(flags):

        def low(m):
            before = s[max(0, m.start() - 5) : m.start()].split()
            if (
                m.group(1) in ('Nichts', 'Etwas')
                and before
                and before[-1]
                in ('das', 'ein', 'dem', 'des', 'im', 'Das', 'Ein')
            ):
                return m.group(1)
            return m.group(1).lower()

        s2 = PRON.sub(low, s)
        if s2 != s:
            _log[('Großschreibung Pronomen', 'klein')] += 1
            s = s2
    for rx, r in PHRASES:
        s2 = rx.sub(r, s)
        if s2 != s:
            _log[(rx.pattern, r)] += 1
            s = s2
    return s


def transform(root, part):
    _log.clear()
    for b in blocks(root):
        segs = segments(b)
        texts = [getattr(e, a) for e, a in segs]
        joined, offsets, words, pos = '', [], [], 0
        for t in texts:
            for m in WORD.finditer(t):
                words.append(m.group(0))
                offsets.append((pos + m.start(), pos + m.end()))
            joined += t
            pos += len(t)
        flags = foreign_flags(words)
        historic_quotes(joined, offsets, flags)
        k = 0
        for (e, a), t in zip(segs, texts):
            n = len(WORD.findall(t))
            new = modernize_text(t, flags[k : k + n])
            k += n
            if new != t:
                setattr(e, a, new)
    log = HERE.parent / 'build' / f'modern-changes-{part["key"]}.tsv'
    log.parent.mkdir(exist_ok=True)
    with open(log, 'w', encoding='utf-8') as f:
        for (old, new), n in sorted(
            _log.items(), key=lambda kv: (-kv[1], kv[0])
        ):
            f.write(f'{n}\t{old}\t{new}\n')


def adjust(vol):
    vol['title'] = modernize_text(vol['title']).replace(
        ')', ', heutige Rechtschreibung)'
    )
    vol['description'] = (
        modernize_text(vol.get('description', ''))
        + ' Rechtschreibung nach heutigen Regeln.'
    )
    vol['principle'] = (
        'Diese Ausgabe ist eine Leseausgabe der Erstausgabe in heutiger'
        ' Rechtschreibung. Sie gibt deren Wortlaut vollständig wieder und'
        ' berichtigt nur offensichtliche Fehler; alle Eingriffe sind im'
        ' Folgenden genannt.'
    )
    for part in vol['parts']:
        for key in ('toc_contents', 'part_label'):
            if key in part:
                part[key] = modernize_text(part[key])
        if part.get('formulas'):
            part['formulas'] = [
                (
                    f
                    if f.startswith('img:')
                    else re.sub(
                        r'(?<!\\)\b[A-Za-zÄÖÜäöüß]{2,}\b',
                        lambda m: MAP.get(m.group(0), m.group(0)),
                        f,
                    )
                )
                for f in part['formulas']
            ]
        for key in ('toc_fixes',):
            if part.get(key):
                part[key] = [
                    (modernize_text(a), modernize_text(b)) for a, b in part[key]
                ]
        if part.get('toc_skip'):
            part['toc_skip'] = tuple(
                modernize_text(s) for s in part['toc_skip']
            )
        if part.get('toc_title'):
            part['toc_title'] = modernize_text(part['toc_title'])
