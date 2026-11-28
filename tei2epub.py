#!/usr/bin/env python3
"""DTA TEI-P5 (Marx, Das Kapital) -> EPUB 3."""

import argparse
import datetime
import difflib
import importlib
import os
import re
import sys
import uuid
import zipfile
from collections import Counter
from pathlib import Path

from lxml import etree

import tables

TEI = '{http://www.tei-c.org/ns/1.0}'
XML = '{http://www.w3.org/XML/1998/namespace}'
XH = 'http://www.w3.org/1999/xhtml'
EP = 'http://www.idpf.org/2007/ops'
H = '{%s}' % XH
LICENSE_URL = 'https://creativecommons.org/licenses/by-sa/4.0/deed.de'
EPT = '{%s}type' % EP

HERE = Path(__file__).parent
CSS = HERE / 'kapital.css'


def build_time():
    epoch = os.environ.get('SOURCE_DATE_EPOCH')
    if epoch:
        return datetime.datetime.fromtimestamp(
            int(epoch), datetime.timezone.utc
        )
    return datetime.datetime.now(datetime.timezone.utc)


def build_version():
    return os.environ.get('KAPITAL_VERSION', '')


def german_date(t):
    month = (
        'Januar Februar März April Mai Juni Juli August September Oktober'
        ' November Dezember'
    ).split()[t.month - 1]
    return f'{t.day}. {month} {t.year}'


DTA_VIEW = 'https://www.deutschestextarchiv.de/book/view/{}?p={}'
A11Y_SUMMARY = (
    'Fließtext mit gegliederten Überschriften, Inhaltsverzeichnis, verlinkten'
    ' Fußnoten und den Seitenzahlen der Erstausgabe; Tabellen und Formeln sind'
    ' als Text gesetzt.'
)
TABLE_CLASS = {'l': 'al', 'r': 'ar', 'u': 'un', 't': 'tx', 'm': 'al'}
TABLE_TEXT = 7  # em that a column of running text counts for at most
# classes of kapital.css with their font size and cell padding in em; a table
# gets the first one
# with which its estimated width stays within TABLE_LINE em of the running text
TABLE_SIZES = [
    ('', 0.86, 0.8),
    ('s8', 0.78, 0.8),
    ('s7', 0.7, 0.44),
    ('s6', 0.64, 0.44),
]
TABLE_LINE = 23

GREEK_VARIANTS = str.maketrans(
    {'ϰ': 'κ', 'ϱ': 'ρ', 'ϑ': 'θ', 'ϐ': 'β', 'ϕ': 'φ'}
)
CONJ = {'und', 'oder', 'bis', 'resp', 'u', 'sowie', 'zum', 'zur'}
LETTER = "A-Za-zÄÖÜäöüßÀ-ÖØ-öø-ÿ\u0370-\u03ff\u1f00-\u1fff"
BLOCK_TAGS = ('list', 'table', 'lg', 'cit')


def local(e):
    return etree.QName(e).localname if isinstance(e.tag, str) else None


def text_of(e):
    e = etree.fromstring(etree.tostring(e))
    for n in list(e.iter(TEI + 'note')) + list(e.iter(TEI + 'sic')):
        remove_keep_tail(n)
    return ' '.join(''.join(e.itertext()).split())


def remove_keep_tail(e):
    parent, prev, tail = e.getparent(), e.getprevious(), e.tail or ''
    if prev is not None:
        prev.tail = (prev.tail or '') + tail
    else:
        parent.text = (parent.text or '') + tail
    parent.remove(e)


# ---------------------------------------------------------------- preprocessing


def apply_raw_fixes(s, fixes):
    """(old, new) must match exactly once; (old, new, n) exactly n times. The
    ditto mark 〃 of the transcription becomes „ as in the print, and the s
    of a possessive joins the highlighted name before it."""
    for old, new, *n in fixes:
        n = n[0] if n else 1
        if s.count(old) != n:
            sys.exit(
                f'raw fix: {old!r} found {s.count(old)} times, expected {n}'
            )
        s = s.replace(old, new)
    s = s.replace('&#x3003;', '&#x201E;')
    s = re.sub(r'(&#x2019;|’)</hi>s(?![A-Za-zäöüß])', r'\1s</hi>', s)
    return re.sub(r'<fw\b[^>]*>.*?</fw>', '', s, flags=re.S)


SPACED_HYPHEN = re.compile(
    rf'(?<=[{LETTER}])((?:</hi>)?) - ((?:<hi[^>]*>)?)(?=[{LETTER}])'
)


def spaced_hyphens(s):
    """A hyphen between spaces: suspended before a conjunction (Gold- resp.
    Silber), otherwise joining a compound (New-York)."""

    def sub(m):
        if re.match(
            r'(und|oder|bis|als|wie|noch)\b|resp\.', m.string[m.end() :]
        ):
            return m.group(1) + '- ' + m.group(2)
        return m.group(1) + '-' + m.group(2)

    parts = re.split(r'(<formula\b.*?</formula>)', s, flags=re.S)
    return ''.join(
        p if p.startswith('<formula') else SPACED_HYPHEN.sub(sub, p)
        for p in parts
    )


def merge_note_chains(root):
    by_id = {
        n.get(XML + 'id'): n
        for n in root.iter(TEI + 'note')
        if n.get(XML + 'id')
    }
    merged = 0
    for cont in [n for n in root.iter(TEI + 'note') if n.get('prev')]:
        head = by_id[cont.get('prev').lstrip('#')]
        while head.get('prev'):
            head = by_id[head.get('prev').lstrip('#')]
        lb = etree.SubElement(head, TEI + 'lb')
        lb.tail = cont.text
        for child in list(cont):
            head.append(child)
        remove_keep_tail(cont)
        merged += 1
    return merged


def normalize_greek(root):
    for t in root.iter():
        if isinstance(t.tag, str):
            if t.text:
                t.text = t.text.translate(GREEK_VARIANTS)
            if t.tail:
                t.tail = t.tail.translate(GREEK_VARIANTS)


def is_empty_table(e):
    return local(e) == 'table' and all(
        not (len(c) or (c.text or '').strip()) for c in e.iter(TEI + 'cell')
    )


def en_dashes(root):
    """Em dashes of the print as en dashes, as in present-day German typesetting
    (ranges, Gedankenstrich)."""
    n = 0
    for e in root.find(TEI + 'text').iter():
        if not isinstance(e.tag, str):
            continue
        for attr in ('text', 'tail'):
            v = getattr(e, attr)
            if v and '—' in v:
                n += v.count('—')
                setattr(e, attr, v.replace('—', '–'))
    return n


DOTS = re.compile(r'(^|[^\s.])(\s?)\.((?:\s?\.){2,})(?=\s*(.?))')


def ellipses(root):
    """Spaced dots of the print as an ellipsis; a dot set close to the word
    stays as a full stop. Long runs and runs before a number are leaders and
    only kept from breaking. The two dots ‥ of the transcription likewise."""

    def sub(m):
        if m.group(3).count('.') >= 6 or m.group(4).isdigit():
            return (
                m.group(1)
                + m.group(2)
                + re.sub(
                    r'\s', '\u202f', m.group(0)[len(m.group(1) + m.group(2)) :]
                )
            )
        if not m.group(1):
            return m.group(2) + '…'
        return m.group(1) + ('\u00a0…' if m.group(2) else '.\u00a0…')

    for e in root.find(TEI + 'text').iter():
        if not isinstance(e.tag, str):
            continue
        for attr in ('text', 'tail'):
            v = getattr(e, attr)
            if v and '‥' in v:
                v = re.sub(r'‥(?!\s*\d)', '…', v)
                setattr(e, attr, v)
            if v and ('. .' in v or '...' in v):
                setattr(e, attr, DOTS.sub(sub, v))


STOP = re.compile(r'“?[.!?]“?|“')


def marks_after_stop(root):
    """Footnote marks after the full stop and closing quote that the print sets
    them before; after an abbreviation the stop is not doubled."""
    for note in root.iter(TEI + 'note'):
        if note.get('place') != 'foot' or local(note.getparent()) == 'cell':
            continue
        host = note
        if (
            not note.tail
            and note.getnext() is not None
            and local(note.getnext()) == 'lb'
        ):
            host = note.getnext()
        m = STOP.match(host.tail or '')
        if not m:
            continue
        host.tail = host.tail[m.end() :]
        stop = m.group()
        prev = note.getprevious()
        if prev is not None:
            before = prev.tail or ''.join(prev.itertext())
        else:
            before = note.getparent().text or ''
        if stop.startswith('.') and before.rstrip().endswith('.'):
            stop = stop[1:]
        if prev is not None:
            prev.tail = (prev.tail or '').rstrip() + stop
        else:
            parent = note.getparent()
            parent.text = (parent.text or '').rstrip() + stop


def merge_empty_tables(root):
    for tab in list(root.iter(TEI + 'table')):
        if tab.getparent() is None or not is_empty_table(tab):
            continue
        nxt = tab.getnext()
        while (
            nxt is not None
            and is_empty_table(nxt)
            and not (tab.tail or '').strip()
        ):
            tab.set('_count', str(int(tab.get('_count', '1')) + 1))
            tab.tail = nxt.tail
            nxt.getparent().remove(nxt)
            nxt = tab.getnext()


def text_width(s):
    """Rough width of a string in em, for a text face of ordinary width."""
    return sum(
        (
            0.5
            if ch.isdigit() or ch == '\u2007'
            else (
                0.75
                if ch in '½⅓⅔¼¾⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞—%'
                else (
                    0.6
                    if ch in '+=×−'
                    else (
                        0.64
                        if ch.isupper() or ch in 'mw'
                        else 0.46 if ch.isalpha() else 0.26
                    )
                )
            )
        )
        for ch in s
    )


def link_page(item, prefix):
    """Link the page number that opens an entry of an errata list."""
    m = re.match(r'(\s*(?:S\.|Seite|„)\s*)(\d+)', item.text or '')
    if m:
        a = etree.Element(H + 'a', href=f'@@PAGE:{prefix}{m.group(2)}@@')
        a.text, a.tail, item.text = m.group(2), item.text[m.end() :], m.group(1)
        item.insert(0, a)


def insert_table_notes(root, part):
    """Footnotes whose markers stand in untranscribed tables, after the table
    (group) they belong to."""
    groups = []
    for t in root.iter(TEI + 'table'):
        if not is_empty_table(t):
            continue
        prev = t.getprevious()
        if (
            groups
            and prev is not None
            and is_empty_table(prev)
            and not (prev.tail or '').strip()
        ):
            groups[-1] = t
        else:
            groups.append(t)
    for tid, (n, inner, *_) in part['table_notes'].items():
        if (part['table_dir'] / f'tab-{tid}.txt').exists():
            continue
        last = groups[part['tables'].index(tid)]
        note = etree.fromstring(
            f'<note xmlns="{TEI[1:-1]}" place="foot" n="{n}">{inner}</note>'
        )
        note.tail, last.tail = last.tail, None
        last.addnext(note)


def lift_table(tab):
    """Move a table out of the inline element that wraps it together with its
    caption."""
    hi = tab.getparent()
    rest = etree.Element(hi.tag, hi.attrib)
    rest.text, tab.tail = tab.tail, None
    for sib in list(tab.itersiblings()):
        rest.append(sib)
    rest.tail, hi.tail = hi.tail, None
    if len(hi) and hi[-1].tag == TEI + 'lb' and not (hi[-1].tail or '').strip():
        hi.remove(hi[-1])
    hi.addnext(tab)
    if len(rest) or (rest.text or '').strip():
        tab.addnext(rest)
    else:
        tab.tail = rest.tail


