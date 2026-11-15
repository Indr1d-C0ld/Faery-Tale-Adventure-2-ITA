# Strumenti per FTA2

Tutti gli strumenti sono script Python. Si eseguono dalla cartella del progetto con `python3 -I`.
Il formato dei dati viene dal motore `saga2` di ScummVM (`scummvm/engines/saga2`).

| Strumento | Cosa fa |
|---|---|
| `hreslib.py` | Libreria di lettura degli archivi HRES (gruppi e voci) |
| `hres.py FILE [profondità]` | Elenca il contenuto di un archivio |
| `hreswrite.py ORIG COPIA` | Ricostruisce un archivio. Come libreria, `rewrite(src, dst, {(gruppo, indice): byte})` sostituisce risorse anche di dimensione diversa |
| `sagadis.py SCRIPTS.HRS DIR` | Disassembla tutti i moduli di script in `DIR/modNNN.asm`, più `xref_stringhe.tsv` |
| `sagaasm.py FILE.asm OUT` | Assembla un listato. `--verifica SCRIPTS.HRS DIR` riassembla tutti i moduli e li confronta |
| `stringhe.py` | Legge e ricostruisce le tabelle di stringhe degli script e la tabella `NAME` |
| `estrai_testi.py SCRIPTS.HRS FTAVOICE.HRS OUT.tsv` | Tabella di tutti i testi degli script, con tipo, voce e funzioni che li usano |
| `estrai_nomi.py FTA.HRS OUT.tsv` | Nomi di oggetti e personaggi |
| `estrai_immagini.py FTAIMAGE.HRS DIR` | Immagini dell'interfaccia in PNG (sprite, tile e pose esclusi) |
| `costruisci.py` | Costruisce gli archivi del restauro in `build/`, a cui puntano i collegamenti in `gioco/`. Legge le patch di `patch/`: listati degli script, esportazioni, nomi, prototipi e oggetti nuovi, byte da cambiare. Il formato è descritto in testa al file |
| `traduzione.py prepara\|blocchi N\|unisci\|stato` | Traduzione italiana: estrae i testi inglesi da `build/*_en.hrs` in `traduzione/testi.tsv` e `traduzione/nomi.tsv`, li divide in blocchi, unisce i blocchi tradotti con controlli automatici (segnaposto, a capo, pulsanti `@`, Latin-1, lunghezza) |
| `impagina.py` | Simula l'impaginazione dei libri (font Script10) e segnala le righe italiane che escono dalla colonna |
| `collaudo.sh [asan\|normale] [fotogrammi]` | Collaudo automatico in gioco. Esegue gli scenari del modulo `engines/saga2/collaudo.cpp` (quest, salvataggio, giri nel mondo) e scrive `prove/collaudo/RAPPORTO.txt` |
| `trova_font.py EXE` | Cerca i font SAGA2 dentro un eseguibile |
| `cfunc_*.txt`, `vtable_member.tsv` | Nomi delle funzioni C del motore chiamabili dagli script, presi da `sagafunc.cpp` di ScummVM |

## Verifiche fatte (15/11/2026)

- **Archivi:** `hreswrite.py` ricostruisce identici bit per bit tutti e sei i `.HRS`.
- **Script:** `sagaasm.py --verifica` riassembla identici tutti i 161 moduli (1.062 funzioni).
- **Tabelle di stringhe:** le 161 tabelle degli script si ricostruiscono identiche. `NAME` ha lo
  stesso contenuto, ma nell'originale i byte di riempimento non sono inizializzati.
- **Modifica nel gioco:** ho cambiato il nome di Julian sia in `NAME` sia nello script, ho
  ricostruito gli archivi e ScummVM mostra il nome nuovo al passaggio del mouse
  (`prove/prova_modifica_nome.png`).

## Formato degli script SAGA

- **Moduli:** ogni modulo di codice è una voce del gruppo `SAGA` di `SCRIPTS.HRS`. Il numero di
  segmento usato dal bytecode è l'indice della voce nel gruppo. L'intestazione è
  `word 1, word risorsa_stringhe, word offset_stringhe`.
- **Funzioni:** ogni funzione è preceduta dal suo nome e da un byte con la lunghezza del nome,
  e comincia con `enter`.
- **Tabella di stringhe:** `word 1`, poi gli offset `uint16` relativi alla posizione 2, poi le
  stringhe Latin-1 terminate da zero.
- **Battute parlate:** `strlit testo`, `strlit "F097"`, `ccall 1 scriptResID`, flag, poi
  `call_member_v 3 ...`. Il tag della voce, qui `F097`, è il nome del campione nel gruppo
  `TALK` di `FTAVOICE.HRS`.
