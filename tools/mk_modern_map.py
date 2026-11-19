#!/usr/bin/env python3
"""Build the spelling table for the 'modern' variant (variants/modern_map.json).

Input: the word forms of all volumes (tools/dump_vocab.py), e.g.

    python3 tools/dump_vocab.py build/vocab.json
    python3 tools/mk_modern_map.py build/vocab.json

Each old form gets candidate spellings from a small set of historical-to-modern
rules (th→t, aa→a, c→k/z, -iren→-ieren, -niss→-nis, Ae→Ä, ss→ß …); a candidate
wins if it is clearly more frequent in present-day German (wordfreq). ß is only
kept where the ss form is not at least as common today (Prozess, not Prozeß).
Compounds unknown to wordfreq are rewritten piecewise with the morphemes learned
from the simple words. Manual decisions in variants/modern_overrides.py win.
Requires: pip install wordfreq
"""

import itertools
import json
import re
import sys
from collections import Counter
from functools import lru_cache
from pathlib import Path

import wordfreq

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

RULES = [
    (r'th', 't'),
    (r'Th', 'T'),
    (r'aa', 'a'),
    (r'Aa', 'A'),
    (r'dt', 't'),
    (r'(?<=g)ie(?=b)', 'i'),
    (r'iess$', 'ies'),
    (r'^Ae', 'Ä'),
    (r'^Oe', 'Ö'),
    (r'^Ue', 'Ü'),
    (r'(?<=[a-z])ae', 'ä'),
    (r'(?<=[a-z])oe', 'ö'),
    (r'(?<=[a-z])ue', 'ü'),
    (r'c', 'k'),
    (r'c', 'z'),
    (r'C', 'K'),
    (r'C', 'Z'),
    (r'cc', 'kk'),
    (r'cc', 'kz'),
    (
        r'ir(?=(en|end|ende|enden|ender|endes|endem|t|te|ten|tes|ter|tem'
        r'|ung|ungen|bar|bare|baren|barer)$)',
        'ier',
    ),
    (r'iss$', 'is'),
    (r'ph', 'f'),
    (r'Ph', 'F'),
    (r'mmt', 'mt'),
    (r'ieen$', 'ien'),
    (r'^wieder(?=spieg|sprech|stand|streb|sinn|rechtl)', 'wider'),
]
FOREIGN_LANGS = ('en', 'fr', 'it', 'es', 'nl')


@lru_cache(maxsize=None)
def z(w):
    return max(
        wordfreq.zipf_frequency(w, 'de'),
        wordfreq.zipf_frequency(w.lower(), 'de') - 0.3,
    )


@lru_cache(maxsize=None)
def zf(w):
    return max(wordfreq.zipf_frequency(w, l) for l in FOREIGN_LANGS)


def candidates(w, limit=4):
    spots = sorted(
        {
            (m.start(), m.end(), rep)
            for pat, rep in RULES
            for m in re.finditer(pat, w)
        }
    )
    out = set()
    for k in range(1, min(limit, len(spots)) + 1):
        for combo in itertools.combinations(spots, k):
            if any(a[1] > b[0] for a, b in zip(combo, combo[1:])):
                continue
            s, pos = '', 0
            for a, b, rep in combo:
                s, pos = s + w[pos:a] + rep, b
            out.add(s + w[pos:])
    return out


def direct_map(vocab):
    out = {}
    for w in vocab:
        if len(w) < 2:
            continue
        z0 = z(w)
        best, bz = None, z0
        for c in candidates(w):
            if z(c) > bz:
                best, bz = c, z(c)
        if best and bz >= 1.8 and bz > z0 + 0.6:
            out[w] = best
    return out


def morphemes(direct, overrides, morph):
    """Learned piece rewrites for compounds: lowercase old -> new, only from
    unambiguous German words."""
    rules = {}
    for old, new in direct.items():
        if len(old) < 4 or zf(old) >= 2.5 or overrides.get(old, '') is None:
            continue
        if old.lower().startswith(('mass', 'staat')):
            continue
        rules[old.lower()] = new.lower()
    for old, new in morph.items():
        if new is None:
            rules.pop(old, None)
            rules[old] = old
        else:
            rules[old] = new
    return dict(sorted(rules.items(), key=lambda kv: -len(kv[0])))


