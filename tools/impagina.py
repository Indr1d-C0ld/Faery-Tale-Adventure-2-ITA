#!/usr/bin/env python3
"""Simula l'impaginazione dei libri del gioco (font Script10, colonne di 131/135/149 pixel) e
confronta inglese e italiano.

Uso:
  impagina.py [LARGHEZZA RIGHE_PER_PAGINA]           riepilogo per libro
  impagina.py LARGHEZZA RIGHE elenco                 righe brevi che in italiano vanno a capo,
                                                     con la larghezza reale del documento
La larghezza di ogni testo (pergamena, libro o carta) è in traduzione/larghezze_documenti.json.
"""
import struct,sys,re
sys.path.insert(0,'tools')
from traduzione import decodifica
d=open('gioco/fta2.exe','rb').read()
o=0x216C78  # Script10
h,b,rm=struct.unpack_from('<HHH',d,o)
kern=struct.unpack_from('<256b',d,o+6+512+256); space=struct.unpack_from('<256b',d,o+6+512+512)
cw=lambda c: kern[c]+space[c]
def wrap(text,W):
    """righe come GTextWrap: a capo esplicito o per parole."""
    lines=[]
    for para in text.split('\n'):
        words=para.split(' '); cur=''; 
        for w in words:
            t=(cur+' '+w) if cur else w
            if sum(cw(c) for c in t.encode('latin-1','replace'))>W and cur:
                lines.append((cur,True)); cur=w
            else: cur=t
        lines.append((cur,False))
    return lines
rows=[l.rstrip('\n').split('\t') for l in open('traduzione/testi.tsv',encoding='utf-8')][1:]
libri={}
for r in rows:
    if len(r)<6 or r[1]!='testo': continue
    for u in r[3].split(','):
        fn=u.split(':')[1]
        if fn.endswith('Text') or fn.endswith('Text2'):
            libri.setdefault(u,[]).append(r)
W=int(sys.argv[1]) if len(sys.argv)>1 else 131; LPP=int(sys.argv[2]) if len(sys.argv)>2 else 15
out=[]
for k,rs in libri.items():
    rs.sort(key=lambda r:int(r[0].split(':')[2]))
    en=''.join(decodifica(r[4]) for r in rs); it=''.join(decodifica(r[5]) if r[5]!='<vuota>' else '' for r in rs)
    le=wrap(en,W); li=wrap(it,W)
    pe=-(-len(le)//LPP); pi=-(-len(li)//LPP)
    # righe brevi volute (paragrafi che in inglese stanno in una riga) e che in italiano vanno a capo
    pe_par=[p for p in en.split('\n')]; pi_par=[p for p in it.split('\n')]
    rotte=0
    for a,b2 in zip(pe_par,pi_par):
        if len(wrap(a,W))==1 and len(wrap(b2,W))>1 and len(a)<40: rotte+=1
    out.append((k,len(en),len(it),pe,pi,rotte))
out.sort(key=lambda x:(-x[5],-x[4]))
print(f'larghezza {W}, righe per pagina {LPP}: {len(out)} libri')
print('oltre 32 pagine:',[x for x in out if x[4]>32])
print('libri con righe brevi spezzate (righe):')
for x in out[:25]:
    if x[5]: print(f'  {x[0]:32s} car {x[1]}->{x[2]} pagine {x[3]}->{x[4]} righe spezzate {x[5]}')

import json
LARG=json.load(open('traduzione/larghezze_documenti.json'))
if len(sys.argv)>3 and sys.argv[3]=='elenco':
    pw=lambda s: sum(cw(c) for c in s.encode('latin-1','replace'))
    for k,rs in libri.items():
        W=LARG.get(k,131)
        for r in rs:
            if r[5]=='<vuota>': continue
            ep=decodifica(r[4]).split('\n'); ip=decodifica(r[5]).split('\n')
            for j,(a,b2) in enumerate(zip(ep,ip)):
                if len(wrap(a,W))==1 and len(wrap(b2,W))>1 and len(a)<40:
                    print(f'{k}\t{W}\t{r[0]}\t{j}\t{pw(a)}\t{pw(b2)}\t{a!r}\t{b2!r}')
