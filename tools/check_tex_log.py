#!/usr/bin/env python3
"""Fail on overfull lines and on warnings of LaTeX, classes and packages in
LuaLaTeX logs."""

import re
import sys

WARNING = re.compile(
    r'Overfull \\hbox|(LaTeX( Font)?|(Class|Package) \S+) Warning'
)
# intended: polytonic Greek via greek.ldf, German in the 1901 orthography
IGNORE = re.compile(
    r"Package babel Warning: (Name 'polutonikogreek' is deprecated"
    r"|The name 'german' with the 'ldf' mechanism)"
)


def main():
    found = False
    for path in sys.argv[1:]:
        with open(path, encoding='utf-8', errors='replace') as f:
            lines = f.read().splitlines()
        for i, line in enumerate(lines):
            if WARNING.match(line) and not IGNORE.match(line):
                print(path + ': ' + '\n  '.join(lines[i : i + 3]))
                found = True
    sys.exit(1 if found else 0)


if __name__ == '__main__':
    main()
