# FTA2: catalogo di bug, contenuti tagliati e quest incomplete

Fase 3 del [piano](PIANO.md). Stato al 15/11/2026.

Ogni voce dice da dove viene l'indizio e quanto è solida:
- **Confermata:** verificata nel codice o nei dati.
- **Probabile:** ci sono indizi nei dati, ma va vista in gioco.
- **Da verificare:** viene solo da fonti esterne.

Gli strumenti e i dati grezzi sono in `tools/` e in `estratti/analisi/`.

## Come è stato costruito

| Analisi | Strumento | Risultato grezzo |
|---|---|---|
| Grafo delle chiamate: funzioni mai raggiungibili | `tools/analisi.py` | `estratti/analisi/morte.txt`, `funzioni.tsv` |
| Variabili globali lette ma mai scritte, o viceversa | `tools/analisi.py` | `estratti/analisi/variabili.tsv`, `sospette.txt` |
| Pacchetti di dialogo mai assegnati, PNG con nome ma senza dialogo | `tools/conoscenze.py` | `estratti/analisi/conoscenze.txt` |
| Oggetti mai presenti nel mondo e mai creati | `tools/oggetti.py` | `estratti/analisi/oggetti.txt` |
| Voci registrate mai usate, battute senza voce | `tools/estrai_testi.py`, `tools/shn/shn2wav` | `estratti/voci_inutilizzate/*.wav` |
| Soluzioni d'epoca | lettura di `docs/Walkthroughs` | — |

Lo stato delle quest non usa i flag a bit, che nessuno script tocca. Passa per 47 interi
globali, per i pacchetti di conoscenza dei personaggi, per gli oggetti posseduti e per i cambi
di prototipo.

## A. Bug

