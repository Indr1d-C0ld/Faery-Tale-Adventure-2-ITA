#!/bin/bash
# Scarica ScummVM 2026.4.0, applica le patch del restauro (motore/*.patch) e compila il solo
# motore SAGA2.
#
# Uso:
#   tools/compila_motore.sh [cartella]      (predefinita: scummvm/ nella cartella del progetto)
#
# Servono git, un compilatore C++ e le librerie di sviluppo di SDL2, zlib, FreeType e libpng.
# Su Debian e Ubuntu: sudo apt install build-essential git libsdl2-dev zlib1g-dev libfreetype-dev libpng-dev
# Il programma compilato è <cartella>/scummvm.

set -euo pipefail
QUI="$(cd "$(dirname "$0")/.." && pwd)"
DEST="${1:-$QUI/scummvm}"
VERSIONE=v2026.4.0

if [ ! -d "$DEST/.git" ]; then
	git clone --depth 1 --branch "$VERSIONE" https://github.com/scummvm/scummvm.git "$DEST"
fi
cd "$DEST"
if ! git rev-parse --verify -q melchior-fta2 >/dev/null; then
	git checkout -q -b melchior-fta2 "$VERSIONE"
	git -c user.name="FTA2 restauro" -c user.email="fta2-restauro@localhost" am -q "$QUI"/motore/*.patch
fi
git checkout -q melchior-fta2
[ -f config.mk ] || ./configure --disable-all-engines --enable-engine=saga2 --enable-release --disable-debug --disable-tts
make -j"$(nproc)"
echo "Motore pronto: $DEST/scummvm"
