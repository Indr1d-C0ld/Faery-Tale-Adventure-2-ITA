#!/bin/bash
# Collaudo automatico del restauro di Faery Tale Adventure II.
#
# Uso:
#   tools/collaudo.sh [asan|normale] [fotogrammi_giro]
#
# Esegue gli scenari del modulo di collaudo del motore (engines/saga2/collaudo.cpp):
#   quest  da una partita nuova (slot 100): quest restaurate e correzioni, poi salva nello slot 97
#   salva  carica lo slot 97 e controlla che tutto sia stato salvato
#   giro   per ogni salvataggio d'epoca (000-010) e per la partita nuova: salti casuali nel mondo
# Con "asan" usa build-asan/scummvm (AddressSanitizer): ogni errore di memoria finisce nel rapporto.
# Risultati in prove/collaudo/: un registro per esecuzione e RAPPORTO.txt.
# Le finestre del gioco si aprono e si chiudono da sole; non servono tasti.

set -u
QUI="$(cd "$(dirname "$0")/.." && pwd)"
TIPO="${1:-asan}"
FOTOGRAMMI="${2:-1200}"
OUT="$QUI/prove/collaudo"
SAVE="$OUT/salvataggi"
if [ "$TIPO" = "asan" ]; then BIN="$QUI/build-asan/scummvm"; else BIN="$QUI/scummvm/scummvm"; fi
export ASAN_OPTIONS="detect_leaks=0:abort_on_error=0"

# Servono: una partita nuova costruita col restauro (prove/salvataggi/fta2.100: avviare il gioco
# una volta e copiare fta2.999 in fta2.100) ed eventualmente i salvataggi d'epoca da collaudare
# (docs/Tools and Cheats/Promo Saves/Promo/0*.SAV). Quelli che mancano vengono saltati.
mkdir -p "$SAVE"
if [ ! -f "$QUI/prove/salvataggi/fta2.100" ]; then
	echo "Manca prove/salvataggi/fta2.100 (partita nuova): avvia ./gioca.sh una volta e copia fta2.999 in fta2.100"
	exit 1
fi
cp "$QUI/prove/salvataggi/fta2.100" "$SAVE/fta2.100"
for f in "$QUI/docs/Tools and Cheats/Promo Saves/Promo/"0*.SAV; do
	[ -f "$f" ] && cp "$f" "$SAVE/fta2.$(basename "$f" .SAV)"
done

esegui() {   # nome scenario slot
	local nome="$1" scenario="$2" slot="$3" ini="$OUT/$1.ini"
	printf '[scummvm]\nfullscreen=false\ngfx_mode=surfacesdl\n[fta2]\ngameid=fta2\nengineid=saga2\nsubtitles=true\npath=%s/gioco\nmelchior_collaudo=%s\nmelchior_collaudo_frames=%s\n' \
		"$QUI" "$scenario" "$FOTOGRAMMI" > "$ini"
	timeout 900 "$BIN" --config="$ini" --savepath="$SAVE" -x "$slot" fta2 > "$OUT/$nome.log" 2>&1
	local rc=$?
	local esito
	if grep -q "ERROR: AddressSanitizer" "$OUT/$nome.log"; then esito="ERRORE DI MEMORIA (vedi $nome.log)"
	elif ! grep -q "COLLAUDO FINE" "$OUT/$nome.log"; then esito="NON TERMINATO, codice $rc (vedi $nome.log)"
	else esito="$(grep -a "COLLAUDO FINE" "$OUT/$nome.log" | sed 's/.*COLLAUDO FINE //; s/!$//')"; fi
	echo "== $nome (scenario $scenario, slot $slot): $esito" | tee -a "$OUT/RAPPORTO.txt"
	grep -a "COLLAUDO FALLITO" "$OUT/$nome.log" | sed 's/^WARNING: /   /; s/!$//' | tee -a "$OUT/RAPPORTO.txt"
}

echo "Collaudo $(date '+%d/%m/%Y %H:%M'), binario $TIPO, giro di $FOTOGRAMMI fotogrammi" > "$OUT/RAPPORTO.txt"
rm -f "$SAVE/fta2.097"
esegui quest quest 100
esegui salva salva 97
for s in 100 000 001 002 003 004 005 006 007 008 009 010; do
	[ -f "$SAVE/fta2.$s" ] && esegui "giro_$s" giro "$s"
done
echo
echo "Rapporto: $OUT/RAPPORTO.txt"