def rewrite_compound(w, rules):
    low = w.lower()
    out, i, changed = [], 0, False
    keys = list(rules)
    while i < len(low):
        for k in keys:
            if low.startswith(k, i):
                nxt = low[i + len(k) : i + len(k) + 1]
                if k.endswith('iss') and nxt and nxt in 'aeiouäöü':
                    continue
                rep = rules[k]
                out.append(rep)
                i += len(k)
                changed = changed or rep != k
                break
        else:
            out.append(low[i])
            i += 1
    if not changed:
        s = w
    else:
        s = ''.join(out)
        s = ''.join(
            c.upper() if o.isupper() and k == 0 else c
            for k, (c, o) in enumerate(zip(s, w + ' ' * len(s)))
        )
        if w[0].isupper():
            s = s[0].upper() + s[1:]
    # generic, safe endings for remaining old forms
    s = re.sub(r'(?<=[a-zäöü])niss(?=$|mässig|mäßig|voll|los)', 'nis', s)
    s = re.sub(r'^Ae', 'Ä', s)
    s = re.sub(r'^Oe(?=[kfrlh])', 'Ö', s)
    s = re.sub(r'^Ue(?=[bn])', 'Ü', s)
    s = re.sub(
        r'(?<=[a-zäöü]{3})(?<![aeiouäöü])ir(?=(t|te|ten|tes|ter|tem|en|end'
        r'|ende|enden|ender|endes|endem|ung|ungen|bar|bare|baren|barer)$)',
        'ier',
        s,
    )
    if re.search(
        r'ier(t|te|ten|tes|ter|tem|en|end|ende|enden|ender|endes|endem'
        r'|ung|ungen|bar|bare|baren|barer)$',
        s,
    ):
        s = re.sub(r'ci(?=i?er)', 'zi', s)
        s = re.sub(
            r'(?<![a-zäöü])([Cc])(?=o[nm])',
            lambda m: 'K' if m.group(1) == 'C' else 'k',
            s,
        )
        s = re.sub(r'(?<=[a-z])c(?=o[nm])', 'k', s)
        s = re.sub(r'contr', 'kontr', s)
        s = re.sub(r'([Kk])ontrol(?!l)', r'\1ontroll', s)
    s = re.sub(r'mercantil', 'merkantil', s)
    return s


