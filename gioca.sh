#!/bin/bash
# Avvia Faery Tale Adventure II con la ScummVM del progetto (motore saga2 con supporto alla versione DOS).
# Configurazione e salvataggi restano in prove/, separati da quelli della ScummVM di sistema.
QUI="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$QUI/prove/salvataggi" "$QUI/prove/schermate"
[ -f "$QUI/prove/scummvm.ini" ] || printf '[scummvm]\nfullscreen=false\n[fta2]\ngameid=fta2\nengineid=saga2\nsubtitles=true\npath=%s/gioco\n' "$QUI" > "$QUI/prove/scummvm.ini"
exec "$QUI/scummvm/scummvm" --config="$QUI/prove/scummvm.ini" --savepath="$QUI/prove/salvataggi" \
    --screenshotpath="$QUI/prove/schermate" "$@" fta2