def fill_tables(root, part):
    """Name the tables the DTA left empty after the table list of the part;
    those transcribed in tab-<name>.txt take the place of the empty ones."""
    empty = [t for t in root.iter(TEI + 'table') if is_empty_table(t)]
    for tab, tid in zip(empty, part.get('tables') or ()):
        tab.set('_tid', tid)
        src = part['table_dir'] / f'tab-{tid}.txt'
        if not src.exists():
            continue
        if tab.getparent().tag == TEI + 'hi':
            lift_table(tab)
        new = tables.parse(src.read_text(encoding='utf-8'))
        for t in new:
            for note in [
                x for x in t.iter(TEI + 'note') if not len(x) and not x.text
            ]:
                n, inner = part['table_notes'][tid][:2]
                filled = etree.fromstring(
                    f'<note xmlns="{TEI[1:-1]}" place="foot"'
                    f' n="{n}">{inner}</note>'
                )
                filled.tail = note.tail
                note.getparent().replace(note, filled)
        new[-1].tail = tab.tail
        parent, at = tab.getparent(), tab.getparent().index(tab)
        parent.remove(tab)
        new[0].set('_count', tab.get('_count', '1'))
        for i, t in enumerate(new):
            parent.insert(at + i, t)


def annotate_pages(root):
    """Page of each table, formula and figure, and the document-order index of
    the empty formulas, which the formula list of a part refers to."""
    page, facs = '', 0
    seq = Counter()
    for e in root.iter():
        tag = local(e)
        if tag == 'pb':
            page = (e.get('n') or page).strip('[]')
            facs = int((e.get('facs') or '#f0')[2:])
        elif tag in ('table', 'formula', 'figure'):
            if not e.get('_page'):
                e.set('_page', page)
                e.set('_facs', str(facs))
            if tag == 'formula' and e.get('notation') != 'TeX':
                e.set('_idx', str(seq[tag]))
                seq[tag] += 1


def dehyphenate(s):
    marker = re.sub(r'-((?:</hi>)*)\s*<lb/>', '\x00', s)
    plain = re.sub(r'<[^>]+>', ' ', marker)
    vocab = Counter(
        t.lower()
        for t in re.findall(
            rf"(?<![\x00{LETTER}])[{LETTER}]+"
            rf"(?:-[{LETTER}]+)*(?![\x00{LETTER}])",
            plain,
        )
    )
    stats, kept = Counter(), Counter()
    pat = re.compile(
        rf"(?P<w1>[{LETTER}'’]+)(?P<c0>(?:</hi>)*)-"
        rf"(?P<close>(?:</hi>)*)"
        rf"(?P<mid>(?:\s*<lb/>)+\s*(?:(?:<pb [^>]*/>|<milestone"
        rf" [^>]*/>|<cb/>)\s*(?:<lb/>\s*)*)*)"
        rf"(?P<open>(?:<hi rendition=\"[^\"]*\">)*)(?P<w2>[{LETTER}]+)"
    )

    def repl(m):
        w1, w2, tags = m['w1'], m['w2'], m['close'] + m['open']
        pbs = ''.join(re.findall(r'<pb [^>]*/>|<milestone [^>]*/>', m['mid']))
        joined = (w1 + w2).lower()
        sep = ''
        if w2.lower() in CONJ:
            kind, a, hy, b, sep = 'keep', w1, '-', w2, ' '
        elif w2[0].isupper() or vocab[(w1 + '-' + w2).lower()] > vocab[joined]:
            kind, a, hy, b = 'keep', w1, '-', w2
        elif (
            w1.endswith('k')
            and w2.startswith('k')
            and vocab[(w1[:-1] + 'ck' + w2[1:]).lower()] > vocab[joined]
        ):
            kind, a, hy, b = 'ck', w1[:-1] + 'c', '', w2
        elif (
            len(w1) > 1
            and w1[-1] == w1[-2] == w2[0]
            and vocab[(w1 + w2[1:]).lower()] > vocab[joined]
        ):
            kind, a, hy, b = 'triple', w1, '', w2[1:]
        else:
            kind, a, hy, b = 'join', w1, '', w2
        stats[kind] += 1
        if kind != 'join':
            kept[a + hy + sep + b] += 1
        if sep:
            return a + m['c0'] + hy + tags + pbs + sep + b
        return a + m['c0'] + hy + tags + b + pbs

    return pat.sub(repl, s), stats, kept


# ---------------------------------------------------------------- XHTML helpers


def el(parent, tag, cls=None, **attrs):
    e = etree.SubElement(parent, H + tag)
    if cls:
        e.set('class', cls)
    for k, v in attrs.items():
        e.set(k.rstrip('_'), v)
    return e


def add_text(parent, s):
    if not s:
        return
    if len(parent):
        parent[-1].tail = (parent[-1].tail or '') + s
    else:
        parent.text = (parent.text or '') + s


def rstrip_end(e):
    if len(e):
        if e[-1].tail:
            e[-1].tail = e[-1].tail.rstrip()
    elif e.text:
        e.text = e.text.rstrip()


def noteref_link(parent, href, label, cls, rid=None):
    sup = el(parent, 'sup', cls)
    a = el(sup, 'a', href=href, role='doc-noteref')
    if rid:
        a.set('id', rid)
    a.set(EPT, 'noteref')
    a.text = label
    return sup


# ---------------------------------------------------------------- formulas (TeX
# subset)


def read_group(src, i):
    assert src[i] == '{', (src, i)
    depth, j = 0, i
    while True:
        depth += {'{': 1, '}': -1}.get(src[j], 0)
        if depth == 0:
            return src[i + 1 : j], j + 1
        j += 1


def split_top(src, sep):
    parts, depth, last, i = [], 0, 0, 0
    while i < len(src):
        c = src[i]
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
        elif depth == 0 and src.startswith(sep, i):
            parts.append(src[last:i])
            i += len(sep)
            last = i
            continue
        i += 1
    parts.append(src[last:])
    return parts


def read_arg(src, i):
    while i < len(src) and src[i] == ' ':
        i += 1
    if src[i] == '{':
        return read_group(src, i)
    if src[i] == '\\':
        m = re.match(r'\\[A-Za-z]+', src[i:])
        return m.group(0), i + len(m.group(0))
    return src[i], i + 1


def tex_text(parent, s, roman):
    s = s.replace('&lt;', '<').replace('&gt;', '>').replace('~', '\u00a0')
    s = re.sub(r'(?<=\S) - (?=\S|$)', ' – ', s)
    if roman:
        s = re.sub(r'^- ', '– ', s)
    add_text(parent, s)


def braced(rows, body, parent, roman):
    """Text under overlapping brackets. rows names the brackets of each row,
    above (^) and below (_) the text, nearest row first, e.g. '^tu _ab _c'; body
    holds 'text :ids' segments separated by '|'.
    """
    rows = rows.split()
    segs = []
    for seg in split_top(body, '|'):
        text, _, ids = seg.rpartition(':') if ':' in seg else (seg, '', '')
        segs.append((text.strip(), set(ids.replace(' ', ''))))
    box = el(parent, 'span', 'brz')
    box.set('data-rows', ' '.join(rows))
    above = [r[1:] for r in rows if r[0] == '^'][::-1]
    below = [r[1:] for r in rows if r[0] == '_']
    for n, (text, ids) in enumerate(segs):
        s = el(box, 'span', 'bseg')
        s.set('data-on', ' '.join(sorted(ids)))

        def bar(row, side):
            on = ids & set(row)
            cls = ['bar', side] + (['on'] if on else [])
            cls += (
                ['l']
                if any(
                    n == min(k for k, x in enumerate(segs) if b in x[1])
                    for b in on
                )
                else []
            )
            cls += (
                ['r']
                if any(
                    n == max(k for k, x in enumerate(segs) if b in x[1])
                    for b in on
                )
                else []
            )
            el(s, 'span', ' '.join(cls)).text = '\u00a0'

        for row in above:
            bar(row, 'up')
        render_tex(text, el(s, 'span', 'btx'), roman)
        for row in below:
            bar(row, 'dn')


def render_tex(src, parent, roman=False):
    i, buf = 0, ''

    def flush():
        nonlocal buf
        if buf:
            tex_text(parent, buf, roman)
            buf = ''

    while i < len(src):
        if src.startswith('\\frac', i):
            flush()
            a, i = read_arg(src, i + 5)
            b, i = read_arg(src, i)
            fr = el(parent, 'span', 'frac')
            render_tex(a.strip(), el(fr, 'span', 'num'), roman)
            el(fr, 'span', 'fs').text = '/'
            render_tex(b.strip(), el(fr, 'span', 'den'), roman)
        elif src.startswith('\\mathrm', i):
            flush()
            a, i = read_arg(src, i + 7)
            render_tex(a.strip(), parent, True)
        elif src.startswith('\\ldots', i):
            flush()
            add_text(parent, '…')
            i += 6
        elif src.startswith('\\begin{cases}', i):
            flush()
            end = src.index('\\end{cases}', i)
            rows = split_top(src[i + 13 : end], '\\\\')
            box = el(parent, 'span', 'cases')
            for r in rows:
                render_tex(r.strip(), el(box, 'span', 'row'), roman)
            i = end + 11
        elif src.startswith('\\bcases', i) or src.startswith('\\rows', i):
            flush()
            kind = 'cases bb' if src.startswith('\\bcases', i) else 'cases nb'
            a, i = read_arg(src, i + (7 if kind == 'cases bb' else 5))
            box = el(parent, 'span', kind)
            for r in split_top(a, '\\\\'):
                render_tex(r.strip(), el(box, 'span', 'row'), roman)
        elif src.startswith('\\braced', i):
            flush()
            a, i = read_arg(src, i + 7)
            b, i = read_arg(src, i)
            braced(a, b, parent, roman)
        elif src.startswith('\\lab', i):
            flush()
            a, i = read_arg(src, i + 4)
            b, i = read_arg(src, i)
            box = el(parent, 'span', 'lab')
            el(box, 'span', 'lt').text = a
            el(box, 'span', 'lbr').text = '\u00a0'
            render_tex(b, el(box, 'span', 'ln'), roman)
        elif src.startswith('\\nt', i):
            flush()
            a, i = read_arg(src, i + 3)
            b, i = read_arg(src, i)
            box = el(parent, 'span', 'lab nt')
            el(box, 'span', 'lt').text = a
            render_tex(b, el(box, 'span', 'ln'), roman)
        elif src.startswith('\\ov', i):
            flush()
            a, i = read_arg(src, i + 3)
            render_tex(a, el(parent, 'span', 'ov'), roman)
        elif src.startswith('\\br', i) and not src.startswith('\\brace', i):
            flush()
            a, i = read_arg(src, i + 3)
            box = el(parent, 'span', 'stack')
            for r in split_top(a, '\\\\'):
                render_tex(r.strip(), el(box, 'span', 'row'), roman)
        elif src[i] == '{':
            flush()
            g, i = read_group(src, i)
            parts = split_top(g, '\\atop')
            if len(parts) == 2:
                box = el(parent, 'span', 'stack')
                for r in parts:
                    render_tex(r.strip(), el(box, 'span', 'row'), roman)
            else:
                render_tex(g, parent, roman)
        elif src[i] in '_^':
            flush()
            tag = 'sub' if src[i] == '_' else 'sup'
            a, i = read_arg(src, i + 1)
            render_tex(a, el(parent, tag), roman)
        else:
            buf += src[i]
            i += 1
    flush()


# ---------------------------------------------------------------- converter


