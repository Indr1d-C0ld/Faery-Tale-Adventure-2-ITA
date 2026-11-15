# Faery Tale Adventure II: Halls of the Dead (Melchior)

## Cosa c'è nella cartella

- `pre_assets/fta2/`: archivi originali (non toccarli).
- `original/HallsoftheDead/disk/FTA2/`: gioco estratto, versione DOS (DOS/4G).
- `docs/`: manuale, mappe, soluzioni, salvataggi di fine gioco, trainer.
- `tools/`: strumenti di estrazione, disassemblaggio, assemblaggio e ricostruzione
  (vedi `tools/README.md`).
- `estratti/`: testi in TSV, listati degli script (`script/modNNN.asm`), immagini in PNG.
- `gioco/`: la cartella che legge ScummVM (per ora collegamenti agli originali).

## Cosa ho scoperto

Il gioco gira sul motore **SAGA2** di The Dreamers Guild. Tutti i file `.HRS` sono archivi
`HRES` con un indice di voci a 4 caratteri, e `tools/hres.py` li legge già.

| File | Contenuto |
|---|---|
| `SCRIPTS.HRS` (1 MB) | Bytecode SAGA (`SEG`/`SEH` per segmento): logica delle quest e **tutti i dialoghi** (circa 6.500 battute, 350 KB di testo) |
| `FTA.HRS` | Database del mondo: attori, oggetti, prototipi, nomi |
| `FTADATA.HRS` | Oggetti, effetti, incantesimi, mappe automatiche |
| `FTAIMAGE.HRS` (21 MB) | Grafica: tile, sprite, volti, interfaccia, libri e pergamene, font |
| `FTASOUND.HRS` | Musica XMIDI ed effetti sonori |
| `FTAVOICE.HRS` (268 MB) | Parlato in inglese, una voce per battuta (`A001`…) |
| `FTA2.EXE` | Motore, con circa 400 messaggi di interfaccia scritti direttamente nell'eseguibile |

## Piattaforma: ScummVM (scelta del 15/11/2026)

Il gioco finale gira su una ScummVM modificata (`scummvm/`, ramo `melchior-fta2`, base v2026.4.0).
Il motore `saga2` riconosceva solo la versione Windows. Ora carica anche la DOS: font,
cursori, indicatore e tabella dei colori vengono letti da `FTA2.EXE` (gli offset sono in
`engines/saga2/saga2.cpp`). Si avvia con `./gioca.sh`.

- **Compilazione:** le intestazioni di sviluppo vengono dai pacchetti Debian estratti in
  `sysroot/`, senza sudo. Configurazione:
  `./configure --with-sdl-prefix=$S --disable-all-engines --enable-engine=saga2 --enable-release --disable-tts`,
  più `CPPFLAGS`/`LDFLAGS` verso `sysroot/usr`.
- **Mancano** i video Smacker (`TRIMARK`, `INTRO`, `END_1`, `END_2`). Stavano nella cartella
  `VIDEO` del CD e non sono in questo pacchetto: il gioco parte direttamente.
- I font hanno già i glifi Latin-1, comprese le lettere accentate. Vanno solo verificati a video.

## Piano a fasi

1. **Spacchettamento completo.** Estrarre tutte le risorse in formati leggibili: immagini in
   PNG, testi in tabelle, script disassemblati. Poi ricostruirle: prima un archivio identico
   bit per bit all'originale, poi un archivio modificato.
2. **Decompilatore e compilatore degli script SAGA.** Senza questi strumenti non si possono
   correggere le quest.
3. **Catalogo dei bug e delle quest incomplete.** Fonti: script morti o mai chiamati, battute
   orfane (voci senza dialogo che le usi), documentazione e soluzioni d'epoca, salvataggi di
   fine gioco. Ogni voce del catalogo va confermata nel codice.
4. **Correzioni.** I bug del motore si correggono in C++ in ScummVM, quelli della logica degli
   script nel bytecode. In alternativa, un aggancio nel motore può sostituire una funzione di
   script. Ghidra e REA servono per confrontare il comportamento con `FTA2.EXE`.
5. **Completamento delle quest lasciate a metà.** Prima va scritto un progetto: ricostruire
   l'intenzione originale dagli indizi rimasti nei dati, poi implementarla riusando le risorse
   esistenti.
6. **Traduzione italiana.** Il motore legge i testi da una tabella di traduzione esterna (file
   `.po`), quindi non serve ricompilare `SCRIPTS.HRS`. Vanno tradotti dialoghi, interfaccia,
   nomi degli oggetti, libri e le immagini con testo. Il parlato resta in inglese, con i
   sottotitoli in italiano.
7. **Collaudo** in ScummVM, con i salvataggi d'epoca e con partite nuove.

## Stato

### Fasi 1 e 2: fatte (15/11/2026)

- **Archivi:** i sei `.HRS` si ricostruiscono identici, anche con risorse cambiate di dimensione.
- **Script:** il disassemblatore copre 161 moduli e 1.062 funzioni, e l'assemblatore li riproduce
  identici. Il formato è descritto in `tools/README.md`.
