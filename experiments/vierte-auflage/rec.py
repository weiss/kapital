"""Reconstruct the 1890 text from two OCR witnesses (ABBYY, Tesseract) on the
same scan images."""

import csv
import pickle
import re
import statistics
from functools import lru_cache

import wordfreq

import os

W = os.environ.get(
    'K4WORK', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'work')
)
PAGES = pickle.load(open(f'{W}/abbyy.pkl', 'rb'))
LEX = pickle.load(open(f'{W}/dta_lex.pkl', 'rb'))
PUNCT_L = '„"\'»«‚(['
PUNCT_R = '.,;:!?"\'“”«»)]*'


def tess(leaf):
    path = f'{W}/tess/leaf_{leaf:04d}.tsv'
    rows = list(
        csv.DictReader(
            open(path, encoding='utf-8'), delimiter='\t', quoting=csv.QUOTE_NONE
        )
    )
    out = []
    for r in rows:
        if r['level'] != '5' or not (r['text'] or '').strip():
            continue
        x, y, w, h = (int(r[k]) for k in ('left', 'top', 'width', 'height'))
        out.append(
            {
                't': r['text'].strip(),
                'x0': x,
                'y0': y,
                'x1': x + w,
                'y1': y + h,
                'c': float(r['conf']),
                'line': (r['block_num'], r['par_num'], r['line_num']),
            }
        )
    return out


def abbyy_lines(leaf):
    lines = []
    for par in PAGES[leaf]['paras']:
        for ln in par:
            ws = [
                {'t': t.strip(), 'x0': x0, 'y0': y0, 'x1': x1, 'y1': y1, 'c': c}
                for t, x0, y0, x1, y1, c in ln
                if t.strip()
            ]
            if ws:
                lines.append(ws)
    lines.sort(
        key=lambda l: (statistics.median(w['y1'] for w in l), l[0]['x0'])
    )
    return lines


def overlap(a, b):
    ox = min(a['x1'], b['x1']) - max(a['x0'], b['x0'])
    oy = min(a['y1'], b['y1']) - max(a['y0'], b['y0'])
    return max(0, ox) * max(0, oy)


def attach(lines, tw):
    """For every ABBYY word, collect the Tesseract words whose box mostly lies
    inside it."""
    used = set()
    for ln in lines:
        for w in ln:
            cands = []
            for i, t in enumerate(tw):
                ov = overlap(w, t)
                area = max(1, (t['x1'] - t['x0']) * (t['y1'] - t['y0']))
                if ov / area > 0.5:
                    cands.append(i)
            w['tess'] = ' '.join(
                tw[i]['t'] for i in sorted(cands, key=lambda i: tw[i]['x0'])
            )
            w['tc'] = min((tw[i]['c'] for i in cands), default=0)
            used.update(cands)
    return [t for i, t in enumerate(tw) if i not in used]


def split_punct(s):
    m = re.match(
        r'^([%s]*)(.*?)([%s]*)$' % (re.escape(PUNCT_L), re.escape(PUNCT_R)), s
    )
    return m.group(1), m.group(2), m.group(3)


@lru_cache(maxsize=None)
def lexscore(core):
    if not core:
        return 0
    if LEX.get(core) or LEX.get(core.lower()) or LEX.get(core.capitalize()):
        return 3 + min(2, (LEX.get(core, 0) + LEX.get(core.lower(), 0)) / 50)
    if re.fullmatch(r'\d+([.,]\d+)*', core):
        return 2
    z = max(
        wordfreq.zipf_frequency(core, 'de'),
        wordfreq.zipf_frequency(core, 'en'),
        wordfreq.zipf_frequency(core, 'fr'),
        wordfreq.zipf_frequency(core, 'la'),
    )
    return min(2.5, z / 2)


def tess_lines(leaf):
    tw = tess(leaf)
    groups = {}
    for t in tw:
        groups.setdefault(t['line'], []).append(t)
    lines = [sorted(g, key=lambda t: t['x0']) for g in groups.values()]
    lines.sort(
        key=lambda l: (statistics.median(t['y1'] for t in l), l[0]['x0'])
    )
    for l in lines:
        lh = statistics.median(t['y1'] - t['y0'] for t in l)
        for t in l:
            t['lh'] = lh
    return lines


