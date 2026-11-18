"""Assemble reconstructed pages into DTA-style TEI (pilot: prefaces, chapter 1,
chapter 8)."""

import html
import pickle
import re
import statistics

import rec

pages = pickle.load(open(f'{rec.W}/pages.pkl', 'rb'))
BIGR = pickle.load(open(f'{rec.W}/bigr.pkl', 'rb'))
PATCH = {}
try:
    from patches import PATCH, TOKFIX  # noqa
except ImportError:
    TOKFIX = {}

ROMAN = [
    'V',
    'VI',
    'VII',
    'VIII',
    'IX',
    'X',
    'XI',
    'XII',
    'XIII',
    'XIV',
    'XV',
    'XVI',
    'XVII',
    'XVIII',
    'XIX',
    'XX',
    'XXI',
    'XXII',
    'XXIII',
    'XXIV',
    'XXV',
    'XXVI',
    'XXVII',
    'XXVIII',
    'XXIX',
    'XXX',
    'XXXI',
    'XXXII',
]


def page_label(leaf):
    if leaf >= 37:
        return str(leaf - 36)
    if 9 <= leaf <= 36:
        return ROMAN[leaf - 9]
    return None


def esc(s):
    return html.escape(s, quote=False)


def spaced(leaf, t):
    s = rec.sperr_score(leaf, t, BIGR)
    core = re.sub(r'[^A-Za-zÄÖÜäöüß]', '', t['x'])
    if s is None:
        g = rec.glyph_gaps(leaf, t)
        return (
            len(core) >= 3
            and len(g) >= 2
            and sum(1 for x in g if x >= 0.13) / len(g) >= 0.75
        )
    return (s >= 0.085 and len(core) >= 3) or s >= 0.12


def line_info(leaf, r, i, tl):
    x0, x1 = tl[0]['x0'] - r['bx0'], r['bx1'] - tl[-1]['x1']
    return {'left': x0, 'right': x1, 'h': r['body_h']}


def tokens_of_line(leaf, tl, li, part):
    out = []
    for j, t in enumerate(tl):
        txt = TOKFIX.get((leaf, part, li, j), t['x'])
        if txt == '':
            continue
        out.append(
            {
                'x': txt,
                'sp': (
                    spaced(leaf, t)
                    if txt[:1].isalpha() or txt[:1] in '„"('
                    else False
                ),
                'leaf': leaf,
                'li': li,
                'j': j,
                's': t['s'],
                'orig': t,
            }
        )
    # smoothing: an unspaced word between two spaced ones with some extra
    # spacing counts as spaced
    for k in range(1, len(out) - 1):
        if not out[k]['sp'] and out[k - 1]['sp'] and out[k + 1]['sp']:
            s = rec.sperr_score(leaf, out[k]['orig'], BIGR)
            if s is None or s > 0.04:
                out[k]['sp'] = True
    return out


NOTE_START = re.compile(r'^([0-9*?!°®¹²³⁴⁵⁶⁷⁸⁹⁰‘’“\'".,%lI]{1,4})[)\],]')
REF_TAIL = re.compile(
    r'(?<=[A-Za-zÄÖÜäöüß.,;:!?“”"\'‘’)\]])'
    r'([0-9*?!°®¹²³⁴⁵⁶⁷⁸⁹⁰‘’“”\'"]{1,4}[a-z]?)\)'
)


def find_refs(tok, depth=0):
    """Footnote reference inside a token, e.g. 'Sache?).' -> ('Sache', '.')"""
    m = REF_TAIL.search(tok)
    if not m or '(' in tok[: m.start()]:
        return None
    mark = m.group(1)
    if depth > 0 and re.fullmatch(r'[“”"\'‘’!?]+', mark):
        return None
    return tok[: m.start()], tok[m.end() :]


def mark_refs(stream):
    """Flag reference tokens, tracking parenthesis depth within paragraphs."""
    depth = 0
    for it in stream:
        if it[0] != 'line':
            continue
        if it[1] in ('para', 'center'):
            depth = 0
        for t in it[2]:
            x = t['x']
            a = (t['orig'].get('a') or '') if 'orig' in t else ''
            r = find_refs(x, depth)
            if (
                r is None
                and re.fullmatch(
                    r'[0-9*?!°®¹²³⁴⁵⁶⁷⁸⁹⁰‘’“”\'"]{1,4}\)[.,;:]*', x
                )
                and depth == 0
            ):
                r = ('', x[x.index(')') + 1 :])
            if (
                r is None
                and re.search(r'[A-Za-zäöü.,;:“"\']\d{1,3}\)', a)
                and not re.search(r'\(', a)
            ):
                r = (x, '')
            t['ref'] = r is not None
            depth += x.count('(') - (x.count(')') - (1 if r else 0))
            depth = max(depth, 0)


