# Guida alla traduzione italiana di Faery Tale Adventure II

Valida per tutti i traduttori, persone o agenti. Lo scopo è un'unica voce coerente su circa
9.700 stringhe e 1.155 nomi.

## Regole tecniche (obbligatorie: il programma scarta le righe che non le rispettano)

1. **Segnaposto:** `%d`, `%s`, `%n` e simili restano identici, nello stesso numero e nello stesso
   ordine. `%n` è il nome di un personaggio o di un oggetto e `%d` un numero.
2. **A capo:** il numero di `\n` è identico all'originale. Si spostano solo se proprio necessario,
   mai si aggiungono o si tolgono.
3. **Pulsanti di scelta:** `@` apre un pulsante ("`\n@Accept @Decline.`"). Va tenuto lo stesso
   numero di `@`, nello stesso ordine, con etichette brevi: "`\n@Accetta @Rifiuta.`".
4. **Frammenti:** molte stringhe sono pezzi di una frase che il gioco completa con un numero o con
   un'altra stringa. Esempio: "`I'll teach you a few tricks for `" + 150 + "` sovereigns.  Deal?`".
   Vanno tradotte come frammenti che si incastrano nello stesso modo, e gli **spazi iniziali e
   finali si conservano**: "`Ti insegnerò qualche trucco per `" + 150 + "` sovrane. Affare fatto?`".
5. **Solo caratteri Latin-1:** lettere accentate italiane sì (à è é ì ò ù À È É Ì Ò Ù). Niente
   virgolette tipografiche, apostrofi curvi, puntini di sospensione in un solo carattere o
   lineette lunghe. Si usano `"` `'` `...` `-`.
6. **Lunghezza:** una battuta al massimo 480 byte. Tenersi vicini alla lunghezza inglese: le
   battute sono doppiate in inglese e il sottotitolo italiano scorre nello stesso tempo.
7. **I codici restano invariati:** i tag delle voci (es. `H520`) non sono nelle stringhe da
   tradurre. Se compare qualcosa che sembra un codice (es. `SFX:41`, nomi di funzione), resta com'è.

## Tono e registro

- **Ambientazione:** fantasy medievale, italiano scorrevole e naturale, niente arcaismi pesanti.
  I libri (tipo "testo") hanno un registro più letterario dei dialoghi.
- **Dare del voi:** i personaggi si rivolgono ai fratelli col **voi**, che vale sia per uno solo
  di loro sia per tutti e tre. Usano il **tu** solo i personaggi rozzi o ostili (goblin, ogre,
  pirati, briganti, mostri parlanti), i bambini, gli amici intimi e la famiglia.
- **Parlate particolari:** si rendono con un italiano equivalente, senza esagerare.
  - Goblin e ogre parlano in modo sgrammaticato: "Me eat your arm" diventa "Io mangiare tuo braccio".
  - Pirati, contadini e popolani sono colloquiali: "Ya wants ta fight, eh?" diventa "Vuoi
    imparare a menare le mani, eh?".
  - Niente dialetti regionali italiani riconoscibili.
- **Giochi di parole e battute:** si adattano perché funzionino in italiano, anche cambiando
  l'immagine, piuttosto che tradurli alla lettera.

## Nomi propri

