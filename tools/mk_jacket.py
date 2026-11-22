#!/usr/bin/env python3
"""Write the LaTeX source of a Lulu dust jacket (linen hardcover).

Usage: mk_jacket.py <jackets.json> <part> <book.log> <variant> <out.tex>

The page count comes from the LaTeX log of the book.
"""

import json
import re
import sys

# Lulu, hardcover spine width in inches by page count (last page of the range)
SPINE = [
    (84, 0.25),
    (140, 0.5),
    (168, 0.625),
    (194, 0.6875),
    (222, 0.75),
    (250, 0.8125),
    (278, 0.875),
    (306, 0.9375),
    (334, 1.0),
    (360, 1.0625),
    (388, 1.125),
    (416, 1.1875),
    (444, 1.25),
    (472, 1.3125),
    (500, 1.375),
    (528, 1.4375),
    (556, 1.5),
    (582, 1.5625),
    (610, 1.625),
    (638, 1.6875),
    (666, 1.75),
]
BLEED, FLAP, FOLD, COVER, HEIGHT = 0.125, 3.25, 0.25, 5.75, 9.25

TEMPLATE = r"""\documentclass{article}
\usepackage[paperwidth=%(width)sin,paperheight=%(height)sin,margin=0pt]%%
  {geometry}
\usepackage[ngerman,shorthands=off]{babel}
\usepackage{fontspec}
\usepackage{tikz}
\pagestyle{empty}
\setlength{\parindent}{0pt}
\frenchspacing
\setmainfont{CrimsonPro-VF.ttf}[
  ItalicFont=CrimsonPro-Italic-VF.ttf,
  Ligatures=Common,
  Numbers={OldStyle,Proportional}]
\newfontfamily\light{CrimsonPro-VF.ttf}[
  RawFeature={axis={wght=280}}, Numbers=Lining]
\newfontfamily\lightit{CrimsonPro-Italic-VF.ttf}[
  RawFeature={axis={wght=300}}]
\newfontfamily\lightup{CrimsonPro-VF.ttf}[RawFeature={axis={wght=300}}]
\renewcommand{\textup}[1]{{\lightup #1}}
\newfontfamily\caps{CrimsonPro-VF.ttf}[
  RawFeature={axis={wght=420}}, Renderer=Node, LetterSpace=22,
  Numbers=Lining]
\definecolor{bg}{HTML}{F2EDE2}
\definecolor{fg}{HTML}{1E2A45}
\definecolor{tone}{HTML}{E7E0D0}
\definecolor{accent}{HTML}{6F82A6}
\begin{document}
\begin{tikzpicture}[remember picture, overlay, x=1in, y=1in,
  shift={(current page.south west)}, inner sep=0pt]
\fill[bg] (0,0) rectangle (%(width)s,%(height)s);
\begin{scope}
\clip (%(front)s,0) rectangle (%(front_end)s,%(height)s);
\begin{scope}[color=tone, font=\light\fontsize{%(msize)s}{%(msize)s}%%
  \selectfont]
%(motif)s
\end{scope}
\end{scope}
\begin{scope}[color=fg]
\node[anchor=north west] at (%(left)s,7.75)
  {\caps\fontsize{12.5}{15}\selectfont KARL MARX};
\node[anchor=north west] at (%(left_title)s,7.35)
  {\light\fontsize{50}{54}\selectfont Das\hspace{.24em}Kapital};
\node[anchor=north west] at (%(left)s,6.48)
  {\lightit\fontsize{15.5}{18}\selectfont %(subtitle)s};
\node[anchor=north west] at (%(left)s,5.75)
  {\caps\fontsize{10}{12}\selectfont %(vol_line)s};
\node[anchor=north west] at (%(left)s,5.45)
  {\lightit\fontsize{12.5}{15}\selectfont %(book)s};
%(editor)s\node[anchor=south west] at (%(left)s,1.22)
  {\caps\fontsize{9.5}{11}\selectfont %(place)s};
\node[anchor=south west] at (%(left)s,0.95)
  {\lightit\fontsize{10.5}{12}\selectfont %(edition)s};
\node[rotate=-90] at (%(spine)s,5.15)
  {\caps\fontsize{10}{12}\selectfont KARL MARX\hspace{1.6em}%%
   \light\fontsize{17}{20}\selectfont Das Kapital\hspace{1.4em}%%
   \lightit\fontsize{12}{14}\selectfont %(spine_text)s};
\node[color=accent] at (%(spine)s,0.85)
  {\light\fontsize{15}{18}\selectfont %(label)s};
\node[anchor=north, text width=3.6in, align=center] at (%(back)s,5.6)
  {\lightit\fontsize{14}{19}\selectfont\hyphenpenalty=10000 %(quote)s\\[10pt]
   \color{accent}\caps\fontsize{8.5}{10}\selectfont %(quote_source)s};
\node[anchor=north west, text width=2.55in, align=left]
  at (%(front_flap)s,7.4)
  {\fontsize{10.5}{14}\selectfont\raggedright %(front_flap_text)s\par};
\node[anchor=north west, text width=2.55in, align=left]
  at (%(back_flap)s,7.4)
  {\fontsize{10.5}{14}\selectfont\raggedright %(back_flap_text)s\par};
\end{scope}
\end{tikzpicture}
\end{document}
"""


