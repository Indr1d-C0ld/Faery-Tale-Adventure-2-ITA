#!/usr/bin/env python3
"""Lettura e ricostruzione delle tabelle di stringhe di SCRIPTS.HRS e di LIST/NAME in FTA.HRS.

Tabella di script: word 1, poi alla posizione 2 la tabella di offset (uint16, relativi alla
posizione 2), poi le stringhe in Latin-1 terminate da zero.
NAME: tabella di offset relativi all'inizio della risorsa, poi le stringhe allineate a 2 byte.
Uso (verifica): stringhe.py SCRIPTS.HRS FTA.HRS   ricostruisce tutte le tabelle e le confronta.
"""
import os, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hreslib import HRes

def parse_table(d, base):
    if base + 2 > len(d):
        return []
    n = struct.unpack_from('<H', d, base)[0] // 2
    out = []
    for i in range(n):
        o = base + struct.unpack_from('<H', d, base + 2 * i)[0]
        e = d.find(b'\0', o)
        out.append(d[o:e if e >= 0 else len(d)].decode('latin-1'))
    return out

def build_table(strings, prefix=b'', terminate_last=True, align=1):
    """Ricostruisce tabella + stringhe; gli offset sono relativi all'inizio della tabella."""
    n = len(strings)
    body = bytearray()
    offs = []
    for i, s in enumerate(strings):
        offs.append(2 * n + len(body))
        body += s.encode('latin-1')
        if terminate_last or i < n - 1:
            body += b'\0'
        while len(body) % align:
            body += b'\0'
    if max(offs, default=0) > 0xffff:
        raise ValueError('tabella di stringhe oltre 64 KB')
    return prefix + struct.pack(f'<{n}H', *offs) + bytes(body)

def build_script_strings(strings):
    if not strings:
        return struct.pack('<H', 1)
    return build_table(strings, prefix=struct.pack('<H', 1))

if __name__ == '__main__':
    import sagadis as sd
    g = HRes(sys.argv[1]).group('SAGA')
    special = {g.index_of(b'__DA'), g.index_of(b'_EXP')}
    res = set()
    for idx in range(len(g.entries)):
        if idx in special or g.entries[idx][2] < 8: continue
        m = sd.Module(g, idx)
        if sd.find_functions(m.d): res.add((m.strres, m.stroff))
    ok = 0
    for r, off in sorted(res):
        d = g.read_index(r)
        assert off == 2
        if build_script_strings(parse_table(d, 2)) == d: ok += 1
        else: print('diversa', r)
    print(f'tabelle di script identiche: {ok}/{len(res)}')
    d = HRes(sys.argv[2]).group('LIST').read(b'NAME')
    names = parse_table(d, 0)
    # l'originale ha byte di riempimento non inizializzati: il confronto si fa sul contenuto
    print('NAME equivalente:', parse_table(build_table(names, align=2), 0) == names)
