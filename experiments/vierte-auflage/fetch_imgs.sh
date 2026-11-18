#!/bin/bash
ID=bub_gb_Tns7AAAAMAAJ
for n in "$@"; do
  f=${K4WORK:-work}/img/leaf_$(printf %04d $n).jpg
  [ -s $f ] || curl -sSfL -m 120 -o $f \
    "https://archive.org/download/$ID/page/n$n.jpg" || echo "FAIL $n"
done