- **Esportazioni:** `__DA` è il segmento dati globale, `_EXP` la tabella delle esportazioni.
  Ogni voce della tabella occupa 4 byte, `segmento:offset`, all'offset `4·n − 2`.
- **Puntatore alle tabelle:** nei 4 byte che precedono la directory principale c'è l'offset della
  prima tabella dei gruppi. ScummVM lo usa per caricare le tabelle.

## Scrivere codice nuovo per gli script

`sagaasm.py` accetta, oltre alla sintassi del disassemblatore:
- **etichette:** `@nome:` definisce un'etichetta; `@nome` vale come offset in salti, `call_near`,
  `call_far SEG:@nome`, casi dei `jmp_switch`, `.word` e righe `.data`;
- **`.word A B ...`:** parole a 16 bit, comode per scrivere vtable ed esportazioni;
- **`strlit "testo"`:** una stringa nuova. `costruisci.py` la accoda alla tabella di stringhe del
  modulo.

Il codice nuovo va in coda al modulo, così nessun offset originale si sposta. Per far usare il
codice nuovo a una classe esistente si cambia la voce della sua vtable in `.data` con
`@etichetta`. Per un personaggio solo si copia la vtable della sua classe in coda al modulo, si
aggiunge un'esportazione in `patch/esportazioni.tsv` e si cambia lo script nel suo record `ACTO`.

**Attenzione a `this`:** nei metodi, `this` non appartiene al thread. È un argomento nascosto che
`call_member` spinge sullo stack: segmento in `stack[8]`, indice in `stack[10]`. Una funzione che
usa `this[...]`, richiamata con `call_near` o `call_far`, deve riceverlo esplicitamente:
`getint stack[10]`, `getint stack[8]`, poi `call_near 2+N ...`. Gli argomenti veri seguono, da
`stack[12]`.

**Byte liberi nel segmento dati `__DA`:** la zona 4854–5099 non è mai usata dagli script
originali, e il restauro la usa a partire da 5000 (vedi `patch/script/mod020.asm`). Il segmento non
va ingrandito: i salvataggi ne contengono una copia della dimensione originale.

## Traduzione

1. `costruisci.py` scrive gli archivi inglesi con le patch: `build/scripts_en.hrs` e
   `build/fta_en.hrs`.
2. `traduzione.py prepara` aggiorna `traduzione/testi.tsv` e `traduzione/nomi.tsv` e conserva le
   traduzioni esistenti la cui stringa inglese non è cambiata.
   - Conserva anche le righe tradotte che l'estrazione non trova più ma che esistono ancora
     identiche nell'archivio.
   - Capita alle funzioni originali che una patch raggiunge con un salto, come `sayNumber`:
     seguendo il flusso, il disassemblatore non arriva più al resto del corpo.
3. Si traduce, per blocchi (`traduzione.py blocchi`, poi `unisci`) oppure correggendo
   direttamente la colonna `italiano` di `testi.tsv`.
   - `unisci` non sovrascrive le righe già tradotte, a meno di usare `--forza`.
   - `<vuota>` indica una traduzione volutamente vuota.
4. `costruisci.py` applica le traduzioni e scrive `build/scripts.hrs` e `build/fta.hrs`.

Regole e glossario sono in `traduzione/GUIDA.md`. Le scritte del motore (interfaccia, stati,
mappa) sono tradotte direttamente nei sorgenti di ScummVM (`localize.h`, `uitext.h`,
`mapfeatr.cpp`).

## Collaudo

`tools/collaudo.sh asan` usa `build-asan/scummvm` (AddressSanitizer, va ricompilata con
`make -j20` dentro `build-asan/` dopo ogni modifica al motore). Senza argomenti usa la build
normale. Gli scenari stanno nel motore, in `engines/saga2/collaudo.cpp`, e si attivano solo se la
configurazione contiene `melchior_collaudo`, che lo script scrive in una configurazione a parte:
il gioco normale non ne è toccato.

- **quest** (dalla partita nuova, slot 100), 22 controlli:
  - collocazione di Corona e Scettro e classi nuove di Brythe e Wort;
  - Globo colpito e quest completa della Regalia, con pergamene e oro;
  - flauto e topi, ricompensa di Wort data una volta sola;
  - immunità di Rallo, attacchi speciali di Krogatt, cuore di Roska prima e dopo la sua morte;
  - incantesimo 36 risolto come incantesimo;
  - contenitori abbandonati pieni conservati e vuoti eliminati;
  - alla fine salva nello slot 97.
- **salva** (slot 97): persistenza di globali, pergamene, immunità e classi nuove.
- **giro** (ogni salvataggio d'epoca e la partita nuova): salti casuali nel mondo per N
  fotogrammi, alla ricerca di crash ed errori di memoria.