class Converter:
    def __init__(self, vol):
        self.vol = vol
        self.pending_pb = []
        self.pages = []
        self.file = None
        self.notes = []
        self.note_seq = 0
        self.toc = []
        self.toc_front = []
        self.table_widths = []
        self.part = None

    def start_part(self, part):
        self.part = part
        part['text_tables'] = []
        part['formula_pages'] = []
        part['formula_index'] = 0
        part['figure_page'] = None

    # -- pages ------------------------------------------------------------

    def page_label(self, n):
        return self.part['prefix'] + n.strip('[]')

    def page_anchor(self, parent, n):
        label = self.page_label(n)
        pid = 'p' + self.part['idp'] + n.strip('[]')
        sp = el(parent, 'span', 'pb', id=pid, role='doc-pagebreak')
        sp.set('aria-label', label)
        sp.set(EPT, 'pagebreak')
        self.pages.append((label, self.file, pid))

    def new_block(self, parent, tag, cls=None, **attrs):
        b = el(parent, tag, cls, **attrs)
        for n in self.pending_pb:
            self.page_anchor(b, n)
        self.pending_pb = []
        return b

    # -- inline -----------------------------------------------------------

    def inline(self, node, out, br=False):
        add_text(out, node.text)
        for c in node:
            self.inline_el(c, out, br)
            add_text(out, c.tail)

    def inline_el(self, c, out, br):
        tag = local(c)
        if tag is None or tag in ('milestone', 'cb'):
            return
        if tag == 'lb':
            if br:
                rstrip_end(out)
                last = out[-1] if len(out) else None
                if (
                    last is None
                    or last.get('class') not in ('line', 'blockish')
                    or (last.tail or '').strip()
                ):
                    el(out, 'br')
            else:
                add_text(out, ' ')
        elif tag == 'pb':
            if c.get('n'):
                self.page_anchor(out, c.get('n'))
        elif tag == 'hi':
            self.hi(c, out, br)
        elif tag == 'note':
            self.noteref(c, out)
        elif tag == 'formula':
            self.formula(c, out)
        elif tag == 'choice':
            corr = c.find(TEI + 'corr')
            self.inline(corr if corr is not None else c, out, br)
        elif tag == 'seg':
            spec = re.findall(r'(\D+?)(\d+)', c.text or '')
            self.line_figure(out, [(lab.strip(), int(n)) for lab, n in spec])
        elif tag == 'figure':
            self.figure(c, out)
        elif tag in (
            'supplied',
            'quote',
            'ref',
            'bibl',
            'docAuthor',
            'pubPlace',
            'publisher',
            'docDate',
        ):
            self.inline(c, out, br)
        elif tag == 'table' and is_empty_table(c):
            self.table(c, out)
        elif tag in BLOCK_TAGS:
            span = el(out, 'span', 'blockish')
            self.inline(c, span, True)
        elif tag in ('item', 'row', 'l', 'head'):
            span = el(out, 'span', 'line')
            self.inline(c, span, False)
        elif tag == 'cell':
            self.inline(c, el(out, 'span', 'cell'), False)
            add_text(out, ' ')
        else:
            sys.exit(f'unhandled inline <{tag}>')

    def hi(self, c, out, br):
        rend = c.get('rendition', '')
        txt = ''.join(c.itertext())
        if rend == '#g':
            e = el(out, 'em')
        elif rend == '#i':
            if (
                re.search('[\u0370-\u03ff\u1f00-\u1fff]', txt)
                and len(txt.strip()) > 1
            ):
                e = el(out, 'span', 'grc', lang='grc')
                e.set(XML + 'lang', 'grc')
            elif txt.strip() in ('£', '℔', 'Δ', ':', '£.'):
                self.inline(c, out, br)
                return
            else:
                e = el(out, 'i')
        elif rend == '#b':
            e = el(out, 'strong')
        elif rend == '#sup':
            e = el(out, 'sup')
        elif rend == '#sub':
            e = el(out, 'sub')
        elif rend == '#u':
            e = el(out, 'span', 'u')
        elif rend == '#vf':
            e = el(out, 'span', 'vf')
            num, den = txt.split('/')
            el(e, 'sup').text = num
            e[0].tail = '/'
            el(e, 'sub').text = den
            return
        elif rend == '#fr':
            self.inline(c, out, br)
            return
        elif rend in ('#c', '#et', '#right'):
            e = el(out, 'span', rend[1:])
            self.inline(c, e, True)
            return
        else:
            sys.exit(f'unhandled rendition {rend}')
        self.inline(c, e, br)

    def formula(self, c, out):
        if c.get('notation') == 'TeX':
            render_tex(c.text or '', out)
            return
        part = self.part
        idx = int(c.get('_idx'))
        part['formula_index'] += 1
        part['formula_pages'].append(c.get('_page'))
        formulas = part.get('formulas') or []
        if idx >= len(formulas):
            sys.exit(f'formula on p. {c.get("_page")} not supplied')
        src = formulas[idx]
        display = c.get('rend') == 'display' or src.startswith('!')
        src = src.lstrip('!')
        box = el(out, 'span', 'rek disp' if display else 'rek')
        if c.get('n'):
            el(box, 'span', 'dl').text = c.get('n')
            add_text(box, ' ')
        for i, seg in enumerate(split_top(src, ' = ')):
            if i:
                add_text(box, ' ')
                seg = '= ' + seg
            render_tex(seg, el(box, 'span', 'seg'))
        add_text(box, c.get('suffix'))
        if display:
            m = re.match(r'\s*([,;.:])', c.tail or '') or re.match(
                r'\s*…\s*etc\.()', c.tail or ''
            )
            if m:
                add_text(box, m.group(1))
                c.tail = c.tail[m.end() :].lstrip()
            elif c.tail:
                c.tail = c.tail.lstrip()

    def line_figure(self, out, segs):
        wrap = el(out, 'span', 'linefig')
        for label, length in segs:
            el(wrap, 'span', 'lf-l').text = label
            if length:
                el(wrap, 'span', f'lf-s w{length}').text = '\u00a0'

    def figure(self, c, out):
        self.part['figure_page'] = c.get('_page')
        box = el(out, 'span', 'arbeitstage')
        for roman, extra in (('I', 1), ('II', 3), ('III', 6)):
            row = el(box, 'span', 'at-row')
            el(row, 'span', 'at-lab').text = f'Arbeitstag {roman}.'
            self.line_figure(row, [('a', 6), ('b', extra), ('c', 0)])

    def noteref(self, note, out):
        label = (note.get('n') or '').rstrip(')').strip()
        self.note_seq += 1
        fid, rid = f'fn{self.note_seq}', f'fr{self.note_seq}'
        rstrip_end(out)
        noteref_link(out, '@@NOTES@@#' + fid, label, 'fnref', rid)
        self.notes.append((fid, rid, label, note))

    # -- blocks -----------------------------------------------------------

    def flow(self, nodes, parent):
        for c in nodes:
            tag = local(c)
            if tag is None or tag in ('head', 'lb', 'milestone', 'cb'):
                continue
            if tag == 'p':
                self.paragraph(c, parent)
            elif tag == 'pb':
                if c.get('n'):
                    self.pending_pb.append(c.get('n'))
            elif tag == 'div':
                self.div(c, parent)
            elif tag in BLOCK_TAGS:
                self.block(c, parent)
            else:
                sys.exit(f'unhandled block <{tag}>')

    def mixed(self, node, parent, first):
        cur = first
        add_text(cur, node.text)
        for c in node:
            tail = c.tail
            if local(c) == 'list' and c.get('rendition') == '#rightBraced':
                right_text, _, rest = (tail or '').partition('\n')
                self.braced_list(c, parent, right_text)
                cur = self.new_block(parent, 'p', 'cont')
                tail = rest
            elif local(c) in BLOCK_TAGS:
                self.block(c, parent)
                cur = self.new_block(parent, 'p', 'cont')
            else:
                self.inline_el(c, cur, False)
                tail = c.tail
            add_text(cur, tail)

    def paragraph(self, p, parent, cls=None):
        self.mixed(p, parent, self.new_block(parent, 'p', cls))

    def block(self, c, parent):
        tag = local(c)
        if tag == 'list':
            if c.get('rendition') == '#rightBraced':
                self.braced_list(c, parent, '')
            else:
                self.list_(c, parent)
        elif tag == 'table':
            self.table(c, parent)
        elif tag == 'lg':
            d = self.new_block(parent, 'div', 'poem')
            for line in c.iter(TEI + 'l'):
                self.inline(line, el(d, 'div', 'l'))
        elif tag == 'cit':
            bq = self.new_block(parent, 'blockquote')
            q = c.find(TEI + 'quote')
            src = q
            if (
                len(q) == 1
                and q[0].get('rendition') == '#et'
                and not (q.text or '').strip()
            ):
                src = q[0]
            self.inline(src, el(bq, 'p', 'verse'), True)

    def list_(self, lst, parent):
        items = lst.findall(TEI + 'item')
        if any(
            it.find(TEI + 'list') is not None
            and it.find(TEI + 'list').get('rendition') == '#rightBraced'
            for it in items
        ):
            for it in items:
                inner = it.find(TEI + 'list')
                right = el(etree.Element('x'), 'td')
                add_text(right, inner.tail)
                nxt = inner.getnext()
                while nxt is not None:
                    self.inline_el(nxt, right, False)
                    add_text(right, nxt.tail)
                    nxt = nxt.getnext()
                self.braced_list(inner, parent, right)
            return
        corr = lst.get('type') == 'corrigenda'
        d = self.new_block(parent, 'div', 'list corr' if corr else 'list')
        for c in lst:
            tag = local(c)
            if tag == 'item':
                item = el(d, 'div', 'item')
                self.inline(c, item)
                if corr:
                    link_page(item, lst.get('n', self.part['prefix']))
            elif tag == 'pb' and c.get('n'):
                self.page_anchor(d, c.get('n'))

    def braced_list(self, inner, parent, right):
        t = self.new_block(parent, 'table', 'brace')
        tr = el(t, 'tr')
        left = el(tr, 'td', 'bl')
        for i, it in enumerate(inner.findall(TEI + 'item')):
            if i:
                el(left, 'br')
            self.inline(it, left)
            rstrip_end(left)
        el(tr, 'td', 'bm').text = '\u00a0'
        if isinstance(right, str):
            el(tr, 'td', 'br').text = right.strip()
        else:
            right.set('class', 'br')
            tr.append(right)

    def table(self, tab, parent):
        if is_empty_table(tab):
            sys.exit(f'table on p. {tab.get("_page")} not supplied')
        if tab.get('_cols'):
            self.text_table(tab, parent)
            return
        t = self.new_block(parent, 'table', 'data')
        for row in tab.findall(TEI + 'row'):
            tr = el(t, 'tr')
            for cell in row.findall(TEI + 'cell'):
                td = el(tr, 'td')
                self.inline(cell, td)
                rstrip_end(td)

    def text_table(self, tab, parent):
        self.part['text_tables'].append(
            (tab.get('_page'), tab.get('_facs'), int(tab.get('_count', '0')))
        )
        types = tab.get('_cols').split()
        t = self.new_block(parent, 'table', 'tab')
        t.set('data-cols', tab.get('_cols'))
        breaks = list(t)
        for pb in breaks:
            t.remove(pb)
        rows = tab.findall(TEI + 'row')
        width, wide = [0] * len(types), []
        for i, row in enumerate(rows):
            head = row.get('role') == 'label'
            cls = (
                ['h']
                if head
                else (
                    ['rule']
                    if row.get('_rule')
                    or (i and rows[i - 1].get('role') == 'label')
                    else []
                )
            )
            tr = el(t, 'tr', ' '.join(cls) or None)
            for cell in row.findall(TEI + 'cell'):
                j, span, down = (
                    int(cell.get('_col')),
                    int(cell.get('cols', 1)),
                    int(cell.get('rows', 1)),
                )
                if head:
                    c = el(
                        tr,
                        'th',
                        (
                            TABLE_CLASS[types[j]]
                            if span == 1 and types[j] in 'lr'
                            else None
                        ),
                    )
                    if (
                        span > 1
                        and i + down < len(rows)
                        and rows[i + down].get('role') == 'label'
                    ):
                        c = el(c, 'span', 'grp')
                else:
                    kind = (
                        [TABLE_CLASS[types[j]]]
                        if span == 1 and types[j] in TABLE_CLASS
                        else []
                    )
                    if types[j + span : j + span + 1] == ['u']:
                        kind.append('pu')
                    c = el(tr, 'td', ' '.join(kind) or None)
                self.inline(cell, c, br=True)
                rstrip_end(c)
                if c.tag == H + 'th' and not ''.join(c.itertext()).strip():
                    c.tag = H + 'td'
                lines = re.split(
                    r'<[^<>]*br\s*/>',
                    etree.tostring(c, encoding='unicode', with_tail=False),
                )
                w = max(text_width(re.sub(r'<[^>]*>', '', ln)) for ln in lines)
                if types[j] == 't' and not head:
                    words = re.split(
                        r'[\s-]+', re.sub(r'<[^>]*>', '', lines[0])
                    )
                    w = max(
                        min(w, TABLE_TEXT),
                        max(text_width(x) for x in words) + 0.4,
                    )
                if span == 1:
                    width[j] = max(width[j], w)
                elif head or span < len(types):
                    wide.append((j, span, w))
                c = c if c.tag != H + 'span' else c.getparent()
                if span > 1:
                    c.set('colspan', str(span))
                if down > 1:
                    c.set('rowspan', str(down))
        for j, span, w in wide:
            width[j] += max(0, w + 0.65 * (1 - span) - sum(width[j : j + span]))
        for pb in reversed(breaks):
            first = t[0][0]
            pb.tail, first.text = first.text, None
            first.insert(0, pb)
        gaps = sum(0.5 if k == 'u' else 1 for k in types)
        fit = [
            (cls, (sum(width) + gaps * pad) * size)
            for cls, size, pad in TABLE_SIZES
        ]
        cls, em = next((x for x in fit if x[1] <= TABLE_LINE), fit[-1])
        t.set('class', f'tab {cls}'.strip())
        t.set('data-em', str(round(sum(width) + gaps * 0.8)))
        self.table_widths.append(
            (self.page_label(tab.get('_page')), round(em, 1))
        )

    def heading(self, head, parent, level, hid, toc=True, cls=None):
        h = self.new_block(parent, f'h{min(level, 6)}', cls, id=hid)
        self.inline(head, h, br=level <= self.part['br_levels'])
        etree.strip_tags(h, H + 'em', H + 'strong')
        for extra in h.findall(H + 'br')[1:]:
            add_text_before = extra.getprevious()
            if add_text_before is not None:
                add_text_before.tail = (
                    (add_text_before.tail or '') + ' ' + (extra.tail or '')
                )
            else:
                h.text = (h.text or '') + ' ' + (extra.tail or '')
            h.remove(extra)
        rstrip_end(h)
        if toc:
            self.toc_add(level, head, hid)
        return h

    def div(self, d, parent):
        level = int(d.get('n', '2'))
        head = d.find(TEI + 'head')
        if head is not None:
            skip = any(
                text_of(head).startswith(s)
                for s in self.part.get('toc_skip', ())
            )
            self.heading(
                head,
                parent,
                level,
                f'h{len(self.toc) + len(self.toc_front) + 1}_{self.note_seq}',
                toc=not skip,
            )
        self.flow(d, parent)

    def toc_add(self, level, head, hid):
        h = etree.fromstring(etree.tostring(head))
        for n in list(h.iter(TEI + 'note')) + list(h.iter(TEI + 'sic')):
            remove_keep_tail(n)
        txt = text_of(h).rstrip('.')
        for old, new in self.part.get('toc_fixes', ()):
            txt = txt.replace(old, new)
        txt = PRIMES.sub(
            lambda m: m.group(1) + PRIME_MARKS[len(m.group(2))], txt
        )
        self.toc.append((level, txt, self.file, hid))


