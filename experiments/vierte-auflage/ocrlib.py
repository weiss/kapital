import re, json
from lxml import etree


def load_abbyy(path='djvu.xml'):
    """Return list of pages: each
    {'w','h','lines':[{'words':[(text,x0,y0,x1,y1,conf)]}], 'paras': [...] }"""
    tree = etree.parse(path)
    pages = []
    for obj in tree.iter('OBJECT'):
        pg = {
            'w': int(obj.get('width')),
            'h': int(obj.get('height')),
            'paras': [],
        }
        for par in obj.iter('PARAGRAPH'):
            lines = []
            for ln in par.iter('LINE'):
                ws = []
                for w in ln.iter('WORD'):
                    c = [int(v) for v in w.get('coords').split(',')]
                    x0, y1, x1, y0 = c[:4]
                    ws.append(
                        (
                            w.text or '',
                            x0,
                            y0,
                            x1,
                            y1,
                            int(w.get('x-confidence') or 0),
                        )
                    )
                if ws:
                    lines.append(ws)
            if lines:
                pg['paras'].append(lines)
        pages.append(pg)
    return pages
