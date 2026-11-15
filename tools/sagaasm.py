#!/usr/bin/env python3
"""Assemblatore degli script SAGA2 di FTA2: il percorso inverso di sagadis.py.

Uso:
  sagaasm.py FILE.asm OUT.bin            assembla un listato
  sagaasm.py --verifica SCRIPTS.HRS DIR   riassembla tutti i listati di DIR e li confronta con gli originali

Sintassi (una istruzione per riga, il ';' apre un commento):
  [offset]  .module N           numero del modulo (informativo)
  [offset]  .func Nome          nome della funzione: emette il nome e il byte di lunghezza
  [offset]  .data 01 02 ff      byte grezzi
  [offset]  .org N              riempie di zeri fino all'offset N (per le patch in coda al modulo)
  [offset]  opcode operandi     vedi sagadis.decode per il formato di ogni opcode
            + v:o v:o ...       continuazione dei casi di jmp_switch
L'offset iniziale di ogni riga è facoltativo. Se c'è, l'assemblatore controlla che corrisponda
alla posizione corrente: è il modo per accorgersi di uno spostamento non voluto.
"""
import os, re, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sagadis as sd

SEGS = {v: k for k, v in sd.BUILTIN.items()}
LAST_LABELS = {}

class AsmError(Exception):
    pass

def seg(s):
    return SEGS[s] if s in SEGS else int(s)

def u16(v):
    v = int(v)
    if not -32768 <= v <= 65535: raise AsmError(f'valore fuori 16 bit: {v}')
    return struct.pack('<H', v & 0xffff)

def addr(s):
    s = s.strip()
    m = re.fullmatch(r'(\w+)\[(.*)\]', s)
    if not m: raise AsmError(f'indirizzo non valido: {s}')
    kind, inner = m.groups()
    if kind == 'thread': return bytes([0]) + u16(inner)
    if kind == 'stack': return bytes([1]) + u16(inner)
    if kind == 'near': return bytes([2]) + u16(inner)
    if kind == 'data': return bytes([3]) + u16(inner)
    if kind == 'this': return bytes([7]) + u16(inner)
    if kind == 'far':
        a, b = inner.split(':'); return bytes([4]) + u16(seg(a)) + u16(b)
    if kind == 'array':
        a, b, c = inner.split(':'); return bytes([5]) + u16(seg(a)) + u16(b) + u16(c)
    if kind == 'deref':
        i = inner.rindex('->')
        a, b = inner[i + 2:].strip().split(':')
        return bytes([6]) + addr(inner[:i]) + u16(seg(a)) + u16(b)
    raise AsmError(f'modo di indirizzamento sconosciuto: {kind}')

def cfunc(s):
    if s.startswith('#'): return int(s[1:])
    if '@' in s: return int(s.split('@')[1])
    names = sd.CF['global']
    if s not in names: raise AsmError(f'funzione C sconosciuta: {s}')
    return names.index(s)

def pairs(items):
    out = b''
    for it in items:
        a, b = it.split(':'); out += u16(a) + u16(b)
    return out

def instr(op, args, extra):
    o = sd.OP.get(op)
    if o is None: raise AsmError(f'opcode sconosciuto: {op}')
    b = bytes([o])
    if o in sd.NOARG: return b
    if o in (sd.OP['constint'], sd.OP['constid']): return b + u16(args[0])
    if o == sd.OP['strlit']: return b + u16(args[0].lstrip('#'))
    if o in sd.ADDR_OPS or o == sd.OP['symref_x']: return b + addr(' '.join(args))
    if o == sd.OP['enter']: return b + u16(args[0])
    if o == sd.OP['call_near']: return b + bytes([int(args[0])]) + u16(args[1])
    if o == sd.OP['call_far']:
        a, c = args[1].split(':'); return b + bytes([int(args[0])]) + u16(a) + u16(c)
    if o in (sd.OP['ccall'], sd.OP['ccall_v']): return b + bytes([int(args[0])]) + u16(cfunc(args[1]))
    if o in (sd.OP['call_member'], sd.OP['call_member_v']):
        return b + bytes([int(args[0]), int(args[1])]) + addr(' '.join(args[2:]))
    if o in sd.JUMPS: return b + u16(args[0])
    if o == sd.OP['jmp_switch']:
        cases = args[1:] + extra
        return b + u16(len(cases)) + pairs(cases) + u16(args[0])
    if o == sd.OP['jmp_random']:
        cases = args[1:]
        return b + u16(len(cases)) + u16(args[0]) + pairs(cases)
    if o == sd.OP['jmp_seedrandom']:
        cases = args[2:]
        return b + u16(args[0]) + u16(len(cases)) + u16(args[1]) + pairs(cases)
    raise AsmError(f'opcode non assemblabile: {op}')

def _split_args(raw):
    """Divide una riga in token, tenendo insieme le stringhe fra virgolette."""
    out, cur, q = [], '', False
    i = 0
    while i < len(raw):
        ch = raw[i]
        if q:
            cur += ch
            if ch == '\\' and i + 1 < len(raw):
                cur += raw[i + 1]; i += 1
            elif ch == '"':
                q = False
        elif ch == '"':
            q = True; cur += ch
        elif ch.isspace():
            if cur: out.append(cur); cur = ''
        else:
            cur += ch
        i += 1
    if cur: out.append(cur)
    return out