- **Testi** (`estratti/testi_script.tsv`): 17.867 stringhe.
  - 4.786 battute parlate, ciascuna collegata al proprio campione vocale.
  - 4.897 testi mostrati: nomi, libri, cartelli, risposte dei menu di dialogo.
  - 3.398 voci interne: etichette di debug e codici, da non tradurre.
  - 4.786 tag di voce.
- **Nomi** (`estratti/nomi.tsv`): 1.153 nomi di oggetti e personaggi.
- **Immagini:** 210 immagini dell'interfaccia. L'unico testo dipinto è sulle targhette Julian,
  Phillip e Kevin, che restano invariate. Le etichette dei pulsanti le disegna il motore.
- **Prova di modifica:** un nome cambiato compare nel gioco (`prove/prova_modifica_nome.png`).

### Fase 3: catalogo in `CATALOGO.md` (15/11/2026)

La scoperta principale è un bug sistemico di ScummVM: il segmento dati degli script esiste in
due copie (A3). Rompe Navis e Muybridge, Timequake e altri tre meccanismi. Gli altri risultati:
contenuti doppiati ma irraggiungibili, 15 pacchetti di dialogo mai assegnati e personaggi
senza dialogo. Ci sono anche quest confermate come incomplete: Pentere, Darnoc, il cuore di
Roska, il flauto.

### Fase 4: correzioni (in corso)

- **A3, fatta il 15/11/2026.** Commit `b866e146` nel ramo `melchior-fta2` di `scummvm/`. Ora
  `segmentAddress` e `segmentArrayAddress` restituiscono, per il segmento 130 (`__DA`), lo stesso
  buffer usato da `data[]` e salvato con la partita. L'aggiramento cablato di Navis è stato tolto.
  - Verificato: all'avvio l'indice del segmento vale 130 e i salvataggi d'epoca 000, 004, 006 e
    009 (`prove/salvataggi/`) si caricano e girano.
  - Non riprodotti in gioco: gli eventi A3a–A3e.
- **A1 e A2, chiuse senza modifiche il 15/11/2026.** Sono le uniche due voci mancanti negli script ed entrambe appartengono a Galchmay. `I194` non è la voce di Galchmay ma di un abitante di Bilton (confronto acustico). Il motore mostra già queste battute come solo testo.
- **B1, fatta il 15/11/2026.** Krogatt ora usa in combattimento anche le sue battute cannibali (4 byte in `mod200`).
  - Le patch agli script stanno in `patch/script/modNNN.asm`.
  - `python3 -I tools/costruisci.py` le assembla in `build/scripts.hrs`, e `gioco/scripts.hrs` punta lì.
- **D1, fatta il 15/11/2026.** Commit `02d57f43`: le stelle del mana restano nell'indicatore anche sopra 200.
- **A4, fatta il 15/11/2026.** Rallo Jovanc non può più morire e la quest dell'orsacchiotto resta completabile.
  - Le patch ai dati stanno in `patch/dati.tsv` (archivio, gruppo, voce, offset, byte originali e nuovi). `tools/costruisci.py` controlla i byte originali prima di scrivere.
  - Commit del motore `1d93384a`: al caricamento le immunità del prototipo si uniscono a quelle salvate.
- **D8, fatta il 15/11/2026.** Commit `e95069c9`: i contenitori pieni abbandonati non vengono più eliminati.
- **D6 e D9, verificate il 15/11/2026:** sono comportamenti voluti, senza correzione.
- **A5, fatta il 15/11/2026.** Il crash nell'oltretomba si riproduceva in ScummVM ed era nella conversione degli ID degli incantesimi (commit `fa4fc360`). C'è anche un controllo del null in più (`ddc98012`).
  - Per la diagnosi c'è `build-asan/`, una build di ScummVM con AddressSanitizer e simboli di debug. Si aggiorna con `make -j20` dentro la cartella.
- **Stato della fase 4:**
  - Restano solo voci "da verificare in gioco" senza un indizio concreto.
  - La fase 5 è iniziata.

### Fase 5: quest incomplete (in corso)

- **Regalia di Pentere (C1) e flauto di Padavis (C4): fatte e provate il 15/11/2026.**
  - Le patch sono in `patch/`. Si costruiscono con `python3 -I tools/costruisci.py`.
  - `prove/salvataggi/fta2.100` è una partita nuova con i dati del restauro, da caricare con
    `./gioca.sh -x 100`.
- **Cuore di Roska (C3): fatto e provato il 16/11/2026.** Dopo la morte di Roska il cuore si spezza e Karminac è liberata.
- **Da decidere:** le proposte 4 (Corona di Smeraldo) e 5 (Darnoc) di `PROPOSTE_QUEST.md`.
- **Poi:** la fase 6, la traduzione.

### Fase 6: traduzione italiana (testi completi il 15/11/2026)

- **Testi degli script:** tradotte tutte le 7.315 stringhe visibili, circa 373.000 caratteri.
  - Sono comprese le battute nuove delle quest.
  - Le stringhe di debug restano in inglese.
  - Il lavoro è stato diviso in 15 blocchi, tradotti in parallelo con `traduzione/GUIDA.md` e
    uniformati alla fine.
