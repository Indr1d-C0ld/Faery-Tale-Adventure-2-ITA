#!/usr/bin/env python3
"""Costruisce gli archivi del restauro a partire dagli originali e dalle patch in patch/.

Uso:
  costruisci.py

Patch lette (tutte facoltative, righe che iniziano con '#' ignorate):
  patch/script/modNNN.diff  differenza (diff -u) fra il listato originale del modulo NNN, prodotto da
                            sagadis.py, e quello modificato. Se esiste patch/script/modNNN.asm
                            (copia di lavoro, non pubblicata) si usa quella. costruisci.py --diff
                            rigenera le .diff dalle copie di lavoro.
  patch/script/modNNN.asm   copia modificata di estratti/script/modNNN.asm; sostituisce la voce NNN
                            del gruppo SAGA. Le stringhe nuove (strlit "testo") si accodano alla
                            tabella di stringhe del modulo. Le etichette (@nome:) si possono usare in
                            patch/esportazioni.tsv.
  patch/esportazioni.tsv    indice  modulo  offset|@etichetta   voce della tabella _EXP (nuova o cambiata)
  patch/nomi.tsv            indice  nome                        nomi nuovi in coda a LIST/NAME
  patch/prototipi.tsv       indice  copia_da  campo=valore,...  prototipi nuovi in coda a LIST/PRO0
  patch/oggetti.tsv         indice  proto  u  v  z  nome  genitore  script  flag  pv  misc
                                                                oggetti nuovi in coda a LIST/OBJE
  patch/dati.tsv            archivio gruppo voce offset originali nuovi motivo   byte da cambiare
Gli indici sono quelli attesi e vengono controllati. Nei campi numerici si può scrivere nome:XYZ
per l'indice di un nome nuovo o esistente. Gli originali in original/ non vengono toccati:
gli archivi modificati vanno in build/ e i collegamenti in gioco/ puntano lì.
Prima della traduzione si scrivono build/scripts_en.hrs e build/fta_en.hrs (patch in inglese, da cui
traduzione.py estrae i testi); poi si applicano traduzione/testi.tsv e traduzione/nomi.tsv.
"""
import os, re, struct, sys
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sagaasm
from sagaasm import assemble
from hreswrite import rewrite
from hreslib import HRes
from stringhe import parse_table, build_table, build_script_strings

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#  Cartelle: si possono cambiare con le variabili d'ambiente (le usa l'installatore del pacchetto)
ORIGDIR = os.environ.get('FTA2_ORIGINALI', os.path.join(RADICE, 'original/HallsoftheDead/disk/FTA2'))
USCITA = os.environ.get('FTA2_USCITA', os.path.join(RADICE, 'build'))
LAVORO = os.environ.get('FTA2_LAVORO', USCITA)
GIOCO = None if 'FTA2_USCITA' in os.environ else os.path.join(RADICE, 'gioco')

def originale(nome):
    """Percorso di un file della copia originale, senza badare a maiuscole e minuscole."""
    for f in os.listdir(ORIGDIR):
        if f.lower() == nome.lower():
            return os.path.join(ORIGDIR, f)
    raise SystemExit(f'manca {nome} nella cartella del gioco originale {ORIGDIR}')
PATCH = os.path.join(RADICE, 'patch')

PROTO_CAMPI = ('classType script nameIndex iconSprite groundSprite c0 c1 c2 c3 mass bulk cross height '
               'tough breakType maxCap lockType accept wDamage wRate maxRange missile wearable absorb '
               'divider defBonus maxCharges chargeType flags price heldSprite resist immun sfx').split()
PROTO_FMT = '<hHhHH4BBBBBBBHBBBBBBBbbbBBhhhhhB7x'
OBJE_FMT = '<hhhhHHHHBH'

def righe(nome):
    p = os.path.join(PATCH, nome)
    if not os.path.exists(p): return []
    out = []
    for r in open(p, encoding='utf-8'):
        r = r.rstrip('\n')
        if r.strip() and not r.startswith('#'): out.append(r.split('\t'))
    return out

def tag(s):
    """'PRO\\1' -> b'PRO\\x01', 'LIST' -> b'LIST'."""
    return re.sub(r'\\(\d)', lambda m: chr(int(m.group(1))), s).encode('latin-1')

def collega(nome):
    if GIOCO is None: return
    link = os.path.join(GIOCO, nome)
    out = os.path.join(USCITA, nome)
    if os.path.realpath(link) != os.path.realpath(out):
        if os.path.lexists(link): os.remove(link)
        os.symlink(os.path.relpath(out, GIOCO), link)

def listato_originale(g, idx):
    """Listato del modulo idx dell'archivio originale, identico a estratti/script/modNNN.asm."""
    import sagadis as sd
    out, nf, ok = sd.disasm_module(sd.Module(g, idx), [])
    return ('\n'.join(out) + '\n').encode('utf-8').decode('latin-1')

