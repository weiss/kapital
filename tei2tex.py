#!/usr/bin/env python3
"""Das Kapital: LaTeX (LuaLaTeX) aus demselben Zwischenstand wie das EPUB."""

import argparse
import re
from pathlib import Path

import tei2epub as T

H = T.H
HERE = Path(__file__).resolve().parent
SPECIAL = {
    '\\': r'\textbackslash{}',
    '{': r'\{',
    '}': r'\}',
    '$': r'\$',
    '&': r'\&',
    '#': r'\#',
    '%': r'\%',
    '_': r'\_',
    '^': r'\^{}',
    '~': r'\~{}',
    '\u00a0': '~',
    '\u2009': r'\,',
    '\u202f': r'\,',
    '\u3003': '\u2033',
    '\u00ad': '',
    '\u2007': r'\phantom{0}',
    '\u2008': r'\phantom{,}',
    '\u2002': r'\phantom{½}',
    '\u2004': '',
}
SPECIAL.update(
    {
        ch: r'\vfrac{' + ch_n + '}{' + ch_d + '}'
        for ch, ch_n, ch_d in (
            ('⅑', '1', '9'),
            ('⅒', '1', '10'),
            ('⅓', '1', '3'),
            ('⅔', '2', '3'),
            ('⅕', '1', '5'),
            ('⅖', '2', '5'),
            ('⅗', '3', '5'),
            ('⅘', '4', '5'),
            ('⅙', '1', '6'),
            ('⅚', '5', '6'),
            ('⅛', '1', '8'),
            ('⅜', '3', '8'),
            ('⅝', '5', '8'),
            ('⅞', '7', '8'),
        )
    }
)
ESC = re.compile('[' + re.escape(''.join(SPECIAL)) + ']')
LEVELS = ['hdI', 'hdII', 'hdIII', 'hdIV', 'hdV', 'hdVI']


HYPHEN = re.compile(r'(?<=[^\W\d_])-(?=[^\W\d_])')


def esc(s):
    return HYPHEN.sub(
        r'\\babelhyphen{hard}', ESC.sub(lambda m: SPECIAL[m.group(0)], s or '')
    )


def tag(e):
    return (
        e.tag[len(H) :]
        if isinstance(e.tag, str) and e.tag.startswith(H)
        else None
    )


def cls(e):
    return (e.get('class') or '').split()


def plain(e):
    return ' '.join(''.join(x for x in e.itertext()).split())


def running(title):
    title = title.replace(' (Erstausgabe)', '')
    if len(title) <= 68:
        return title
    return title[:64].rsplit(' ', 1)[0].rstrip(' –,;:') + ' …'


# Seitenwechsel vor einer zentrierten Zeile: nur die Randziffer, kein Strich auf
# eigener Zeile
LONE_PB = re.compile(
    r'\n\n(?:\\noindent ?)?\\pb(\{[^}]*\}\{[^}]*\})\s*\n\n\\(cenline|dispf)\{'
)


