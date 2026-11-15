#!/bin/bash
# Crea il pacchetto da distribuire del restauro italiano di Faery Tale Adventure II.
#
# Uso:
#   tools/crea_pacchetto.sh VERSIONE        (es. 1.0.0)
#
# Il pacchetto (dist/fta2-restauro-ita-VERSIONE-linux-x86_64.tar.gz) NON contiene file del gioco:
# contiene il motore ScummVM modificato (GPL3), gli strumenti, le patch e la traduzione.
# Chi lo riceve esegue installa.sh indicando la propria copia originale del gioco, e
# l'installatore costruisce lì accanto la versione restaurata e tradotta.

set -euo pipefail
QUI="$(cd "$(dirname "$0")/.." && pwd)"
VER="${1:?indica la versione, es. 1.0.0}"
NOME="fta2-restauro-ita-$VER-linux-x86_64"
DEST="$QUI/dist/$NOME"

rm -rf "${DEST:?}"
mkdir -p "$DEST/tools" "$DEST/patch/script" "$DEST/traduzione"

# motore: la build di rilascio del ramo melchior-fta2
install -m 755 "$QUI/scummvm/scummvm" "$DEST/scummvm"
strip "$DEST/scummvm"

# strumenti necessari all'installazione
for f in costruisci.py traduzione.py hreslib.py hreswrite.py sagadis.py sagaasm.py stringhe.py \
         cfunc_actor.txt cfunc_global.txt cfunc_mission.txt cfunc_tag.txt vtable_member.tsv; do
	cp "$QUI/tools/$f" "$DEST/tools/"
done

# patch (solo differenze e tabelle: niente copie dei moduli originali) e traduzione
cp "$QUI"/patch/*.tsv "$DEST/patch/"
cp "$QUI"/patch/script/*.diff "$DEST/patch/script/"
cp "$QUI/traduzione/testi_it.tsv" "$QUI/traduzione/nomi_it.tsv" "$DEST/traduzione/"

cp "$QUI/LICENSE" "$DEST/LICENSE"
cp "$QUI/distribuzione/LEGGIMI.txt" "$QUI/distribuzione/installa.sh" "$QUI/distribuzione/gioca.sh" "$DEST/"
chmod +x "$DEST/installa.sh" "$DEST/gioca.sh"
sed -i "s/@VERSIONE@/$VER/g" "$DEST/LEGGIMI.txt"

tar -C "$QUI/dist" -czf "$QUI/dist/$NOME.tar.gz" "$NOME"
( cd "$QUI/dist" && sha256sum "$NOME.tar.gz" > "$NOME.tar.gz.sha256" )
echo "Pacchetto: dist/$NOME.tar.gz ($(du -h "$QUI/dist/$NOME.tar.gz" | cut -f1))"