# ---------------------------------------------------------------- documents

# U+202F marks a narrow space; wrap_narrow() turns it into a thin space inside
# span.nobr
NBSP_RULES = [
    (re.compile(r'\bu\. ?s\. ?([wf])\.'), 'u.\u202fs.\u202f\\1.'),
    (re.compile(r'\bu\. d\. g\.'), 'u.\u202fd.\u202fg.'),
    (
        re.compile(
            r'\b(z|Z|d|D|u|U|s|l|v|i|o|resp|vgl)\.'
            r' (B|h|s|a|c|o|u|e|g|i|w|T|dgl|dergl)\.'
            r'(?!\u202f)'
        ),
        '\\1.\u202f\\2.',
    ),
    (re.compile(r'\bPfd\. (St|Sterl)\b'), 'Pfd.\u202f\\1'),
    (re.compile(r'(\d)(£|℔)'), '\\1\u202f\\2'),
    (re.compile(r'([\d½⅓⅔¼¾⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞]) (%|£|℔)'), '\\1\u202f\\2'),
    (
        re.compile(
            r'([\d½⅓⅔¼¾⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞])'
            r' (Pfd\.|l\.|sh\b|d\.|lbs?\.|fcs?\.'
            r'|Acres|Stunden|Ellen|Quarters?|qrs?\.)'
        ),
        '\\1\u00a0\\2',
    ),
    (
        re.compile(r'(?<![\d½⅓⅔¼¾⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞]\u202f)(£|℔) (\d)'),
        '\\1\u202f\\2',
    ),
    (re.compile(r'([½⅓⅔¼¾⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞])(sh\.|d\.)'), '\\1\u00a0\\2'),
    (re.compile(r'\b(S|p|pp|Z|Nr|No|n|t|ch|Bd|Vol)\. (\d)'), '\\1.\u00a0\\2'),
    (re.compile(r'§\. (\d)'), '§.\u00a0\\1'),
]
NARROW = re.compile(r'(?:\S|\u202f)*\u202f(?:\S|\u202f)*')
# G', W'', m'n, kp': the print's apostrophes after a variable are primes (but
# not in l'homme)
PRIMES = re.compile(
    rf"(?<![{LETTER}])([A-Za-z]|Pm|kp|Bp|bp|Cz|Kz)('{{1,3}})(?![{LETTER}]{{3}})"
)
PRIME_MARKS = {1: '′', 2: '″', 3: '″′'}


def join_centered(root):
    """Centered and right-aligned blocks keep the print's line breaks only where
    a line is short (lists, formulas)."""
    for sp in list(root.iter(H + 'span')):
        if (
            sp.get('class') not in ('c', 'et')
            or sp.find('.//' + H + 'br') is None
        ):
            continue
        tail, sp.tail = sp.tail, None
        segs = etree.tostring(sp, encoding='unicode').split('<br/>')
        out = segs[0]
        for seg in segs[1:]:
            prev = re.sub(r'<[^>]+>', '', out.split('<br/>')[-1]).strip()
            nxt = re.sub(r'<[^>]+>', '', seg).strip()
            if (
                len(prev) >= 40
                and re.search(rf'[{LETTER},]$', prev)
                and re.match(rf'[{LETTER}\d\u00bd]', nxt)
            ):
                out += ' ' + seg
            else:
                out += '<br/>' + seg
        new = etree.fromstring(out)
        new.tail = tail
        sp.getparent().replace(sp, new)


def wrap_narrow(root):
    """Thin spaces don't stretch in justified text, but allow a break; keep the
    group together."""
    n = 0
    for e in list(root.iter()):
        if not isinstance(e.tag, str):
            continue
        for attr in ('text', 'tail'):
            v = getattr(e, attr)
            if not v or '\u202f' not in v:
                continue
            if e.tag == H + 'title':
                setattr(e, attr, v.replace('\u202f', '\u00a0'))
                continue
            parts = NARROW.split(v)
            groups = NARROW.findall(v)
            setattr(e, attr, parts[0])
            if attr == 'text':
                parent, pos = e, 0
            else:
                parent, pos = e.getparent(), e.getparent().index(e) + 1
            for k, (g, rest) in enumerate(zip(groups, parts[1:])):
                sp = etree.Element(H + 'span', {'class': 'nobr'})
                sp.text, sp.tail = g.replace('\u202f', '\u2009'), rest
                parent.insert(pos + k, sp)
            n += len(groups)
    return n


def split_displays(root):
    for p in list(root.iter(H + 'p')):
        disp = next(
            (d for d in p if 'disp' in (d.get('class') or '').split()), None
        )
        if disp is None:
            continue
        before = list(p)[: p.index(disp)]
        if not (p.text or '').strip() and all(
            b.get('class') == 'pb' and not (b.tail or '').strip()
            for b in before
        ):
            continue
        head = etree.Element(H + 'p', dict(p.attrib))
        p.addprevious(head)
        head.text, p.text = p.text, None
        for b in before:
            head.append(b)
        p.attrib.pop('id', None)
        p.set('class', ' '.join(filter(None, [p.get('class'), 'cont'])))


def tidy(root):
    split_displays(root)
    for e in root.iter():
        if not isinstance(e.tag, str):
            continue
        for attr in ('text', 'tail'):
            v = getattr(e, attr)
            if v:
                v = re.sub(r'[ \t\r\n]+', ' ', v)
                for rx, rep in NBSP_RULES:
                    v = rx.sub(rep, v)
                v = PRIMES.sub(
                    lambda m: m.group(1) + PRIME_MARKS[len(m.group(2))], v
                )
                setattr(e, attr, v)
    for e in root.iter(H + 'span'):
        if e.get('class') == 'frac' and re.match(r' [%£℔]', e.tail or ''):
            e.tail = '\u00a0' + e.tail[1:]
    for e in root.iter(H + 'span'):
        if e.get('class') != 'pb' or not (e.tail or '').startswith(' '):
            continue
        prev = e.getprevious()
        while prev is not None and prev.get('class') == 'pb' and not prev.tail:
            prev = prev.getprevious()
        before = prev.tail if prev is not None else e.getparent().text
        if before is None or before.endswith(' '):
            e.tail = e.tail.lstrip()
    for e in root.iter():
        if (
            isinstance(e.tag, str)
            and len(e) == 0
            and e.text
            and e.text.startswith(' ')
            and e.tag in (H + 'em', H + 'i')
        ):
            prev = e.getprevious()
            before = prev.tail if prev is not None else e.getparent().text
            if before and before.endswith(' '):
                e.text = e.text.lstrip()
    for e in root.iter(
        H + 'p',
        H + 'h1',
        H + 'h2',
        H + 'h3',
        H + 'h4',
        H + 'h5',
        H + 'h6',
        H + 'div',
        H + 'td',
    ):
        if e.text:
            e.text = e.text.lstrip()
        k = 0
        while (
            k < len(e)
            and e[k].get('class') == 'pb'
            and not e[k].text
            and not (e.text or '').strip()
        ):
            if e[k].tail:
                e[k].tail = e[k].tail.lstrip()
                if e[k].tail:
                    break
            k += 1
        rstrip_end(e)
    for br in root.iter(H + 'br'):
        if br.tail:
            br.tail = br.tail.lstrip()
    for sp in root.iter(H + 'span'):
        if (
            (sp.get('class') or '').startswith('rek')
            and sp.tail
            and re.match(r' [+=—-] ', sp.tail)
        ):
            sp.tail = '\u00a0' + sp.tail[1:3] + '\u00a0' + sp.tail[3:]
    for sp in root.iter(H + 'span'):
        if sp.get('class') in ('c', 'et', 'right'):
            if sp.text:
                sp.text = sp.text.lstrip()
            rstrip_end(sp)
            prev = sp.getprevious()
            if prev is not None and prev.tail:
                prev.tail = prev.tail.rstrip()
            elif prev is None and sp.getparent().text:
                sp.getparent().text = sp.getparent().text.rstrip()
            if sp.tail:
                sp.tail = sp.tail.lstrip()
    for p in list(root.iter(H + 'p')):
        if not len(p) and not (p.text or '').strip():
            p.getparent().remove(p)
        elif (
            all(c.get('class') == 'pb' for c in p)
            and not (p.text or '').strip()
            and not any((c.tail or '').strip() for c in p)
        ):
            nxt = p.getnext()
            if nxt is not None and nxt.tag in (
                H + 'p',
                H + 'div',
                H + 'table',
                H + 'blockquote',
            ):
                for c in reversed(list(p)):
                    nxt.insert(0, c)
                    c.tail = None
                p.getparent().remove(p)
    join_centered(root)
    wrap_narrow(root)


