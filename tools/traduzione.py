#!/usr/bin/env python3
"""Gestione della traduzione italiana dei testi di FTA2.

Uso:
  traduzione.py prepara          aggiorna traduzione/testi.tsv e traduzione/nomi.tsv dai testi inglesi
                                 (build/scripts_en.hrs e build/fta_en.hrs, scritti da costruisci.py),
                                 conservando le traduzioni già fatte
  traduzione.py blocchi N        divide le stringhe ancora da tradurre in blocchi di circa N caratteri
                                 in traduzione/blocchi/NN.tsv (un modulo non viene mai spezzato)
  traduzione.py unisci [--forza] legge traduzione/blocchi/NN.it.tsv, controlla ogni riga e la copia in
                                 testi.tsv; le righe scartate finiscono in traduzione/scarti.tsv
  traduzione.py stato            conta stringhe tradotte e mancanti
  traduzione.py esporta          scrive traduzione/testi_it.tsv e traduzione/nomi_it.tsv: solo
                                 l'italiano, con il CRC32 del testo inglese al posto del testo
                                 stesso (il testo originale del gioco non si ridistribuisce).
                                 costruisci.py li usa quando mancano testi.tsv e nomi.tsv

traduzione/testi.tsv, colonne TAB:
  id (risorsa:offset:numero)  tipo  voce  usi  inglese  italiano
traduzione/nomi.tsv: indice  inglese  italiano
Nei campi di testo a capo e tabulazioni si scrivono \\n e \\t.

Controlli su ogni traduzione (vedi controlla()):
  - stessi segnaposto %d %s %n ... nello stesso ordine;
  - stesso numero di '@' (pulsanti di scelta) e di a capo;
  - solo caratteri Latin-1 (i font hanno le lettere accentate italiane);
  - battute non oltre 480 byte (il buffer delle battute del motore è di 512).
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TDIR = os.path.join(RADICE, 'traduzione')
TESTI = os.path.join(TDIR, 'testi.tsv')
NOMI = os.path.join(TDIR, 'nomi.tsv')
TESTI_IT = os.path.join(TDIR, 'testi_it.tsv')
NOMI_IT = os.path.join(TDIR, 'nomi_it.tsv')

def crc(testo):
    """CRC32 (esadecimale) del testo originale, codificato Latin-1 come nel gioco."""
    import zlib
    return '%08x' % zlib.crc32(testo.encode('latin-1'))
DA_TRADURRE = ('battuta', 'testo')
SEGNAPOSTO = re.compile(r'%[-+ #0-9.]*[a-zA-Z]')
VUOTA = '<vuota>'
FORZA = '--forza' in sys.argv       # unisci --forza: i blocchi sovrascrivono anche le righe già tradotte   # traduzione volutamente vuota (es. i pezzi di sayNumber, solo voce)

def leggi_tsv(p):
    if not os.path.exists(p): return []
    righe = []
    for l in open(p, encoding='utf-8'):
        l = l.rstrip('\n')
        if not l or l.startswith('#'): continue
        righe.append(l.split('\t'))
    return righe

def scrivi_tsv(p, intest, righe):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8') as f:
        f.write('\t'.join(intest) + '\n')
        for r in righe: f.write('\t'.join(r) + '\n')

def decodifica(s):
    mappa = {'n': '\n', 't': '\t', 'r': '\r', '\\': '\\'}
    return re.sub(r'\\(.)', lambda m: mappa.get(m.group(1), '\\' + m.group(1)), s)

def controlla(inglese, italiano, tipo):
    """Restituisce l'elenco dei problemi (vuoto se la traduzione è accettabile)."""
    err = []
    if not italiano.strip() and inglese.strip(): err.append('vuota')
    if SEGNAPOSTO.findall(inglese) != SEGNAPOSTO.findall(italiano):
        err.append(f'segnaposto {SEGNAPOSTO.findall(inglese)} -> {SEGNAPOSTO.findall(italiano)}')
    if inglese.count('@') != italiano.count('@'): err.append('numero di @ diverso')
    if inglese.count('\\n') != italiano.count('\\n'): err.append('numero di a capo diverso')
    if '\t' in italiano: err.append('tabulazione vera nel testo')
    bordi = lambda t: re.match(r'^(?:\\n)*( *).*?( *)(?:\\n)*$', t, re.S).groups()
    be, bi = bordi(inglese), bordi(italiano)
    if (be[0] != '') != (bi[0] != '') or (be[1] != '') != (bi[1] != ''):
        err.append('spazi iniziali o finali diversi (le stringhe si concatenano)')
    try:
        b = decodifica(italiano).encode('latin-1')
    except UnicodeEncodeError as e:
        err.append(f'carattere non Latin-1: {italiano[e.start:e.end]!r}'); b = b''
    if tipo == 'battuta' and len(b) > 480: err.append(f'battuta troppo lunga ({len(b)} byte)')
    return err

