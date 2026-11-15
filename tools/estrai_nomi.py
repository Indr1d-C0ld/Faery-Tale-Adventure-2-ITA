#!/usr/bin/env python3
"""Estrae la tabella dei nomi di oggetti e personaggi (FTA.HRS, LIST/NAME). Uso: estrai_nomi.py FTA.HRS OUT.tsv"""
import os, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hreslib import HRes
d = HRes(sys.argv[1]).group('LIST').read(b'NAME')
n = struct.unpack_from('<H', d, 0)[0] // 2
with open(sys.argv[2], 'w', encoding='utf-8') as f:
    f.write('id\ttesto\n')
    for i in range(n):
        o = struct.unpack_from('<H', d, 2 * i)[0]
        f.write(f'{i}\t{d[o:(d.find(b"\0", o) if d.find(b"\0", o) >= 0 else len(d))].decode("latin-1")}\n')
print(n, 'nomi')
