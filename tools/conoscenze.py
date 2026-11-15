#!/usr/bin/env python3
"""Pacchetti di conoscenza (dialoghi) di FTA2: quali esistono, a chi sono assegnati, quali no.

Uso:
  conoscenze.py SCRIPTS.HRS FTA.HRS NOMI.tsv OUT.txt

Un pacchetto di conoscenza è una classe esportata (voce di _EXP) la cui vtable ha nello slot 0
evalResponse e nello slot 1 executeResponse (methods.r di ScummVM). Un personaggio lo usa se è
fra i suoi 16 pacchetti iniziali (FTA.HRS, LIST/ACTO, record di 91 byte, offset 39) oppure se gli
script lo aggiungono. Per gli script si cerca il numero del pacchetto come costante in qualunque
chiamata AddKnowledge (slot 130 della vtable degli attori) o AddMissionKnowledge (slot 132), e se
l'argomento è un parametro lo si risale nelle funzioni chiamanti (fino a 6 livelli). Un argomento
calcolato in altro modo sfugge all'analisi: i pacchetti 'MAI ASSEGNATO' vanno confermati a mano.
"""
import os, struct, sys
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hreslib import HRes
import sagadis as sd
from analisi import walk

def main():
    scripts, fta, nomi, outp = sys.argv[1:5]
    g = HRes(scripts).group('SAGA')
    special = {g.index_of(b'__DA'), g.index_of(b'_EXP')}
    funcs = {}
    mods = {}
    for idx in range(len(g.entries)):
        if idx in special or g.entries[idx][2] < 8: continue
        m = sd.Module(g, idx)
        fl = sd.find_functions(m.d)
        if not fl: continue
        mods[idx] = m
        for k, (p, name, ns) in enumerate(fl):
            end = fl[k + 1][2] if k + 1 < len(fl) else len(m.d)
            funcs[(idx, p)] = (name, end)
    e = g.read(b'_EXP')
    packages = {}
    for k in range(1, len(e) // 4 + 1):
        if 4 * k + 2 > len(e): break
        s, o = struct.unpack_from('<HH', e, 4 * k - 2)
        if s not in mods: continue
        d = mods[s].d
        if o + 8 > len(d): continue
        s0, o0, s1, o1 = struct.unpack_from('<HHHH', d, o)
        f0, f1 = funcs.get((s0, o0)), funcs.get((s1, o1))
        if f0 and f1 and f0[0] == 'evalResponse' and f1[0] == 'executeResponse':
            packages[k] = (s1, o1)
    # chiamate AddKnowledge (slot 130) e AddMissionKnowledge (slot 132), con i parametri
    # risaliti attraverso le funzioni chiamanti (args spinti da destra: stack[8] è l'ultimo)
    bodies = {key: walk(mods[key[0]], key[1], funcs[key][1]) for key in funcs}
    def arg_source(ins, i, n, which):
        """Istruzione che ha spinto l'argomento 'which' (0 = ultimo spinto) prima di ins[i]."""
        j = i - 1 - which
        return ins[j][1] if j >= 0 else ''
    callers = defaultdict(list)   # funzione -> [(chiamante, indice istruzione, nargs)]
    for key, ins in bodies.items():
        for i, (at, text, note) in enumerate(ins):
            op, *args = text.split()
            if op == 'call_far':
                sg, of = args[1].split(':'); callers[(int(sg), int(of))].append((key, i, int(args[0])))
            elif op == 'call_near':
                callers[(key[0], int(args[1]))].append((key, i, int(args[0])))
    consts = defaultdict(set)
    def resolve(key, src, where, depth):
        op, *args = src.split() if src else ('',)
        if op == 'constint':
            consts[int(args[0])].add(where); return
        if op == 'getint' and args and args[0].startswith('stack[') and depth < 6:
            off = int(args[0][6:-1])
            if off >= 8:
                pi = (off - 8) // 2
                for ck, ci, n in callers.get(key, []):
                    resolve(ck, arg_source(bodies[ck], ci, n, pi), where, depth + 1)
    for key, ins in bodies.items():
        for i, (at, text, note) in enumerate(ins):
            op, *args = text.split()
            if op in ('call_member', 'call_member_v') and args[1] in ('130', '132'):
                which = 0 if args[1] == '130' else 0
                resolve(key, arg_source(ins, i, int(args[0]), which), f'{key[0]}:{funcs[key][0]}', 0)
    # conoscenze iniziali degli attori
    names = {}
    for l in open(nomi, encoding='utf-8'):
        a = l.rstrip('\n').split('\t')
        if a[0].isdigit(): names[int(a[0])] = a[1] if len(a) > 1 else ''
    acto = HRes(fta).group('LIST').read(b'ACTO')
    holders = defaultdict(list)
    for i in range(len(acto) // 91):
        r = acto[i * 91:(i + 1) * 91]
        name = names.get(struct.unpack_from('<H', r, 8)[0], '?')
        for kid in struct.unpack_from('<16H', r, 39):
            if kid: holders[kid].append(f'{name}#{i}')
    lines = []
    unused = []
    for k in sorted(packages):
        s, o = packages[k]
        m = mods[s]
        ins = walk(m, o, funcs[(s, o)][1])
        texts = [n for a, t, n in ins if t.startswith('strlit') and n and not sd.VOICE_RE.match(n.strip("'\"")) ] if hasattr(sd, 'VOICE_RE') else \
                [n for a, t, n in ins if t.startswith('strlit') and n]
        h = holders.get(k, [])
        c = consts.get(k, set())
        state = 'assegnato' if h else ('aggiunto dagli script' if c else 'MAI ASSEGNATO')
        if not h and not c: unused.append(k)
        lines.append(f'pacchetto {k:5d}  modulo {s:3d} @{o:<6d} {state:24s} stringhe={len(texts):3d}  '
                     f'attori: {", ".join(h[:6])}{" …" if len(h) > 6 else ""}  costante in: {", ".join(sorted(c)[:4])}')
    with open(outp, 'w', encoding='utf-8') as f:
        f.write(f'# {len(packages)} pacchetti di conoscenza, {len(unused)} mai assegnati\n')
        f.write('\n'.join(lines) + '\n')
        f.write('\n# Pacchetti mai assegnati: testo completo\n')
        for k in unused:
            s, o = packages[k]
            f.write(f'\n## pacchetto {k} (modulo {s}, executeResponse @{o})\n')
            for a, t, n in walk(mods[s], o, funcs[(s, o)][1]):
                if t.startswith('strlit') and n: f.write(f'    {n}\n')
    print(len(packages), 'pacchetti;', len(unused), 'mai assegnati;', len(acto) // 91, 'attori')

if __name__ == '__main__':
    main()
