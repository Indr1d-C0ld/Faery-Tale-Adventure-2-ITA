# Istruzioni per tradurre un blocco

Traduci in italiano un blocco di testi del gioco fantasy "Faery Tale Adventure II: Halls of the
Dead" (1997). I percorsi sono relativi alla cartella del progetto.

1. **Leggi per intero `traduzione/GUIDA.md`.** È obbligatoria: regole tecniche, registro (dare
   del voi), nomi propri, glossario fisso.
2. **Glossario dei nomi:** è `traduzione/nomi.tsv`, colonne indice, inglese, italiano. Quando un
   testo nomina un oggetto, un mostro, un incantesimo o un personaggio, usa la sua traduzione. Per
   cercarla usa grep, per esempio `grep -i "fireball" traduzione/nomi.tsv`.
3. **Input:** `traduzione/blocchi/NN.tsv`, con colonne TAB:
   - `id`;
   - `tipo`: `battuta` è una frase parlata, doppiata in inglese, di cui scrivi il sottotitolo;
     `testo` è un libro, un messaggio o una scelta;
   - `usi`: modulo e funzione, che dicono chi parla o di che libro si tratta;
   - `inglese`.
   Le righe consecutive di uno stesso modulo e di una stessa funzione formano un dialogo o un
   libro: leggile insieme per capire il contesto prima di tradurle.
4. **Output:** `traduzione/blocchi/NN.it.tsv`, l'unico file che puoi scrivere.
   - Prima riga: `id<TAB>italiano`.
   - Poi una riga per ogni riga dell'input, nello stesso ordine e con lo stesso id.
   - Scrivi in UTF-8 con soli caratteri Latin-1.
   - Scrivi gli a capo come `\n`, esattamente come nell'input. Mai un vero a capo o un vero TAB
     dentro il testo.
   - Se una stringa è fatta solo di spazi o di `\n`, copiala identica.
5. **Controllo:** per ogni riga, prima di consegnare, verifica:
   - stessi segnaposto `%d`, `%s`, `%n` nello stesso ordine;
   - stesso numero di `\n`;
   - stesso numero di `@`;
   - spazi iniziali e finali conservati.
   Uno script Python breve, scritto nella cartella temporanea e non nel progetto, è il modo più
   sicuro per fare il controllo su tutte le righe.
6. **Risposta finale**, breve e in italiano:
   - righe scritte;
   - scelte di traduzione che altri traduttori dovrebbero conoscere (nomi di luoghi o di gruppi
     ricorrenti, soprannomi, termini nuovi non presenti nel glossario);
   - casi dubbi.
