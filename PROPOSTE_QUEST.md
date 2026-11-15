# Fase 5: proposte per le quest incomplete

> **Stato al 15/11/2026:** l'utente ha scelto la **1** (Regalia e Brythe) e la **2** (flauto e
> topi). Sono **realizzate e provate in gioco**; il dettaglio è in `CATALOGO.md`, voci C1 e C4.
> La **3** (il cuore di Roska) è realizzata il 16/11/2026, senza le battute degli abitanti. Le
> proposte 4 e 5 restano da decidere.

Data: 15/11/2026. Fonti: `CATALOGO.md` (sezione C), libri e dialoghi del gioco
(`estratti/testi_script.tsv`), soluzioni d'epoca in `docs/`. I numeri fra parentesi sono gli id
dei testi (`risorsa:offset:numero`).

## Vincoli tecnici

- **Voci:** le battute nuove sono solo testo, senza audio, e il motore le mostra come tutte le
  altre. In italiano saranno comunque sottotitoli: con la traduzione la differenza si sente poco.
- **Grafica:** niente immagini nuove. Gli oggetti nuovi riusano lo sprite di un oggetto esistente
  con un nome nuovo. Esempio: la Corona di Pentere col disegno della Emerald Crown.
- **Cosa si può fare:**
  - Funzioni nuove in coda ai moduli di script, collegate alle vtable.
  - Stringhe nuove nelle tabelle degli script e nomi nuovi nella tabella `NAME`.
  - Prototipi nuovi in coda a `PRO\0`.
  - Oggetti posati nel mondo dagli script.

  Ogni pezzo va prima verificato con il disassemblatore e una prova in gioco, come per le
  correzioni della fase 4.
- **Fedeltà:** dove il gioco ha già i testi, la quest li usa. Ciò che manca è segnato come
  **invenzione** e va approvato.

## Quest chiuse senza lavoro

| Voce | Esito |
|---|---|
| **C6, "jolly slicers"** | Non è una quest tagliata. È la trappola di Muybridge: chi accetta diventa un Dark Warrior (H379–H382) e il fratello si perde. È già implementata. Le voci H387, H389 e H390 sono probabilmente varianti della proposta: per esserne certi vanno trascritte. |
| **D3, Object of Hope** | Il libro dice che l'Object of Hope ripara la Stargate negli Halls, e questo funziona già (`mod302`, "%n has restored a broken Star Gate."). Nessun testo lo lega al cuore di Roska. |
| **D2, Ione** | Il gioco la nomina una sola volta, come terra scomparsa "che un tempo stava nell'angolo nord-est di Farr" (134:2:387). Non c'è nessun personaggio, oggetto o luogo. Proposta: non costruirla, al massimo esplorare la mappa a nord-est per vedere se c'è un frammento. |

## Proposte, in ordine di fondamento nei testi

### 1. La Regalia di Pentere e la regina Brythe (C1): fondamento forte

**Cosa c'è già:**
- Le leggi e la storia della Regalia: Corona, Globo e Scettro, che "determinano senza equivoci il
  vero erede" (138:2:110–172).
- Il re Karassmus morto, la principessa Brythe data per uccisa e il ciambellano Comsbone che
  annuncia un'elezione pilotata (138:2:154).
- Brythe è viva: fa la guaritrice nella sua casetta in campagna.
- C'è già il proclama "our new Sovereign, Lady Brythe, lost daughter of King Karassmus… proven
  by the Regalia" (138:2:2), seguito dal decreto reale con le riforme (138:2:4–17).
- Il Globo Celeste è nei sotterranei del palazzo.

**Proposta:**
1. Il Globo Celeste smette di trasformarsi in chiave e diventa raccoglibile. Il passaggio
   Brass Key + scheletri si sposta altrove o resta su un colpo, così il percorso dei sotterranei
   non cambia.
2. **Invenzione:** la Corona di Pentere e lo Scettro di Pentere sono oggetti nuovi. Hanno lo
   sprite della Emerald Crown e dello Scepter of Zerox e si trovano in due luoghi del palazzo e
   dei sotterranei già esistenti e poco usati, da scegliere esplorando la mappa.
3. Si portano i tre pezzi a Brythe. Lei riconosce la Regalia e il proclama e il decreto già
   scritti diventano visibili: compaiono come pergamene, o li legge un araldo.
4. Ricompensa:
   - Brythe dà un oggetto di valore, da scegliere fra quelli unici esistenti.
   - **Invenzione:** se Comsbone è nel gioco, una battuta di Brythe lo smaschera.

**Costo:** medio-alto. Richiede:
- 2 prototipi nuovi;
- una nuova `onReceive` per Brythe;
- uno script per il Globo;
- circa 10–15 battute nuove.

### 2. Il flauto e i topi di Padavis (C4): fondamento buono