def box(ws):
    return {
        'x0': min(w['x0'] for w in ws),
        'y0': min(w['y0'] for w in ws),
        'x1': max(w['x1'] for w in ws),
        'y1': max(w['y1'] for w in ws),
    }


def vov(a, b):
    return max(0, min(a['y1'], b['y1']) - max(a['y0'], b['y0'])) / max(
        1, min(a['y1'] - a['y0'], b['y1'] - b['y0'])
    )


def key(s):
    return re.sub(r'[^0-9a-zäöüß]', '', s.lower())


def align_line(tl, al):
    """Pair each Tesseract token with the ABBYY text covering the same stretch
    (string alignment)."""
    from difflib import SequenceMatcher

    tk = [key(t['t']) for t in tl]
    ak = [key(a['t']) for a in al]
    sm = SequenceMatcher(None, tk, ak, autojunk=False)
    for t in tl:
        t['a'] = None
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == 'equal':
            for k in range(i2 - i1):
                tl[i1 + k]['a'] = al[j1 + k]['t']
        elif op == 'replace':
            atext = ' '.join(a['t'] for a in al[j1:j2])
            if i2 - i1 == 1:
                tl[i1]['a'] = atext
            elif key(atext) == ''.join(tk[i1:i2]):
                for k in range(i1, i2):
                    tl[k]['a'] = tl[k]['t']
            else:
                # distribute by character offsets
                pos, acc = 0, []
                joined = ''.join(key(a['t']) for a in al[j1:j2])
                for k in range(i1, i2):
                    n = len(tk[k])
                    tl[k]['a'] = joined[pos : pos + n] or None
                    tl[k]['a_raw'] = True
                    pos += n


def hocr_lines(leaf):
    s = open(f'{W}/hocr/leaf_{leaf:04d}.hocr', encoding='utf-8').read()
    rows = re.findall(
        r"class='ocr_(?:line|caption|textfloat|header)' id='[^']*' title=\"bbox"
        r" (\d+) (\d+) (\d+) (\d+);"
        r"[^\"]*x_size ([\d.]+);[^\"]*x_descenders ([\d.]+); x_ascenders"
        r" ([\d.]+)\"",
        s,
    )
    return [
        {
            'x0': int(r[0]),
            'y0': int(r[1]),
            'x1': int(r[2]),
            'y1': int(r[3]),
            'xh': float(r[4]) - float(r[5]) - float(r[6]),
        }
        for r in rows
    ]


def page_lines(leaf):
    tls = tess_lines(leaf)
    hl = hocr_lines(leaf)
    for tl in tls:
        b = box(tl)
        best = max(hl, key=lambda h: overlap(b, h), default=None)
        xh = best['xh'] if best is not None and overlap(b, best) > 0 else 0
        for t in tl:
            t['xh'] = xh
    als = abbyy_lines(leaf)
    for tl in tls:
        b = box(tl)
        best = max(als, key=lambda al: vov(b, box(al)), default=None)
        if best is not None and vov(b, box(best)) > 0.4:
            align_line(tl, best)
        else:
            for t in tl:
                t['a'] = None
    return tls


_IMG = {}


def image(leaf):
    if leaf not in _IMG:
        import numpy as np
        from PIL import Image

        _IMG.clear()
        _IMG[leaf] = np.array(
            Image.open(f'{W}/img/leaf_{leaf:04d}.jpg').convert('L')
        )
    return _IMG[leaf]