- **Nomi:** tradotti 1.153 nomi di oggetti, mostri e incantesimi. I nomi propri di persone e
  luoghi restano invariati.
- **Motore:** interfaccia, stati, calendario ed etichette della mappa tradotti nel commit
  `085e50a2`.
  - I plurali sono nel formato "Moneta d'Oro (150)".
  - Il buffer dei libri passa da 4.096 a 16.384 caratteri.
- **Prezzi parlati:** `sayNumber` componeva i numeri a pezzi. Ora il numero è scritto in cifre e
  i pezzi restano come sola voce inglese (`patch/script/mod160.asm` e altri otto moduli).
- **Voci:** restano in inglese, con i sottotitoli italiani attivi di serie.
- **Verificato in gioco:**
  - lettere accentate nei fumetti e nella riga di stato;
  - un dialogo (`prove/it_dialogo.png`);
  - la pergamena della Regalia (`prove/it_libro.png`).
- **Scelte dubbie decise il 16/11/2026:** sono in fondo a `traduzione/GUIDA.md`.
- **Impaginazione dei libri, rivista il 16/11/2026:** `tools/impagina.py` simula l'impaginazione
  del motore.
  - Nessun libro supera le 32 pagine.
  - 57 righe di versi e colonne strette sono state riscritte per stare nella colonna.
  - Restano su due righe solo titoli, insegne e voci di menu.
  - Corrette 22 stringhe che avevano perso gli spazi ai bordi, che servono a concatenare i pezzi.
    Il controllo ora è automatico.
  - Verificata a schermo la lettera di Roska (`prove/it_lettera_roska.png`).

### Indizi raccolti per la fase 3 (ora nel catalogo)

- **32 campioni vocali registrati che nessuno script usa:**
  `D166 H014 H017 H387 H389 H390 H429 H435 H436 H516 H528 H630 H823 H835 H837 H967 H968 H969 H970 H999
  I001 I002 I003 I004 I019 I020 I021 I022 I023 I024 I054 I194`.
  Possono essere dialoghi tagliati: vanno ascoltati e trascritti.
- **2 battute che chiamano un campione inesistente**, entrambe in `estratti/script/mod093.asm`, funzione `executeResponse`:
  - `95:2:90`, voce `I195` ("I think you already know more than I could teach you."). Il campione
    `I194` esiste ed è inutilizzato: probabile errore di numerazione.
  - `95:2:96`, voce `G807` ("You don't seem to have enough gold.").
- **ScummVM corregge già un solo bug di quest:** Capitan Navis a Maldavith non porta alle rovine di
  Tamnath anche quando Muybridge è morto (`interp.cpp`, `byteAddress`).
- **Mancano i video del CD:** `INTRO`, `TRIMARK`, `END_1` ed `END_2`.

### Fase 7: collaudo (16/11/2026)

- **Controlli statici, tutti superati:**
  - l'assemblatore riproduce identici i 161 moduli;
  - gli archivi originali si ricostruiscono identici;
  - la costruzione è ripetibile;
  - l'archivio finale si disassembla senza errori;
  - le 7.317 traduzioni superano i controlli;
  - nessun libro supera le 32 pagine.
- **Collaudo in gioco ripetibile:**
  - `tools/collaudo.sh` con gli scenari del modulo `engines/saga2/collaudo.cpp`, commit
    `1065e4f8`;
  - si esegue sulla build con AddressSanitizer (`build-asan/`).
- **Esito finale:** 14 esecuzioni su 14, senza errori di memoria:
  - quest: 22 controlli su 22;
  - salvataggio: 5 su 5;
  - giri da 2.500 fotogrammi sulla partita nuova e sugli 11 salvataggi d'epoca.
- **Bug trovati dal collaudo e corretti** (catalogo, sezione E):
  - E1: salvataggi con più battute in sospeso che non si caricano;
  - E2: salvataggi DOS con un incantesimo in volo;
  - E3: ricerca di oggetti in una regione fuori dalla mappa.
- **Non coperto dal collaudo automatico:**
  - le partite giocate davvero (combattimenti, dialoghi scelti dal giocatore, percorso completo
    delle quest a piedi);
  - l'audio;
  - i video del CD, assenti.

### Distribuzione (16/11/2026)

- **Repository pubblico** con licenza GPL3: https://github.com/Indr1d-C0ld/faery-tale-adventure-2-ita
  - Un `.gitignore` a lista bianca esclude ogni file del gioco.
  - Le patch degli script sono differenze rispetto al disassemblato.
  - La traduzione contiene solo l'italiano, con un CRC32 al posto del testo inglese.
  - Il motore è una serie di patch a ScummVM 2026.4.0 (`motore/`).
- **Pacchetto Linux x86_64:** si crea con `tools/crea_pacchetto.sh VERSIONE`. Contiene motore,
  strumenti, patch, traduzione e l'installatore, che costruisce il gioco restaurato dalla copia
  originale dell'utente.
  - Verificato: l'installazione da zero produce archivi identici a quelli del progetto.
  - Verificato: il gioco installato supera un giro del collaudo.
