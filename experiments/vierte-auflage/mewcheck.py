import re
import pickle
from difflib import SequenceMatcher

import rec

MEW = open(f'{rec.W}/mew23.txt', encoding='utf-8').read().split('\n')
RANGES = {'front': (134, 1601), 'k1': (1602, 4188), 'k8': (11317, 15325)}
LEAVES = {'front': range(9, 32), 'k1': range(37, 87), 'k8': range(228, 303)}


def norm(w):
    w = w.lower().replace('ß', 'ss').replace('ſ', 's')
    w = re.sub(r'[^a-zäöü0-9]', '', w)
    w = w.replace('ii', 'ü')
    for a, b in (
        ('iert', 'irt'),
        ('ae', 'ä'),
        ('oe', 'ö'),
        ('ue', 'ü'),
        ('th', 't'),
        ('dt', 't'),
        ('aa', 'a'),
        ('ie', 'i'),
        ('y', 'i'),
        ('c', 'k'),
        ('z', 'k'),
        ('ss', 's'),
        ('kk', 'k'),
        ('ph', 'f'),
    ):
        w = w.replace(a, b)
    return (
        w.replace('ä', 'a')
        .replace('ö', 'o')
        .replace('ü', 'u')
        .replace('1', 'i')
        .replace('l', 'i')
    )


def mew_tokens(sec):
    a, b = RANGES[sec]
    lines = MEW[a - 1 : b]
    out = []
    for ln in lines:
        s = ln.strip()
        if re.match(
            r'^(\d+\. Kapitel\s*-|Vorwort zur|Nachwort zur|Zur'
            r' (dritten|vierten) Auflage|\d{1,3}$)',
            s,
        ):
            continue
        out.append(s)
    text = '\n'.join(out)
    text = re.sub(r'(\w)-\s*\n\s*(\w)', r'\1\2', text)
    return [w for w in (norm(x) for x in text.split()) if w]


def our_tokens(pages, sec, part):
    toks = []
    for leaf in LEAVES[sec]:
        if leaf not in pages:
            continue
        lines = pages[leaf][part]
        for i, tl in enumerate(lines):
            for j, t in enumerate(tl):
                toks.append((leaf, i, j, t))
    # join line-end hyphenation for comparison
    seq, refs = [], []
    k = 0
    while k < len(toks):
        leaf, i, j, t = toks[k]
        x = t['x']
        if (
            x.endswith('-')
            and k + 1 < len(toks)
            and toks[k + 1][1] != i
            and toks[k + 1][3]['x'][:1].islower()
        ):
            x = x[:-1] + toks[k + 1][3]['x']
            refs.append([toks[k], toks[k + 1]])
            k += 2
        else:
            refs.append([toks[k]])
            k += 1
        n = norm(x)
        if n:
            seq.append(n)
        else:
            refs.pop()
    return seq, refs


def compare(pages, sec, part='body'):
    ours, refs = our_tokens(pages, sec, part)
    mew = mew_tokens(sec)
    sm = SequenceMatcher(None, ours, mew, autojunk=False)
    regions = []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == 'equal':
            continue
        if op == 'insert':
            continue  # MEW has more (notes, editorial)
        regions.append((op, i1, i2, j1, j2, ours[i1:i2], mew[j1:j2]))
    return ours, refs, mew, regions


if __name__ == '__main__':
    pages = pickle.load(open(f'{rec.W}/pages.pkl', 'rb'))
    for sec in ('front', 'k1', 'k8'):
        ours, refs, mew, regions = compare(pages, sec)
        print(
            sec,
            len(ours),
            len(mew),
            'regions',
            len(regions),
            'tokens',
            sum(r[2] - r[1] for r in regions),
        )
        pickle.dump((ours, refs, mew, regions), open(f'cmp_{sec}.pkl', 'wb'))
        for r in regions[:40]:
            print('  ', r[0], r[5][:6], '|', r[6][:6])


def squash(w):
    return re.sub(r'(.)\1+', r'\1', w)


def char_compare(pages, sec, part='body'):
    from rapidfuzz.distance import Levenshtein

    ours, refs = our_tokens(pages, sec, part)
    mew = mew_tokens(sec)
    os_, omap = [], []
    for i, w in enumerate(ours):
        w = squash(w)
        os_.append(w)
        omap.extend([i] * len(w))
    ms = ''.join(squash(w) for w in mew)
    ostr = ''.join(os_)
    flagged = {}
    for op in Levenshtein.opcodes(ostr, ms):
        if op.tag == 'equal' or op.tag == 'insert':
            continue
        idx = set(omap[op.src_start : op.src_end])
        ctx = ms[max(0, op.dest_start - 12) : op.dest_end + 12]
        for i in idx:
            flagged.setdefault(i, []).append(
                (
                    op.tag,
                    ostr[op.src_start : op.src_end],
                    ms[op.dest_start : op.dest_end],
                    ctx,
                )
            )
    return ours, refs, flagged


def block_compare(pages, sec, part='body'):
    """Token-level alignment (robust to MEW's interleaved notes); a replace
    region whose letters agree after removing spaces is only a word-division
    difference."""
    ours, refs = our_tokens(pages, sec, part)
    mew = mew_tokens(sec)
    o2 = [squash(w) for w in ours]
    m2 = [squash(w) for w in mew]
    sm = SequenceMatcher(None, o2, m2, autojunk=False)
    regions = []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op in ('equal', 'insert'):
            continue
        if op == 'replace' and squash(''.join(o2[i1:i2])) == squash(
            ''.join(m2[j1:j2])
        ):
            continue
        regions.append((op, i1, i2, j1, j2))
    return ours, refs, mew, regions