def pick(value, variant):
    if isinstance(value, dict) and '' in value:
        return value.get(variant, value[''])
    if isinstance(value, list):
        return [pick(v, variant) for v in value]
    return value


def spine_width(pages):
    for last, width in SPINE:
        if pages <= last:
            return width
    sys.exit(f'no spine width for {pages} pages')


def fmt(x):
    return f'{x:.4f}'.rstrip('0').rstrip('.')


def main():
    path, part, log, variant, out = sys.argv[1:]
    text = open(log, encoding='utf-8', errors='replace').read()
    pages = re.search(r'Output written on .*?\((\d+) pages', text, re.S)[1]
    data = json.load(open(path, encoding='utf-8'))
    vol = data['volumes'][part]
    while 'base' in vol:
        vol = {**data['volumes'][vol['base']], **vol}
        del vol['base']
    vol = {**data, **vol}
    v = {k: pick(x, variant) for k, x in vol.items()}
    spine = spine_width(int(pages))
    back = BLEED + FLAP + FOLD
    front = back + COVER + spine
    width = 2 * (BLEED + FLAP + FOLD + COVER) + spine
    left = front + 0.625
    motif = v['motif']
    lines = '\n'.join(
        rf'\node[anchor=base west] at ({fmt(left + dx)},{fmt(y)}) {{{t}}};'
        for t, dx, y in zip(motif['lines'], motif['dx'], motif['y'])
    )
    for x0, x1, y, w in motif.get('rules', []):
        lines += (
            f'\n\\draw[line width={w}pt] ({fmt(left + x0)},{fmt(y)})'
            f' -- ({fmt(left + x1)},{fmt(y)});'
        )
    editor = (
        rf'\node[anchor=north west] at ({fmt(left)},5.1)'
        rf' {{\lightit\fontsize{{11}}{{13}}\selectfont {v["editor"]}}};'
        '\n'
        if v.get('editor')
        else ''
    )
    part_sep = '\\enspace·\\enspace '
    tex = TEMPLATE % {
        'width': fmt(width),
        'height': fmt(HEIGHT),
        'front': fmt(front),
        'front_end': fmt(front + COVER),
        'left': fmt(left),
        'left_title': fmt(left - 0.03),
        'spine': fmt(back + COVER + spine / 2),
        'back': fmt(back + COVER / 2),
        'front_flap': fmt(front + COVER + FOLD + 0.35),
        'back_flap': fmt(BLEED + 0.35),
        'msize': motif['size'],
        'motif': lines,
        'subtitle': v['subtitle'],
        'vol_line': part_sep.join(
            x.upper() for x in (v['vol'], v.get('part')) if x
        ),
        'book': v['book'],
        'editor': editor,
        'place': v['place'].upper(),
        'edition': v['edition'],
        'spine_text': ', '.join(x for x in (v['vol'], v.get('part')) if x),
        'label': v['label'],
        'quote': v['quote'],
        'quote_source': v['quote_source'].upper(),
        'front_flap_text': r'\par\vspace{7pt}'.join(v['front_flap']),
        'back_flap_text': r'\par\vspace{7pt}'.join(v['back_flap']),
    }
    with open(out, 'w', encoding='utf-8') as f:
        f.write(tex)
    print(
        f'{part}: {pages} pages, spine {fmt(spine)} in,'
        f' jacket {fmt(width)} x {fmt(HEIGHT)} in'
    )


if __name__ == '__main__':
    main()
