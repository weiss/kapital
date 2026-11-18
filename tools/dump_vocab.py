#!/usr/bin/env python3
"""Word forms of all volumes (after dehyphenation, before any variant) with
counts, as JSON."""

import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import tei2epub  # noqa: E402

TEI = '{http://www.tei-c.org/ns/1.0}'
WORD = re.compile(r"[A-Za-zÄÖÜäöüßſàâçéèêëîïôûùœæ]+")


def main():
    out = (
        sys.argv[1] if len(sys.argv) > 1 else str(ROOT / 'build' / 'vocab.json')
    )
    edition = sys.argv[2] if len(sys.argv) > 2 else 'erstausgaben'
    vocab = Counter()
    for band in ('1', '2', '3'):
        book = tei2epub.Book(tei2epub.load_volume(edition, band, []))
        book.run()
        for part in book.vol['parts']:
            for e in part['root'].find(TEI + 'text').iter():
                if isinstance(e.tag, str):
                    for v in (e.text, e.tail):
                        if v:
                            vocab.update(WORD.findall(v))
    Path(out).parent.mkdir(exist_ok=True)
    json.dump(dict(vocab), open(out, 'w'), ensure_ascii=False)
    print(len(vocab), 'forms ->', out)


if __name__ == '__main__':
    main()
