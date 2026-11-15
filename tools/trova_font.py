#!/usr/bin/env python3
"""Cerca strutture gFont (SAGA2) in un eseguibile. Uso: trova_font.py EXE"""
import struct, sys
d = open(sys.argv[1], 'rb').read()
for o in range(0, len(d) - 1300):
    h, b, rm = struct.unpack_from('<HHH', d, o)
    if not (6 <= h <= 30 and 0 < b <= h and 16 <= rm <= 400): continue
    xo = struct.unpack_from('<256H', d, o + 6)
    if xo[0] != 0 and xo[32] == 0: continue
    if any(xo[i] > xo[i+1] for i in range(32, 126)): continue
    if xo[126] == 0 or xo[126] > rm * 8: continue
    w = d[o+518:o+518+256]
    if not all(0 < w[i] < 30 for i in range(65, 91)): continue
    print(f'{o:#09x} altezza={h} base={b} rowMod={rm} fine={o+518+768+h*rm:#09x}')
