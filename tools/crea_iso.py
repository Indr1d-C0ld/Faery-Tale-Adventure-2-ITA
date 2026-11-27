#!/usr/bin/env python3
"""Crea un'immagine CD ISO 9660 (livello 1, nomi 8.3) con una sola cartella di file.

Uso:
  crea_iso.py ETICHETTA CARTELLA_NEL_CD OUT.iso FILE...

Esempio: crea_iso.py FTA2DATI FTA2 dati.iso FTAIMAGE.HRS FTASOUND.HRS FTAVOICE.HRS
produce un CD con D:\\FTA2\\FTAIMAGE.HRS ecc. È il minimo che serve a MSCDEX: descrittore
primario, tabelle dei percorsi, directory radice e una sottocartella; niente Joliet né Rock Ridge.
"""
import os, struct, sys, time

SETTORE = 2048

def both16(v): return struct.pack('<H', v) + struct.pack('>H', v)
def both32(v): return struct.pack('<I', v) + struct.pack('>I', v)

def data_record(t):
    return bytes([t.tm_year - 1900, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec, 0])

def data_pvd(t):
    return time.strftime('%Y%m%d%H%M%S00', t).encode('ascii') + b'\0'

def record(lba, dim, nome, cartella, t):
    """Record di directory ISO 9660."""
    lung = 33 + len(nome) + (1 - len(nome) % 2)   # riempimento a pari
    r = bytes([lung, 0]) + both32(lba) + both32(dim) + data_record(t)
    r += bytes([2 if cartella else 0, 0, 0]) + both16(1) + bytes([len(nome)]) + nome
    return r + b'\0' * (lung - len(r))

def nome83(n):
    base, _, est = os.path.basename(n).upper().partition('.')
    if len(base) > 8 or len(est) > 3 or not base:
        raise SystemExit(f'nome non 8.3: {n}')
    return f'{base}.{est};1'.encode('ascii') if est else f'{base}.;1'.encode('ascii')

def main():
    etichetta, cartella, out, *file = sys.argv[1:]
    t = time.gmtime()
    etichetta = etichetta.upper()[:32]
    cartella_b = cartella.upper().encode('ascii')
    file = sorted(file, key=lambda f: os.path.basename(f).upper())
    # disposizione: 16 settori di sistema, PVD (16), terminatore (17), tabelle dei percorsi L (18)
    # e M (19), directory radice (20), sottocartella (21), poi i file
    LBA_RADICE, LBA_SUB = 20, 21
    voci = []
    lba = 22
    for f in file:
        dim = os.path.getsize(f)
        voci.append((f, nome83(f), lba, dim))
        lba += (dim + SETTORE - 1) // SETTORE
    totale = lba

    def directory(lba_qui, lba_padre, figli):
        d = record(lba_qui, SETTORE, b'\0', True, t) + record(lba_padre, SETTORE, b'\1', True, t)
        for r in figli: d += r
        if len(d) > SETTORE: raise SystemExit('troppi file per una directory di un settore')
        return d + b'\0' * (SETTORE - len(d))

    radice = directory(LBA_RADICE, LBA_RADICE, [record(LBA_SUB, SETTORE, cartella_b, True, t)])
    sub = directory(LBA_SUB, LBA_RADICE, [record(l, s, n, False, t) for f, n, l, s in voci])

    def tabella(fmt):
        e = lambda nome, lba_e, padre: (bytes([len(nome), 0]) + struct.pack(fmt + 'I', lba_e)
                                         + struct.pack(fmt + 'H', padre) + nome + (b'\0' if len(nome) % 2 else b''))
        return e(b'\0', LBA_RADICE, 1) + e(cartella_b, LBA_SUB, 1)
    tl, tm = tabella('<'), tabella('>')

    pvd = bytearray(SETTORE)
    pvd[0:7] = b'\x01CD001\x01'
    pvd[8:40] = b' ' * 32
    pvd[40:72] = etichetta.encode('ascii').ljust(32)
    pvd[80:88] = both32(totale)
    pvd[120:124] = both16(1); pvd[124:128] = both16(1); pvd[128:132] = both16(SETTORE)
    pvd[132:140] = both32(len(tl))
    pvd[140:144] = struct.pack('<I', 18); pvd[148:152] = struct.pack('>I', 19)
    pvd[156:190] = record(LBA_RADICE, SETTORE, b'\0', True, t)
    for a, b in ((190, 318), (318, 446), (446, 574), (574, 702), (702, 739), (739, 776), (776, 813)):
        pvd[a:b] = b' ' * (b - a)
    pvd[318:318 + 28] = b'FTA2 RESTAURO ITALIANO'.ljust(28)
    for a in (813, 830):
        pvd[a:a + 17] = data_pvd(t)
    pvd[847:864] = b'0' * 16 + b'\0'; pvd[864:881] = b'0' * 16 + b'\0'
    pvd[881] = 1
    term = b'\xffCD001\x01' + b'\0' * (SETTORE - 7)

    with open(out, 'wb') as o:
        o.write(b'\0' * SETTORE * 16)
        o.write(bytes(pvd)); o.write(term)
        o.write(tl.ljust(SETTORE, b'\0')); o.write(tm.ljust(SETTORE, b'\0'))
        o.write(radice); o.write(sub)
        for f, n, l, s in voci:
            assert o.tell() == l * SETTORE
            with open(f, 'rb') as i:
                while True:
                    blocco = i.read(1 << 20)
                    if not blocco: break
                    o.write(blocco)
            if s % SETTORE: o.write(b'\0' * (SETTORE - s % SETTORE))
    print(f'{out}: {totale} settori, {totale * SETTORE / 1048576:.1f} MB, {len(voci)} file in \\{cartella.upper()}')

if __name__ == '__main__':
    main()
