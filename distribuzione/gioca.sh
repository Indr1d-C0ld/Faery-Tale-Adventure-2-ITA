#!/bin/bash
# Avvia Faery Tale Adventure II restaurato e tradotto. Prima va eseguito ./installa.sh.
# Impostazioni e salvataggi restano in questa cartella (impostazioni/ e salvataggi/).
# Per riprendere una partita all'avvio: ./gioca.sh -x NUMERO_DEL_SALVATAGGIO
QUI="$(cd "$(dirname "$0")" && pwd)"
[ -f "$QUI/gioco/scripts.hrs" ] || { echo "Prima esegui ./installa.sh CARTELLA_DEL_GIOCO_ORIGINALE"; exit 1; }
exec "$QUI/scummvm" --config="$QUI/impostazioni/scummvm.ini" --savepath="$QUI/salvataggi" "$@" fta2
