#!/usr/bin/env python3
"""Riscrive un archivio HRES di FTA2, opzionalmente sostituendo delle risorse.

Uso da riga di comando (verifica): hreswrite.py ORIGINALE COPIA
  Ricostruisce l'archivio senza modifiche. La copia deve risultare identica all'originale.
Uso come libreria:
  rewrite(src, dst, {(b'SAGA', indice): nuovi_byte, ...})

La disposizione dell'originale si conserva (con il puntatore alla prima tabella dei gruppi,
nei 4 byte che precedono la directory): intestazione, poi i dati delle risorse in ordine
di offset (compresi eventuali spazi), poi le tabelle dei gruppi e infine la directory principale.
Se una risorsa cambia dimensione, tutto ciò che la segue viene spostato e gli offset ricalcolati.
"""
import os, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hreslib import HRes

def rewrite(src, dst, repl=None):
    repl = repl or {}
    h = HRes(src)
    f = h.f
    f.seek(0, 2); fsize = f.tell()
    # blocchi: dati delle risorse e tabelle dei gruppi, ciascuno con la propria posizione originale
    blocks = []   # (offset_orig, size_orig, tipo, chiave)
    topdir = list(h._entries(h.dir_off, h.dir_size))
    for gtag, go, gs in topdir:
        blocks.append((go, gs, 'tabella', gtag))
        for i, (t, o, s) in enumerate(h.groups[gtag].entries):
            blocks.append((o, s, 'dato', (gtag, i)))
    blocks.append((h.dir_off, h.dir_size, 'dir', None))
    # lo stesso blocco di dati può essere condiviso da più voci: si deduplica per (offset, size)
    blocks.sort(key=lambda b: (b[0], b[2] != 'tabella'))
    newpos = {}
    out = bytearray(b'\0' * 12)
    seen = {}
    pending_tables = []
    # ricostruzione sequenziale: si copiano anche gli spazi fra blocchi
    cur = 12
    for o, s, kind, key in blocks:
        if kind == 'dato' and s == 0 and key not in repl:
            newpos[key] = (o, 0)                  # voce vuota: l'originale ha un offset qualsiasi
            continue
        if o < cur and kind == 'dato' and (o, s) in seen:
            newpos[key] = seen[(o, s)]
            continue
        if o > cur:
            f.seek(cur); out += f.read(o - cur)     # spazio originale
            cur = o
        if kind == 'dato':
            data = repl.get(key)
            if data is None:
                f.seek(o); data = f.read(s)
            newpos[key] = (len(out), len(data))
            seen[(o, s)] = newpos[key]
            out += data
            cur = max(cur, o + s)
        else:
            pending_tables.append((len(out), kind, key, s))
            out += b'\0' * s                      # segnaposto, scritto dopo
            cur = max(cur, o + s)
    if cur < fsize:
        f.seek(cur); out += f.read(fsize - cur)
    # tabelle dei gruppi e directory principale
    gpos = {}
    for at, kind, key, s in pending_tables:
        if kind == 'tabella':
            g = h.groups[key]
            tb = bytearray()
            for i, (t, o, sz) in enumerate(g.entries):
                no, ns = newpos[(key, i)]
                tb += struct.pack('<4sII', t, no, ns)
            out[at:at + len(tb)] = tb
            gpos[key] = (at, len(tb))
    for at, kind, key, s in pending_tables:
        if kind == 'dir':
            tb = bytearray()
            for gtag, go, gs in topdir:
                tb += struct.pack('<4sII', gtag, *gpos[gtag])
            out[at:at + len(tb)] = tb
            struct.pack_into('<4sII', out, 0, b'HRES', at, len(tb))
            # i 4 byte prima della directory puntano alla prima tabella dei gruppi (hresmgr.cpp)
            first = min(p for p, k, _, _ in pending_tables if k == 'tabella')
            struct.pack_into('<I', out, at - 4, first)
    with open(dst, 'wb') as w:
        w.write(out)
    return len(out)

if __name__ == '__main__':
    n = rewrite(sys.argv[1], sys.argv[2])
    print(n, 'byte scritti')
