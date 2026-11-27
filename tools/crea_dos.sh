#!/bin/bash
# Prepara l'edizione per MS-DOS del restauro, per un PC vero o emulato (es. Retro486).
#
# Uso:
#   tools/crea_dos.sh [CARTELLA_ORIGINALI]
#
# Scrive in build/dos/:
#   FTA2/          da copiare in C:\GIOCHI\FTA2 (o dove si vuole): FTA2.EXE, gli archivi FTA.HRS e
#                  SCRIPTS.HRS del restauro (tradotti), FTADATA.HRS, i driver audio e un FTA2.INI
#                  che legge immagini, suoni e voci dal CD (D:\FTA2)
#   FTA2DATI.ISO   CD con FTAIMAGE.HRS, FTASOUND.HRS e FTAVOICE.HRS originali in \FTA2
# Sotto DOS valgono le correzioni ai dati e agli script e la traduzione dei testi del gioco;
# le correzioni al motore riguardano solo ScummVM, e l'interfaccia di FTA2.EXE resta in inglese.

set -euo pipefail
QUI="$(cd "$(dirname "$0")/.." && pwd)"
ORIG="${1:-$QUI/original/HallsoftheDead/disk/FTA2}"
DEST="$QUI/build/dos"
trova() { find "$1" -maxdepth 1 -iname "$2" -print -quit; }

FTA2_ORIGINALI="$ORIG" FTA2_USCITA="$DEST/hrs" FTA2_LAVORO="$DEST/lavoro" \
	python3 -I "$QUI/tools/costruisci.py" | grep -E "traduzione|fatto"

rm -rf "${DEST:?}/FTA2"
mkdir -p "$DEST/FTA2/DRIVERS"
cp "$(trova "$ORIG" fta2.exe)" "$DEST/FTA2/FTA2.EXE"
cp "$(trova "$ORIG" ftadata.hrs)" "$DEST/FTA2/FTADATA.HRS"
cp "$DEST/hrs/fta.hrs" "$DEST/FTA2/FTA.HRS"
cp "$DEST/hrs/scripts.hrs" "$DEST/FTA2/SCRIPTS.HRS"
DRV="$(find "$ORIG" -maxdepth 1 -type d -iname drivers -print -quit)"
for f in "$DRV"/*; do cp "$f" "$DEST/FTA2/DRIVERS/$(basename "${f^^}")"; done
printf '%s\r\n' \
	'; CONFIGURATION FILE FOR Faery Tale Adventure II' \
	'; Restauro italiano: immagini, suoni e voci sul CD (D:\FTA2)' \
	'' \
	'[Sound]' 'VoiceVolume=120' 'SoundVolume=70' 'MusicVolume=90' \
	'' \
	'[Paths]' 'VideoPath=D:\VIDEO' 'SoundFile=D:\FTA2' 'ImageFile=D:\FTA2' 'VoiceFile=D:\FTA2' \
	'' \
	'[Options]' 'Night=1' 'SpeechText=1' 'AutoWeapon=0' 'AutoAggression=1' > "$DEST/FTA2/FTA2.INI"

python3 -I "$QUI/tools/crea_iso.py" FTA2DATI FTA2 "$DEST/FTA2DATI.ISO" \
	"$(trova "$ORIG" ftaimage.hrs)" "$(trova "$ORIG" ftasound.hrs)" "$(trova "$ORIG" ftavoice.hrs)"
rm -rf "${DEST:?}/lavoro" "${DEST:?}/hrs"
echo "Cartella per C:: $(du -sh "$DEST/FTA2" | cut -f1), $(find "$DEST/FTA2" -type f | wc -l) file"