def xhtml_doc(title, body_cls=None, css='../css/kapital.css'):
    html = etree.Element(H + 'html', nsmap={None: XH, 'epub': EP})
    html.set('lang', 'de')
    html.set(XML + 'lang', 'de')
    head = el(html, 'head')
    el(head, 'meta', charset='utf-8')
    el(head, 'title').text = title
    el(head, 'link', rel='stylesheet', type='text/css', href=css)
    body = el(html, 'body')
    if body_cls:
        body.set('class', body_cls)
    return html, body


def split_blocks(html):
    """Lift centered and indented lines out of their paragraph: some reading
    systems (KOReader) mis-indent a paragraph that holds a block-level span."""
    html = etree.fromstring(etree.tostring(html))
    for p in list(html.iter(H + 'p')):
        if not any(
            c.tag == H + 'span' and c.get('class') in ('c', 'et', 'right')
            for c in p
        ):
            continue
        cur = etree.Element(H + 'p', dict(p.attrib))
        cur.text = p.text
        out = [cur]
        for c in list(p):
            if c.tag == H + 'span' and c.get('class') in ('c', 'et', 'right'):
                blk = etree.Element(H + 'p', {'class': c.get('class')})
                blk.text = c.text
                blk.extend(list(c))
                cur = etree.Element(H + 'p', {'class': 'cont'})
                cur.text = c.tail
                out += [blk, cur]
            else:
                cur.append(c)
        parent, i = p.getparent(), p.getparent().index(p)
        parent.remove(p)
        for n in out:
            if len(n) or (n.text or '').strip():
                parent.insert(i, n)
                i += 1
            elif n.text and i:
                prev = parent[i - 1]
                prev.tail = (prev.tail or '') + n.text
        last = parent[i - 1] if i else None
        nxt = last.getnext() if i else None
        if (
            i
            and last.get('class') in ('c', 'et', 'right')
            and nxt is not None
            and nxt.tag == H + 'table'
        ):
            last.set('class', last.get('class') + ' keep')
    return html


def serialize(html):
    return (
        b'<?xml version="1.0" encoding="utf-8"?>\n<!DOCTYPE html>\n'
        + etree.tostring(split_blocks(html), encoding='utf-8')
    )