def prepara():
    import subprocess, tempfile
    from hreslib import HRes
    from stringhe import parse_table
    vecchie = {r[0]: r for r in leggi_tsv(TESTI)}
    with tempfile.TemporaryDirectory() as td:
        out = os.path.join(td, 't.tsv')
        subprocess.run([sys.executable, '-I', os.path.join(RADICE, 'tools/estrai_testi.py'),
                        os.path.join(RADICE, 'build/scripts_en.hrs'), os.path.join(RADICE, 'gioco/ftavoice.hrs'), out],
                       check=True, capture_output=True)
        righe = [r for r in leggi_tsv(out)[1:] if r[1] in DA_TRADURRE]
    nuove, perse = [], 0
    for r in righe:
        r = (r + [''] * 5)[:5]
        it = ''
        if r[0] in vecchie and vecchie[r[0]][4] == r[4]: it = vecchie[r[0]][5] if len(vecchie[r[0]]) > 5 else ''
        elif r[0] in vecchie: perse += 1
        nuove.append(r + [it])
    # righe tradotte che l'estrazione non trova più (es. codice raggiunto solo da un salto aggiunto
    # dal restauro, come sayNumber): si conservano se la stringa esiste ancora identica
    g = HRes(os.path.join(RADICE, 'build/scripts_en.hrs')).group('SAGA')
    presenti = {r[0] for r in nuove}
    tabelle = {}
    conservate = 0
    for k, v in vecchie.items():
        if k in presenti or k.count(':') != 2 or len(v) < 6 or not v[5]: continue
        res, _, num = k.split(':')
        if res not in tabelle: tabelle[res] = parse_table(g.read_index(int(res)), 2)
        tab = tabelle[res]
        if int(num) < len(tab) and tab[int(num)] == decodifica(v[4]):
            nuove.append(v[:6]); conservate += 1
    nuove.sort(key=lambda r: tuple(int(x) for x in r[0].split(':')))
    if conservate: print(f'conservate {conservate} righe tradotte non più raggiunte dall estrazione')
    scrivi_tsv(TESTI, ['id', 'tipo', 'voce', 'usi', 'inglese', 'italiano'], nuove)
    # nomi
    vn = {r[0]: r for r in leggi_tsv(NOMI)}
    d = HRes(os.path.join(RADICE, 'build/fta_en.hrs')).group('LIST').read(b'NAME')
    nomi = parse_table(d, 0)
    rn = []
    for i, n in enumerate(nomi):
        k = str(i)
        it = vn[k][2] if k in vn and len(vn[k]) > 2 and vn[k][1] == n else ''
        rn.append([k, n, it])
    scrivi_tsv(NOMI, ['indice', 'inglese', 'italiano'], rn)
    print(f'testi: {len(nuove)} stringhe, {sum(1 for r in nuove if r[5])} già tradotte'
          f'{f", {perse} da rifare perché l inglese è cambiato" if perse else ""}; nomi: {len(rn)}')

def blocchi(dim):
    righe = leggi_tsv(TESTI)[1:]
    da_fare = [r for r in righe if len(r) < 6 or not r[5]]
    per_mod = {}
    for r in da_fare: per_mod.setdefault(int(r[0].split(':')[0]), []).append(r)
    bdir = os.path.join(TDIR, 'blocchi')
    os.makedirs(bdir, exist_ok=True)
    blocco, n, tot = [], 0, 0
    def chiudi():
        nonlocal blocco, n
        if blocco:
            scrivi_tsv(os.path.join(bdir, f'{n:02d}.tsv'), ['id', 'tipo', 'usi', 'inglese'], blocco)
            n += 1; blocco = []
    for res in sorted(per_mod):
        rr = per_mod[res]
        if blocco and sum(len(x[3]) for x in blocco) + sum(len(x[4]) for x in rr) > dim: chiudi()
        blocco += [[x[0], x[1], x[3], x[4]] for x in rr]
    chiudi()
    print(f'{len(da_fare)} stringhe in {n} blocchi in {bdir}')