**Cosa c'è già:**
- Il diario di Nimdok, il flautista che infesta Padavis di topi per vendetta (138:2:293–297).
- Gli abitanti che si lamentano dei topi.
- Il registro dei crimini: "Rats! Get rid of them! Meet with Wort to discuss." (136:2:56).
- One-eyed Wort al granaio.
- Lo sceriffo Jar Dighton.
- Il flauto, i topi, 4 generatori e le tane.
- Una soluzione d'epoca dice che "i topi si fermano quando sentono il flauto".

**Proposta:**
1. Suonare il flauto a Padavis attira i topi vicini e li immobilizza per qualche secondo, così si
   possono colpire. In pratica è la cosa che i giocatori credevano di vedere.
2. Si ripulisce il granaio, cioè si spengono i generatori di Padavis dopo un certo numero di topi.
   Wort, che ora ignora la morte dei topi, ringrazia e paga.
3. **Invenzione facoltativa:** si porta il diario di Nimdok a Dighton, che fa una battuta sulla
   truffa.

**Costo:** basso-medio. Richiede:
- uno script del flauto;
- un contatore;
- una nuova `onReceive` o un nuovo dialogo per Wort;
- 3–6 battute.

### 3. Il cuore di Roska (C3): fondamento debole

**Cosa c'è già:**
- Il cuore pulsa nella cittadella: si sente da lontano ed è "d'oro, oro maligno" (225:2:37).
- Roska "ha rubato il cuore della terra" (134:2).
- Gli abitanti di Karminac aspettano qualcuno che lo affronti.
- Lo script fa solo pulsare e suonare il cuore.

**Proposta**, **invenzione** che parte da "ha rubato il cuore della terra":
1. Dopo la morte di Roska, colpire il cuore lo spezza, con lo stesso effetto in più stadi della
   Rock of Despair.
2. Il battito si ferma e un messaggio dice che la terra di Karminac è liberata.
3. Gli abitanti di Karminac ottengono una battuta nuova di sollievo.

Prima della morte di Roska, il cuore respinge i colpi.

**Costo:** medio. Richiede:
- un `onAcceptStrike` per il cuore;
- una globale nuova;
- battute degli abitanti, condizionate.

### 4. La Corona di Smeraldo e Jolly Roger (C5): fondamento medio, molta invenzione

**Cosa c'è già:**
- La leggenda: Jolly Roger e Hans Gelbard rubano la Corona sacra di Darnok, Roger tradisce
  Gelbard, il fantasma di Gelbard resta sul relitto e Roger si nasconde nelle grotte di
  Maldavith (118:2:37–44, 118:2:88–93).
- Esistono i nomi di Gelbard, del fantasma di Gelbard e di Jolly Roger, e uno script
  `JollyRoger_type`. Nessuno dei tre parla.
- La corona esiste, ma ne girano tre copie, anche come bottino casuale.

**Proposta, invenzione:**
- Il fantasma di Gelbard, sulla nave fantasma, chiede vendetta su Roger con poche battute.
- Jolly Roger, nel nascondiglio, custodisce la corona "sacra", che diventa un oggetto unico con
  un nome distinto.
- Riportare la corona al fantasma lo libera, con una ricompensa.

**Costo:** medio-alto, e quasi tutto è da scrivere.

### 5. Darnoc e i ribelli (C2): fondamento debole

**Cosa c'è già:**
- Una lettera dei ribelli di Darnok contro Roska (118:2:9–14).
- Lo sceriffo Dighton, ex capitano della guardia di Darnoc, che si chiede se tornare dai ribelli
  (136:2:7–8).
- Gli abitanti che sperano in qualcuno di coraggioso.
- Conrad non ha nessun testo e nessun ruolo.

**Proposta, invenzione leggera:**
- Portare la lettera dei ribelli a Dighton gli fa decidere di tornare a Darnoc.
- Dopo la morte di Roska, Dighton è a Darnoc e ringrazia.

Conrad resta una comparsa.

**Costo:** medio. Il valore narrativo è modesto.

### Fuori dalle quest, facoltativi

- **Lasciapassare dei quartieri** (legge 1 di Bilton: bianco, verde, blu): aggiungerebbero solo
  ostacoli a un gioco che oggi si attraversa liberamente. Proposta: non farli.
- **Personaggi muti con nome** (B6) e **le sei virtù** (B7): non ci sono testi su cui basarsi.
  Proposta: lasciarli come sono.

## Raccomandazione

Fare la **1** (Regalia e Brythe) e la **2** (flauto e topi): hanno quasi tutto già scritto nel
gioco e chiudono le due trame più evidenti. Poi, se interessano, la **3** (il cuore di Roska),
che è breve. La 4 e la 5 sono soprattutto invenzione e conviene valutarle dopo aver visto le
prime in gioco.
