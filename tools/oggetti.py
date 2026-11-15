#!/usr/bin/env python3
"""Oggetti di FTA2: quali prototipi esistono nel mondo, quali creano gli script, quali nessuno.

Uso:
  oggetti.py SCRIPTS.HRS FTA.HRS NOMI.tsv OUT.txt

Dati (ScummVM saga2, objects.cpp e objproto.h):
  LIST/PRO0  prototipi degli oggetti, 52 byte: classType, script, nameIndex (offset 4) ...
  LIST/OBJE  oggetti iniziali, 19 byte: protoIndex (0), location (2), nameIndex (8), parentID (10) ...
Gli script creano oggetti con scriptMakeObject(proto, nome, script): il prototipo è l'ultimo
argomento spinto. Se è un parametro, lo si risale nei chiamanti come per i pacchetti di conoscenza.
Conta anche il cambio di prototipo con SetProto (slot 10 della vtable), usato per gli stati di un oggetto.
Un prototipo che non è nel mondo e che nessuno script crea è un oggetto irraggiungibile.
"""
import os, struct, sys
from collections import defaultdict, Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hreslib import HRes
import sagadis as sd
from analisi import walk

def main():
    scripts, fta, nomi, outp = sys.argv[1:5]
    names = {}
    for l in open(nomi, encoding='utf-8'):
        a = l.rstrip('\n').split('\t')
        if a[0].isdigit(): names[int(a[0])] = a[1] if len(a) > 1 else ''
    lst = HRes(fta).group('LIST')
    pro = lst.read(b'PRO\x00')
    protos = [struct.unpack_from('<hHh', pro, i * 52) for i in range(len(pro) // 52)]
    obje = lst.read(b'OBJE')
    world = Counter()
    for i in range(len(obje) // 19):
        world[struct.unpack_from('<h', obje, i * 19)[0]] += 1
    g = HRes(scripts).group('SAGA')
    special = {g.index_of(b'__DA'), g.index_of(b'_EXP')}
    funcs, mods = {}, {}
    for idx in range(len(g.entries)):
        if idx in special or g.entries[idx][2] < 8: continue
        m = sd.Module(g, idx)
        fl = sd.find_functions(m.d)
        if not fl: continue
        mods[idx] = m
        for k, (p, name, ns) in enumerate(fl):
            end = fl[k + 1][2] if k + 1 < len(fl) else len(m.d)
            funcs[(idx, p)] = (name, end)
    bodies = {key: walk(mods[key[0]], key[1], funcs[key][1]) for key in funcs}
    callers = defaultdict(list)
    for key, ins in bodies.items():
        for i, (at, text, note) in enumerate(ins):
            op, *args = text.split()
            if op == 'call_far':
                sg, of = args[1].split(':'); callers[(int(sg), int(of))].append((key, i))
            elif op == 'call_near':
                callers[(key[0], int(args[1]))].append((key, i))
    made = defaultdict(set)
    unresolved = []
    def resolve(key, i, which, where, depth):
        j = i - 1 - which
        src = bodies[key][j][1] if j >= 0 else ''
        op, *args = src.split() if src else ('',)
        if op == 'constint':
            made[int(args[0])].add(where); return
        if op in ('zero', 'one'):
            made[0 if op == 'zero' else 1].add(where); return
        if op == 'getint' and args[0].startswith('stack[') and depth < 6:
            off = int(args[0][6:-1])
            if off >= 8:
                for ck, ci in callers.get(key, []):
                    resolve(ck, ci, (off - 8) // 2, where, depth + 1)
                return
        unresolved.append(f'{where}: {src}')
    for key, ins in bodies.items():
        for i, (at, text, note) in enumerate(ins):
            t = text.split()
            if t[0] in ('ccall', 'ccall_v') and t[2] == 'scriptMakeObject':
                resolve(key, i, 0, f'{key[0]}:{funcs[key][0]}', 0)
            elif t[0] in ('call_member', 'call_member_v') and t[1] == '1' and t[2] == '10':
                # slot 10 = scriptActorSetProto: l'oggetto cambia prototipo (stati di un oggetto)
                resolve(key, i, 0, f'{key[0]}:{funcs[key][0]} (SetProto)', 0)
    out = []
    lost = []
    for p, (ctype, script, ni) in enumerate(protos):
        n = names.get(ni, '?')
        w, c = world.get(p, 0), made.get(p, set())
        state = 'nel mondo' if w else ('creato dagli script' if c else 'IRRAGGIUNGIBILE')
        if not w and not c: lost.append((p, n))
        out.append(f'{p:4d}  {n:32s} {state:20s} nel mondo={w:4d}  creato in: {", ".join(sorted(c)[:3])}')
    with open(outp, 'w', encoding='utf-8') as f:
        f.write(f'# {len(protos)} prototipi di oggetto; {len(lost)} né nel mondo né creati dagli script\n')
        f.write(f'# chiamate a scriptMakeObject con prototipo non risolto: {len(unresolved)}\n')
        for u in unresolved: f.write(f'#   {u}\n')
        f.write('\n'.join(out) + '\n')
    print(len(protos), 'prototipi;', len(lost), 'irraggiungibili;', len(unresolved), 'non risolti')

if __name__ == '__main__':
    main()
