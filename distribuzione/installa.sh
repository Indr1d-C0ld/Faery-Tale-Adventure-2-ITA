#!/bin/bash
# Installa il restauro italiano di Faery Tale Adventure II partendo dalla tua copia originale.
#
# Uso:
#   ./installa.sh CARTELLA_DEL_GIOCO_ORIGINALE
#
# La cartella deve contenere FTA2.EXE, i file .HRS e la sottocartella DRIVERS della versione
# DOS (per esempio la cartella FTA2 copiata dal CD o dall'installazione). Non viene modificata:
# i file del gioco vengono copiati qui in gioco/, e gli archivi FTA.HRS e SCRIPTS.HRS vengono
# ricostruiti con correzioni, quest completate e traduzione italiana.

set -euo pipefail
QUI="$(cd "$(dirname "$0")" && pwd)"
ORIG="${1:-}"
EXE_MD5=5b2ad4c23bc192a2c05bf0b4709b8e82

if [ -z "$ORIG" ] || [ ! -d "$ORIG" ]; then
	echo "Uso: ./installa.sh CARTELLA_DEL_GIOCO_ORIGINALE"
	echo "La cartella deve contenere FTA2.EXE e i file .HRS della versione DOS."
	exit 1
fi
command -v python3 >/dev/null || { echo "Serve Python 3 (pacchetto python3)."; exit 1; }

trova() {   # trova un file nella cartella indicata senza badare a maiuscole e minuscole
	find "$1" -maxdepth 1 -iname "$2" -print -quit
}

EXE="$(trova "$ORIG" fta2.exe)"
[ -n "$EXE" ] || { echo "Non trovo FTA2.EXE in $ORIG"; exit 1; }
if [ "$(md5sum "$EXE" | cut -d' ' -f1)" != "$EXE_MD5" ]; then
	echo "Attenzione: FTA2.EXE non è quello della versione DOS supportata (md5 $EXE_MD5)."
	echo "Il restauro potrebbe non funzionare. Continuo comunque."
fi

mkdir -p "$QUI/gioco" "$QUI/salvataggi" "$QUI/impostazioni"
echo "Copio i file del gioco..."
for f in fta2.exe ftadata.hrs ftaimage.hrs ftasound.hrs ftavoice.hrs; do
	src="$(trova "$ORIG" "$f")"
	[ -n "$src" ] || { echo "Manca $f in $ORIG"; exit 1; }
	cp "$src" "$QUI/gioco/$f"
done
DRV="$(find "$ORIG" -maxdepth 1 -type d -iname drivers -print -quit)"
for f in sample.ad sample.opl; do
	src=""
	[ -n "$DRV" ] && src="$(trova "$DRV" "$f")"
	[ -n "$src" ] || src="$(trova "$ORIG" "$f")"
	[ -n "$src" ] || { echo "Manca DRIVERS/$f in $ORIG"; exit 1; }
	cp "$src" "$QUI/gioco/$f"
done

echo "Ricostruisco FTA.HRS e SCRIPTS.HRS con il restauro e la traduzione..."
FTA2_ORIGINALI="$ORIG" FTA2_USCITA="$QUI/gioco" FTA2_LAVORO="$QUI/.lavoro" \
	python3 -I "$QUI/tools/costruisci.py" | grep -E "traduzione|fatto"
rm -rf "${QUI:?}/.lavoro"

if [ ! -f "$QUI/impostazioni/scummvm.ini" ]; then
	printf '[scummvm]\nfullscreen=false\ngfx_mode=surfacesdl\n[fta2]\ngameid=fta2\nengineid=saga2\nsubtitles=true\npath=%s/gioco\n' \
		"$QUI" > "$QUI/impostazioni/scummvm.ini"
fi
echo
echo "Installazione completata. Per giocare: ./gioca.sh"