def gaps(leaf, t, thr=150):
    """Widths of the white column runs between the glyphs of a word (letter
    spacing)."""
    import numpy as np

    im = image(leaf)
    y0, y1 = t['y0'], t['y1']
    h = y1 - y0
    band = im[y0 + h // 4 : y1 - h // 4, t['x0'] : t['x1']]
    if band.size == 0:
        return []
    ink = (band < thr).sum(axis=0) > 0
    runs, cur, seen = [], 0, False
    for v in ink:
        if v:
            if seen and cur:
                runs.append(cur)
            seen, cur = True, 0
        else:
            cur += 1
    return runs


ALPHA = re.compile(r'^[A-Za-zÄÖÜäöüß]+$')


def fit_widths(leaves):
    """Least-squares glyph widths (in units of line height) from plain words on
    the given pages."""
    import numpy as np

    rows, ys, chars = [], [], {}
    for leaf in leaves:
        for tl in tess_lines(leaf):
            h = statistics.median(t['y1'] - t['y0'] for t in tl)
            lh = line_height(tl)
            for t in tl:
                if ALPHA.match(t['t']) and len(t['t']) >= 2:
                    for ch in t['t']:
                        chars.setdefault(ch, len(chars))
                    rows.append(t['t'])
                    ys.append((t['x1'] - t['x0']) / lh)
    A = np.zeros((len(rows), len(chars)))
    for i, w in enumerate(rows):
        for ch in w:
            A[i, chars[ch]] += 1
    sol, *_ = np.linalg.lstsq(A, np.array(ys), rcond=None)
    return {ch: sol[i] for ch, i in chars.items()}


def line_height(tl):
    """x-height proxy: median height of words without ascenders/descenders is
    noisy; use median box height."""
    return statistics.median(t['y1'] - t['y0'] for t in tl)


def spacing(t, widths, lh):
    core = re.sub(r'[^A-Za-zÄÖÜäöüß]', '', t['t'])
    if len(core) < 2 or any(c not in widths for c in core):
        return None
    pre, c, post = split_punct(t['t'])
    exp = sum(widths[ch] for ch in core) * lh
    extra = (t['x1'] - t['x0']) - exp
    if pre or post:
        return None
    return extra / (len(core) - 1) / lh


def glyph_gaps(leaf, t, thr=140):
    """Gaps between connected glyph components inside a word box, in units of
    box height."""
    import numpy as np
    from scipy import ndimage

    im = image(leaf)
    sub = im[t['y0'] : t['y1'], t['x0'] : t['x1']] < thr
    if sub.size == 0:
        return []
    lab, n = ndimage.label(sub)
    if n < 2:
        return []
    objs = ndimage.find_objects(lab)
    spans = sorted(
        (o[1].start, o[1].stop)
        for o in objs
        if (o[0].stop - o[0].start) * (o[1].stop - o[1].start) > 12
    )
    merged = []
    for a, b in spans:
        if merged and a < merged[-1][1] - 1:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    h = t.get('lh') or (t['y1'] - t['y0'])
    return [
        (merged[i + 1][0] - merged[i][1]) / h for i in range(len(merged) - 1)
    ]


LETTERS = re.compile(r'[A-Za-zÄÖÜäöüß]')


def word_pairs(leaf, t):
    """(bigram, gap) for a word whose glyph components map one-to-one onto its
    letters."""
    core = ''.join(LETTERS.findall(t['t']))
    if len(core) < 2 or not re.fullmatch(
        r'[„"\'(]*[A-Za-zÄÖÜäöüß]+[.,;:!?"\')“]*', t['t']
    ):
        return None
    pre, c, post = split_punct(t['t'])
    g = glyph_gaps(leaf, t)
    npunct = len(pre) + len(post)
    if len(g) + 1 == len(core):
        return [(core[i : i + 2], g[i]) for i in range(len(core) - 1)]
    if len(g) + 1 == len(core) + npunct:
        g = g[len(pre) : len(pre) + len(core) - 1]
        return [(core[i : i + 2], g[i]) for i in range(len(core) - 1)]
    return None


def fit_bigrams(leaves):
    import collections

    acc = collections.defaultdict(list)
    for leaf in leaves:
        for tl in tess_lines(leaf):
            for t in tl:
                p = word_pairs(leaf, t)
                if p:
                    for bg, g in p:
                        acc[bg].append(g)
    return {bg: statistics.median(v) for bg, v in acc.items() if len(v) >= 3}


def sperr_score(leaf, t, bigr):
    p = word_pairs(leaf, t)
    if not p:
        return None
    d = [g - bigr[bg] for bg, g in p if bg in bigr]
    if not d:
        return None
    return statistics.median(d)


REF = re.compile(
    r'^(.*?[A-Za-zÄÖÜäöüß.,;:!?"“”\'‘’])'
    r'([0-9*?!°¹²³⁴⁵⁶⁷⁸⁹⁰‘“”\'"]{1,4}\))([.,;:!?]*)$'
)
NOTE_START = re.compile(r'^[0-9*?!°¹²³⁴⁵⁶⁷⁸⁹⁰‘“\'".,]{0,4}\)$')
JUNK = re.compile(r'^(Digitized|by|Google|Googl[ec]?)$')


def parse_page(leaf):
    """Split a page into running head, body lines and footnote lines; drop
    marginalia."""
    tls = page_lines(leaf)
    tls = [
        tl
        for tl in tls
        if not all(
            JUNK.match(t['t']) or t['x0'] > 1900 and t['y0'] > 3700 for t in tl
        )
    ]
    if not tls:
        return {'page': None, 'body': [], 'notes': []}
    head = None
    if (
        tls[0][0]['y0'] < 400
        and len(tls[0]) <= 4
        and any(re.search(r'\d|[IVXL]{2,}', t['t']) for t in tls[0])
    ):
        head = ' '.join(t['t'] for t in tls[0])
        tls = tls[1:]
    xs0 = sorted(tl[0]['x0'] for tl in tls if len(tl) > 4)
    xs1 = sorted(tl[-1]['x1'] for tl in tls if len(tl) > 4)
    bx0 = xs0[len(xs0) // 5] if xs0 else 300
    bx1 = xs1[-1 - len(xs1) // 5] if xs1 else 2200
    for tl in tls:
        tl[:] = [
            t for t in tl if not (t['x1'] < bx0 - 15 or t['x0'] > bx1 + 25)
        ]
    tls = [tl for tl in tls if tl]
    # signature line ("Marx, Kapital I. 4. Aufl.  1") and sheet marks ("1*") at
    # the foot
    tls = [
        tl
        for tl in tls
        if not (
            'Kapital' in ' '.join(t['t'] for t in tl)
            and 'Aufl' in ' '.join(t['t'] for t in tl)
        )
    ]
    tls = [
        tl
        for tl in tls
        if not (
            len(tl) <= 2
            and tl[0]['x0'] - bx0 > 0.6 * (bx1 - bx0)
            and len(''.join(t['t'] for t in tl)) <= 4
        )
    ]
    tls = [
        tl
        for tl in tls
        if not (
            len(tl) <= 3
            and not re.search(r'[A-Za-zäöü]{2}|\d', ''.join(t['t'] for t in tl))
        )
    ]
    hs = [tl[0]['lh'] for tl in tls if len(tl) > 3][:8]
    body_h = statistics.median(hs) if hs else 60
    split = len(tls)
    xhs = [tl[0].get('xh', 0) for tl in tls]
    sx = sorted(x for x in xhs if x) or [34]
    body_xh = sx[int(len(sx) * 0.8)] if len(sx) > 4 else 34
    small = [0 < x <= 0.9 * body_xh for x in xhs]
    for i in range(1, len(tls)):
        tail = small[i:]
        if (
            small[i]
            and (len(tail) < 2 or small[i + 1])
            and sum(tail) >= 0.75 * len(tail)
        ):
            split = i
            break
    return {
        'page': head,
        'body': tls[:split],
        'notes': tls[split:],
        'bx0': bx0,
        'bx1': bx1,
        'body_h': body_h,
    }


CONF = [
    ('ſs', 'ss'),
    ('fs', 'ss'),
    ('ls', 'ss'),
    ('Is', 'ss'),
    ('tlh', 'th'),
    ('tlı', 'th'),
    ('tli', 'th'),
    ('lı', 'h'),
    ('li', 'h'),
    ('lh', 'h'),
    ('ı', 'i'),
    ('rn', 'm'),
    ('m', 'rn'),
    ('e', 'c'),
    ('c', 'e'),
    ('Ü', 'C'),
    ('Ö', 'O'),
    ('ö', 'o'),
    ('&', 'é'),
    ('ä', 'a'),
    ('ü', 'u'),
    ('ii', 'ü'),
    ('u', 'n'),
    ('n', 'u'),
    ('o', 'a'),
    ('y', 'u'),
    ('8', 's'),
    ('2', 'Z'),
    (']', 'I'),
    ('|', 'l'),
    ('1', 'l'),
    ('l', 'I'),
    ('Il', 'II'),
    ('111', 'III'),
    ('wait', 'weil'),
    ('aich', 'auch'),
    ('Ae', 'Ae'),
]


def variants(core):
    out = {core}
    for a, b in CONF:
        i = core.find(a)
        while i >= 0:
            out.add(core[:i] + b + core[i + len(a) :])
            i = core.find(a, i + 1)
    return out


def choose(t):
    """Pick the reading for a Tesseract token given the ABBYY reading; return
    (text, status)."""
    tt, aa = t['t'], t.get('a')
    tp, tc, ts = split_punct(tt)
    if aa is not None and not t.get('a_raw') and key(tt) == key(aa):
        if lexscore(tc) >= 3 or not re.search(r'[A-Za-zäöü]{3}', tc):
            return tt, 'agree'
        fix = max(variants(tc), key=lambda c: (lexscore(c), c == tc))
        if fix != tc and lexscore(fix) >= 3:
            return tp + fix + ts, 'fixed'
        return tt, 'agree'
    cands = {}
    for c in variants(tc):
        cands[c] = lexscore(c) - (0 if c == tc else 0.6)
    if aa is not None and not t.get('a_raw'):
        ap, ac, as_ = split_punct(aa)
        if ' ' not in ac:
            for c in variants(ac):
                cands[c] = max(
                    cands.get(c, -9), lexscore(c) - (0.2 if c == ac else 0.7)
                )
    best = max(cands, key=lambda c: (cands[c], c == tc))
    if lexscore(tc) >= 3:
        return tt, 'lex' if aa is not None else 'tonly'
    if best != tc and cands[best] >= 2.4:
        return tp + best + ts, 'fixed'
    return tt, 'conflict' if aa is not None else 'tonly'


def ocr_digits(leaf, t, pad=6, scale=3):
    """Re-read a small token (footnote number) with a digit whitelist at higher
    magnification."""
    import subprocess
    from PIL import Image

    im = Image.fromarray(image(leaf))
    box_ = (
        max(0, t['x0'] - pad),
        max(0, t['y0'] - pad),
        t['x1'] + pad,
        t['y1'] + pad,
    )
    crop = im.crop(box_)
    crop = crop.resize((crop.width * scale, crop.height * scale), Image.LANCZOS)
    path = f'{W}/tmp_dig.png'
    crop.save(path)
    out = subprocess.run(
        [
            'tesseract',
            path,
            '-',
            '--psm',
            '8',
            '-c',
            'tessedit_char_whitelist=0123456789)a',
        ],
        capture_output=True,
        text=True,
    ).stdout.strip()
    return out


def ocr_sup(leaf, x0, x1, y0, y1, scale=5):
    """Read superscript digits in a box (top part of a line) with a digit
    whitelist."""
    import subprocess
    from PIL import Image, ImageOps

    im = Image.fromarray(image(leaf)).crop((x0, y0, x1, y1))
    im = im.resize(
        (max(1, im.width * scale), max(1, im.height * scale)), Image.LANCZOS
    )
    im = im.point(lambda v: 0 if v < 150 else 255)
    im = ImageOps.expand(im, border=30, fill=255)
    path = f'{W}/tmp_sup.png'
    im.save(path)
    return subprocess.run(
        [
            'tesseract',
            path,
            '-',
            '--psm',
            '7',
            '-c',
            'tessedit_char_whitelist=0123456789',
        ],
        capture_output=True,
        text=True,
    ).stdout.strip()


def note_number(leaf, t):
    """Footnote number at the start of a note line: superscript digits before
    ')'."""
    h = t['y1'] - t['y0']
    lh = t.get('lh', h)
    # the number + ')' is the first token; keep left part, top 60 %
    x1 = (
        t['x1'] - int(0.25 * lh)
        if len(t['t']) <= 6
        else t['x0'] + int(1.6 * lh)
    )
    x1 = max(x1, t['x0'] + int(0.5 * lh))
    return ocr_sup(leaf, t['x0'] - 3, x1, t['y0'] - 4, t['y0'] + int(0.62 * h))