ORD = [
    'Erstes',
    'Zweites',
    'Drittes',
    'Viertes',
    'Fünftes',
    'Sechstes',
    'Siebentes',
    'Achtes',
    'Neuntes',
]


def classify(r, lines):
    h = r['body_h']
    lefts = [tl[0]['x0'] for tl in lines]
    kinds = []
    for i, tl in enumerate(lines):
        win = sorted(lefts[max(0, i - 4) : i + 5])
        base = win[len(win) // 3]
        left = tl[0]['x0'] - base
        right = r['bx1'] - tl[-1]['x1']
        if left >= 2.5 * h and right >= 2.5 * h:
            kinds.append('center')
        elif left >= 0.8 * h:
            kinds.append('para')
        else:
            kinds.append('cont')
    return kinds


def note_groups(leaf, r):
    groups = []
    lines = r['notes']
    if not lines:
        return groups
    lefts = [tl[0]['x0'] for tl in lines]
    for li, tl in enumerate(lines):
        first = TOKFIX.get((leaf, 'notes', li, 0), tl[0]['x'])
        win = sorted(lefts[max(0, li - 4) : li] + lefts[li + 1 : li + 5]) or [
            min(lefts)
        ]
        base = win[len(win) // 3]
        ind = tl[0]['x0'] - base > 0.6 * r['body_h']
        start = ind and (
            bool(NOTE_START.match(first)) or not first[:1].islower()
        )
        if PATCH.get((leaf, 'notes', li)) == 'START':
            start = True
        elif PATCH.get((leaf, 'notes', li)) == 'CONT':
            start = False
        if start or not groups:
            groups.append({'start': start, 'lines': []})
        groups[-1]['lines'].append((li, tl))
    return groups


def render_tokens(toks):
    """Tokens (with hyphenation already joined) -> TEI string with Sperrung."""
    out, run = [], []

    def flush():
        if run:
            core = ' '.join(run)
            m = re.match(r'^(.*?)([.,;:!?“”"\')]*)$', core)
            out.append(
                f'<hi rendition="#g">{esc(m.group(1))}</hi>{esc(m.group(2))}'
            )
            run.clear()

    for t in toks:
        if t.get('tei'):
            flush()
            out.append(t['tei'])
            continue
        if t['sp']:
            pre = re.match(r'^([„"(\[‚]*)(.*)$', t['x'])
            if not run and pre.group(1):
                out.append(esc(pre.group(1)))
                run.append(pre.group(2))
            else:
                run.append(t['x'])
            continue
        flush()
        out.append(esc(t['x']))
    flush()
    s = ' '.join(out)
    s = s.replace('<lbx/> ', '').replace(' <lbx/>', '')
    return re.sub(r'\s+', ' ', s)


ELLIPSIS_NEXT = {
    'und',
    'oder',
    'bis',
    'wie',
    'als',
    'u.',
    'resp.',
    'noch',
    'sowie',
}


class Note:
    def __init__(self, n):
        self.n, self.toks = n, []


def build(leaves, first_head_level=3, stop=None, start=None, note_reset=True):
    stream = []
    started = start is None
    for leaf in leaves:
        r = pages[leaf]
        lines = r['body']
        kinds = classify(r, lines)
        page_items = [('pb', leaf)]
        for li, tl in enumerate(lines):
            p = PATCH.get((leaf, 'body', li))
            text = ' '.join(t['x'] for t in tl)
            if not started:
                if re.search(start, text):
                    started = True
                else:
                    continue
            if stop and re.search(stop, text) and li >= 0 and stream:
                stream.extend(page_items)
                return finish(stream)
            if p == 'DROP':
                continue
            if isinstance(p, tuple) and p[0] == 'tei':
                page_items.append(
                    ('tei', p[1], leaf, p[2] if len(p) > 2 else 'block')
                )
                continue
            kind = (
                p[1] if isinstance(p, tuple) and p[0] == 'kind' else kinds[li]
            )
            page_items.append(
                ('line', kind, tokens_of_line(leaf, tl, li, 'body'), leaf)
            )
        if started:
            page_items.append(('notes', leaf, note_groups(leaf, r)))
            stream.extend(page_items)
    return finish(stream)


def finish(stream):
    # 1. hyphenation across line (and page) ends
    lines = [it for it in stream if it[0] == 'line']
    for a, b in zip(lines, lines[1:]):
        if not a[2] or not b[2]:
            continue
        last, first = a[2][-1], b[2][0]
        if (
            last['x'].endswith('-')
            and len(last['x']) > 1
            and first['x'][:1].islower()
            and first['x'] not in ELLIPSIS_NEXT
            and b[1] != 'center'
        ):
            last['x'] = last['x'][:-1] + first['x']
            last['sp'] = last['sp'] or first['sp']
            b[2].pop(0)
    # 2. footnotes: note starts numbered by DP over the section; refs chosen per
    # page
    import notes_dp

    mark_refs(stream)
    leaves = [it[1] for it in stream if it[0] == 'notes']
    cands = notes_dp.note_candidates(leaves)
    assigned = notes_dp.assign(cands)
    start_num = {
        (cands[i]['leaf'], cands[i]['li']): n for i, n in assigned.items()
    }
    notes, cur_note, problems = [], None, []
    for idx, it in enumerate(stream):
        if it[0] != 'notes':
            continue
        leaf = it[1]
        r = pages[leaf]
        groups = []
        for li, tl in enumerate(r['notes']):
            if PATCH.get((leaf, 'notes', li)) == 'DROP':
                continue
            n = start_num.get((leaf, li))
            if n is not None or not groups:
                groups.append({'n': n, 'lines': []})
            groups[-1]['lines'].append((li, tl))
        page_notes = []
        for g in groups:
            toks = []
            for li, tl in g['lines']:
                p = PATCH.get((leaf, 'notes', li))
                if isinstance(p, tuple) and p[0] == 'tei':
                    toks.append({'x': '', 'sp': False, 'tei': p[1]})
                    continue
                lt = tokens_of_line(leaf, tl, li, 'notes')
                if (
                    toks
                    and lt
                    and toks[-1]['x'].endswith('-')
                    and lt[0]['x'][:1].islower()
                    and lt[0]['x'] not in ELLIPSIS_NEXT
                ):
                    toks[-1]['x'] = toks[-1]['x'][:-1] + lt[0]['x']
                    toks[-1]['sp'] = toks[-1]['sp'] or lt[0]['sp']
                    lt = lt[1:]
                toks.extend(lt)
            if g['n'] is not None:
                if toks:
                    m = NOTE_START.match(toks[0]['x'])
                    if m:
                        rest = toks[0]['x'][m.end() :]
                        if rest:
                            toks[0]['x'] = rest
                        else:
                            toks.pop(0)
                    elif (
                        len(toks[0]['x']) <= 4
                        and not toks[0]['x'][:1].isalpha()
                    ):
                        toks.pop(0)
                cur_note = Note(g['n'])
                cur_note.toks = toks
                notes.append(cur_note)
                page_notes.append(cur_note)
            elif cur_note is not None:
                if (
                    cur_note.toks
                    and toks
                    and cur_note.toks[-1]['x'].endswith('-')
                    and toks[0]['x'][:1].islower()
                ):
                    cur_note.toks[-1]['x'] = (
                        cur_note.toks[-1]['x'][:-1] + toks[0]['x']
                    )
                    toks = toks[1:]
                cur_note.toks.extend(toks)
        page_lines = [
            jt for jt in stream[:idx] if jt[0] == 'line' and jt[3] == leaf
        ]
        cand = [
            t
            for jt in page_lines
            for t in jt[2]
            if t.get('ref') or PATCH.get(('ref', leaf, t['li'], t['j']))
        ]
        forced = [t for t in cand if PATCH.get(('ref', leaf, t['li'], t['j']))]
        if forced:
            cand = forced
        if len(cand) != len(page_notes):
            problems.append(
                (
                    leaf,
                    len(cand),
                    [n.n for n in page_notes],
                    [t['x'] for t in cand],
                )
            )
        for t, n in zip(cand, page_notes):
            t['note'] = n
    return stream, notes, problems


DIGMAP = str.maketrans(
    {
        'l': '1',
        'I': '1',
        'ı': '1',
        '|': '1',
        'i': '1',
        '!': '1',
        'O': '0',
        'o': '0',
        'S': '5',
        's': '5',
        'B': '8',
        'Z': '2',
        'z': '2',
        '°': '0',
        '¹': '1',
        '²': '2',
        '³': '3',
        '⁴': '4',
        '⁵': '5',
        '⁶': '6',
        '⁷': '7',
        '⁸': '8',
        '⁹': '9',
        '⁰': '0',
    }
)


def num_guess(*readings):
    out = set()
    for r in readings:
        if not r:
            continue
        m = re.search(r'([0-9lIı|i!OoSsBZz°¹²³⁴⁵⁶⁷⁸⁹⁰]{1,3})[a-z]?[)\],]', r)
        if m:
            d = m.group(1).translate(DIGMAP)
            if d.isdigit():
                out.add(int(d))
        m = re.search(r'(\d{1,3})', r)
        if m:
            out.add(int(m.group(1)))
    return out


LABEL = re.compile(
    r'^(\w+ (Buch|Abschnitt|Kapitel)|Vorwort|Nachwort|Zur'
    r' (zweiten|dritten|vierten) Auflage)',
    re.I,
)
MARK = [
    ('num_paren', re.compile(r'^\d+\)')),
    ('num_dot', re.compile(r'^\d+\.\s')),
    ('upper', re.compile(r'^[A-H]\)')),
    ('lower', re.compile(r'^[a-h]\)')),
    ('roman', re.compile(r'^[IVX]+\.\s')),
]


def marker_type(text):
    for name, rx in MARK:
        if rx.match(text):
            return name
    return None


def line_text(toks):
    return ' '.join(t['x'] for t in toks)


def ref_split(t):
    r = find_refs(t['x']) if t.get('ref') else None
    if r is None:
        m = re.fullmatch(r'[0-9*?!°®¹²³⁴⁵⁶⁷⁸⁹⁰‘’“”\'"]{1,4}\)([.,;:]*)', t['x'])
        return ('', m.group(1)) if m else (t['x'], '')
    return r


def note_tei(n):
    body = render_tokens(n.toks)
    return f'<note place="foot" n="{n.n})">{body}</note>'


def emit_tokens(toks):
    out = []
    for t in toks:
        if t.get('note') is not None:
            before, after = ref_split(t)
            tt = dict(t, x=before)
            out.append(tt) if before else None
            out.append(
                {'x': '', 'sp': False, 'tei': note_tei(t['note']) + esc(after)}
            )
        else:
            out.append(t)
    return render_tokens(out)


def to_tei(stream, base_level=3):
    out, para, heads = [], None, []
    stack = []  # open div levels
    mstack = []  # marker types for section levels

    def close_para():
        nonlocal para
        if para is not None and para.strip():
            out.append(f'<p>{para.strip()}</p>')
        para = None

    def open_div(level, head):
        while stack and stack[-1] >= level:
            out.append('</div>')
            stack.pop()
        out.append(f'<div n="{level}"><head>{head}</head>')
        stack.append(level)

    def flush_heads():
        if not heads:
            return
        groups = []
        for toks in heads:
            txt = line_text(toks)
            if LABEL.match(txt) or marker_type(txt) or not groups:
                groups.append([toks])
            else:
                groups[-1].append(toks)
        for g in groups:
            txt = line_text(g[0])
            head = '<lb/>'.join(emit_tokens(l) for l in g)
            m = LABEL.match(txt)
            if m and re.search('Buch', txt):
                lvl = 1
            elif m and re.search('Abschnitt', txt):
                lvl = 2
            elif m and re.search('Kapitel', txt):
                lvl = base_level
                mstack.clear()
            elif m:
                lvl = base_level
            else:
                mt = marker_type(txt) or 'none'
                if mt in mstack:
                    del mstack[mstack.index(mt) + 1 :]
                else:
                    mstack.append(mt)
                lvl = base_level + len(mstack)
            open_div(lvl, head)
        heads.clear()

    pending_pb = []
    for idx, it in enumerate(stream):
        if it[0] == 'pb':
            tag = f'<pb n="{page_label(it[1])}" facs="#f{it[1]:04d}"/>'
            if para is not None:
                para += tag
            else:
                pending_pb.append(tag)
            continue
        if it[0] == 'notes':
            continue
        if it[0] == 'tei':
            close_para()
            flush_heads()
            out.extend(pending_pb)
            pending_pb.clear()
            if it[3] == 'inline' and out and out[-1].startswith('<p>'):
                out[-1] = out[-1][:-4] + ' ' + it[1] + '</p>'
            else:
                out.append(it[1])
            continue
        kind, toks = it[1], it[2]
        if not toks:
            continue
        txt = line_text(toks)
        nxt = next(
            (jt for jt in stream[idx + 1 :] if jt[0] == 'line' and jt[2]), None
        )
        is_head = (
            kind == 'center'
            and '=' not in txt
            and (
                heads
                or LABEL.match(txt)
                or marker_type(txt)
                or sum(t['sp'] for t in toks) >= len(toks) / 2
            )
        )
        if (
            not is_head
            and marker_type(txt)
            and nxt is not None
            and nxt[1] == 'center'
            and sum(t['sp'] for t in toks) >= len(toks) / 2
        ):
            is_head = True
        if is_head:
            close_para()
            out.extend(pending_pb)
            pending_pb.clear()
            heads.append(toks)
            continue
        flush_heads()
        if kind == 'center':
            close_para()
            out.extend(pending_pb)
            pending_pb.clear()
            out.append(f'<p rendition="#c">{emit_tokens(toks)}</p>')
            continue
        if kind == 'para' or para is None:
            close_para()
            para = ''.join(pending_pb)
            pending_pb.clear()
        para += ' ' + emit_tokens(toks)
    close_para()
    flush_heads()
    out.extend(pending_pb)
    out.extend('</div>' for _ in stack)
    return '\n'.join(out)
