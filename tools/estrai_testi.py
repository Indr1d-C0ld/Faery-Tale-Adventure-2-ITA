#!/usr/bin/env python3
"""Estrae tutti i testi degli script di FTA2 in una tabella per la traduzione.

Uso:
  estrai_testi.py SCRIPTS.HRS FTAVOICE.HRS OUT.tsv

Ogni riga è una stringa di una tabella di stringhe di SCRIPTS.HRS, con colonne:
  id         risorsa:offset:numero, la chiave stabile della stringa
  tipo       battuta (parlata, con voce), testo (mostrato), id_voce, interno (etichette e codici),
             orfana (mai usata dal codice)
  voce       tag del campione in FTAVOICE.HRS (solo per le battute), con * se il campione manca
  usi        moduli e funzioni che la usano
  testo      il testo originale; a capo e tabulazioni scritti come \\n e \\t
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hreslib import HRes
import sagadis as sd

VOICE_RE = re.compile(r'^[A-Z][0-9A-Z]{3}$')
# funzioni del motore che ricevono una stringa da mostrare al giocatore
SHOW = {'scriptPlacard', 'scriptErrorDialog', 'scriptOpenBook', 'scriptOpenScroll', 'scriptOpenParchment',
        'scriptStatus', 'scriptPlayIntro'}   # scriptWriteObject scrive solo nel registro di debug

def esc(s):
    return s.replace('\\', '\\\\').replace('\n', '\\n').replace('\t', '\\t').replace('\r', '\\r')

def main():
    scripts, voice, outp = sys.argv[1:4]
    h = HRes(scripts)
    g = h.group('SAGA')
    talk = {t.decode('latin-1') for t, _, _ in HRes(voice).group('TALK').entries}
    special = {g.index_of(b'__DA'), g.index_of(b'_EXP')}
    tables = {}       # (res, off) -> lista di stringhe
    uses = {}         # chiave -> lista di (modulo, funzione, ruolo, voce)
    for idx in range(len(g.entries)):
        if idx in special or g.entries[idx][2] < 8: continue
        m = sd.Module(g, idx)
        funcs = sd.find_functions(m.d)
        if not funcs: continue
        tables[(m.strres, m.stroff)] = m.strings()
        for k, (p, name, nstart) in enumerate(funcs):
            end = funcs[k + 1][2] if k + 1 < len(funcs) else len(m.d)
            out = []
            # flusso di controllo come il disassemblatore, conservando l'ordine
            ins = []
            seen = set()
            work = [p]
            while work:
                at = work.pop()
                while p <= at < end and at not in seen:
                    try:
                        text, note, nxt, targets, term = sd.decode(m, at, [])
                    except (sd.Bad, IndexError):
                        break
                    seen.add(at)
                    ins.append((at, text, nxt))
                    work.extend(targets)
                    if term: break
                    at = nxt
            ins.sort()
            for i, (at, text, nxt) in enumerate(ins):
                if not text.startswith('strlit'): continue
                num = int(text.split('#')[1])
                key = (m.strres, m.stroff, num)
                s = m.string(num)
                if s is None: continue
                role, vtag = 'testo', ''
                nxt1 = ins[i + 1][1] if i + 1 < len(ins) else ''
                nxt2 = ins[i + 2][1] if i + 2 < len(ins) else ''
                prev1 = ins[i - 1][1] if i > 0 else ''
                prev2 = ins[i - 2][1] if i > 1 else ''
                if 'scriptResID' in nxt1:
                    role = 'id_voce'
                elif nxt1.startswith('strlit') and 'scriptResID' in nxt2:
                    role = 'battuta'
                    vnum = int(nxt1.split('#')[1])
                    vtag = m.string(vnum) or ''
                else:
                    # prima chiamata che segue: decide se la stringa è mostrata o interna
                    call = ''
                    for j in range(i + 1, min(i + 12, len(ins))):
                        t = ins[j][1]
                        if t.startswith(('ccall', 'call_')):
                            call = t; break
                    if 'scriptWriteMessage' in call or 'scriptWriteLog' in call or 'scriptDebug' in call or 'scriptWriteObject' in call:
                        role = 'interno'
                    elif s.startswith((' resp:', 'resp:', 'General_')) or (VOICE_RE.match(s) and 'scriptResID' in call):
                        role = 'interno'
                uses.setdefault(key, []).append((m.idx, name, role, vtag))
    rows = []
    stats = {}
    for (res, off), strs in sorted(tables.items()):
        for num, s in enumerate(strs):
            key = (res, off, num)
            u = uses.get(key, [])
            roles = {r for _, _, r, _ in u}
            if not u:
                tipo = 'orfana'
            elif 'battuta' in roles:
                tipo = 'battuta'
            elif 'testo' in roles:
                tipo = 'testo'
            elif 'id_voce' in roles:
                tipo = 'id_voce'
            else:
                tipo = 'interno'
            if tipo in ('testo', 'orfana') and s.strip() == '':
                tipo = 'interno'
            vt = sorted({v for _, _, _, v in u if v})
            voce = ','.join(v + ('' if v in talk else '*') for v in vt)
            usi = ','.join(sorted({f'{mi}:{fn}' for mi, fn, _, _ in u}))
            rows.append((f'{res}:{off}:{num}', tipo, voce, usi, esc(s)))
            stats[tipo] = stats.get(tipo, 0) + 1
    with open(outp, 'w', encoding='utf-8') as f:
        f.write('id\ttipo\tvoce\tusi\ttesto\n')
        for r in rows: f.write('\t'.join(r) + '\n')
    print(len(rows), stats)

if __name__ == '__main__':
    main()