def applica_diff(orig, diff):
    """Applica una differenza unificata (testo) a orig; il contesto deve coincidere esattamente."""
    righe = orig.split('\n')
    out, pos = [], 0
    d = diff.split('\n')
    i = 0
    while i < len(d):
        m = re.match(r'@@ -(\d+)(?:,(\d+))? \+\d+(?:,\d+)? @@', d[i])
        if not m:
            i += 1; continue
        inizio = int(m.group(1)) - 1 if m.group(2) != '0' else int(m.group(1))
        out += righe[pos:inizio]; pos = inizio
        i += 1
        while i < len(d) and not d[i].startswith('@@'):
            r = d[i]
            if r.startswith(' ') or r.startswith('-'):
                if righe[pos] != r[1:]:
                    raise SystemExit(f'differenza non applicabile alla riga {pos + 1}: atteso {r[1:]!r}, trovato {righe[pos]!r}')
                if r.startswith(' '): out.append(righe[pos])
                pos += 1
            elif r.startswith('+'):
                out.append(r[1:])
            i += 1
    out += righe[pos:]
    return '\n'.join(out)

def scrivi_diff():
    """Rigenera patch/script/modNNN.diff dalle copie di lavoro patch/script/modNNN.asm."""
    import difflib
    g = HRes(originale('SCRIPTS.HRS')).group('SAGA')
    pdir = os.path.join(PATCH, 'script')
    for fn in sorted(os.listdir(pdir)):
        if not (fn.startswith('mod') and fn.endswith('.asm')): continue
        idx = int(fn[3:6])
        a = listato_originale(g, idx).split('\n')
        b = open(os.path.join(pdir, fn), encoding='latin-1').read().split('\n')
        diff = '\n'.join(difflib.unified_diff(a, b, f'a/{fn}', f'b/{fn}', n=3, lineterm='')) + '\n'
        if applica_diff('\n'.join(a), diff) != '\n'.join(b):
            raise SystemExit(f'{fn}: la differenza non ricostruisce il listato')
        open(os.path.join(pdir, fn[:-4] + '.diff'), 'w', encoding='latin-1').write(diff)
        print(f'{fn[:-4]}.diff: {diff.count(chr(10))} righe')

def costruisci_script():
    src = originale('SCRIPTS.HRS')
    g = HRes(src).group('SAGA')
    repl, etichette = {}, {}
    pdir = os.path.join(PATCH, 'script')
    moduli = {}
    for fn in sorted(os.listdir(pdir)) if os.path.isdir(pdir) else []:
        if fn.startswith('mod') and fn.endswith('.diff'):
            moduli.setdefault(int(fn[3:6]), fn)
    for fn in sorted(os.listdir(pdir)) if os.path.isdir(pdir) else []:
        if fn.startswith('mod') and fn.endswith('.asm'):
            moduli[int(fn[3:6])] = fn          # la copia di lavoro ha la precedenza
    for idx, fn in sorted(moduli.items()):
        orig = g.read_index(idx)
        strres = struct.unpack_from('<H', orig, 2)[0]
        vecchie = parse_table(g.read_index(strres), 2)
        testo = open(os.path.join(pdir, fn), encoding='latin-1').read()
        if fn.endswith('.diff'):
            testo = applica_diff(listato_originale(g, idx), testo)
        b, nuove = assemble(testo, nstr=len(vecchie))
        etichette[idx] = dict(sagaasm.LAST_LABELS)
        diff = sum(1 for x, y in zip(b, orig) if x != y) + abs(len(b) - len(orig))
        print(f'{fn}: {len(b)} byte ({len(b) - len(orig):+d}), {diff} byte diversi, {len(nuove)} stringhe nuove')
        repl[(b'SAGA', idx)] = b
        if nuove:
            repl[(b'SAGA', strres)] = build_script_strings(vecchie + [s.decode('latin-1') for s in nuove])
    exp_righe = righe('esportazioni.tsv')
    if exp_righe:
        ie = g.index_of(b'_EXP')
        e = bytearray(g.read_index(ie))
        for indice, modulo, dove in exp_righe:
            k, mod = int(indice), int(modulo)
            off = etichette[mod][dove[1:]] if dove.startswith('@') else int(dove)
            pos = 4 * k - 2
            if pos > len(e): raise SystemExit(f'esportazione {k}: la tabella ne ha solo {(len(e) + 2) // 4}')
            if pos == len(e): e += b'\0' * 4
            e[pos:pos + 4] = struct.pack('<HH', mod, off)
            print(f'_EXP {k} -> {mod}:{off}')
        repl[(b'SAGA', ie)] = bytes(e)
    os.makedirs(USCITA, exist_ok=True); os.makedirs(LAVORO, exist_ok=True)
    rewrite(src, os.path.join(LAVORO, 'scripts_en.hrs'), repl)
    # traduzione: sostituisce le stringhe tradotte nelle tabelle di stringhe dei moduli
    from traduzione import traduzioni_testi, coincide
    per_res = defaultdict(dict)
    for (res, num), coppia in traduzioni_testi().items(): per_res[res][num] = coppia
    tradotte, diverse = 0, 0
    for res, voci in per_res.items():
        tab = parse_table(repl.get((b'SAGA', res)) or g.read_index(res), 2)
        for num, (en, it) in voci.items():
            if num >= len(tab) or not coincide(en, tab[num]):
                diverse += 1; continue
            tab[num] = it; tradotte += 1
        repl[(b'SAGA', res)] = build_script_strings(tab)
    print(f'traduzione: {tradotte} stringhe applicate' + (f', {diverse} ignorate perché l inglese non coincide' if diverse else ''))
    rewrite(src, os.path.join(USCITA, 'scripts.hrs'), repl)
    collega('scripts.hrs')

