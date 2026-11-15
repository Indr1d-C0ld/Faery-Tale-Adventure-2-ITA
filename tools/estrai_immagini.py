#!/usr/bin/env python3
"""Estrae in PNG le immagini dell'interfaccia di FTA2 (FTAIMAGE.HRS).

Uso:
  estrai_immagini.py FTAIMAGE.HRS OUTDIR

Formato (ScummVM saga2, document.h e blitters.cpp): ogni immagine è
  int16 larghezza, int16 altezza, int16 compressione, poi i pixel.
I pixel sono grezzi, oppure compressi con il RLE di unpackImage. Una risorsa può contenere
più immagini di fila (per esempio i due stati di un pulsante). La palette è TILE/PAL0, in
VGA a 6 bit. Sprite, tile e pose usano formati diversi e vengono saltati.
"""
import os, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hreslib import HRes, tagstr
from PIL import Image

SKIP = {b'SPRI', b'TILE', b'POSE', b'SCHM', b'FRML'}

def unpack(src, p, w, h):
    out = bytearray()
    bc = (w + 1) & ~1
    for _ in range(h):
        k = 0
        row = bytearray()
        while k < bc:
            c = src[p]; p += 1
            c = c - 256 if c > 127 else c
            if c == -128:
                continue
            if c >= 0:
                n = c + 1
                row += src[p:p + n]; p += n
            else:
                n = 1 - c
                row += bytes([src[p]]) * n; p += 1
            k += n
        if bc & 1:
            p += 1
        out += row[:w]
    return bytes(out), p

def images(d):
    p = 0
    while p + 6 <= len(d):
        w, h, comp = struct.unpack_from('<hhh', d, p)
        if not (0 < w <= 640 and 0 < h <= 480 and comp in (0, 1)):
            return
        p += 6
        if comp == 0:
            if p + w * h > len(d):
                return
            yield w, h, d[p:p + w * h]
            p += w * h
        else:
            try:
                px, p = unpack(d, p, w, h)
            except IndexError:
                return
            yield w, h, px
        if p & 1 and p < len(d) and d[p] == 0:   # allineamento a parola
            p += 1

def main():
    src, outdir = sys.argv[1], sys.argv[2]
    h = HRes(src)
    pal = h.group('TILE').read(b'PAL\x00')
    palette = bytes(min(255, c * 4 + (c >> 4)) for c in pal)
    tot = 0
    for gtag, g in h.groups.items():
        if gtag in SKIP:
            continue
        gd = os.path.join(outdir, tagstr(gtag))
        os.makedirs(gd, exist_ok=True)
        for i, (t, o, s) in enumerate(g.entries):
            if s == 0:
                continue
            d = g.read_index(i)
            for k, (w, hh, px) in enumerate(images(d)):
                im = Image.frombytes('P', (w, hh), px)
                im.putpalette(palette)
                name = tagstr(t).replace('\\x', 'x')
                im.save(os.path.join(gd, f'{name}_{k}.png'))
                tot += 1
    print(tot, 'immagini')

if __name__ == '__main__':
    main()