class Book:
    def __init__(self, vol, fmt='epub'):
        self.vol = vol
        self.fmt = fmt
        self.C = Converter(vol)
        self.files = []
        self.file_seq = 0
        self.first_body = None
        self.stats = Counter()
        self.kept = Counter()
        self.merged = 0
        self.dashes = 0
        self.note_groups = []
        self.notes_files = []
        self.note_file = {}
        for part in vol['parts']:
            raw = Path(part['tei']).read_text(encoding='utf-8')
            part['empty_formulas'] = raw.count('<formula/>')
            raw = apply_raw_fixes(raw, part.get('raw_fixes', ()))
            if part.get('raw_hook'):
                raw = part['raw_hook'](raw)
            root = etree.fromstring(raw.encode('utf-8'))
            self.merged += merge_note_chains(root)
            if part.get('struct_hook'):
                part['struct_hook'](root)
            if part.get('table_notes'):
                insert_table_notes(root, part)
            normalize_greek(root)
            s, st, kp = dehyphenate(etree.tostring(root, encoding='unicode'))
            s = spaced_hyphens(s)
            self.stats.update(st)
            self.kept.update(kp)
            root = etree.fromstring(s.encode('utf-8'))
            merge_empty_tables(root)
            fill_tables(root, part)
            self.dashes += en_dashes(root)
            ellipses(root)
            if part.get('marks_after_stop'):
                marks_after_stop(root)
            for variant in vol.get('variants', ()):
                variant.transform(root, part)
            annotate_pages(root)
            part['root'] = root
            part['header'] = root.find(TEI + 'teiHeader')

    def name(self, stem=None):
        self.file_seq += 1
        return (
            f'{self.file_seq:02d}-{stem}.xhtml'
            if stem
            else f'{self.file_seq:02d}.xhtml'
        )

    def start(self, name, title, body_cls=None):
        self.C.file = name
        self.C.notes = []
        return xhtml_doc(title, body_cls)

    def finish(self, name, html, body):
        C = self.C
        saved, C.pending_pb = C.pending_pb, []
        if C.notes:
            sec = etree.Element(H + 'section', {'class': 'notes'})
            self.note_groups.append(
                (name, html.find(f'{H}head/{H}title').text, sec)
            )
            for fid, rid, label, note in C.notes:
                aside = el(sec, 'aside', 'fn', id=fid, role='doc-footnote')
                aside.set(EPT, 'footnote')
                first = el(aside, 'p')
                back = el(
                    first,
                    'a',
                    'fnlabel',
                    href=f'{name}#{rid}',
                    role='doc-backlink',
                )
                back.text = label
                back.tail = ' '
                C.mixed(note, aside, first)
        C.pending_pb = saved
        tidy(html)
        self.files.append((name, html))

    # -- front ------------------------------------------------------------

    def run(self):
        for part in self.vol['parts']:
            self.C.start_part(part)
            self.front(part)
            self.body(part)
            self.back(part)
        self.endnotes()
        self.notice()
        link_contents(self)

    def endnotes(self):
        toc = self.C.toc
        book = min(
            (t[0] for t in toc if re.search(r'\bBuch\b', t[1])), default=0
        )
        firsts = Counter(
            next(t[0] for t in toc if t[2] == f) for f in {t[2] for t in toc}
        )
        unit = firsts.most_common(1)[0][0]
        shown = set()
        for n, (src, title, notes) in enumerate(self.note_groups):
            name = self.name('anmerkungen')
            self.notes_files.append(name)
            html, body = self.start(name, 'Anmerkungen')
            sec = el(body, 'section', 'chapter endnotes', role='doc-endnotes')
            sec.set(EPT, 'endnotes')
            if not n:
                el(sec, 'h1', id='anmerkungen').text = 'Anmerkungen'
                toc.append((1, 'Anmerkungen', name, 'anmerkungen'))
            k = next((i for i, t in enumerate(toc) if t[2] == src), None)
            if k is None:
                el(el(sec, 'h2'), 'a', href=src).text = title
            else:
                chain, level = [toc[k]], toc[k][0]
                for t in reversed(toc[:k]):
                    if t[0] < level:
                        chain.insert(0, t)
                        level = t[0]
                j = k + 1
                while (
                    j < len(toc)
                    and toc[j][2] == src
                    and unit >= toc[j][0] > toc[j - 1][0]
                ):
                    chain.append(toc[j])
                    j += 1
                for t in chain:
                    if (
                        t[0] <= book
                        and re.search(r'\bBuch\b', t[1])
                        or id(t) in shown
                    ):
                        continue
                    shown.add(id(t))
                    tag = f'h{min(4, 2 + max(t[0], book + 1) - book - 1)}'
                    el(el(sec, tag), 'a', href=f'{t[2]}#{t[3]}').text = t[1]
            sec.append(notes)
            for aside in notes.iter(H + 'aside'):
                self.note_file[aside.get('id')] = name
            self.finish(name, html, body)

    def front(self, part):
        C = self.C
        fr = part['root'].find(f'.//{TEI}front')
        for c in fr:
            tag = local(c)
            if tag == 'pb' and c.get('n'):
                C.pending_pb.append(c.get('n'))
            elif tag == 'titlePage':
                self.titlepage(part, c)
            elif tag == 'div' and c.get('type') == 'dedication':
                self.dedication(c)
            elif tag == 'div' and c.get('type') == 'contents':
                self.contents(part, c)
            elif tag == 'div':
                name = self.name('vorwort')
                html, body = self.start(
                    name, text_of(c.find(TEI + 'head')).rstrip('.')
                )
                sec = el(body, 'section', 'chapter')
                sec.set(EPT, 'preface')
                sec.set('role', 'doc-preface')
                C.div(c, sec)
                self.finish(name, html, body)

    def titlepage(self, part, tp):
        C = self.C
        name = self.name('titel')
        if part is self.vol['parts'][0]:
            self.title_file = name
        html, body = self.start(name, 'Titel', 'titlepage')
        sec = el(body, 'section', 'titlepage')
        sec.set(EPT, 'titlepage')
        first = C.new_block(sec, 'div', 'tp-anchor')
        n_imprint = 0
        for c in tp.iter():
            tag = local(c)
            if tag == 'titlePart' and c.get('type') == 'main':
                e = el(sec, 'h1', 't-main', id='titel')
                C.inline(c, e, True)
            elif tag == 'byline':
                author = c.find(TEI + 'docAuthor')
                if author is not None:
                    el(sec, 'p', 't-von').text = (c.text or '').strip()
                    C.inline(author, el(sec, 'p', 't-author'))
                else:
                    C.inline(c, el(sec, 'p', 't-ed'), True)
            elif tag == 'titlePart' and c.get('type') == 'volume':
                C.inline(c, el(sec, 'p', 't-vol'), True)
            elif tag == 'titlePart' and c.get('type') == 'copyright':
                C.inline(c, el(sec, 'p', 't-copy'))
            elif tag == 'docImprint':
                p = el(sec, 'p', 't-imprint' if n_imprint == 0 else 't-ny')
                n_imprint += 1
                C.inline(c, p, n_imprint == 1)
        etree.strip_tags(sec, H + 'em', H + 'strong')
        if part.get('toc_title'):
            C.toc_front.append((1, part['toc_title'], name, 'titel'))
        self.finish(name, html, body)

    def dedication(self, div):
        C = self.C
        name = self.name('widmung')
        html, body = self.start(name, 'Widmung', 'dedication')
        sec = el(body, 'section', 'dedication')
        sec.set(EPT, 'dedication')
        sec.set('role', 'doc-dedication')
        for p in div.findall(TEI + 'p'):
            e = C.new_block(sec, 'p', 'd-text')
            C.inline(p, e, True)
        for b in sec.iter(H + 'strong'):
            b.tag = H + 'span'
            b.set('class', 'd-name')
        self.finish(name, html, body)

    def contents(self, part, div):
        C = self.C
        name = self.name('inhalt')
        if part is self.vol['parts'][0]:
            self.contents_file = name
        html, body = self.start(
            name, 'Inhaltsverzeichnis der Erstausgabe', 'contents'
        )
        sec = el(body, 'section', 'orig-toc')
        n = self.vol['parts'].index(part)
        hid = f'inhalt-{n + 1}' if n else 'inhalt'
        h = C.new_block(sec, 'h1', id=hid)
        C.inline(div.find(TEI + 'head'), h)
        etree.strip_tags(h, H + 'em', H + 'strong')
        C.toc_front.append((1, part['toc_contents'], name, hid))
        t = el(sec, 'table', 'toc')
        stack, pending = [], []
        for c in div.find(TEI + 'list'):
            if local(c) == 'pb':
                pending.append(c.get('n'))
                continue
            if local(c) != 'item':
                continue
            if (
                c.find(TEI + 'hi') is not None
                and c.find(TEI + 'hi').get('rendition') == '#right'
                and not text_of(c).replace('Seite', '').strip()
            ):
                continue
            headers, txt, ref = [], c.text or '', c.find(TEI + 'ref')
            for ch in c:
                if local(ch) == 'hi' and ch.get('rendition') == '#c':
                    hx = etree.Element('x')
                    C.inline(ch, el(hx, 'td'), True)
                    headers.append(hx[0])
                elif local(ch) == 'lb':
                    txt += ' '
                elif local(ch) != 'ref':
                    txt += ''.join(ch.itertext())
                if local(ch) != 'ref':
                    txt += ch.tail or ''
            label = ' '.join(txt.split())
            for hd in headers:
                tr = el(t, 'tr', 'lv-book')
                hd.set('colspan', '2')
                etree.strip_tags(hd, H + 'em', H + 'strong')
                tr.append(hd)
                for n in pending:
                    C.page_anchor(hd, n)
                pending = []
            if not label:
                continue
            if re.match(
                r'\w+ Kapitel|Vorwort|Vorrede|Inhaltsverzeichnis|Nachtr|Anhang',
                label,
            ):
                lv, stack = 0, []
            else:
                m = re.match(r'([IVX]+\.|\d+\)|[A-D][.)]|[a-c]\))\s', label)
                kind = None
                if m:
                    tok = m.group(1)
                    kind = (
                        'roman'
                        if tok[0] in 'IVX'
                        else (
                            'digit'
                            if tok[0].isdigit()
                            else 'upper' if tok[0].isupper() else 'lower'
                        )
                    )
                if kind is None:
                    lv = 1
                elif kind in stack:
                    lv = stack.index(kind) + 1
                    stack = stack[:lv]
                else:
                    stack.append(kind)
                    lv = len(stack)
            tr = el(t, 'tr', f'lv{lv}')
            td = el(tr, 'td', 'ti')
            for n in pending:
                C.page_anchor(td, n)
            pending = []
            tdp = el(tr, 'td', 'pg')
            if ref is not None:
                pg = re.split(r'[—–-]', ref.text.strip())[0].strip()
                href = f'@@PAGE:{part["prefix"]}{pg}@@'
                el(td, 'a', href=href).text = label
                el(tdp, 'a', href=href).text = ref.text.strip()
            else:
                add_text(td, label)
        self.finish(name, html, body)

    # -- body ---------------------------------------------------------------

    def body(self, part):
        C = self.C
        body_el = part['root'].find(f'.//{TEI}body')
        buch = body_el.find(TEI + 'div')
        for c in body_el:
            if c is buch:
                break
            if local(c) == 'pb' and c.get('n'):
                C.pending_pb.append(c.get('n'))
        buch_head = buch.find(TEI + 'head')
        first = True
        for grp in buch:
            tag = local(grp)
            if tag == 'pb' and grp.get('n'):
                C.pending_pb.append(grp.get('n'))
            if tag != 'div':
                continue
            head = grp.find(TEI + 'head')
            htxt = text_of(head)
            subdivs = grp.findall(TEI + 'div')
            if not subdivs or htxt.startswith(('Nachtrag', 'Anhang')):
                name = self.name()
                html, body = self.start(name, htxt.rstrip('.'))
                sec = el(body, 'section', 'chapter')
                if htxt.startswith('Anhang'):
                    sec.set(EPT, 'appendix')
                    sec.set('role', 'doc-appendix')
                if first:
                    self.book_heading(part, buch_head, sec)
                    first = False
                C.div(grp, sec)
                self.finish(name, html, body)
                continue
            sec_no, pre = 0, []
            for node in grp:
                t = local(node)
                if t == 'div':
                    sec_no += 1
                    name = self.name()
                    html, body = self.start(
                        name, text_of(node.find(TEI + 'head')).rstrip('.')
                    )
                    sec = el(body, 'section', 'chapter')
                    if self.first_body is None:
                        self.first_body = name
                    if sec_no == 1:
                        if first:
                            self.book_heading(part, buch_head, sec)
                            first = False
                        hid = f'g{self.file_seq}'
                        skip = any(
                            htxt.startswith(s) for s in part.get('toc_skip', ())
                        )
                        C.heading(head, sec, 2, hid, toc=not skip)
                        C.flow(pre, sec)
                    C.div(node, sec)
                    self.finish(name, html, body)
                elif t == 'pb':
                    if sec_no == 0:
                        pre.append(node)
                    elif node.get('n'):
                        C.pending_pb.append(node.get('n'))
                elif t in ('head', 'lb', 'milestone', 'cb', None):
                    continue
                elif sec_no == 0:
                    pre.append(node)
                else:
                    sys.exit(f'content between sections: {t}')

    def book_heading(self, part, buch_head, sec):
        skip = any(
            text_of(buch_head).startswith(s) for s in part.get('toc_skip', ())
        )
        self.C.heading(
            buch_head, sec, 1, f'buch{self.file_seq}', toc=not skip, cls='book'
        )

    def back(self, part):
        C = self.C
        bk = part['root'].find(f'.//{TEI}back')
        divs = [c for c in bk if local(c) == 'div']
        if not divs:
            return
        corr = [d for d in divs if d.get('type') == 'corrigenda']
        if corr:
            name = self.name('druckfehler')
            html, body = self.start(name, 'Druckfehler')
            sec = el(body, 'section', 'chapter')
        else:
            name, html, body = self.files[-1][0], None, None
            sec = None
        for c in bk:
            if local(c) == 'pb' and c.get('n'):
                C.pending_pb.append(c.get('n'))
            elif local(c) == 'div' and c.get('type') == 'corrigenda':
                C.heading(
                    c.find(TEI + 'head'), sec, 1, 'druckfehler', toc=False
                )
                C.toc.append(
                    (
                        1,
                        text_of(c.find(TEI + 'head')).rstrip('.'),
                        name,
                        'druckfehler',
                    )
                )
                d = C.new_block(sec, 'div', 'list corr')
                for it in c.iter(TEI + 'item'):
                    item = el(d, 'div', 'item')
                    C.inline(it, item)
                    link_page(item, part['prefix'])
            elif local(c) == 'div' and c.get('type') == 'imprint':
                if sec is None:
                    last_html = self.files[-1][1]
                    target = last_html.find(f'.//{H}section[@class="chapter"]')
                    C.file = name
                    for p in c.findall(TEI + 'p'):
                        e = C.new_block(etree.Element('x'), 'p', 'imprint')
                        C.inline(p, e)
                        etree.strip_tags(e, H + 'strong')
                        notes = last_html.find(f'.//{H}section[@class="notes"]')
                        if notes is not None:
                            notes.addprevious(e)
                        else:
                            target.getparent().append(e)
                    tidy(last_html)
                else:
                    for p in c.findall(TEI + 'p'):
                        C.paragraph(p, sec, 'imprint')
        if corr:
            self.finish(name, html, body)

    # -- editorial notice ---------------------------------------------------

    def notice(self):
        C, vol = self.C, self.vol
        name = self.name('notiz')
        html, body = self.start(name, 'Editorische Notiz')
        sec = el(body, 'section', 'chapter notice')
        el(sec, 'h1', id='notiz').text = 'Editorische Notiz'
        C.toc.append((1, 'Editorische Notiz', name, 'notiz'))

        def para(*parts, cls=None):
            p = el(sec, 'p', cls)
            for x in parts:
                if isinstance(x, tuple):
                    el(p, 'a', href=x[1]).text = x[0]
                else:
                    add_text(p, x)
            return p

        def h(t):
            el(sec, 'h2').text = t

        def items(lst):
            ul = el(sec, 'ul')
            for it in lst:
                el(ul, 'li').text = it

        para(
            vol.get(
                'principle',
                'Diese Ausgabe ist eine Leseausgabe der Erstausgabe. Sie gibt'
                ' deren Text vollständig und in seiner Orthographie und'
                ' Interpunktion wieder und berichtigt nur offensichtliche'
                ' Fehler; alle Eingriffe sind im Folgenden genannt.',
            )
        )
        h('Textgrundlage')
        for part in vol['parts']:
            hd = part['header']
            bf = hd.find(f'.//{TEI}biblFull')
            title = text_of(bf.find(f'.//{TEI}title[@type="volume"]'))
            pub = text_of(bf.find(f'.//{TEI}publisher'))
            place = text_of(bf.find(f'.//{TEI}pubPlace'))
            date = text_of(bf.find(f'.//{TEI}date'))
            extent = text_of(bf.find(f'.//{TEI}measure[@type="pages"]'))
            shelf = text_of(hd.find(f'.//{TEI}idno[@type="shelfmark"]'))
            urn = text_of(hd.find(f'.//{TEI}idno[@type="URN"]'))
            url = text_of(hd.find(f'.//{TEI}idno[@type="URLWeb"]'))
            ed = (
                ' Hrsg. von Friedrich Engels.'
                if bf.find(f'.//{TEI}editor') is not None or vol['index'] > 1
                else ''
            )
            para(
                'Karl Marx: Das Kapital. Kritik der politischen Oekonomie.'
                f' {title}.{ed} {place}: {pub} {date} (Erstausgabe; {extent}).'
                ' Exemplar der Staatsbibliothek zu Berlin – Preußischer'
                f' Kulturbesitz, Signatur {shelf}. Transkription: ',
                ('Deutsches Textarchiv', url),
                f' (URN: {urn}).',
            )
        para(
            'Das Deutsche Textarchiv (DTA) der Berlin-Brandenburgischen'
            ' Akademie der Wissenschaften hat den Text im'
            ' Double-Keying-Verfahren erfasst und in XML/TEI-P5 kodiert;'
            ' verwendet wurde die TEI-Fassung vom 28. Februar 2025. Lizenz: ',
            (
                (
                    'Creative Commons Namensnennung – Weitergabe unter gleichen'
                    ' Bedingungen 4.0 (CC BY-SA 4.0)'
                ),
                LICENSE_URL,
            ),
            '. Diese Ausgabe ist eine Bearbeitung davon und steht unter'
            ' derselben Lizenz.',
        )

        h('Textkorrekturen')
        items(
            vol.get('corrections', [])
            + [
                'Vom DTA ausgewiesene Korrekturen (sic/corr) sind übernommen.',
                'Sachliche Fehler sind nicht berichtigt: Namen, Daten,'
                ' Seitenangaben und der Wortlaut von Zitaten stehen wie im'
                ' Druck' + vol.get('factual_note', '.'),
            ]
        )
        structure = vol.get('structure', []) + vol.get(
            'structure_' + ('pdf' if self.fmt == 'pdf' else 'epub'), []
        )
        if structure:
            h('Weitere Eingriffe')
            items(structure)
        if vol.get('spelling'):
            h('Rechtschreibung')
            para(vol['spelling'])

        h('Satz und Erschließung')
        pdf = self.fmt == 'pdf'
        items(
            [
                'Sperrsatz, im Druck die einzige Form der Hervorhebung, ist als'
                ' Kursive wiedergegeben; in Überschriften entfällt er.'
                + vol.get('emphasis_note', ''),
                (
                    'Silbentrennungen am Zeilenende sind aufgelöst.'
                    ' Geviertstriche (—) sind, wie heute im deutschen Satz'
                    ' üblich, als Halbgeviertstriche (–) gesetzt,'
                    ' Auslassungspunkte aus gesperrten Punkten („. . . .“) als'
                    ' „…“; ein Punkt dicht am Wort bleibt als Satzpunkt stehen.'
                ),
                (
                    'Fußnoten behalten ihre Zählung.'
                    if pdf
                    else (
                        'Fußnoten behalten ihre Zählung und sind verlinkt; sie'
                        ' stehen, nach Kapiteln geordnet, in den „Anmerkungen“'
                        ' am Ende des Bandes.'
                    )
                )
                + ' Über Seitengrenzen fortgesetzte Fußnoten sind'
                ' zusammengeführt.' + vol.get('footnote_note', ''),
                (
                    'Die Seitenzahlen der Erstausgabe stehen am Rand, ein'
                    ' Strich im Text markiert den Seitenwechsel.'
                    + vol.get('pages_note_pdf', '')
                    + ' Das ursprüngliche Inhaltsverzeichnis ist erhalten und'
                    ' verweist auf die Seiten dieser Ausgabe.'
                    if pdf
                    else (
                        'Die Seitenzählung der Erstausgabe ist als Seitenliste'
                        ' enthalten.'
                    )
                    + vol.get('pages_note', '')
                    + ' Das ursprüngliche Inhaltsverzeichnis ist erhalten und'
                    ' verlinkt.'
                ),
                (
                    'Bogensignaturen sind weggelassen; die griechischen'
                    ' Buchstabenvarianten ϰ, ϱ, ϑ sind als κ, ρ, θ'
                    ' wiedergegeben.'
                ),
            ]
        )

        gaps = [
            (
                p,
                p['formula_pages'],
                p.get('figure_page'),
                p['text_tables'],
            )
            for p in vol['parts']
        ]
        if any(f or g or x or p.get('table_notes') for p, f, g, x in gaps):
            h('Lücken der Vorlage, nach dem Faksimile ergänzt')
        for part, fpages, fig, texts in gaps:
            pre = part['prefix']
            if fpages:
                pages = sorted(set(int(x) for x in fpages))
                para(
                    f'{part["empty_formulas"]}'
                    f' Formelfelder{part.get("part_label", "")} sind in der'
                    ' DTA-Transkription leer geblieben (S.'
                    f' {", ".join(pre + str(x) for x in pages)}). Sie sind hier'
                    ' nach dem Faksimile des DTA nachgesetzt, einschließlich'
                    ' der Satzweise des Drucks.'
                    + part.get('formula_note', '')
                    + ('' if pdf else part.get('formula_note_epub', ''))
                )
            if fig:
                para(
                    f'Die Strichgrafik der drei Arbeitstage (S. {fig}) fehlt in'
                    ' der Transkription und ist nach dem Faksimile'
                    ' nachgesetzt.'
                )
            if part.get('table_notes'):
                tn = sorted(
                    part['table_notes'].items(),
                    key=lambda kv: part['tables'].index(kv[0]),
                )

                def page(tid, v):
                    return v[2] if len(v) > 2 else re.match('[0-9]+', tid)[0]

                where = '; '.join(
                    f'S. {pre}{page(t, v)}: {v[0].rstrip(")")}' for t, v in tn
                )
                one = len(tn) == 1
                para(
                    f'{"Eine Fußnote" if one else f"{len(tn)} Fußnoten"}'
                    f'{part.get("part_label", "")},'
                    f' deren {"Marke in einer" if one else "Marken in den"}'
                    f' nicht transkribierten Tabelle{"" if one else "n"}'
                    f' {"steht, fehlt" if one else "stehen, fehlen"} in der'
                    f' DTA-Transkription ganz ({where}). Sie'
                    f' {"ist" if one else "sind"} nach dem Faksimile ergänzt.'
                )

            def page_list(pairs):
                p = el(sec, 'p', 'pagelist')
                for i, (page, facs) in enumerate(
                    sorted(set(pairs), key=lambda x: int(x[1]))
                ):
                    if i:
                        add_text(p, ', ')
                    el(p, 'a', href=DTA_VIEW.format(part['dir'], facs)).text = (
                        f'S.\u00a0{pre}{page}'
                    )

            if texts:
                para(
                    f'{sum(c for _, _, c in texts)}'
                    f' Tabellen{part.get("part_label", "")}, die das DTA nicht'
                    ' transkribiert hat, sind nach dem Faksimile abgeschrieben'
                    ' und neu gesetzt: mit waagerechten Linien allein und mit'
                    ' waagerechten Spaltenköpfen, wo der Druck sie stürzt.'
                    + part.get('text_table_note', '')
                    + ' Seiten:'
                )
                page_list((page, facs) for page, facs, _ in texts)
                fixed = [
                    (
                        c.getparent().getparent().get('_page'),
                        c.get('_corr'),
                        c.get('_sic'),
                    )
                    for c in part['root'].iter(TEI + 'cell')
                    if c.get('_sic')
                ]
                if fixed:
                    para(
                        (
                            f'In diesen Tabellen sind {len(fixed)} Angaben'
                            ' berichtigt, die'
                            if len(fixed) > 1
                            else (
                                'In diesen Tabellen ist eine Angabe'
                                ' berichtigt, die'
                            )
                        )
                        + f' der Rechengang oder die Schreibweise der Tabelle'
                        f' selbst als Druckfehler ausweist: '
                        + '; '.join(
                            f'S.\u00a0{pre}{page} „{corr}“ statt „{sic}“'
                            for page, corr, sic in fixed
                        )
                        + '. Andere Unstimmigkeiten der Tabellen bleiben wie'
                        ' gedruckt.'
                    )
        editor, _, mail = vol.get('editor', ('', '', ''))
        version = build_version()
        para(
            ', '.join(
                filter(
                    None,
                    (
                        editor,
                        version and f'Version {version}',
                        german_date(build_time()),
                    ),
                )
            ),
            cls='sign',
        )
        if mail and not pdf:
            para(
                'Hinweise auf Fehler bitte an ',
                (mail, f'mailto:{mail}'),
                '.',
                cls='contact',
            )
        self.finish(name, html, body)