def _strip_comment(line):
    """Toglie il commento ';' che non sta dentro una stringa."""
    q = False
    for i, ch in enumerate(line):
        if ch == '"' and (i == 0 or line[i - 1] != '\\'): q = not q
        elif ch == ';' and not q: return line[:i]
    return line

def _unquote(tok):
    body = tok[1:-1]
    return body.encode('latin-1').decode('unicode_escape').encode('latin-1')

def assemble(text, check=True, nstr=None):
    """Assembla un listato.

    Estensioni per il codice nuovo:
      @nome:              definisce un'etichetta nella posizione corrente
      @nome negli operandi  è sostituito dall'offset dell'etichetta (salti, call_near,
                          call_far SEG:@nome, casi v:@nome, .word)
      .word A B ...       parole a 16 bit (numeri o etichette)
      strlit "testo"      stringa nuova, accodata alla tabella del modulo: richiede nstr
                          (numero di stringhe esistenti) e allora si restituisce
                          (byte, [stringhe nuove])
    """
    lines = text.split('\n')
    labels = {}
    new_strings = []

    def resolve(tok, final):
        def rep(m):
            name = m.group(1)
            if name in labels: return str(labels[name])
            if final: raise AsmError(f'etichetta sconosciuta: @{name}')
            return '0'
        return re.sub(r'@([A-Za-z_][A-Za-z0-9_]*)', rep, tok)

    def one_pass(final):
        out = bytearray()
        new_strings.clear()
        i = 0
        while i < len(lines):
            raw = _strip_comment(lines[i]).rstrip()
            i += 1
            if not raw.strip(): continue
            toks = _split_args(raw)
            off = None
            if toks[0].lstrip('-').isdigit():
                off = int(toks[0]); toks = toks[1:]
            if not toks: continue
            if check and off is not None and off != len(out):
                raise AsmError(f'riga {i}: offset {off} atteso, posizione reale {len(out)}')
            if re.fullmatch(r'@[A-Za-z_][A-Za-z0-9_]*:', toks[0]):
                name = toks[0][1:-1]
                if not final and name in labels and labels[name] != len(out) and labels.get('__pass') == 1:
                    raise AsmError(f'etichetta doppia: {name}')
                labels[name] = len(out)
                toks = toks[1:]
                if not toks: continue
            op, args = toks[0], toks[1:]
            extra = []
            while i < len(lines) and _strip_comment(lines[i]).strip().startswith('+'):
                extra += _strip_comment(lines[i]).strip()[1:].split(); i += 1
            try:
                if op == '.module': continue
                if op == '.func':
                    n = args[0].encode('ascii'); out += n + bytes([len(n)])
                elif op == '.data':
                    for x in args:
                        if x.startswith('@'): out += u16(resolve(x, final))
                        else: out += bytes([int(x, 16)])
                elif op == '.word':
                    for a in args: out += u16(resolve(a, final))
                elif op == '.org':
                    t = int(args[0])
                    if t < len(out): raise AsmError(f'.org {t} indietro (posizione {len(out)})')
                    out += b'\0' * (t - len(out))
                elif op == 'strlit' and args and args[0].startswith('"'):
                    if nstr is None: raise AsmError('stringa nuova senza nstr')
                    s_ = _unquote(' '.join(args))
                    if s_ in new_strings: idx = nstr + new_strings.index(s_)
                    else: new_strings.append(s_); idx = nstr + len(new_strings) - 1
                    out += instr('strlit', [str(idx)], [])
                else:
                    args = [resolve(a, final) for a in args]
                    extra = [resolve(a, final) for a in extra]
                    out += instr(op, args, extra)
            except (AsmError, ValueError, IndexError) as e:
                raise AsmError(f'riga {i}: {raw.strip()}: {e}')
        return out

    one_pass(False)
    out = one_pass(True)
    global LAST_LABELS
    LAST_LABELS = {k: v for k, v in labels.items() if not k.startswith('__')}
    if nstr is not None:
        return bytes(out), list(new_strings)
    return bytes(out)

def main():
    if sys.argv[1] == '--verifica':
        from hreslib import HRes
        g = HRes(sys.argv[2]).group('SAGA')
        d = sys.argv[3]
        ok = bad = 0
        for fn in sorted(os.listdir(d)):
            if not fn.endswith('.asm'): continue
            idx = int(fn[3:6])
            try:
                b = assemble(open(os.path.join(d, fn)).read())
            except AsmError as e:
                print(fn, e); bad += 1; continue
            if b == g.read_index(idx): ok += 1
            else:
                bad += 1
                orig = g.read_index(idx)
                k = next((k for k in range(min(len(b), len(orig))) if b[k] != orig[k]), min(len(b), len(orig)))
                print(f'{fn}: diverso dal byte {k} (lunghezze {len(b)} / {len(orig)})')
        print(f'moduli identici: {ok}, diversi: {bad}')
    else:
        b = assemble(open(sys.argv[1]).read())
        open(sys.argv[2], 'wb').write(b)
        print(len(b), 'byte')

if __name__ == '__main__':
    main()
