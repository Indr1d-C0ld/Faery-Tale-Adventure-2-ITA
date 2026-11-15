#!/usr/bin/env python3
"""Disassemblatore degli script SAGA2 di Faery Tale Adventure II (SCRIPTS.HRS).

Uso:
  sagadis.py SCRIPTS.HRS OUTDIR

Scrive in OUTDIR un file .asm per ogni modulo di codice. Ogni stringa letterale è annotata con il
testo e ogni chiamata C con il nome della funzione del motore (tabelle prese da ScummVM).
Il formato del bytecode viene da engines/saga2/interp.cpp e code.h di ScummVM.
"""
import os, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hreslib import HRes, tagstr

OPS = ['undefined', 'nextblock', 'dup', 'drop', 'zero', 'one', 'constint', 'constid', 'strlit', 'sym',
       'symref', 'classref', 'deref', 'getflag', 'getbyte', 'getint', 'getstr', 'getid', 'putflag',
       'putbyte', 'putint', 'putstr', 'putid', 'pea', 'putflag_v', 'putbyte_v', 'putint_v', 'putstr_v',
       'putid_v', 'call_near', 'call_far', 'ccall', 'ccall_v', 'call_member', 'call_member_v', 'enter',
       'return', 'return_v', 'jmp', 'jmp_true_v', 'jmp_false_v', 'jmp_true', 'jmp_false', 'jmp_switch',
       'jmp_strswitch', 'jmp_random', 'negate', 'not', 'compl', 'inc_v', 'dec_v', 'postinc', 'postdec',
       'add', 'sub', 'mul', 'div', 'mod', 'conditional', 'comma', 'eq', 'ne', 'gt', 'lt', 'ge', 'le',
       'str_eq', 'str_ne', 'str_gt', 'str_lt', 'str_ge', 'str_le', 'rsh', 'lsh', 'and', 'or', 'xor',
       'land', 'lor', 'lxor', 'strcat', 'strformat', 'assign', 'asplus', 'asminus', 'astimes', 'asdiv',
       'asmod', 'asrshift', 'aslshift', 'asand', 'asor', 'speak', 'dialog_begin', 'dialog_end', 'reply',
       'animate', 'jmp_seedrandom', 'symref_x']
OP = {n: i for i, n in enumerate(OPS)}
ADDR_OPS = {OP[n] for n in ('getflag', 'getbyte', 'getint', 'getstr', 'getid', 'putflag', 'putbyte',
            'putint', 'putstr', 'putid', 'pea', 'putflag_v', 'putbyte_v', 'putint_v', 'putstr_v',
            'putid_v', 'inc_v', 'dec_v', 'postinc', 'postdec')}
NOARG = {OP[n] for n in ('nextblock', 'dup', 'drop', 'zero', 'one', 'return', 'return_v', 'negate', 'not',
         'compl', 'add', 'sub', 'mul', 'div', 'mod', 'eq', 'ne', 'gt', 'lt', 'ge', 'le', 'rsh', 'lsh',
         'and', 'or', 'xor', 'land', 'lor', 'lxor')}
JUMPS = {OP[n] for n in ('jmp', 'jmp_true_v', 'jmp_false_v', 'jmp_true', 'jmp_false')}
TERMINAL = {OP['return'], OP['return_v'], OP['jmp'], OP['jmp_switch'], OP['jmp_random']}
BUILTIN = {0xffff: 'GameObject', 0xfffe: 'TAG', 0xfffd: 'Abstract', 0xfffc: 'Mission'}

def load_names(kind):
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), f'cfunc_{kind}.txt')
    return [l.strip() for l in open(p) if l.strip()]

CF = {k: load_names(k) for k in ('global', 'actor', 'tag', 'mission')}

def load_slots():
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vtable_member.tsv')
    out = {}
    if os.path.exists(p):
        for l in open(p):
            if l.startswith('#') or not l.strip(): continue
            i, _, name = l.rstrip('\n').split('\t')
            out[int(i)] = name
    return out

SLOTS = load_slots()

class Bad(Exception):
    pass

def w16(d, p):
    if p + 2 > len(d): raise Bad('fine del segmento')
    return struct.unpack_from('<H', d, p)[0]

def segname(s):
    return BUILTIN.get(s, str(s))