# ---------------------------------------------------------------- packaging


def build_nav_tree(toc):
    root = []
    stack = [(0, root)]
    for level, label, f, hid in toc:
        node = {'label': label, 'href': f'text/{f}#{hid}', 'children': []}
        while level <= stack[-1][0]:
            stack.pop()
        stack[-1][1].append(node)
        stack.append((level, node['children']))
    return root


def full_toc(book):
    """Merge front-matter entries (title/contents pages) into the body TOC in
    spine order. A front entry takes the level of the body entry it precedes, so
    a title page of the second Theil sits among the chapters of the section that
    spans the split."""

    def seq(f):
        return int(f.split('/')[-1][:2])

    out = list(book.C.toc)
    for entry in book.C.toc_front:
        lv, txt, f, hid = entry
        pos = next(
            (i for i, e in enumerate(out) if seq(e[2]) > seq(f)), len(out)
        )
        if pos < len(out):
            lv = (
                max(1, out[pos][0])
                if pos and out[pos][0] > 1 and seq(out[pos - 1][2]) < seq(f)
                else lv
            )
        out.insert(pos, (lv, txt, f, hid))
    return out


def nav_doc(book):
    nav, body = xhtml_doc('Inhalt', css='css/kapital.css')
    navel = el(body, 'nav', id='toc', role='doc-toc')
    navel.set(EPT, 'toc')
    el(navel, 'h1').text = 'Inhalt'

    def emit(parent, nodes):
        ol = el(parent, 'ol')
        for n in nodes:
            li = el(ol, 'li')
            el(li, 'a', href=n['href']).text = n['label']
            if n['children']:
                emit(li, n['children'])

    emit(navel, build_nav_tree(full_toc(book)))
    pl = el(body, 'nav', id='page-list', hidden='hidden', role='doc-pagelist')
    pl.set(EPT, 'page-list')
    el(pl, 'h1').text = 'Seiten der Erstausgabe'
    ol = el(pl, 'ol')
    for label, f, pid in book.C.pages:
        el(el(ol, 'li'), 'a', href=f'text/{f}#{pid}').text = label
    lm = el(body, 'nav', id='landmarks', hidden='hidden')
    lm.set(EPT, 'landmarks')
    el(lm, 'h1').text = 'Orientierung'
    ol = el(lm, 'ol')
    for typ, href, label in (
        ('cover', 'text/cover.xhtml', 'Umschlag'),
        ('titlepage', f'text/{book.title_file}', 'Titel'),
        ('toc', f'text/{book.contents_file}', 'Inhalt'),
        ('bodymatter', f'text/{book.first_body}', 'Text'),
    ):
        a = el(el(ol, 'li'), 'a', href=href)
        a.set(EPT, typ)
        a.text = label
    return nav


def ncx_doc(book, uid):
    toc, pages = full_toc(book), book.C.pages
    NS = 'http://www.daisy.org/z3986/2005/ncx/'
    N = '{%s}' % NS
    ncx = etree.Element(N + 'ncx', nsmap={None: NS}, version='2005-1')
    ncx.set(XML + 'lang', 'de')
    head = etree.SubElement(ncx, N + 'head')
    for n, c in (
        ('dtb:uid', uid),
        ('dtb:depth', str(max(l for l, *_ in toc))),
        ('dtb:totalPageCount', '0'),
        ('dtb:maxPageNumber', '0'),
    ):
        etree.SubElement(head, N + 'meta', name=n, content=c)
    etree.SubElement(etree.SubElement(ncx, N + 'docTitle'), N + 'text').text = (
        book.vol['title']
    )
    navmap = etree.SubElement(ncx, N + 'navMap')
    targets = []

    def emit(parent, nodes):
        for n in nodes:
            np_ = etree.SubElement(
                parent, N + 'navPoint', id=f'np{len(targets) + 1}'
            )
            etree.SubElement(
                etree.SubElement(np_, N + 'navLabel'), N + 'text'
            ).text = n['label']
            etree.SubElement(np_, N + 'content', src=n['href'])
            targets.append((n['href'], np_))
            emit(np_, n['children'])

    emit(navmap, build_nav_tree(toc))
    plist = etree.SubElement(ncx, N + 'pageList')
    etree.SubElement(
        etree.SubElement(plist, N + 'navLabel'), N + 'text'
    ).text = 'Seiten der Erstausgabe'
    kinds = [
        ('normal', int(n)) if n.isdigit() else ('front', roman(n))
        for n in (label.split('/')[-1] for label, _, _ in pages)
    ]
    unique = len(set(kinds)) == len(kinds)
    for i, ((label, f, pid), (kind, num)) in enumerate(zip(pages, kinds), 1):
        pt = etree.SubElement(
            plist,
            N + 'pageTarget',
            id=f'pt{i}',
            type=kind,
            value=str(num if unique else i),
        )
        etree.SubElement(
            etree.SubElement(pt, N + 'navLabel'), N + 'text'
        ).text = label
        etree.SubElement(pt, N + 'content', src=f'text/{f}#{pid}')
        targets.append((f'text/{f}#{pid}', pt))
    pos = {}
    for k, (name, doc) in enumerate(book.files):
        pos[f'text/{name}'] = (k, -1)
        for j, e in enumerate(doc.iter()):
            if e.get('id'):
                pos[f'text/{name}#{e.get("id")}'] = (k, j)
    order = {
        p: i for i, p in enumerate(sorted({pos[t] for t, _ in targets}), 1)
    }
    for t, e in targets:
        e.set('playOrder', str(order[pos[t]]))
    return ncx