| # | Bug | Dove | Stato | Correzione proposta |
|---|---|---|---|---|
| A1 | La battuta "I think you already know more than I could teach you." di Galchmay, l'istruttore di magia di `mod093` (non l'istruttore d'armi), chiama la voce `I195`, che non esiste. L'ipotesi `I194` è **smentita**: il confronto acustico (altezza mediana e timbro MFCC) colloca `I194` fra le voci `I190`–`I193` di un abitante di Bilton (`mod033`), con F0 di circa 253 Hz contro i 202 Hz di Galchmay. Nessuna delle 32 voci inutilizzate ha durata e timbro compatibili con Galchmay. | `mod093.asm`, `executeResponse` @5836 | Verificata il 15/11/2026: la voce non è mai stata registrata | Nessuna modifica: ScummVM (`speech.cpp`) toglie il flag della voce e mostra la battuta solo come testo, come le altre. In italiano sarà comunque un sottotitolo |
| A2 | "You don't seem to have enough gold." di Galchmay chiama la voce `G807`, che non esiste. Galchmay non ha un'altra battuta registrata sull'oro, quindi riusare la voce di un altro personaggio (per esempio `H529` del mercante d'armature) gli cambierebbe voce a metà dialogo. | `mod093.asm` @6027 | Verificata il 15/11/2026 | Nessuna modifica, per lo stesso motivo di A1: la battuta appare come testo. Sono le uniche due voci mancanti in tutti gli script |
| A3 | **Bug di ScummVM: il segmento dati degli script esiste in due copie.** Gli script scrivono le globali con `data[N]` e alcuni le leggono con `far[130:N]`. Il segmento 130 è `__DA`, ma ScummVM lo carica due volte: `initScripts` usa `loadResource`, `segmentAddress` usa `loadIndexResource`, con due allocazioni separate. In più `dataSegIndex` non viene mai assegnato e salvataggi e caricamenti includono solo la prima copia. Così le scritture non arrivano a chi legge, e quelle fatte con `far` si perdono al salvataggio. Il motore originale aveva un'unica copia. | `scummvm/engines/saga2/interp.cpp` (`initScripts`, `segmentAddress`, `segmentArrayAddress`) | **Corretta** (commit `b866e146`, 15/11/2026) | Nel motore: assegnare `dataSegIndex` e far restituire `dataSegment` a `segmentAddress` e `segmentArrayAddress` per quel segmento. Poi togliere l'aggiramento di Navis |
| A3a | Conseguenza 1: Capitan Navis a Maldavith non porta alle rovine di Tamnath anche dopo la morte di Muybridge (globale 2862, scritta da `mod248:onDie`, letta da `mod246` 12 volte). | | Confermata. ScummVM aggira solo questo caso, con un controllo cablato su Muybridge | Risolta dalla correzione A3 |
| A3b | Conseguenza 2: l'incantesimo Timequake (`mod073:spellEffect_Timequake`) legge le globali 2866–2870, scritte dal timer di `mod248`, e vede sempre i valori iniziali. | | Confermata nel codice | Risolta dalla correzione A3 |
| A3c | Conseguenza 3: la globale 2796 è scritta con `far` da `mod020`, `mod040` e `mod097` e con `data` da `mod244`, ed è letta con `far` da `mod064:executeResponse`. La scrittura di `mod244` non arriva e le altre si perdono quando si salva. | | Confermata nel codice | Risolta dalla correzione A3 |
| A3d | Conseguenza 4: la globale 3748 è scritta da `mod300:onRelease` con `data` e letta da `mod296:onTimerTick` con `far`. Il collegamento fra le due trappole o i due meccanismi non scatta mai. | | Confermata nel codice | Risolta dalla correzione A3 |
| A3e | Conseguenza 5: la globale 416 è scritta con `far` da `mod097:onReceive` e letta con `data` da `mod040:onReceive`, quindi la consegna non viene registrata. | | Confermata nel codice | Risolta dalla correzione A3 |
| A4 | Il fantasma bambino Rallo Jovanc (attore 33184) non porta l'oggetto con sé. Il suo unico script (`mod312:onReceive`) crea il Bastone della Vita (prototipo 108) quando riceve l'orsacchiotto (prototipo 894). Se muore nello scontro con gli scheletri, la ricompensa è persa. | Soluzione d'epoca (HOD1, "ghost of a little kid") | **Corretta** il 15/11/2026 | Il prototipo 101, usato solo da Rallo, ora è immune a tutti i danni (`patch/dati.tsv`, 2 byte di `FTA.HRS`). Nel motore (commit `1d93384a`) le immunità del prototipo si riuniscono a quelle salvate al caricamento, così la correzione vale anche per i salvataggi già fatti. Prova: 16 colpi da 50, uno per tipo di danno, lasciano Rallo a vitalità 10 anche caricando un salvataggio d'epoca. Krogatt, per confronto, muore |
| A5 | Crash casuali nell'oltretomba ("Halls of the Dead"): il gioco torna al desktop di Windows 95. | Soluzione d'epoca (HOD4) | **Corretta in ScummVM** (commit `fa4fc360`, 15/11/2026) | Riprodotto: dal salvataggio 009, girando per gli Halls of the Dead, ScummVM andava in crash (segmentation fault) dopo circa 7.800 fotogrammi. AddressSanitizer indica `castSpellAction`: un mostro lancia un incantesimo per numero (36). `skillProtoFromID` di ScummVM legge prima i numeri ≤ 128 come ID di oggetto e restituiva il prototipo di un oggetto qualunque, che non è un incantesimo, quindi la chiamata virtuale saltava all'indirizzo 0. Ora un numero basso vale come oggetto solo se l'oggetto è davvero un'abilità (`kIsSkill`). Dopo la correzione: 560 secondi e 49.800 fotogrammi nello stesso giro senza crash, con 7 lanci che prima sarebbero finiti nel ramo sbagliato. Non è detto che il crash del DOS avesse la stessa causa. Correzione collegata (commit `ddc98012`): un controllo del null mancante nel cambio di mondo della regione attiva. La riserva di oggetti e attori non si è mai esaurita |
| A6 | Due globali scritte e mai lette: 2186 (puzzle delle pietre-chiave, `mod204`) e 4852 (lettera d'amore per Birket, `mod097`). | `sospette.txt` | Confermata, innocua | Nessuna; restano come indizi |

## B. Contenuti presenti nei dati ma irraggiungibili

| # | Contenuto | Prova | Stato |
|---|---|---|---|
| B1 | **Insulti cannibali di Krogatt in combattimento.** Lo script 601 (`Krogatt_Type` in `mod004`) è quello del capo goblin Krogatt, non di un orco. `mod200` ha due `onSpecialAttack`: la vtable usa solo la seconda (incantesimo 28 nel 25% dei casi, con un insulto). La prima, orfana, sceglie fra 10 battute cannibali ("Me cook you in soup", "How you taste?"…). Le voci `A186`–`A193` e `A224` si sentono già nelle chiacchiere dei goblin (`mod156`): mancava solo il loro uso in combattimento. | `mod200` @22 e @385 | **Corretta** il 15/11/2026 (`patch/script/mod200.asm`, 4 byte) | Il ramo "non fare nulla" della seconda funzione salta nella prima, dopo le inizializzazioni identiche. Il peso del silenzio passa da 60/99 a 120/159. Prova con 60 attacchi speciali forzati: 26 battute (43%), di cui 5 cannibali, nessun errore |
| B2 | **32 voci registrate mai usate**, a gruppi: il reclutamento pirata dei "jolly slicers" (`H387`, `H389`, `H390`, accanto a `mod248`); il finale con le pietre-chiave e Thorolis (`H835`, `H837`, fra `mod204` e `mod300`); un marinaio ("Ahoy mate", `I001`–`I004`); l'istruttore d'armi (`I019`–`I024`); un oste che racconta voci (`H967`–`H970`); una battuta in più dell'abitante di Bilton (`I194`, 4,6 s, stesso timbro di `I190`–`I193` in `mod033`); e altre sparse. | `estratti/voci_inutilizzate/` | Confermata, da trascrivere |
| B3 | **15 pacchetti di dialogo generici mai assegnati:** mendicante anziano, intrattenitrice, intrattenitore giovane, contadino e mago degli Elfi Scuri, maga anziana, maga matrona, mercante anziana, saggia anziana, sciamano anziano, sciamana matrona, ragazzo ladro, guerriera matrona, due Wildevarr. Sono tipologie di PNG che nel gioco non compaiono. | `conoscenze.txt` (pacchetti 46, 543, 545, 563, 567, 699, 783, 787, 789, 1658, 1662, 1664, 1758, 1798, 1822, 1824) | Confermata |
| B4 | **Generatore di quest tagliato:** `makeTestMission` crea missioni e oggetti in un luogo scelto a caso ("Site Selected!"), ma non viene mai chiamata. La soluzione d'epoca (HOD4) conferma che il generatore fu tagliato per mancanza di fondi. | `morte.txt`, `mod085` | Confermata |
| B5 | Altre funzioni morte: `makePerson`, `makeDog`, `makeGoblinBand`, `makeNastyBadForestElfBand`, `doBrosPossessThisObject`, `compressInventory`. | `morte.txt` | Confermata |
| B6 | **Personaggi con nome ma senza nessun dialogo:** Kwarrel, Gowin, Bhimrao, Rallo Jovanc (muto, ma ha una quest: vedi A4), Capt. Gelbard. Ci sono anche quattro PNG con nomi di persone reali (James Richey, Stephen McTally, Jean Burntow, Sam Walker), tutti nello stesso punto e a quota 0: probabilmente lo staff, nascosti o di prova. | `conoscenze.py` sugli attori di `FTA.HRS` | Confermata, da vedere in gioco |
| B7 | **Le sei virtù** (Compassion, Honesty, Humility, Insight, Persistance, Tolerance) e "A Memory" esistono come oggetti, ma nessuno le crea. Forse erano "idee" della scheda mentale "Ideas", che il motore prevede. | `oggetti.txt` | Confermata come dato, ignota l'intenzione |
| B8 | Oggetti mai ottenibili, oltre a quelli tecnici come generatori e abilità: un lasciapassare (`Pass`, 547), le chiavi di diamante, del drago, di ferro, di giada, reale, sacra e del sole, `Crystal Ball`, `Spyglass`, `Medallion`, `Drum`, `Horn`, `Holy Hand Grenade` e altri. Nessuna porta chiusa a chiave resta senza la sua chiave, quindi non bloccano zone. | `oggetti.txt`, analisi delle porte (TAG) | Confermata |

## C. Quest incomplete (la parte da progettare)

| # | Quest | Indizi | Stato |
|---|---|---|---|
| C1 | **Corona, Globo e Scettro di Pentere.** I libri del palazzo raccontano la Regalia, che prova il vero erede. Nel gioco c'erano già Brythe, la principessa creduta morta che fa la guaritrice, e il proclama e il decreto della nuova regina, mai mostrati. Del resto c'era solo il Globo Celeste, che colpito diventava la Brass Key. | HOD2; libri 495–497 (`mod137`) | **Completata** il 15/11/2026 (vedi `PROPOSTE_QUEST.md`) | Corona di Pentere (prototipo 970) nell'inventario di Smash, Scettro di Pentere (971) in quello di Bluto. Il Globo colpito ora crea una Brass Key accanto a sé invece di trasformarsi. Brythe ha una classe propria (export 1828): commenta ogni pezzo e, con tutti e tre, consegna le pergamene del proclama e del decreto (libri 496, 497) e 500 monete. Una nota a margine nella pergamena della Regalia indica Brythe. Provata in gioco da una partita nuova. Corona, Scettro e la classe di Brythe richiedono una partita nuova |
| C2 | **Darnoc, "la città incompleta" (Karminac):** molti luoghi citati senza seguito. Lo stregone Conrad ha solo chiacchiere generiche ("Fiddle-dee-dee!"). | HOD2; Conrad ha i pacchetti 571 e 793, entrambi generici | Confermata |
| C3 | **Il cuore di Roska:** pulsava nella cittadella senza nessuna reazione. Lo script del cuore (classe 1143, `mod298`) avvia il battito solo finché Roska (attore 32947) è vivo, ma non c'era nessun seguito. | HOD2; vtable 1143 | **Completata** il 16/11/2026 (proposta 3 di `PROPOSTE_QUEST.md`) | Nuovo `onAcceptStrike` del cuore (`patch/script/mod298.asm`). Finché Roska vive il cuore resiste ai colpi, con un messaggio. Dopo la sua morte il primo colpo lo spezza: suono, messaggio sulla liberazione di Karminac, rimozione dal mondo, globale `data[5020]`. Provato in gioco, prima e dopo la morte di Roska. Le battute di sollievo degli abitanti di Karminac non sono state aggiunte |
| C4 | **Il flauto e i topi di Padavis.** C'erano il diario del flautista Nimdok, le lamentele sui topi, il registro dei crimini ("Meet with Wort") e i generatori dei topi, ma il flauto suonava e basta. | HOD2, KIA1 | **Completata** il 15/11/2026 (vedi `PROPOSTE_QUEST.md`) | Suonare un flauto entro 10 caselle da una delle quattro tane di Padavis scaccia i topi: i generatori 4249–4252 vengono eliminati, una volta sola (`mod298`). One-eyed Wort ha una classe propria (export 1829): la prima volta che gli si parla dopo la liberazione ringrazia e paga 150 monete. Provata in gioco. Il ringraziamento di Wort richiede una partita nuova |
| C5 | **La Corona di Smeraldo:** ne parlano più libri. È nel mondo (3) e la portano i Cavalieri d'Ombra, ma non ha una quest. | HOD2 | Da verificare |
| C6 | **Il reclutamento pirata dei "jolly slicers":** ci sono voci registrate in più (B2). Forse una scelta di unirsi ai pirati è stata tagliata. | **Non è una quest tagliata** (15/11/2026): è la trappola di Muybridge, già implementata (chi accetta diventa un Dark Warrior). Vedi `PROPOSTE_QUEST.md` |

## D. Segnalazioni da fonti esterne (ricerca in rete del 15/11/2026)

Non esistono patch ufficiali né patch di fan: The Dreamers Guild fallì all'uscita del gioco.
Le fonti sono la FAQ di bladekeep, il "Let's Play" su RPG Codex, MobyGames, la soluzione in
tedesco di mogelpower e il tracker di ScummVM.

| # | Segnalazione | Fonte | Riscontro nei dati |
|---|---|---|---|
| D1 | Se il mana di un fratello supera 255, cliccare il ritratto manda in crash il gioco. Secondo la FAQ è l'unico bug ammesso dai programmatori. **Causa trovata:** in modalità individuale (`intrface.cpp`, `getManaLineInfo`) la posizione delle stelle si calcola come mana/200 senza limite, quindi sopra 200 le stelle si disegnano fuori dall'indicatore. Nel DOS è una scrittura fuori dal buffer, in ScummVM `TBlit` ritaglia e le stelle spariscono. | FAQ bladekeep | **Corretta** (commit `02d57f43`, 15/11/2026) | Mana e mana di base disegnati limitati a 200. Prova con mana a 150–1000: prima le stelle uscivano o sparivano (`prove/d1_prima.png`), ora restano sul bordo (`prove/d1_dopo.png`) |
| D2 | **L'isola di Ione**, mai pubblicata. Secondo il programmatore Joe Pearce ne resta un pezzo, raggiungibile solo con un oggetto da trucco. | MobyGames (citazione di uno sviluppatore) | Il nome compare in 6 testi; la mappa va esplorata |
| D3 | Usare l'Object of Hope sul cuore di Roska non fa nulla. Un libro dice che la Stargate si ripara con l'Object of Hope. | mogelpower, RPG Codex | Coerente con C3 Il libro parla della Stargate negli Halls, e quella riparazione funziona già (`mod302`): nessun testo lega l'Object of Hope al cuore |
| D4 | Oggetti senza uso: il liuto di Rosewind, la sfera di cristallo di Vakirin, il medaglione, il braccialetto d'oro; anche Farmer John non serve a nulla. La Map of Ages è sotto un letto, ma non si può prendere. | mogelpower | Gli oggetti esistono (`oggetti.txt`); la Map of Ages compare in un solo testo |
| D5 | HellRazor, una spada descritta in un libro e mai vista. | RPG Codex | **Falso allarme:** il prototipo 397 è nel mondo |
| D6 | Rifoss tiene gli oggetti di quest che gli si danno, e lasciargli la Caldera non ha effetto. | mogelpower | **Comportamento voluto** (verificato il 15/11/2026) | Rifoss (attore 32773) usa la classe generica delle persone (`mod020:onReceive`). Quella classe registra l'oggetto ricevuto nella globale 2796 e fa partire il dialogo adatto al tipo di oggetto, e il personaggio lo tiene: vale per tutti i regali, non solo per lui. I suoi dialoghi (pacchetto 1660, condiviso con Peregrine) sono risposte vaghe da vecchio svanito, come "Clearly, it is better to give than to receive." Nessuno script lo nomina. È una comparsa (omaggio a Kram the Mad), non una quest tagliata. Restituire gli oggetti importanti romperebbe i personaggi che reagiscono ai regali attraverso la stessa classe |
| D7 | Catena di debug a Padavis: la lampada a Birket dà lo Staff of Ugh, che dà l'Ultimate Cheat. Il Tour Guide teletrasporta. | FAQ bladekeep, ScummVM #14046 | Gli oggetti esistono: è contenuto di sviluppo, da lasciare com'è |
| D8 | Gli oggetti lasciati in un forziere spariscono tornando in città. | FAQ bladekeep; HOD1WALK righe 89–99 | **Corretta** (commit `e95069c9`, 15/11/2026) | La causa: ogni oggetto posato dal giocatore diventa "eliminabile" (`kObjectScavengable`), e il motore lo cancella col suo contenuto dopo circa 10 minuti di gioco, o prima se servono oggetti nuovi. Un forziere spostato diventava eliminabile e spariva con tutto quello che c'era dentro, come racconta la soluzione d'epoca. Ora un oggetto che contiene altri oggetti non viene eliminato, mentre il resto della pulizia non cambia. Prova con la simulazione di sfondo accelerata: senza correzione spariscono 5 contenitori pieni su 5, con la correzione nessuno, mentre gli oggetti vuoti di controllo spariscono in entrambi i casi |
| D9 | Kevin non può aprire l'inventario quando gli altri due fratelli sono lontani. | RPG Codex | **Comportamento voluto** (dal codice, 15/11/2026) | `ContainerNode::isAccessable`: il fratello attivo raggiunge l'inventario di un altro fratello solo entro 96 unità, mentre il proprio è sempre accessibile. Se Kevin è lontano, basta renderlo attivo (clic sul suo ritratto o sul pulsante del fratello). Non provato in gioco |
| D10 | Bug di ScummVM già chiusi: #14046 (crash "Wrong spellID"), #14047 (le battute non si saltavano), #14064 (crash "Too many tasks" a Castle Jovanc). La versione 2026.4.0 li include. | tracker ScummVM | Già corretti |

## E. Bug trovati dal collaudo (fase 7, 16/11/2026)

| # | Problema | Dove | Stato | Correzione |
|---|---|---|---|---|
| E1 | I salvataggi fatti mentre due o più personaggi parlano non si caricano: "Active Regions not loaded". | `speech.cpp`, `SpeechTaskList(in)`: il contatore del ciclo è incrementato due volte, anche in un messaggio di debug, quindi si leggono metà delle battute e i blocchi successivi finiscono fuori posto | **Corretto** (commit `08195d07`) | Tolto l'incremento in più. Lo stesso salvataggio, che prima falliva, ora si carica |
| E2 | Un salvataggio del gioco DOS con un incantesimo in volo blocca il caricamento: asserzione sull'elenco degli attori. È il salvataggio d'epoca 003. | `spellio.cpp`: il DOS salva i campi `SpellID` a 32 bit, ScummVM li legge a 8 bit. `objects.cpp`: un ID fra oggetti e attori diventava un indice negativo | **Corretto** (commit `b8f57a2f`) | Si legge ogni istanza nel formato di ScummVM e, se il risultato non è plausibile, in quello DOS. Gli ID fuori intervallo danno un errore chiaro |
| E3 | Una ricerca di oggetti in una regione fuori dalla mappa fa scattare un'asserzione nell'iteratore dei settori. È emerso dai salti casuali del collaudo; nel gioco può succedere solo ai bordi del mondo. | `objects.cpp`: la regione limitata ai bordi diventa vuota, ma `SectorRegionObjectIterator::first()` legge comunque un settore estraneo | **Corretto** (commit `fafe2b63`) | Una regione vuota non restituisce nulla |

## Falsi allarmi

- Gli **anelli di ametista**, che la soluzione d'epoca dice di non aver mai trovato, sono nel mondo
  in 3 copie e vengono anche dati da `giveAmulet`.
- La globale 1368 è letta ma mai scritta: è solo una costante, il numero di pepite.
- Muybridge ha davvero il gestore `onDie` collegato (vtable di `mod248`, slot 138). Il bug di
  Navis non sta nello script ma nel motore (A3).
- La porta con il codice 20 (mondo 1) non ha chiave, ma non è chiusa a chiave.

## Ancora da fare in questa fase

1. Trascrivere le 32 voci inutilizzate (`estratti/voci_inutilizzate/`), ascoltandole oppure con un
   riconoscitore vocale locale.
2. Verificare in gioco le voci segnate "Da verificare" e "Probabile".