def read_addr(d, p):
    """Decodifica un modo di indirizzamento. Restituisce (testo, nuova posizione, segmento|None)."""
    m = d[p]; p += 1
    if m == 0: return f'thread[{w16(d, p)}]', p + 2, None
    if m == 1: return f'stack[{struct.unpack_from("<h", d, p)[0]}]', p + 2, None
    if m == 2: return f'near[{w16(d, p)}]', p + 2, None
    if m == 3: return f'data[{w16(d, p)}]', p + 2, None
    if m == 4: return f'far[{segname(w16(d, p))}:{w16(d, p + 2)}]', p + 4, w16(d, p)
    if m == 5: return f'array[{segname(w16(d, p))}:{w16(d, p + 2)}:{w16(d, p + 4)}]', p + 6, w16(d, p)
    if m == 6:
        inner, p, _ = read_addr(d, p)
        return f'deref[{inner} -> {segname(w16(d, p))}:{w16(d, p + 2)}]', p + 4, w16(d, p)
    if m == 7: return f'this[{w16(d, p)}]', p + 2, None
    raise Bad(f'modo di indirizzamento {m}')

def find_functions(d):
    """Le funzioni iniziano con: nome, byte di lunghezza del nome, opcode enter."""
    funcs = []
    for p in range(7, len(d) - 2):
        if d[p] == OP['enter']:
            n = d[p - 1]
            if 1 <= n <= 64 and p - 1 - n >= 6:
                name = d[p - 1 - n:p - 1]
                if all(48 <= c < 123 and (chr(c).isalnum() or c == 95) for c in name) and chr(name[0]).isalpha():
                    if p + 3 <= len(d) and struct.unpack_from('<H', d, p + 1)[0] < 2048:
                        funcs.append((p, name.decode('ascii'), p - 1 - n))
    return funcs

class Module:
    def __init__(self, g, idx):
        self.g, self.idx = g, idx
        self.d = g.read_index(idx)
        self.strres, self.stroff = struct.unpack_from('<HH', self.d, 2)
        self._strings = None

    def strings(self):
        if self._strings is None:
            sd = self.g.read_index(self.strres)
            base = self.stroff
            if base + 2 > len(sd):
                self._strings = []
                return self._strings
            first = struct.unpack_from('<H', sd, base)[0]
            n = first // 2
            out = []
            for i in range(n):
                o = struct.unpack_from('<H', sd, base + 2 * i)[0]
                e = sd.index(b'\0', base + o)
                out.append(sd[base + o:e].decode('latin-1'))
            self._strings = out
        return self._strings

    def string(self, i):
        s = self.strings()
        return s[i] if 0 <= i < len(s) else None

def cname(f):
    """Nome di una funzione C globale; i nomi presenti due volte nella tabella prendono @indice."""
    names = CF['global']
    if f >= len(names): return f'#{f}'
    n = names[f]
    return n if names.count(n) == 1 else f'{n}@{f}'

def decode(m, at, xref):
    """Decodifica un'istruzione nella sintassi canonica (riassemblabile da sagaasm.py).
    Restituisce (testo, nota, posizione successiva, destinazioni, termina)."""
    d = m.d
    p = at
    op = d[p]; p += 1
    name = OPS[op] if op < len(OPS) else f'op_{op}'
    arg = note = ''
    targets = []
    if op in NOARG:
        pass
    elif op in (OP['constint'], OP['constid']):
        v = w16(d, p); p += 2; arg = f'{struct.unpack("<h", struct.pack("<H", v))[0]}'
    elif op == OP['strlit']:
        v = w16(d, p); p += 2; arg = f'#{v}'
        s = m.string(v)
        note = repr(s) if s is not None else '?? stringa fuori tabella'
        xref.append((m.strres, m.stroff, v, m.idx, at))
    elif op in ADDR_OPS or op == OP['symref_x']:
        arg, p, _ = read_addr(d, p)
    elif op == OP['enter']:
        arg = f'{w16(d, p)}'; p += 2
    elif op == OP['call_near']:
        arg = f'{d[p]} {w16(d, p + 1)}'; p += 3
    elif op == OP['call_far']:
        arg = f'{d[p]} {w16(d, p + 1)}:{w16(d, p + 3)}'; p += 5
    elif op in (OP['ccall'], OP['ccall_v']):
        n, f = d[p], w16(d, p + 1); p += 3
        arg = f'{n} {cname(f)}'
    elif op in (OP['call_member'], OP['call_member_v']):
        n, idx = d[p], d[p + 1]; p += 2
        a, p, seg = read_addr(d, p)
        arg = f'{n} {idx} {a}'
        if seg == 0xffff and idx in SLOTS:
            note = SLOTS[idx]
    elif op in JUMPS:
        t = w16(d, p); p += 2; arg = f'{t}'; targets.append(t)
    elif op == OP['jmp_switch']:
        n = w16(d, p); p += 2
        cases = []
        for _ in range(n):
            cases.append(f'{w16(d, p)}:{w16(d, p + 2)}'); targets.append(w16(d, p + 2)); p += 4
        dflt = w16(d, p); p += 2
        targets.append(dflt)
        rows = [' '.join(cases[i:i + 8]) for i in range(0, len(cases), 8)]
        arg = f'{dflt}' + ''.join('\n' + ' ' * 9 + '+ ' + r for r in rows)
    elif op in (OP['jmp_random'], OP['jmp_seedrandom']):
        pre = ''
        if op == OP['jmp_seedrandom']:
            pre = f'{w16(d, p)} '; p += 2
        n = w16(d, p); tot = w16(d, p + 2); p += 4
        cases = []
        for _ in range(n):
            cases.append(f'{w16(d, p)}:{w16(d, p + 2)}'); targets.append(w16(d, p + 2)); p += 4
        arg = f'{pre}{tot} ' + ' '.join(cases)
    else:
        raise Bad(f'opcode sconosciuto {op} a {at} (byte {d[at:at + 8].hex()})')
    return f'{name:14s} {arg}'.rstrip(), note, p, targets, op in TERMINAL

