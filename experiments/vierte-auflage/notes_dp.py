"""Assign footnote numbers to note starts (DP over candidates) and pick body
references per page."""

import re

import assemble as A
import rec


def note_candidates(leaves):
    cands = []
    for leaf in leaves:
        r = A.pages[leaf]
        lines = r['notes']
        lefts = [tl[0]['x0'] for tl in lines]
        for li, tl in enumerate(lines):
            win = sorted(
                lefts[max(0, li - 4) : li] + lefts[li + 1 : li + 5]
            ) or [min(lefts)]
            ind = (tl[0]['x0'] - win[len(win) // 3]) / r['body_h']
            first = tl[0]['t']
            pat = bool(A.NOTE_START.match(first)) or bool(
                A.NOTE_START.match(tl[0].get('a') or '')
            )
            forced = A.PATCH.get((leaf, 'notes', li))
            if forced == 'CONT':
                continue
            if (
                ind > 0.35
                or pat
                or forced == 'START'
                or isinstance(forced, int)
            ):
                g = A.num_guess(first, tl[0].get('a'))
                sup = rec.note_number(leaf, tl[0])
                if sup.isdigit():
                    g.add(int(sup))
                if isinstance(forced, int):
                    g = {forced}
                strong = forced is not None or (
                    ind > 0.6 and (pat or not first[:1].islower())
                )
                cands.append(
                    {
                        'leaf': leaf,
                        'li': li,
                        'g': g,
                        'strong': strong,
                        'ind': ind,
                        'first': first,
                        'forced': isinstance(forced, int) or forced == 'START',
                    }
                )
    return cands


def match(g, n):
    if not g:
        return -0.3
    if n in g:
        return 4
    if any(x % 10 == n % 10 for x in g):
        return 0.8
    return -1.2


def assign(cands, nmax=400):
    NEG = -1e9
    m = len(cands)
    dp = [[NEG] * (nmax + 1) for _ in range(m + 1)]
    bk = [[None] * (nmax + 1) for _ in range(m + 1)]
    for n in range(nmax + 1):
        dp[0][n] = -0.02 * n
    for i in range(m):
        c = cands[i]
        skip = -6 if c['forced'] else (-2.5 if c['strong'] else 0.3)
        for n in range(nmax + 1):
            v = dp[i][n]
            if v == NEG:
                continue
            if v + skip > dp[i + 1][n]:
                dp[i + 1][n], bk[i + 1][n] = v + skip, (n, None)
            for jump in (1, 2):
                nn = n + jump
                if nn > nmax:
                    break
                s = v + match(c['g'], nn) - (5 if jump == 2 else 0)
                if s > dp[i + 1][nn]:
                    dp[i + 1][nn], bk[i + 1][nn] = s, (n, nn)
    n = max(range(nmax + 1), key=lambda k: dp[m][k])
    out = {}
    for i in range(m, 0, -1):
        pn, assigned = bk[i][n]
        if assigned is not None:
            out[i - 1] = assigned
        n = pn
    return out


if __name__ == '__main__':
    import sys

    lv = range(228, 302)
    cands = note_candidates(lv)
    res = assign(cands)
    nums = [res[i] for i in sorted(res)]
    print(
        len(cands),
        'assigned',
        len(res),
        'max',
        max(nums),
        'missing',
        sorted(set(range(1, max(nums) + 1)) - set(nums)),
    )
    for i, c in enumerate(cands):
        if i in res and res[i] not in c['g'] and c['g']:
            print(
                '  disagree',
                c['leaf'],
                c['first'],
                sorted(c['g']),
                '->',
                res[i],
            )