def unisci():
    righe = leggi_tsv(TESTI)
    intest, righe = righe[0], righe[1:]
    idx = {r[0]: i for i, r in enumerate(righe)}
    scarti, ok = [], 0
    bdir = os.path.join(TDIR, 'blocchi')
    for fn in sorted(os.listdir(bdir)):
        if not fn.endswith('.it.tsv'): continue
        for r in leggi_tsv(os.path.join(bdir, fn)):
            if r[0] == 'id' or len(r) < 2: continue
            i = idx.get(r[0])
            if i is None: scarti.append([fn, r[0], 'id sconosciuto', r[1]]); continue
            base = (righe[i] + [''] * 6)[:6]
            if base[5] == VUOTA: continue      # scelta del coordinatore, non si sovrascrive
            if base[5] and not FORZA: continue # già tradotta (e magari corretta a mano): si conserva
            err = controlla(base[4], r[1], base[1])
            if err: scarti.append([fn, r[0], '; '.join(err), r[1]]); continue
            base[5] = r[1]; righe[i] = base; ok += 1
    scrivi_tsv(TESTI, intest, righe)
    scrivi_tsv(os.path.join(TDIR, 'scarti.tsv'), ['blocco', 'id', 'problema', 'italiano'], scarti)
    print(f'righe accettate: {ok}, scartate: {len(scarti)} (traduzione/scarti.tsv)')

def stato():
    righe = leggi_tsv(TESTI)[1:]
    fatte = sum(1 for r in righe if len(r) > 5 and r[5])
    car = sum(len(r[4]) for r in righe)
    car_f = sum(len(r[4]) for r in righe if len(r) > 5 and r[5])
    nomi = leggi_tsv(NOMI)[1:]
    nf = sum(1 for r in nomi if len(r) > 2 and r[2])
    print(f'testi: {fatte}/{len(righe)} stringhe ({car_f}/{car} caratteri inglesi); nomi: {nf}/{len(nomi)}')

def traduzioni_testi():
    """Per costruisci.py: {(risorsa, numero): (controllo, italiano)}.

    Il controllo è il testo inglese (da testi.tsv) oppure ('crc', valore) (da testi_it.tsv)."""
    out = {}
    if os.path.exists(TESTI):
        for r in leggi_tsv(TESTI)[1:]:
            if len(r) > 5 and r[5]:
                res, _, num = r[0].split(':')
                it = '' if r[5] == VUOTA else decodifica(r[5])
                out[(int(res), int(num))] = (decodifica(r[4]), it)
    else:
        for r in leggi_tsv(TESTI_IT)[1:]:
            res, _, num = r[0].split(':')
            it = '' if r[3] == VUOTA else decodifica(r[3])
            out[(int(res), int(num))] = (('crc', r[2]), it)
    return out

def traduzioni_nomi():
    """Per costruisci.py: {indice: (controllo, italiano)}, come traduzioni_testi()."""
    if os.path.exists(NOMI):
        return {int(r[0]): (r[1], r[2]) for r in leggi_tsv(NOMI)[1:] if len(r) > 2 and r[2]}
    return {int(r[0]): (('crc', r[1]), r[2]) for r in leggi_tsv(NOMI_IT)[1:]}

def esporta():
    righe = leggi_tsv(TESTI)[1:]
    scrivi_tsv(TESTI_IT, ['id', 'tipo', 'crc32_inglese', 'italiano'],
               [[r[0], r[1], crc(decodifica(r[4])), r[5]] for r in righe if len(r) > 5 and r[5]])
    nomi = leggi_tsv(NOMI)[1:]
    scrivi_tsv(NOMI_IT, ['indice', 'crc32_inglese', 'italiano'],
               [[r[0], crc(r[1]), r[2]] for r in nomi if len(r) > 2 and r[2]])
    print(f'esportati {sum(1 for r in righe if len(r) > 5 and r[5])} testi e {sum(1 for r in nomi if len(r) > 2 and r[2])} nomi')

def coincide(controllo, testo):
    """Vero se il testo originale corrisponde al controllo (testo inglese o ('crc', valore))."""
    if isinstance(controllo, tuple): return crc(testo) == controllo[1]
    return controllo == testo

if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'stato'
    if cmd == 'prepara': prepara()
    elif cmd == 'blocchi': blocchi(int(sys.argv[2]) if len(sys.argv) > 2 else 25000)
    elif cmd == 'unisci': unisci()
    elif cmd == 'esporta': esporta()
    else: stato()
