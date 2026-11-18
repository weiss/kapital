"""Tables in the plain-text notation of editions/*/tables/*/tab-*.txt, as TEI.

  @ l n n u   column types (optional): l left, c centred, r right,
              t running text, n numbers aligned at the units digit,
              u unit belonging to the column before, m amounts like
              "1 sh. 6 d.", aligned at their first number
  A | 1 1/3   cells; a cell "<" joins the cell to its left, "^" the cell above
  ===         end of the head
  ---         rule
  :: Text     a line across all columns

A blank line starts another table. Cells hold TEI markup; "1 1/3" and "2/9"
become fractions, "80_c" an index, "9 317 629" a number in groups of three,
"25 5/7 {25 2/7}" a correction of the reading of the print given in braces. An
empty <note/> stands for the footnote that the 'table_notes' of the part give
for the table.
"""

import re

from lxml import etree

NS = 'http://www.tei-c.org/ns/1.0'
VULGAR = {
    '1/2': '½',
    '1/3': '⅓',
    '2/3': '⅔',
    '1/4': '¼',
    '3/4': '¾',
    '1/5': '⅕',
    '2/5': '⅖',
    '3/5': '⅗',
    '4/5': '⅘',
    '1/6': '⅙',
    '5/6': '⅚',
    '1/8': '⅛',
    '3/8': '⅜',
    '5/8': '⅝',
    '7/8': '⅞',
}
FIG, PUNCT, FRAC_GAP = '\u2007', '\u2008', '\u2002\u2004'
FRACTION = re.compile(r'(?<![\d/])(?:(\d+) )?(\d+/\d+)(?![\d/])')
SIC = re.compile(r'\s*\{(.*)\}$')
NUMBER = re.compile(
    r'([−+]?(?:\d{1,3}(?: \d{3})+|\d[\d.,]*?)|−)?(?: ?(\d+/\d+))?([.,]| ?%)?'
)
GROUPS = re.compile(r'(?<=\d) (?=\d{3}(?!\d))')
INDEX = re.compile(r'(?<=\d)_([a-z])')


def fractions(s):
    def sub(m):
        f = VULGAR.get(m.group(2)) or f'<hi rendition="#vf">{m.group(2)}</hi>'
        return (m.group(1) or '') + f

    s = INDEX.sub(r'<hi rendition="#sub">\1</hi>', GROUPS.sub('\u202f', s))
    return FRACTION.sub(sub, s)


def plain(s):
    """A cell of the notation as running text."""
    s = re.sub(r'<[^>]+>', '', s.replace('-<lb/>', '').replace('<lb/>', ' '))
    return FRACTION.sub(
        lambda m: (
            (m.group(1) or '') + VULGAR[m.group(2)]
            if m.group(2) in VULGAR
            else m.group(0)
        ),
        s,
    )


def align(cells):
    """Pad the numbers of a column so that, centred, their units digits stand
    below each other."""
    notes = {i: c.endswith('<note/>') for i, c in enumerate(cells)}
    cells = [c[:-7] if notes[i] else c for i, c in enumerate(cells)]
    nums = {i: NUMBER.fullmatch(c) for i, c in enumerate(cells)}
    nums = {i: m for i, m in nums.items() if m and (m.group(1) or m.group(2))}
    if len(nums) < 2:
        return [c + '<note/>' * notes[i] for i, c in enumerate(cells)]
    longest = max((m.group(1) or '' for m in nums.values()), key=len)
    frac = any(m.group(2) for m in nums.values())
    tail = any(m.group(3) for m in nums.values())
    out = list(cells)
    for i, m in nums.items():
        whole, unit = m.group(1) or '', m.group(3) or ''
        pad = ''.join(
            PUNCT if ch in '.,' else '\u202f' if ch == ' ' else FIG
            for ch in longest[: len(longest) - len(whole)]
        )
        num = ' '.join(
            x for x in (GROUPS.sub('\u202f', whole), m.group(2)) if x
        ).replace('− ', '−')
        gap = FRAC_GAP if frac and not m.group(2) else ''
        out[i] = (
            (gap + pad + num + unit)
            if unit
            else pad + num + gap + (FRAC_GAP if tail else '')
        )
    return [c + '<note/>' * notes[i] for i, c in enumerate(out)]


def column_types(body, n):
    types = []
    for j in range(n):
        cells = [
            r[j]
            for r in body
            if r[j] not in ('', '<', '^') and r[j + 1 :] != ['<'] * (n - j - 1)
        ]
        if cells and all(NUMBER.fullmatch(c) or c in '—–' for c in cells):
            types.append('n')
        else:
            types.append('l' if j == 0 else 'c')
    return types


def table(lines):
    types, rows, head, rule = None, [], 0, False
    for line in lines:
        if line.startswith('@ '):
            types = line[2:].split()
        elif set(line) == {'='}:
            head = len(rows)
        elif set(line) == {'-'}:
            rule = True
        else:
            rows.append(([c.strip() for c in line.split('|')], rule))
            rule = False
    n = max(len(cells) for cells, _ in rows)
    grid = [
        (
            [cells[0][3:]] + ['<'] * (n - 1)
            if cells[0].startswith(':: ')
            else cells + [''] * (n - len(cells))
        )
        for cells, _ in rows
    ]
    sic = {}
    for i, cells in enumerate(grid):
        for j, c in enumerate(cells):
            m = SIC.search(c)
            if m:
                sic[i, j], cells[j] = (m.group(1), c[: m.start()]), c[
                    : m.start()
                ]
    types = types or column_types(grid[head:], n)
    for j, t in enumerate(types):
        if t == 'n':
            col = align([grid[i][j] for i in range(head, len(grid))])
            for i, c in enumerate(col):
                grid[head + i][j] = c
        elif t == 'm':
            lead = {
                i: re.match(r'\d+', grid[i][j]) for i in range(head, len(grid))
            }
            most = max([len(m.group()) for m in lead.values() if m] or [0])
            for i, m in lead.items():
                if m:
                    grid[i][j] = FIG * (most - len(m.group())) + grid[i][j]
    tab = etree.Element(f'{{{NS}}}table', _cols=' '.join(types))
    for i, cells in enumerate(grid):
        row = etree.SubElement(tab, f'{{{NS}}}row')
        if i < head:
            row.set('role', 'label')
        if rows[i][1]:
            row.set('_rule', '1')
        for j, c in enumerate(cells):
            if c in ('<', '^'):
                continue
            inner = fractions(c).replace(' %', '\u202f%')
            if (i, j) in sic:
                inner = (
                    f'<choice><sic>{fractions(sic[i, j][0])}</sic>'
                    f'<corr>{inner}</corr></choice>'
                )
            cell = etree.fromstring(f'<cell xmlns="{NS}">{inner}</cell>')
            if (i, j) in sic:
                cell.set('_sic', plain(sic[i, j][0]))
                cell.set('_corr', plain(sic[i, j][1]))
            span = 1
            while j + span < n and cells[j + span] == '<':
                span += 1
            down = 1
            while i + down < len(grid) and grid[i + down][j] == '^':
                down += 1
            if span > 1:
                cell.set('cols', str(span))
            if down > 1:
                cell.set('rows', str(down))
            cell.set('_col', str(j))
            row.append(cell)
    return tab


def parse(text):
    blocks = [b for b in re.split(r'\n\s*\n', text.strip()) if b.strip()]
    return [
        table([ln.rstrip() for ln in b.split('\n') if ln.strip()])
        for b in blocks
    ]
