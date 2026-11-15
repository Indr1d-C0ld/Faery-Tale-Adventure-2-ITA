#!/usr/bin/env python3
"""Analisi statica degli script di FTA2: grafo delle chiamate e uso delle variabili globali.

Uso:
  analisi.py SCRIPTS.HRS OUTDIR

Scrive in OUTDIR:
  funzioni.tsv     ogni funzione: modulo, offset, nome, chi la chiama, se è raggiungibile
  morte.txt        funzioni mai raggiungibili, con i testi che contengono
  variabili.tsv    ogni variabile globale toccata (segmento dati __DA e accessi far[...]):
                   letture, scritture, funzioni coinvolte
  sospette.txt     variabili lette ma mai scritte (condizioni che non si avverano mai) e
                   scritte ma mai lette (progressi di quest che non servono a nulla)

Radici della raggiungibilità: tutte le voci della tabella delle esportazioni (_EXP) e ogni coppia
segmento:offset nei dati che punti all'inizio di una funzione (vtable delle classi).
"""
import os, re, struct, sys
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hreslib import HRes
import sagadis as sd

def walk(m, start, end):
    """Istruzioni raggiungibili di una funzione: lista di (offset, testo)."""
    ins = {}
    work = [start]
    while work:
        at = work.pop()
        while start <= at < end and at not in ins:
            try:
                text, note, nxt, targets, term = sd.decode(m, at, [])
            except (sd.Bad, IndexError):
                break
            ins[at] = (text, note)
            work.extend(t for t in targets if start <= t < end)
            if term: break
            at = nxt
    return [(a, ins[a][0], ins[a][1]) for a in sorted(ins)]

ADDR_RE = re.compile(r'(data|far)\[(?:(\d+):)?(\d+)\]')
READ_OPS = {'getflag', 'getbyte', 'getint', 'getstr', 'getid', 'postinc', 'postdec', 'inc_v', 'dec_v'}
WRITE_OPS = {'putflag', 'putbyte', 'putint', 'putstr', 'putid', 'putflag_v', 'putbyte_v', 'putint_v',
             'putstr_v', 'putid_v', 'postinc', 'postdec', 'inc_v', 'dec_v'}

