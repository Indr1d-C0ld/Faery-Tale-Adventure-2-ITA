#!/usr/bin/env python3
"""Lettore di archivi HRES (Faery Tale Adventure II). Uso: hres.py FILE [profondita]"""
import struct, sys
def rd(f, off, n):
    f.seek(off); return f.read(n)
def entries(f, off, size):
    d = rd(f, off, size)
    for i in range(0, size - size % 12, 12):
        idb, o, s = struct.unpack_from('<4sII', d, i)
        yield idb, o, s
def tag(b):
    return ''.join(chr(c) if 32 <= c < 127 else '\\x%02x' % c for c in b)
def walk(f, off, size, depth, maxd, fsize):
    for idb, o, s in entries(f, off, size):
        grp = bool(o & 0x80000000) or False
        print('  ' * depth + f'{tag(idb):12s} off={o:#010x} size={s}')
        if depth < maxd and s % 12 == 0 and o + s <= fsize and s > 0 and s < 200000:
            # tentativo: interpretare come sottotabella
            sub = list(entries(f, o, s))
            if sub and all(so + ss <= fsize for _, so, ss in sub) and all(b[:1].isalpha() or b[0] < 0x20 for b, _, _ in sub[:4]):
                walk(f, o, s, depth + 1, maxd, fsize)
if __name__ == '__main__':
    fn = sys.argv[1]; maxd = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    with open(fn, 'rb') as f:
        f.seek(0, 2); fsize = f.tell()
        magic, doff, dsize = struct.unpack('<4sII', rd(f, 0, 12))
        print(fn, magic, f'dir@{doff:#x} size={dsize} ({dsize//12} voci)')
        walk(f, doff, dsize, 0, maxd, fsize)