def roman(s):
    vals = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
    n = [vals[c] for c in s.upper()]
    return sum(-v if v < w else v for v, w in zip(n, n[1:] + [0]))


def cover_doc(vol):
    html, body = xhtml_doc('Umschlag', 'cover')
    sec = el(body, 'section', 'cover')
    sec.set(EPT, 'cover')
    el(sec, 'img', src='../images/cover.png', alt=f'Karl Marx: {vol["title"]}')
    return html


def heading_order(book):
    """Page marks and headings of the main text in reading order:
    (kind, id, text, file)."""
    order = []
    for name, doc in book.files:
        if name in book.notes_files:
            continue
        for e in doc.iter(H + 'span', *(H + f'h{i}' for i in range(1, 7))):
            c = (e.get('class') or '').split()
            if e.tag == H + 'span':
                if 'pb' in c:
                    order.append(('pb', e.get('id'), None, name))
            elif e.get('id') and 't-main' not in c:
                text = ' '.join(''.join(e.itertext()).split())
                order.append(('h', e.get('id'), text, name))
    return order


def toc_target(order, pid, title):
    """The heading an entry of the original contents points to, with its
    file: the closest match among the headings on its page, including those
    before the page mark when the page begins with a heading; a matching first
    word (the number of a chapter or section) counts extra. Without a match
    the page mark itself."""
    idx = next(i for i, o in enumerate(order) if o[0] == 'pb' and o[1] == pid)
    start = idx
    while start > 0 and order[start - 1][0] == 'h':
        start -= 1
    cands = [o for o in order[start:idx] if o[0] == 'h']
    cands += [o for o in order[idx : idx + 40] if o[0] == 'h'][:6]
    norm = lambda s: re.sub(r'\W+', ' ', s.lower()).strip()

    def score(cand):
        a, b = norm(title), norm(cand[2])
        r = difflib.SequenceMatcher(None, a, b).ratio()
        return r + (0.3 if a.split()[:1] == b.split()[:1] else 0)

    best = max(cands, key=score, default=None)
    if best and score(best) > 0.6:
        return best[1], best[3]
    return pid, order[idx][3]


def link_contents(book):
    """Point the entries of the original contents to their headings."""
    order = heading_order(book)
    pages = {label: pid for label, _, pid in book.C.pages}
    for name, doc in book.files:
        for tr in doc.iter(H + 'tr'):
            links = [a for a in tr.iter(H + 'a') if '@@PAGE:' in a.get('href')]
            if not links:
                continue
            label = links[0].get('href')[len('@@PAGE:') : -2]
            hid, f = toc_target(order, pages[label], links[0].xpath('string()'))
            for a in links:
                a.set('href', f'{f}#{hid}')


def package(book, out):
    vol = book.vol
    uid = 'urn:uuid:' + str(uuid.uuid5(uuid.NAMESPACE_URL, vol['uid_key']))
    page_map = {label: f'{f}#{pid}' for label, f, pid in book.C.pages}
    stamp = build_time()
    now = stamp.strftime('%Y-%m-%dT%H:%M:%SZ')
    texts = [('cover.xhtml', cover_doc(vol))] + book.files

    opf_items, spine = [], []
    with zipfile.ZipFile(out, 'w') as z:
        z.writestr(
            zipfile.ZipInfo('mimetype', stamp.timetuple()[:6]),
            'application/epub+zip',
            compress_type=zipfile.ZIP_STORED,
        )

        def put(name, data):
            z.writestr(
                zipfile.ZipInfo(name, stamp.timetuple()[:6]),
                data,
                compress_type=zipfile.ZIP_DEFLATED,
            )

        put(
            'META-INF/container.xml',
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<container version="1.0"'
            ' xmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
            '<rootfiles><rootfile full-path="OEBPS/content.opf"'
            ' media-type="application/oebps-package+xml"/>'
            '</rootfiles></container>',
        )
        put('OEBPS/css/kapital.css', CSS.read_bytes())
        put('OEBPS/images/cover.png', Path(vol['cover']).read_bytes())
        opf_items.append(
            '<item id="css" href="css/kapital.css" media-type="text/css"/>'
        )
        opf_items.append(
            '<item id="cover-img" href="images/cover.png"'
            ' media-type="image/png" properties="cover-image"/>'
        )
        for name, doc in texts:
            data = serialize(doc)
            data = re.sub(
                rb'@@PAGE:([^@]+)@@',
                lambda m: page_map[m.group(1).decode()].encode(),
                data,
            )
            data = re.sub(
                rb'@@NOTES@@#(fn\d+)',
                lambda m: (
                    f'{book.note_file[m.group(1).decode()]}#'.encode()
                    + m.group(1)
                ),
                data,
            )
            put(f'OEBPS/text/{name}', data)
            iid = 'x-' + name.replace('.xhtml', '')
            opf_items.append(
                f'<item id="{iid}" href="text/{name}"'
                ' media-type="application/xhtml+xml"/>'
            )
            spine.append(f'<itemref idref="{iid}"/>')
        put('OEBPS/nav.xhtml', serialize(nav_doc(book)))
        put(
            'OEBPS/toc.ncx',
            b'<?xml version="1.0" encoding="utf-8"?>\n'
            + etree.tostring(ncx_doc(book, uid), encoding='utf-8'),
        )
        opf_items.append(
            '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml"'
            ' properties="nav"/>'
        )
        opf_items.append(
            '<item id="ncx" href="toc.ncx"'
            ' media-type="application/x-dtbncx+xml"/>'
        )
        urn = f'.//{TEI}idno[@type="URN"]'
        sources = '\n'.join(
            f'    <dc:source id="src{i}">'
            f'{text_of(p["header"].find(urn))}</dc:source>\n'
            f'    <meta refines="#src{i}"'
            ' property="source-of">pagination</meta>'
            for i, p in enumerate(vol['parts'], 1)
        )
        version = build_version()
        version_meta = (
            f'\n    <meta property="schema:version">{version}</meta>'
            if version
            else ''
        )
        contrib = (
            '\n    <dc:contributor id="ed">Friedrich Engels</dc:contributor>\n '
            '   <meta refines="#ed" property="role"'
            ' scheme="marc:relators">edt</meta>\n    <meta refines="#ed"'
            ' property="file-as">Engels, Friedrich</meta>'
            if vol['index'] > 1
            else ''
        )
        if vol.get('editor'):
            contrib += (
                '\n    <dc:contributor'
                f' id="bearb">{vol["editor"][0]}</dc:contributor>\n    <meta'
                ' refines="#bearb" property="role"'
                ' scheme="marc:relators">edt</meta>\n    <meta'
                ' refines="#bearb"'
                f' property="file-as">{vol["editor"][1]}</meta>'
            )
        opf = f'''<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="uid" xml:lang="de"
         prefix="calibre: https://calibre-ebook.com">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="uid">{uid}</dc:identifier>
    <dc:title id="t1">{vol['title']}</dc:title>
    <meta refines="#t1" property="title-type">main</meta>
    <meta refines="#t1" property="file-as">Kapital {vol['index']}, Das ({vol['year']})</meta>
    <dc:creator id="au">Karl Marx</dc:creator>
    <meta refines="#au" property="role" scheme="marc:relators">aut</meta>
    <meta refines="#au" property="file-as">Marx, Karl</meta>{contrib}
    <dc:language>de</dc:language>
    <dc:date>{vol['year']}</dc:date>
    <dc:publisher>Deutsches Textarchiv (Textgrundlage)</dc:publisher>
{sources}
    <dc:rights>CC BY-SA 4.0 – Textgrundlage: Deutsches Textarchiv, BBAW</dc:rights>
    <dc:subject>Politische Ökonomie</dc:subject>
    <dc:description>{vol['description']}</dc:description>
    <meta property="dcterms:modified">{now}</meta>{version_meta}
    <meta property="schema:accessMode">textual</meta>
    <meta property="schema:accessModeSufficient">textual</meta>
    <meta property="schema:accessibilityFeature">structuralNavigation</meta>
    <meta property="schema:accessibilityFeature">tableOfContents</meta>
    <meta property="schema:accessibilityFeature">pageNavigation</meta>
    <meta property="schema:accessibilityFeature">printPageNumbers</meta>
    <meta property="schema:accessibilityFeature">readingOrder</meta>
    <meta property="schema:accessibilityFeature">alternativeText</meta>
    <meta property="schema:accessibilityFeature">displayTransformability</meta>
    <meta property="schema:accessibilityHazard">none</meta>
    <meta property="schema:accessibilitySummary">{A11Y_SUMMARY}</meta>
    <meta property="belongs-to-collection" id="coll">Das Kapital</meta>
    <meta refines="#coll" property="collection-type">series</meta>
    <meta refines="#coll" property="group-position">{vol['index']}</meta>
    <meta name="calibre:series" content="Das Kapital"/>
    <meta name="calibre:series_index" content="{vol['index']}"/>
    <meta name="cover" content="cover-img"/>
  </metadata>
  <manifest>
    {chr(10).join('    ' + i for i in opf_items).strip()}
  </manifest>
  <spine toc="ncx">
    {chr(10).join('    ' + s for s in spine).strip()}
  </spine>
</package>
'''
        put('OEBPS/content.opf', opf)


def load_volume(edition, band, variants):
    vol = importlib.import_module(f'editions.{edition}').VOLUMES[band]
    mods = [importlib.import_module(f'variants.{v}') for v in variants]
    if mods:
        vol['variants'] = mods
        vol['uid_key'] += ''.join(f':{m.NAME}' for m in mods)
        vol['spelling'] = ' '.join(m.NOTICE for m in mods)
        for m in mods:
            if hasattr(m, 'adjust'):
                m.adjust(vol)
    return vol


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('band', help='Band, z. B. 1, 2 oder 3')
    ap.add_argument('out', help='Ausgabedatei (.epub)')
    ap.add_argument(
        '-e',
        '--edition',
        default='erstausgaben',
        help='Textgrundlage (Modul unter editions/)',
    )
    ap.add_argument(
        '-v',
        '--variant',
        action='append',
        default=[],
        help='Textbearbeitung (Modul unter variants/)',
    )
    args = ap.parse_args()
    vol = load_volume(args.edition, args.band, args.variant)
    book = Book(vol)
    book.run()
    package(book, args.out)
    C = book.C
    for part in vol['parts']:
        print(
            Path(part['tei']).name,
            'formulas',
            part['formula_index'],
            'of',
            len(part.get('formulas') or []),
            '| tables as text',
            len(part['text_tables']),
        )
    wide = [
        f'{page} ({w} em)' for page, w in C.table_widths if w > TABLE_LINE + 1.5
    ]
    if wide:
        print(
            f'tables wider than {TABLE_LINE + 1.5} em at the smallest size:',
            ', '.join(wide),
        )
    print(
        'files',
        len(book.files),
        'toc',
        len(C.toc) + len(C.toc_front),
        'pages',
        len(C.pages),
        'notes',
        C.note_seq,
        'merged',
        book.merged,
    )
    print('hyphenation', dict(book.stats))


if __name__ == '__main__':
    main()
