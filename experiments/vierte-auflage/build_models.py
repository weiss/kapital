#!/usr/bin/env python3
"""Prepare the inputs: ABBYY pages, DTA lexicon, letter-pair spacing model (run
after OCR)."""

import collections
import os
import pickle
import re
import sys

from lxml import etree

W = os.environ.get(
    'K4WORK', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'work')
)
SRC = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..',
    '..',
    'editions',
    'erstausgaben',
    'sources',
)
TEI = '{http://www.tei-c.org/ns/1.0}'

if 'abbyy' in sys.argv[1:] or not os.path.exists(f'{W}/abbyy.pkl'):
    from ocrlib import load_abbyy

    pickle.dump(load_abbyy(f'{W}/djvu.xml'), open(f'{W}/abbyy.pkl', 'wb'))

cnt = collections.Counter()
for f in sorted(os.listdir(SRC)):
    if not f.endswith('.xml'):
        continue
    body = etree.parse(os.path.join(SRC, f)).getroot().find(f'.//{TEI}text')
    for fw in body.iter(f'{TEI}fw'):
        fw.text = ''
    txt = re.sub(r'(\w)[-¬]\s*\n\s*(\w)', r'\1\2', ''.join(body.itertext()))
    cnt.update(re.findall(r"[A-Za-zÄÖÜäöüßàâçéèêëîïôûùœæ]+", txt))
pickle.dump(cnt, open(f'{W}/dta_lex.pkl', 'wb'))

import rec  # noqa: E402  (needs abbyy.pkl and dta_lex.pkl)

pickle.dump(rec.fit_bigrams(range(37, 87)), open(f'{W}/bigr.pkl', 'wb'))
print('ok')