class TeX:
    def __init__(self, book):
        self.book = book
        self.pages = {label: pid for label, _, pid in book.C.pages}
        self.notes = {}
        self.levels = {
            hid: lv for lv, _, _, hid in book.C.toc + book.C.toc_front
        }
        self.labels = {
            hid: lab for _, lab, _, hid in book.C.toc + book.C.toc_front
        }
        for _, _, sec in book.note_groups:
            for a in sec.iter(H + 'aside'):
                self.notes[a.get('id')] = a
        self.in_note = 0
        self.table_notes = None
        self.after_heading = False
        self.chap = book.vol['parts'][0].get('br_levels', 2)
        self.split = len(book.vol['parts']) > 1

    # -- references -------------------------------------------------------

    def target(self, href):
        m = re.fullmatch(r'@@PAGE:(.+)@@', href)
        if m:
            return self.pages[m.group(1)]
        return href.split('#', 1)[1] if '#' in href else None

    # -- inline -----------------------------------------------------------

    def inl(self, e, text=True):
        out = [esc(e.text)] if text else []
        for c in e:
            out.append(self.inline_el(c))
            out.append(esc(c.tail))
        return ''.join(out)

    def wrap(self, cmd, inner):
        """Apply an inline command to text that may contain block marks."""
        out = []
        for i, seg in enumerate(inner.split('\x00')):
            if i % 2:
                m = re.fullmatch(r'(\\\w+\{)(.*)(\})', seg, re.S)
                out.append(
                    '\x00'
                    + (
                        m.group(1) + cmd + '{' + m.group(2) + '}' + m.group(3)
                        if m
                        else seg
                    )
                    + '\x00'
                )
            elif seg.strip():
                out.append(cmd + '{' + seg + '}')
            else:
                out.append(seg)
        return ''.join(out)

    def inline_el(self, c):
        t, k = tag(c), cls(c)
        if t in ('em', 'i'):
            return self.wrap(r'\emph', self.inl(c))
        if t == 'strong':
            return self.wrap(r'\textbf', self.inl(c))
        if 'd-name' in k:
            return r'{\large ' + self.inl(c) + '}'
        if t == 'sup' and 'fnref' in k:
            return self.footnote(c)
        if t == 'sup':
            return r'\textsuperscript{' + self.inl(c) + '}'
        if t == 'sub':
            return r'\textsubscript{' + self.inl(c) + '}'
        if t == 'br':
            return r'\\' + '\n'
        if t == 'a':
            href = c.get('href', '')
            if href.startswith('http'):
                return (
                    r'\href{'
                    + href.replace('%', r'\%').replace('#', r'\#')
                    + '}{'
                    + self.inl(c)
                    + '}'
                )
            tg = self.target(href)
            return (
                (r'\hyperref[' + tg + ']{' + self.inl(c) + '}')
                if tg
                else self.inl(c)
            )
        if t != 'span':
            raise SystemExit(f'unhandled inline <{t}>')
        if 'pb' in k:
            return self.pb(c)
        if 'nobr' in k or 'seg' in k:
            return self.inl(c)
        if 'grc' in k:
            return r'\grc{' + self.inl(c) + '}'
        if 'vf' in k:
            return r'\vfrac{' + c[0].text + '}{' + c[1].text + '}'
        if 'u' in k:
            return r'\underline{' + self.inl(c) + '}'
        if k[:1] == ['rek'] and 'disp' in k:
            return self.block_mark(r'\dispf{' + self.display(c) + '}')
        if k[:1] == ['rek'] or k[:1] in (
            ['frac'],
            ['lab'],
            ['ov'],
            ['stack'],
            ['cases'],
            ['brz'],
        ):
            return '$' + self.math_el(c) + '$'
        if 'c' in k:
            return self.block_mark(r'\cenline{' + self.inl(c) + '}')
        if 'et' in k:
            return self.block_mark(r'\etline{' + self.inl(c) + '}')
        if 'right' in k:
            return self.block_mark(r'\rline{' + self.inl(c) + '}')
        if 'blockish' in k:
            return self.block_mark(r'\etline{' + self.inl(c) + '}')
        if 'line' in k:
            return self.inl(c) + r'\\' + '\n'
        if 'linefig' in k:
            return self.linefig(c)
        if 'arbeitstage' in k:
            rows = []
            for r in c:
                lab = r.find(H + 'span')
                rows.append(
                    r'\makebox[7.5em][l]{'
                    + self.inl(lab)
                    + '}'
                    + self.linefig(r.find(f'{H}span[@class="linefig"]'))
                )
            return self.block_mark(
                r'\par{\leftskip=1.2em\parindent=0pt\medskip '
                + r'\\'.join(rows)
                + r'\par\medskip}'
            )
        if 'cell' in k:
            return self.inl(c)
        raise SystemExit(f'unhandled span {k}')

    def linefig(self, c):
        out = []
        for s in c:
            k = cls(s)
            if 'lf-l' in k:
                out.append(esc(s.text))
            else:
                w = {'w1': '.7em', 'w2': '1.4em', 'w3': '2.1em', 'w6': '4.2em'}[
                    k[1]
                ]
                out.append(r'\linerule{' + w + '}')
        return ''.join(out)

    def block_mark(self, s):
        m = re.fullmatch(r'(\\\w+\{)(.*)(\})', s, re.S)
        if m and '\x00' in m.group(2):
            s = (
                m.group(1)
                + self.flow_par(m.group(2), indent=False).strip()
                + m.group(3)
            )
        s = re.sub(r'(\\\\\n\s*){2,}', r'\\\\' + '\n', s)
        s = re.sub(r'\\\\\n\s*\}$', '}', s)
        return '\x00' + s + '\x00'

    def plabel(self, c):
        label = c.get('aria-label')
        return label.split('/')[-1] if self.split else label

    def pb(self, c):
        label = self.plabel(c)
        if self.in_note:
            return r'\pbx{' + c.get('id') + '}'
        return r'\pb{' + c.get('id') + '}{' + esc(label) + '}'

    def footnote(self, sup):
        a = sup.find(H + 'a')
        fid = a.get('href').split('#')[1]
        note = self.notes[fid]
        self.in_note += 1
        body = self.note_body(note)
        self.in_note -= 1
        if re.match(
            r'\\(cenline|dispf|etline|begin\{(hanglist|bquote)\})', body
        ):
            body = r'\leavevmode\par\nobreak' + body
        if self.table_notes is not None:
            self.table_notes.append(
                r'\fntext{' + esc(a.text) + '}{' + body + '}'
            )
            return r'\fnmark{' + esc(a.text) + '}'
        return r'\fn{' + esc(a.text) + '}{' + body + '}'

    def note_body(self, note):
        parts = []
        for i, b in enumerate(note):
            if i == 0 and tag(b) == 'p':
                lab = b.find(H + 'a')
                text = (
                    esc(lab.tail.lstrip()) if lab is not None else esc(b.text)
                )
                rest = list(b)[1:] if lab is not None else list(b)
                s = text + ''.join(
                    self.inline_el(c) + esc(c.tail) for c in rest
                )
                parts.append(self.flow_par(s, indent=False))
            else:
                parts.append(self.block(b))
        return '\n'.join(x for x in parts if x.strip()).strip()

    # -- math ---------------------------------------------------------------

    def math(self, e):
        out = [self.mtext(e.text)]
        for c in e:
            out.append(self.math_el(c))
            out.append(self.mtext(c.tail))
        return ''.join(out)

    def braced(self, b):
        rows = b.get('data-rows').split()
        segs = [
            (
                self.math(next(x for x in s if 'btx' in cls(x))),
                set(s.get('data-on').split()),
            )
            for s in b
        ]
        out = []
        half = r'\hspace{.5\wd\brzhalf}'
        for row in rows:
            side, ids = row[0], row[1:]
            level = [r[1:] for r in rows if r[0] == side].index(ids)
            brace = r'\overbrace' if side == '^' else r'\underbrace'
            ats = {
                x: [i for i, (_, on) in enumerate(segs) if x in on] for x in ids
            }
            for x, at in ats.items():
                a, z = at[0], at[-1]
                cut_a = any(o[-1] == a for y, o in ats.items() if y != x)
                cut_z = any(o[0] == z for y, o in ats.items() if y != x)
                if cut_a or cut_z:
                    out.append(
                        r'\global\setbox\brzhalf\hbox{$'
                        + segs[a if cut_a else z][0]
                        + '$}'
                    )
                inner = ''.join(t for t, _ in segs[a + cut_a : z + 1 - cut_z])
                span = (
                    (half if cut_a else '')
                    + r'\phantom{'
                    + inner
                    + '}'
                    + (half if cut_z else '')
                    + (
                        r'\rule{0pt}{1.05em}'
                        if side == '^'
                        else r'\rule[-.3em]{0pt}{0pt}'
                    )
                )
                for _ in range(level):
                    span = r'\phantom{' + brace + '{' + span + '}}'
                pre = (
                    r'\phantom{'
                    + ''.join(t for t, _ in segs[:a])
                    + '}'
                    + (half if cut_a else '')
                )
                out.append(r'\rlap{$' + pre + brace + '{' + span + '}$}')
        return ''.join(out) + ''.join(t for t, _ in segs)

    def display(self, c):
        out = [esc(c.text)]
        for x in c:
            if 'seg' in cls(x):
                out.append('$' + self.math(x) + '$')
            elif 'dl' in cls(x):
                out.append(esc(x.text) + r'\enskip')
            else:
                out.append(self.inline_el(x))
            out.append(esc(x.tail))
        return ''.join(out).strip()

    def frac_part(self, e):
        if len(plain(e)) > 48:
            return (
                r'\text{\parbox{.75\linewidth}{\centering ' + self.inl(e) + '}}'
            )
        return self.math(e)

    def mtext(self, s):
        if not s:
            return ''
        return r'\text{' + esc(s) + '}'

    def math_el(self, c):
        t, k = tag(c), cls(c)
        if t == 'sub':
            return '_{' + self.math(c) + '}'
        if t == 'sup':
            return '^{' + self.math(c) + '}'
        if t in ('em', 'i'):
            return r'\text{\emph{' + self.inl(c) + '}}'
        if t == 'sup' or t == 'a':
            return r'\text{' + self.inline_el(c) + '}'
        if t == 'img':
            return r'\text{' + self.inline_el(c) + '}'
        k0 = k[:1]
        if k0 == ['rek'] or 'seg' in k:
            return self.math(c)
        if 'frac' in k:
            num, den = c.find(f'{H}span[@class="num"]'), c.find(
                f'{H}span[@class="den"]'
            )
            return (
                r'\Frac{'
                + self.frac_part(num)
                + '}{'
                + self.frac_part(den)
                + '}'
            )
        if k == ['lab', 'nt']:
            return r'\nt{' + esc(c[0].text) + '}{' + self.math(c[1]) + '}'
        if 'brz' in k:
            return self.braced(c)
        if 'lab' in k:
            return r'\lab{' + esc(c[0].text) + '}{' + self.math(c[2]) + '}'
        if 'ov' in k:
            return r'\ovarc{' + self.math(c) + '}'
        if 'stack' in k or 'cases' in k:
            rows = r' \\ '.join(self.math(r) for r in c)
            arr = (
                r'\begin{array}{@{}'
                + ('l' if 'cases' in k and 'bb' not in k else 'c')
                + r'@{}}'
                + rows
                + r'\end{array}'
            )
            if 'bb' in k:
                return r'\left\{' + arr + r'\right\}'
            return (
                r'\left\{' + arr + r'\right.'
                if 'cases' in k and 'nb' not in k
                else arr
            )
        if 'dl' in k:
            return r'\text{' + esc(c.text) + r'}\quad '
        if 'nobr' in k:
            return self.mtext(c.text)
        if 'pb' in k:
            return r'\text{' + self.pb(c) + '}'
        if 'grc' in k:
            return r'\text{' + self.inline_el(c) + '}'
        raise SystemExit(f'unhandled math <{t}> {k}')

    # -- blocks -------------------------------------------------------------

    def flow_par(self, s, indent=True):
        """Paragraph text with embedded block marks: blocks break the paragraph,
        text after them continues without indent."""
        out = []
        for i, seg in enumerate(s.split('\x00')):
            if i % 2:
                out.append('\n' + seg + '\n')
            elif seg.strip():
                seg = seg.strip(' ')
                if seg.startswith(r'\\'):
                    seg = seg[2:].lstrip()
                if seg.endswith('\\\\\n'):
                    seg = seg[:-3]
                lead = '' if (indent and i == 0) else r'\noindent '
                out.append(lead + seg.strip() + '\n')
        return ''.join(out).strip() + '\n\n'

    def block(self, b):
        t, k = tag(b), cls(b)
        if t == 'p':
            if 'pagelist' in k:
                return self.flow_par(self.inl(b), indent=False)
            if 'sign' in k:
                return (
                    r'\par\bigskip{\raggedleft\itshape '
                    + self.inl(b)
                    + r'\par}'
                    + '\n\n'
                )
            maths = [x for x in b if {'rek', 'frac'} & set(cls(x))]
            if (
                len(maths) > 1
                and not any({'pb', 'disp'} & set(cls(x)) for x in b.iter())
                and len(plain(b)) - sum(len(plain(x)) for x in maths) < 16
            ):
                return r'\fitline{' + self.inl(b) + '}\n\n'
            return self.flow_par(
                self.inl(b),
                indent=(
                    'cont' not in k
                    and 'verse' not in k
                    and not self.after_heading_take()
                ),
            )
        if t in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            return self.heading(b)
        if t == 'div' and 'list' in k:
            items = []
            for it in b:
                hang = '1.5em' if 'corr' in k else '1em'
                items.append(
                    r'\hitem['
                    + hang
                    + ']'
                    + self.flow_par(self.inl(it), indent=False).removeprefix(
                        r'\noindent '
                    )
                )
            return (
                r'\begin{hanglist}'
                + ('[1.5em]' if 'corr' not in k else '[0pt]')
                + '\n'
                + ''.join(items)
                + r'\end{hanglist}'
                + '\n\n'
            )
        if t == 'div' and 'poem' in k:
            items = [
                r'\hitem '
                + self.flow_par(self.inl(it), indent=False).removeprefix(
                    r'\noindent '
                )
                for it in b
            ]
            return (
                r'\begin{hanglist}[2em]'
                + '\n'
                + ''.join(items)
                + r'\end{hanglist}'
                + '\n\n'
            )
        if t == 'div' and 'tp-anchor' in k:
            return ''.join(r'\pbx{' + s.get('id') + '}' for s in b) + '\n'
        if t == 'blockquote':
            return (
                r'\begin{bquote}'
                + '\n'
                + ''.join(self.block(x) for x in b)
                + r'\end{bquote}'
                + '\n\n'
            )
        if t == 'table' and 'brace' in k:
            return self.brace(b)
        if t == 'table' and 'data' in k:
            return self.data_table(b)
        if t == 'table' and 'toc' in k:
            return self.toc_table(b)
        if t == 'table' and 'tab' in k:
            return self.text_table(b)
        if t == 'ul':
            return (
                r'\begin{itemize}'
                + ''.join(r'\item ' + self.inl(li) + '\n' for li in b)
                + r'\end{itemize}'
                + '\n\n'
            )
        if t == 'section':
            return ''.join(self.block(x) for x in b)
        if t == 'span':
            return self.flow_par(self.inline_el(b), indent=False)
        raise SystemExit(f'unhandled block <{t}> {k}')

    def after_heading_take(self):
        v, self.after_heading = self.after_heading, False
        return v

    def cells(self, row):
        out = []
        for td in row:
            out.append(
                self.inl(td)
                .replace('\x00', '')
                .replace(r'\\' + '\n', r'\newline ')
            )
        return out

    def data_table(self, b):
        rows = [self.cells(tr) for tr in b.iter(H + 'tr')]
        n = max(len(r) for r in rows)
        spec = 'l' * n
        size = r'\footnotesize' if self.in_note else r'\small'
        body = ' \\\\\n'.join(' & '.join(r + [''] * (n - len(r))) for r in rows)
        return (
            r'\par{\centering'
            + size
            + r'\begin{tabular}{@{}'
            + spec
            + r'@{}}'
            + '\n'
            + body
            + '\n'
            + r'\end{tabular}\par}\smallskip'
            + '\n\n'
        )

    def text_table(self, b):
        types = b.get('data-cols').split()
        n = len(types)
        head, body, taken = [], [], {}
        self.table_notes = []
        self.in_note += 1
        for i, tr in enumerate(b):
            j, row = 0, []
            for c in tr:
                while (i, j) in taken:
                    j += 1
                span, down = int(c.get('colspan', 1)), int(c.get('rowspan', 1))
                for di in range(1, down):
                    for dj in range(span):
                        taken[i + di, j + dj] = True
                src = c[0] if len(c) and 'grp' in cls(c[0]) else c
                row.append(
                    (
                        j,
                        span,
                        down,
                        self.inl(src).replace('\x00', '').split('\\\\\n'),
                        src is not c,
                    )
                )
                j += span
            (head if 'h' in cls(tr) else body).append((row, 'rule' in cls(tr)))
        text = {
            j: max(
                [0]
                + [
                    len(re.sub(r'\\[a-zA-Z]+|[{}]', '', ' '.join(c[3])))
                    for row, _ in body
                    for c in row
                    if c[0] == j and c[1] == 1
                ]
            )
            for j, k in enumerate(types)
            if k == 't'
        }
        spec = ''.join(
            (
                '@{\\hskip.3em}l'
                if k == 'u'
                else (
                    'r'
                    if types[j + 1 : j + 2] == ['u']
                    else (
                        'c'
                        if k in 'cn'
                        else (
                            'l'
                            if k == 'm'
                            else (
                                k
                                if k != 't'
                                else r'>{\raggedright\hangindent=1em'
                                r'\arraybackslash}p{'
                                + f'{min(text[j] * .46, 10):.1f}em'
                                + '}'
                            )
                        )
                    )
                )
            )
            for j, k in enumerate(types)
        )
        hgt = [
            max([1] + [len(ln) for _, _, down, ln, _ in row if down == 1])
            for row, _ in head
        ]
        for r, (row, _) in enumerate(head):
            for _, _, down, ln, _ in row:
                hgt[r] += max(0, len(ln) - sum(hgt[r : r + down]))
        out = []
        for r in range(len(head)):
            for li in range(hgt[r]):
                cells, j = [], 0
                while j < n:
                    r0, (j0, span, down, ln, _) = next(
                        (q, c)
                        for q in range(r, -1, -1)
                        for c in head[q][0]
                        if c[0] <= j < c[0] + c[1] and q + c[2] > r
                    )
                    at = (
                        sum(hgt[r0:r])
                        + li
                        - (sum(hgt[r0 : r0 + down]) - len(ln))
                    )
                    txt = ln[at].strip() if 0 <= at < len(ln) else ''
                    side = types[j] if span == 1 and types[j] in 'lr' else 'c'
                    cells.append(
                        r'\multicolumn{'
                        + str(span)
                        + '}{'
                        + side
                        + '}{'
                        + txt
                        + '}'
                    )
                    j += span
                out.append(' & '.join(cells) + r' \\')
            out += [
                r'\cmidrule(lr){' + f'{j + 1}-{j + span}' + '}'
                for j, span, _, _, grp in head[r][0]
                if grp
            ]
        if head:
            out.append(r'\midrule')
        for i, (row, rule) in enumerate(body):
            if rule and i:
                out.append(r'\midrule')
            cells, at = [], 0
            for j, span, _, ln, _ in row:
                cells += [''] * (j - at)
                txt = ' '.join(x.strip() for x in ln)
                cells.append(
                    r'\multicolumn{' + str(span) + '}{c}{' + txt + '}'
                    if span > 1
                    else txt
                )
                at = j + span
            out.append(' & '.join(cells) + r' \\')
        notes, self.table_notes = ''.join(self.table_notes), None
        self.in_note -= 1
        em = float(b.get('data-em'))
        sizes = [r'\small', r'\footnotesize', r'\scriptsize', r'\tiny']
        size = sizes[
            (0 if em <= 33 else 1 if em <= 38 else 2) + (self.in_note > 0)
        ]
        return (
            r'\par\nobreak\medskip{\centering'
            + size
            + r'\tabfont\widetab{\begin{tabular}{@{}'
            + spec
            + '@{}}\n\\toprule\n'
            + '\n'.join(out)
            + '\n'
            + r'\bottomrule'
            + '\n'
            + r'\end{tabular}}\par}'
            + notes
            + r'\medskip'
            + '\n\n'
        )

    def brace(self, b):
        tr = b.find(H + 'tr')
        left, right = tr.find(f'{H}td[@class="bl"]'), tr.find(
            f'{H}td[@class="br"]'
        )
        lrows = self.inl(left).split(r'\\' + '\n')
        lt = (
            r'\begin{tabular}{@{}r@{}}'
            + r' \\ '.join(x.strip() for x in lrows)
            + r'\end{tabular}'
        )
        return (
            r'\par\medskip{\centering$\left.'
            + r'\text{'
            + lt
            + r'}\right\}$\quad '
            + self.inl(right)
            + r'\par}\medskip'
            + '\n\n'
        )

    def toc_table(self, b):
        out = []
        for tr in b.iter(H + 'tr'):
            k = cls(tr)
            if 'lv-book' in k:
                out.append(r'\tocbook{' + self.inl(tr[0]) + '}')
                continue
            ti, pg = tr.find(f'{H}td[@class="ti"]'), tr.find(
                f'{H}td[@class="pg"]'
            )
            if ti is None:
                out.append(
                    r'\tocbook{' + ' '.join(self.inl(td) for td in tr) + '}'
                )
                continue
            a = ti.find(H + 'a')
            lv = int(k[0][2:]) if k and k[0][2:].isdigit() else 0
            if a is None:
                out.append(
                    r'\tocline{'
                    + f'{1.2 * lv:.1f}em'
                    + '}{'
                    + self.inl(ti)
                    + '}{}'
                )
                continue
            tg = self.target(a.get('href'))
            out.append(
                r'\tocline{'
                + f'{1.2 * lv:.1f}em'
                + '}{\\hyperref['
                + tg
                + ']{'
                + self.inl(a)
                + '}}{'
                + tg
                + '}'
            )
        return '\\begingroup\\small\n' + '\n'.join(out) + '\n\\endgroup\n\n'

    def heading(self, h):
        lv = self.levels.get(h.get('id')) or max(3, int(tag(h)[1]))
        pbs = [s for s in h.iter(H + 'span') if 'pb' in cls(s)]
        pre = ''.join(
            r'\pbm{' + s.get('id') + '}{' + esc(self.plabel(s)) + '}'
            for s in pbs
        )
        for s in pbs:
            par, prev = s.getparent(), s.getprevious()
            if s.tail:
                if prev is not None:
                    prev.tail = (prev.tail or '') + s.tail
                else:
                    par.text = (par.text or '') + s.tail
            par.remove(s)
        title = self.inl(h).replace('\x00', '')
        title = re.sub(r'\\cenline\{(.*)\}', r'\1', title)
        out = []
        toc = h.get('id') in self.levels
        if lv == 1:
            out.append(r'\cleardoublepage')
        elif toc and lv <= self.chap and not self.prev_heading:
            out.append(r'\clearpage')
        if toc and lv <= self.chap:
            out.append(r'\thispagestyle{plain.scrheadings}')
        if h.get('id'):
            out.append(r'\phantomsection\label{' + h.get('id') + '}')
            lab = self.labels.get(h.get('id'))
            if lab:
                out.append(
                    r'\bookmark[level='
                    + str(self.levels[h.get('id')] - 1)
                    + ',dest='
                    + h.get('id')
                    + ']{'
                    + lab.replace('\\', '').replace('{', '').replace('}', '')
                    + '}'
                )
                if lv <= self.chap:
                    out.append(
                        r'\markboth{'
                        + esc(running(lab))
                        + '}{'
                        + esc(running(lab))
                        + '}'
                    )
                elif lv == self.chap + 1:
                    out.append(r'\markright{' + esc(running(lab)) + '}')
        style = max(1, lv - (self.chap - 2)) if toc else lv
        out.append(
            '\\' + LEVELS[min(style, 6) - 1] + '{' + pre + title.strip() + '}'
        )
        self.after_heading = True
        return '\n'.join(out) + '\n\n'

    # -- documents ------------------------------------------------------------

    def titlepage(self, sec):
        sizes = {
            't-main': r'\maintitlefont',
            't-von': r'\small',
            't-author': r'\authorfont',
            't-vol': r'\large',
            't-ed': r'\normalsize',
            't-copy': r'\footnotesize',
            't-imprint': r'\normalsize',
            't-ny': r'\small',
        }
        space = {
            't-main': '1.2em',
            't-von': '.4em',
            't-author': '2.5em',
            't-vol': '1.2em',
            't-ed': '2em',
            't-copy': '0pt',
            't-imprint': '.8em',
            't-ny': '0pt',
        }
        out = [
            r'\cleardoublepage',
            r'\thispagestyle{empty}',
            r'\begingroup\centering',
        ]
        for b in sec:
            k = cls(b)
            if 'tp-anchor' in k:
                out.append(self.block(b))
                continue
            c = k[0] if k else ''
            if c == 't-main':
                out.append(r'\vspace*{.08\textheight}')
                if b.get('id'):
                    out.append(r'\phantomsection\label{' + b.get('id') + '}')
            if c == 't-imprint':
                out.append(r'\vfill')
            txt = self.inl(b).replace('\x00', '')
            txt = re.sub(r'\\pb\{([^}]*)\}\{[^}]*\}', r'\\pbx{\1}', txt)
            out.append(
                '{'
                + sizes.get(c, '')
                + ' '
                + txt
                + r'\par}'
                + r'\vspace{'
                + space.get(c, '1em')
                + '}'
            )
            if c == 't-vol':
                out.append(r'\TeilVermerk')
        out.append(r'\par\endgroup')
        return '\n'.join(out) + '\n'

    def imprint(self):
        vol, parts = self.book.vol, self.book.vol['parts']
        version = T.build_version()
        urls = ', '.join(
            r'\url{'
            + T.text_of(p['header'].find(f'.//{T.TEI}idno[@type="URLWeb"]'))
            + '}'
            for p in parts
        )
        return (
            '\n'.join(
                [
                    r'\clearpage\thispagestyle{empty}\vspace*{\fill}',
                    r'{\footnotesize\raggedright\setlength{\parindent}{0pt}'
                    r'\setlength{\parskip}{.5em}',
                    r'Textgrundlage: Deutsches Textarchiv, ' + urls + r'.\par',
                    r'Diese Ausgabe steht unter der Lizenz Creative Commons'
                    r' Namensnennung – Weitergabe unter gleichen '
                    r'Bedingungen 4.0 (CC BY-SA 4.0), \url{'
                    + T.LICENSE_URL
                    + r'}. Die editorische Notiz am'
                    r' Ende des Bandes nennt die Textgrundlage '
                    r'und alle Eingriffe.\par',
                    (
                        r'Bearbeitet von '
                        + esc(vol['editor'][0])
                        + r'. Hinweise auf Fehler bitte an \href{mailto:'
                        + vol['editor'][2]
                        + r'}{\nolinkurl{'
                        + vol['editor'][2]
                        + r'}}.\par'
                        if vol.get('editor')
                        else ''
                    ),
                    (
                        r'EPUB und PDF frei unter \url{'
                        + vol['homepage']
                        + r'}.\par'
                        if vol.get('homepage')
                        else ''
                    ),
                    ' '.join(
                        esc(x) + '.'
                        for x in (
                            vol.get('publisher'),
                            vol.get('printer')
                            and 'Druckausgabe: ' + vol['printer'],
                        )
                        if x
                    )
                    + r'\par',
                    r'Gesetzt in Crimson Pro, Griechisch in Gentium Book.\par',
                    ', '.join(
                        filter(
                            None,
                            (
                                version and 'Version ' + esc(version),
                                T.german_date(T.build_time()),
                            ),
                        )
                    )
                    + r'.\par}',
                    '',
                ]
            )
            + '\n'
        )

    def document(self):
        """LaTeX bodies, one per printed volume; the notice goes into each."""
        b = self.book
        docs, notice, marks = [], [], {}
        self.prev_heading = False
        for name, doc in b.files:
            if name == b.notes_file:
                continue
            body = doc.find(H + 'body')
            if 'titlepage' in cls(body):
                docs.append({'out': [], 'title': False, 'main': False})
            cur = notice if 'notiz' in name else docs[-1]['out']
            start = len(cur)
            if not docs[-1]['main'] and (
                name == b.first_body or (len(docs) > 1 and cls(body) == [])
            ):
                cur.append(
                    r'\mainmatter\thispagestyle{plain.scrheadings}\markboth{}{}'
                )
                docs[-1]['main'] = True
            for sec in body:
                k = cls(sec)
                if 'titlepage' in k:
                    cur.append(self.titlepage(sec))
                    if not docs[-1]['title']:
                        cur.append(self.imprint())
                        docs[-1]['title'] = True
                    continue
                if 'dedication' in k:
                    cur.append(
                        r'\cleardoublepage\thispagestyle{empty}'
                        r'\vspace*{.15\textheight}'
                    )
                    self.in_note += 1
                    cur.append(
                        r'\begingroup\centering\linespread{1.3}\selectfont '
                        + ''.join(
                            self.inl(p).replace('\x00', '') + r'\par'
                            for p in sec
                        )
                        + r'\endgroup'
                    )
                    self.in_note -= 1
                    continue
                for x in sec:
                    cur.append(self.block(x))
                    self.prev_heading = tag(x) in (
                        'h1',
                        'h2',
                        'h3',
                        'h4',
                        'h5',
                        'h6',
                    )
            marks[name] = (start, len(cur))
        split = b.vol.get('print_split')
        if split:
            out, (cut, _), moved = (
                docs[0]['out'],
                marks[split['at']],
                marks[split['move']],
            )
            front = [
                x for name in split['front'] for x in out[slice(*marks[name])]
            ]
            first = out[:cut] + out[moved[0] : moved[1]]
            second = (
                front
                + [
                    r'\mainmatter\setcounter{page}{\numexpr'
                    r'\getpagerefnumber{x-kapital-last}+'
                    r'\ifodd\getpagerefnumber{x-kapital-last} 2\else 1\fi}'
                ]
                + out[cut : moved[0]]
                + out[moved[1] :]
            )
            docs = [{'out': first}, {'out': second}]
        return ['\n'.join(d['out'] + notice) for d in docs]

    def write(self, path, language):
        vol = self.book.vol
        bodies = self.document()
        paths = (
            [Path(path)]
            if len(bodies) == 1
            else [
                Path(path).with_name(f'{Path(path).stem}-{i}.tex')
                for i in range(1, len(bodies) + 1)
            ]
        )
        digits = max(
            (
                len(re.sub(r'\D', '', m))
                for b in bodies
                for m in re.findall(r'\\fn(?:mark|text)?\{([^}]*)\}', b)
            ),
            default=1,
        )
        for i, (p, body) in enumerate(zip(paths, bodies)):
            body = LONE_PB.sub(
                lambda m: '\n\n\\' + m.group(2) + '{\\pbm' + m.group(1), body
            )
            here = set(re.findall(r'\\(?:pb|pbm|pbx|label)\{([^}]+)\}', body))
            body = re.sub(
                r'\\hyperref\[([^\]]+)\]\{',
                lambda m: m.group(0) if m.group(1) in here else '{',
                body,
            )
            title = vol['title']
            if len(bodies) > 1:
                title = title.replace(
                    ')',
                    ', '
                    + ('erster', 'zweiter', 'dritter')[i]
                    + (' Teil)' if vol.get('print_split') else ' Theil)'),
                )
            tex = '\n'.join(
                [
                    r'\newcommand{\Sprache}{' + language + '}',
                    r'\newcommand{\Titel}{Karl Marx: ' + esc(title) + '}',
                    (
                        r'\newcommand{\KapitalOther}{' + paths[1 - i].stem + '}'
                        if vol.get('print_split')
                        else ''
                    ),
                    (
                        r'\newcommand{\TeilVermerk}{{\itshape '
                        + ('Erster', 'Zweiter')[i]
                        + r' Teil\par}\vspace{1em}}'
                        if vol.get('print_split')
                        else ''
                    ),
                    r'\newcommand{\FnWidest}{' + '0' * digits + '}',
                    r'\input{praeambel}',
                    (
                        r'\AtEndDocument{\label{kapital-last}}'
                        if vol.get('print_split') and i == 0
                        else ''
                    ),
                    r'\begin{document}',
                    r'\frontmatter',
                    body,
                    r'\end{document}',
                    '',
                ]
            )
            p.write_text(tex, encoding='utf-8')
        return paths


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('band')
    ap.add_argument('out', help='Ausgabedatei (.tex)')
    ap.add_argument('-e', '--edition', default='erstausgaben')
    ap.add_argument('-v', '--variant', action='append', default=[])
    args = ap.parse_args()
    vol = T.load_volume(args.edition, args.band, args.variant)
    book = T.Book(vol, 'pdf')
    book.run()
    TeX(book).write(args.out, 'ngerman' if args.variant else 'german')


if __name__ == '__main__':
    main()