def data_lines(d, a, b):
    return [f'{q:7d}  .data {d[q:min(q + 16, b)].hex(" ")}' for q in range(a, b, 16)]

def disasm_func(m, start, end, out, xref):
    """Disassembla seguendo il flusso di controllo: i byte non raggiungibili sono dati."""
    ins = {}
    work = [start]
    ok = True
    while work:
        at = work.pop()
        while start <= at < end and at not in ins:
            try:
                text, note, nxt, targets, term = decode(m, at, xref)
            except (Bad, IndexError) as e:
                out.append(f'; !! {e}'); ok = False
                break
            if nxt > end:
                break
            ins[at] = (text, note, nxt)
            work.extend(t for t in targets if start <= t < end)
            if term:
                break
            at = nxt
    # istruzioni sovrapposte (salti dentro un'istruzione): si tengono solo quelle non sovrapposte
    p = start
    for at in sorted(ins):
        if at < p:
            continue
        if at > p:
            out.extend(data_lines(m.d, p, at))
        text, note, nxt = ins[at]
        line = f'{at:7d}  {text}'
        if note:
            first, *rest = line.split('\n')
            line = '\n'.join([f'{first:64s} ; {note}'] + rest)
        out.append(line)
        p = nxt
    if p < end:
        out.extend(data_lines(m.d, p, end))
    return ok

def disasm_module(m, xref=None):
    """Listato completo di un modulo: copre ogni byte, quindi si riassembla identico."""
    xref = [] if xref is None else xref
    funcs = find_functions(m.d)
    out = [f'; modulo {m.idx} ({tagstr(m.g.entries[m.idx][0])}), {len(m.d)} byte, '
           f'stringhe in risorsa {m.strres}+{m.stroff} ({len(m.strings())} stringhe)',
           f'.module {m.idx}']
    first = funcs[0][2] if funcs else len(m.d)
    out.extend(data_lines(m.d, 0, first))
    ok = True
    for k, (p, name, nstart) in enumerate(funcs):
        end = funcs[k + 1][2] if k + 1 < len(funcs) else len(m.d)
        out.append('')
        out.append(f'{nstart:7d}  .func {name}')
        ok &= disasm_func(m, p, end, out, xref)
    return out, len(funcs), ok

def main():
    src, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    h = HRes(src)
    g = h.group('SAGA')
    special = {g.index_of(b'__DA'), g.index_of(b'_EXP')}
    stats = {'moduli': 0, 'funzioni': 0, 'errori': 0, 'stringhe_usate': 0}
    xref = []
    for idx in range(len(g.entries)):
        if idx in special or g.entries[idx][2] < 8: continue
        m = Module(g, idx)
        if not find_functions(m.d): continue
        out, nf, ok = disasm_module(m, xref)
        stats['moduli'] += 1
        stats['funzioni'] += nf
        stats['errori'] += 0 if ok else 1
        open(os.path.join(outdir, f'mod{idx:03d}.asm'), 'w').write('\n'.join(out) + '\n')
    stats['stringhe_usate'] = len(xref)
    with open(os.path.join(outdir, 'xref_stringhe.tsv'), 'w') as f:
        f.write('risorsa\toffset\tnumero\tmodulo\tposizione\n')
        for r in xref: f.write('\t'.join(map(str, r)) + '\n')
    print(stats)

if __name__ == '__main__':
    main()