- **Restano invariati** i nomi di persone e luoghi: Julian, Phillip, Kevin, Farr, Pentere, Bilton,
  Padavis, Karminac, Maldavith, Tamnath, Darnoc/Darnok (come nell'originale), Kiger, Brythe,
  Roska, Muybridge e simili.
- **Titoli:** King → re (il re Karassmus), Queen → regina, Prince/Princess → principe/principessa.
  Lord e Lady restano davanti al nome (Lord Thebe, Lady Brythe). Sir → Ser. Capt. → Cap.
  Lt. → Ten. Sheriff → sceriffo.
- **Soprannomi descrittivi:** si traducono. "One-eyed Wort" diventa "Wort l'Orbo", "Kram the Mad"
  diventa "Kram il Folle", "Kemus the Sensible" diventa "Kemus il Saggio".

## Glossario fisso

| Inglese | Italiano |
|---|---|
| Tapstone (of X) | Pietra Chiave (di X), plurale Pietre Chiave |
| Halls of the Dead | Sale dei Morti |
| Golden Tree | Albero d'Oro |
| Golden Apple | Mela d'Oro |
| Stargate / Star Gate | Porta Stellare |
| Object of Hope | Oggetto della Speranza |
| Rock of Despair | Roccia della Disperazione |
| Regalia (of King Kiger) | Regalia (di re Kiger) |
| Celestial Orb | Globo Celeste |
| Crown of Pentere / Scepter of Pentere | Corona di Pentere / Scettro di Pentere |
| Emerald Crown | Corona di Smeraldo |
| sovereign(s), la moneta | sovrana, sovrane ("150 sovrane") |
| Gold Coin | Moneta d'Oro |
| Red/Orange/Yellow/Green/Blue/Violet Mana | Mana Rosso/Arancione/Giallo/Verde/Blu/Viola |
| spell / scroll / wand / potion | incantesimo / pergamena / bacchetta / pozione |
| Shadow Knight | Cavaliere d'Ombra |
| Dark Warrior / Darkwarrior | Guerriero Oscuro |
| Council of Elders | Consiglio degli Anziani |
| Merchants Quarter | Quartiere dei Mercanti |
| goblin, ogre, kobold, troll | goblin, ogre, coboldo, troll |

Per i nomi di oggetti, incantesimi e mostri vale `traduzione/nomi.tsv` quando è tradotto: nei
testi si usa la stessa traduzione.

## Termini fissati dal blocco pilota (00)

| Inglese | Italiano |
|---|---|
| Inn / Tavern / General Store / Coach House | locanda / taverna / emporio / stazione delle diligenze |
| Moon Priestess / Moon Temple | Sacerdotessa della Luna / Tempio della Luna |
| Mercenary Guild / Wizard's Guild / Archmage | Gilda dei Mercenari / Gilda dei Maghi / Arcimago |
| Lord of Order / Lord of Chaos | Signore dell'Ordine / Signore del Caos |
| Order / Chaos (le forze cosmiche), the Eternals | l'Ordine / il Caos, gli Eterni |
| Amber Castle / Great Trade Road | Castello d'Ambra / Grande Via dei Commerci |
| Brethren of the Coast | Fratellanza della Costa |
| landlubber / matey / ale | terraiolo / compare / birra |
| crown, la moneta dei mendicanti | moneta, spicciolo (mai "corona") |
| Mrs. X nei dialoghi | la signora X |
| un serpente o una creatura sibilante | conserva le "sss" anche in italiano |

## Da uniformare alla fine (scelte divergenti fra i blocchi)

- Overworld: "Sopramondo" (blocco 06) e "Mondo di Sopra" (04). Si sceglie **Sopramondo**.
- Underworld: "Inferi" (06) e "Oltretomba" (01). Si sceglie **Oltretomba**: nel gioco l'Underworld è il regno delle Sale dei Morti. Il Dark-Elf Underworld resta "Sottomondo degli Elfi Oscuri" (04).
- High Priest: "Sommo Sacerdote" (06) e "Gran Sacerdote" (04). Si sceglie **Sommo Sacerdote**.
- Numbscent: "Fiuto Sviato" (04), da aggiungere ai nomi se manca.
- Iron Jack: "Jack di Ferro" (07), ma il nome del personaggio resta **Iron Jack**.
- Lord High X (cariche): **Gran X** (Gran Ciambellano, Gran Maresciallo...), come nel blocco 07.
- Watchriders: **Cavalieri di Ronda**. Sovereign (il sovrano): **il Sovrano / la Sovrana**.
- sayNumber (numeri composti a pezzi): da sistemare alla fine nel codice degli script, non riga per riga.
- Watchriders: "Cavalieri della Guardia" (05) e "Cavalieri di Ronda" (07). Si sceglie **Cavalieri di Ronda**.
- Underworld nel blocco 05: "Inferi" e "Mondo Sotterraneo". Da uniformare in **Oltretomba**, e in "Sottomondo" per gli Elfi Oscuri.
- Un-named (la chiave): "i Senza Nome" (04) e "la Senza Nome" (05). Si sceglie **la Senza Nome**, perché è la chiave.

## Decisioni sui casi dubbi (16/11/2026)

| Caso | Decisione |
|---|---|
| Lapide "Goode (his death wasn't so...)" | Resta "Felice (la sua morte un po' meno...)": il nome è il gioco di parole stesso |
| "Da Caladrin" (insegna, nome 183) | Resta: è un'insegna all'italiana. Nelle frasi si usa "l'emporio di Caladrin" |
| Peasant's / Commoner's Quarter | Entrambi "Quartiere Popolare" |
| GalchMay / Galchmay | "Galchmay" anche nel nome di gioco |
| TAB letterale in 122:2:60 | Tolto: è un refuso dell'originale che il font disegnerebbe come simbolo |
| Royal Coach Service | Nei menu "Servizio Reale Diligenze", anche sulla mappa; nelle frasi "Servizio Reale delle Diligenze" |
| "me rape" (ogre, Krogatt) | Resta fedele all'originale ("io violentare"); si può attenuare su richiesta |
| Refusi dell'originale nei nomi (Pantere, Bitlon, Nadala...) | Normalizzati alla grafia corretta |
| Contraddizioni dell'originale (Consiglio di 3 o 8, Kaiger/Kiger) | Lasciate come sono |
| Elfi | Danno del voi, freddi e superiori |
| Wraith | "Lemure"; Spectre resta "Spettro" |
| Whitedeep, Icewind, Frostwings | Nomi propri di luoghi, invariati |