def main():
    src, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    g = HRes(src).group('SAGA')
    da = g.index_of(b'__DA')
    special = {da, g.index_of(b'_EXP')}
    mods = {}
    funcs = {}                      # (mod, enter_off) -> nome
    ranges = {}                     # (mod, enter_off) -> (fine)
    for idx in range(len(g.entries)):
        if idx in special or g.entries[idx][2] < 8: continue
        m = sd.Module(g, idx)
        fl = sd.find_functions(m.d)
        if not fl: continue
        mods[idx] = m
        for k, (p, name, ns) in enumerate(fl):
            end = fl[k + 1][2] if k + 1 < len(fl) else len(m.d)
            funcs[(idx, p)] = name
            ranges[(idx, p)] = end
    # chiamate
    calls = defaultdict(set)        # chiamato -> chiamanti
    body = {}
    for key, name in funcs.items():
        m = mods[key[0]]
        ins = walk(m, key[1], ranges[key])
        body[key] = ins
        for at, text, note in ins:
            op, *args = text.split()
            if op == 'call_near':
                calls[(key[0], int(args[1]))].add(key)
            elif op == 'call_far':
                s, o = args[1].split(':'); calls[(int(s), int(o))].add(key)
    # radici: esportazioni e riferimenti nei dati
    roots = set()
    e = g.read(b'_EXP')
    for k in range(1, len(e) // 4 + 1):
        if 4 * k + 2 > len(e): break
        s, o = struct.unpack_from('<HH', e, 4 * k - 2)
        if (s, o) in funcs: roots.add((s, o))
    data_refs = set()
    for idx in list(mods) + [da]:
        d = g.read_index(idx)
        for p in range(0, len(d) - 3):
            s, o = struct.unpack_from('<HH', d, p)
            if (s, o) in funcs:
                data_refs.add((s, o))
    roots |= data_refs
    callees = defaultdict(set)
    for callee, callers in calls.items():
        for c in callers: callees[c].add(callee)
    reach = set()
    work = list(roots)
    while work:
        f = work.pop()
        if f in reach or f not in funcs: continue
        reach.add(f)
        work.extend(callees[f])
    # variabili globali
    var = defaultdict(lambda: {'r': set(), 'w': set()})
    for key, ins in body.items():
        for at, text, note in ins:
            op, *args = text.split()
            if op not in READ_OPS and op not in WRITE_OPS: continue
            m_ = ADDR_RE.search(text)
            if not m_ or 'deref' in text: continue
            kind, seg, off = m_.groups()
            off = int(off)
            if kind == 'far' and int(seg) != da: continue
            if op in ('getflag', 'putflag', 'putflag_v'):
                v = f'bit {off >> 3}.{off & 7}'
            else:
                v = f'byte {off}'
            if op in READ_OPS: var[v]['r'].add(key)
            if op in WRITE_OPS: var[v]['w'].add(key)
    fname = lambda k: f'{k[0]}:{funcs.get(k, "?")}'
    with open(os.path.join(outdir, 'funzioni.tsv'), 'w') as f:
        f.write('modulo\toffset\tnome\traggiungibile\tradice\tchiamanti\n')
        for key in sorted(funcs):
            f.write(f'{key[0]}\t{key[1]}\t{funcs[key]}\t{"sì" if key in reach else "NO"}\t'
                    f'{"sì" if key in roots else ""}\t{",".join(sorted(fname(c) for c in calls.get(key, ())))}\n')
    dead = [k for k in sorted(funcs) if k not in reach]
    with open(os.path.join(outdir, 'morte.txt'), 'w') as f:
        f.write(f'# {len(dead)} funzioni mai raggiungibili su {len(funcs)}\n')
        for key in dead:
            texts = [note for at, text, note in body[key] if text.startswith('strlit') and note]
            f.write(f'\n{key[0]}:{key[1]} {funcs[key]} ({len(body[key])} istruzioni)\n')
            for t in texts[:40]: f.write(f'    {t}\n')
    with open(os.path.join(outdir, 'variabili.tsv'), 'w') as f:
        f.write('variabile\tletture\tscritture\tlettori\tscrittori\n')
        for v in sorted(var, key=lambda x: (x.split()[0], float(x.split()[1]))):
            r, w = var[v]['r'], var[v]['w']
            f.write(f'{v}\t{len(r)}\t{len(w)}\t{",".join(sorted(map(fname, r)))}\t{",".join(sorted(map(fname, w)))}\n')
    sus_r = [v for v in var if var[v]['r'] and not var[v]['w']]
    sus_w = [v for v in var if var[v]['w'] and not var[v]['r']]
    with open(os.path.join(outdir, 'sospette.txt'), 'w') as f:
        f.write(f'# lette ma mai scritte dagli script ({len(sus_r)}): valgono sempre il valore iniziale di __DA\n')
        dd = g.read_index(da)
        for v in sorted(sus_r):
            kind, pos = v.split()
            init = (dd[int(pos.split('.')[0])] >> int(pos.split('.')[1]) & 1) if kind == 'bit' else struct.unpack_from('<H', dd, int(pos))[0] if int(pos) + 2 <= len(dd) else '?'
            f.write(f'{v}\tiniziale={init}\tletta da {",".join(sorted(map(fname, var[v]["r"])))}\n')
        f.write(f'\n# scritte ma mai lette dagli script ({len(sus_w)})\n')
        for v in sorted(sus_w):
            f.write(f'{v}\tscritta da {",".join(sorted(map(fname, var[v]["w"])))}\n')
    print(f'funzioni {len(funcs)}, raggiungibili {len(reach)}, morte {len(dead)}, radici {len(roots)}; '
          f'variabili {len(var)}, lette-mai-scritte {len(sus_r)}, scritte-mai-lette {len(sus_w)}')

if __name__ == '__main__':
    main()