SZ = [
    (r'(?<=[a-zäöü])niss(?=mä)', 'nis'),
    (r'gröss', 'größ'),
    (r'Gröss', 'Größ'),
    (r'gross', 'groß'),
    (r'Gross', 'Groß'),
    (r'äusser', 'äußer'),
    (r'Äusser', 'Äußer'),
    (r'(?<![a-z])([Aa])usser', r'\1ußer'),
    (
        r'^([Aa])ussen(?=$|welt|seite|luft|lärm|wänd|handel|posten|steh)',
        r'\1ußen',
    ),
    (r'draussen', 'draußen'),
    (r'mässig', 'mäßig'),
    (
        r'(einiger|gewisser|folgender|^der|gleicher|bekannter|Glied)massen$',
        r'\1maßen',
    ),
    (r'^([Mm])ass(?=$|stab|gabe|geb|regel|nahm|einheit|los|voll)', r'\1aß'),
    (r'(?<=[a-z])mass(?=$|s$|stab|einheit|los|voll)', 'maß'),
    (r'([Bb])loss', r'\1loß'),
    (r'([Ff])uss(?!el)', r'\1uß'),
    (r'([Ff])üsse', r'\1üße'),
    (r'([Gg])russ', r'\1ruß'),
    (r'([Gg])rüss', r'\1rüß'),
    (r'([Ss])pass', r'\1paß'),
    (r'([Ss])toss', r'\1toß'),
    (r'([Ss])töss', r'\1töß'),
    (r'([Ss])trass', r'\1traß'),
    (r'([Ss])üss', r'\1üß'),
    (r'(?<![a-zäöü])([Ww])eiss', r'\1eiß'),
    (r'(?<=[a-zäöü])weiss(?=e|$)', 'weiß'),
    (r'([Hh])eiss', r'\1eiß'),
    (r'([Hh])iess', r'\1ieß'),
    (r'([Ll])iess', r'\1ieß'),
    (r'([Ss])tiess', r'\1tieß'),
    (r'(?<![Pp])([Rr])eiss', r'\1eiß'),
    (r'([Bb])eiss', r'\1eiß'),
    (r'([Ss])chliess', r'\1chließ'),
    (r'([Ff])liess', r'\1ließ'),
    (r'([Gg])iess', r'\1ieß'),
    (r'([Gg])eniess', r'\1enieß'),
    (r'([Ss])chiess', r'\1chieß'),
    (r'([Ss])priess', r'\1prieß'),
    (r'([Gg])efäss', r'\1efäß'),
    (r'([Gg])emäss', r'\1emäß'),
    (r'([Ss])piess', r'\1pieß'),
    (r'([Ff])leiss', r'\1leiß'),
    (r'([Pp])reuss', r'\1reuß'),
    (r'([Ss])chweiss', r'\1chweiß'),
    (r'([Ss])chleiss', r'\1chleiß'),
    (r'([Kk])loss', r'\1loß'),
    (r'^([Bb])usse', r'\1uße'),
    (r'([Bb])üss', r'\1üß'),
    (r'([Bb])lösse', r'\1löße'),
    (r'^([Dd])aß$', r'\1ass'),
    (r'(?<=[a-zäöü])niß', 'nis'),
    (r'([Ss])chluß', r'\1chluss'),
    (r'^([Mm])ißt$', r'\1isst'),
    (r'vergißt', 'vergisst'),
    (r'^((?:[Bb]e|[Ee]r)?[Ss])ass(?=(en|t)?$)', r'\1aß'),
    (r'^([Bb]e)säss', r'\1säß'),
    (r'äussr', 'äußr'),
    (r'([Ss])cheuss', r'\1cheuß'),
    (r'([Gg])eiss(?=el)', r'\1eiß'),
    (r'meissel', 'meißel'),
    (r'([Nn])iess', r'\1ieß'),
    (r'^geweisst$', 'geweißt'),
    (r'(?<=[a-zäöü])nissmässig', 'nismäßig'),
]


def sz(w):
    for pat, rep in SZ:
        w = re.sub(pat, rep, w)
    return w


def main():
    vocab = Counter(json.load(open(sys.argv[1])))
    from variants.modern_overrides import MORPHEMES, OVERRIDES

    direct = direct_map(vocab)
    rules = morphemes(direct, OVERRIDES, MORPHEMES)
    table, kinds = {}, Counter()
    for w in vocab:
        if w in OVERRIDES:
            if OVERRIDES[w]:
                table[w] = [OVERRIDES[w], 'manual']
            kinds['manual'] += 1
            continue
        if w in direct:
            table[w] = [direct[w], 'foreign?' if zf(w) >= 2.5 else 'word']
            kinds['word'] += 1
            continue
        if z(w) < 1.5 and zf(w) < 2.5:
            new = rewrite_compound(w, rules)
            if new != w:
                table[w] = [new, 'compound']
                kinds['compound'] += 1
    for w in vocab:
        if w in OVERRIDES:
            continue
        base = table.get(w, [w, 'sz'])
        new = sz(base[0])
        if new != base[0]:
            table[w] = [new, base[1] if base[1] != 'sz' else 'sz']
            kinds['sz'] += 1
    foreign = sorted(
        w
        for w in vocab
        if zf(w) >= 3.0 and zf(w) > z(table.get(w, [w])[0]) + 0.5
    )
    out = ROOT / 'variants' / 'modern_map.json'
    json.dump(
        {'map': dict(sorted(table.items())), 'foreign': foreign},
        open(out, 'w'),
        ensure_ascii=False,
        indent=0,
    )
    print(dict(kinds), '->', out)


if __name__ == '__main__':
    main()