def costruisci_dati():
    """Nomi, prototipi e oggetti nuovi in FTA.HRS, più le patch a byte di dati.tsv."""
    per_archivio = defaultdict(list)
    for arch, gruppo, voce, off, prima, dopo, motivo in righe('dati.tsv'):
        per_archivio[arch].append((gruppo, tag(voce), int(off), bytes.fromhex(prima), bytes.fromhex(dopo), motivo))
    nomi_r, proto_r, ogg_r = righe('nomi.tsv'), righe('prototipi.tsv'), righe('oggetti.tsv')
    if nomi_r or proto_r or ogg_r: per_archivio.setdefault('fta.hrs', [])
    for arch, patch in per_archivio.items():
        src = originale(arch)
        h = HRes(src)
        voci = {}
        def leggi(gruppo, voce):
            g = h.group(gruppo); idx = g.index_of(voce)
            if (gruppo, idx) not in voci: voci[(gruppo, idx)] = bytearray(g.read_index(idx))
            return voci[(gruppo, idx)]
        nomi_idx = {}
        if arch == 'fta.hrs':
            nd = leggi('LIST', b'NAME')
            nomi = parse_table(bytes(nd), 0)
            nomi_idx = {n: i for i, n in enumerate(nomi)}
            for indice, nome in nomi_r:
                if int(indice) != len(nomi): raise SystemExit(f'nome {nome}: indice {indice}, atteso {len(nomi)}')
                nomi.append(nome); nomi_idx[nome] = len(nomi) - 1
                print(f'NAME {indice}: {nome}')
            if nomi_r: nd[:] = build_table(nomi, align=2)
            def num(v):
                return nomi_idx[v[5:]] if v.startswith('nome:') else int(v)
            pd = leggi('LIST', b'PRO\x00')
            for indice, base, campi in proto_r:
                if int(indice) != len(pd) // 52: raise SystemExit(f'prototipo {indice}: atteso {len(pd) // 52}')
                v = dict(zip(PROTO_CAMPI, struct.unpack_from(PROTO_FMT, pd, int(base) * 52)))
                for c in campi.split(','):
                    k, x = c.split('=')
                    if k not in v: raise SystemExit(f'campo sconosciuto {k}')
                    v[k] = num(x)
                pd += struct.pack(PROTO_FMT, *[v[k] for k in PROTO_CAMPI])
                print(f'PRO0 {indice}: copia di {base}, {campi}')
            od = leggi('LIST', b'OBJE')
            for r in ogg_r:
                indice, valori = int(r[0]), [num(x) for x in r[1:]]
                if indice != len(od) // 19: raise SystemExit(f'oggetto {indice}: atteso {len(od) // 19}')
                od += struct.pack(OBJE_FMT, *valori)
                print(f'OBJE {indice}: {valori}')
        for gruppo, voce, off, prima, dopo, motivo in patch:
            dati = leggi(gruppo, voce)
            if bytes(dati[off:off + len(prima)]) != prima:
                raise SystemExit(f'{arch} {voce} @{off}: attesi {prima.hex()}, trovati {bytes(dati[off:off + len(prima)]).hex()}')
            dati[off:off + len(dopo)] = dopo
            print(f'{arch} {voce!r} @{off}: {prima.hex()} -> {dopo.hex()}  ({motivo.split(":")[0]})')
        chiavi = lambda: {(g.encode() if isinstance(g, str) else g, i): bytes(d) for (g, i), d in voci.items()}
        if arch == 'fta.hrs':
            rewrite(src, os.path.join(LAVORO, 'fta_en.hrs'), chiavi())
            from traduzione import traduzioni_nomi, coincide
            tn = traduzioni_nomi()
            if tn:
                nd = leggi('LIST', b'NAME')
                nomi = parse_table(bytes(nd), 0)
                for i, (en, it) in tn.items():
                    if i < len(nomi) and coincide(en, nomi[i]): nomi[i] = it
                nd[:] = build_table(nomi, align=2)
                print(f'traduzione: {len(tn)} nomi applicati')
        rewrite(src, os.path.join(USCITA, arch), chiavi())
        collega(arch)

def main():
    if '--diff' in sys.argv:
        scrivi_diff(); return
    costruisci_script()
    costruisci_dati()
    print('fatto')

if __name__ == '__main__':
    main()
