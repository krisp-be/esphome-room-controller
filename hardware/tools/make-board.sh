#!/bin/bash
# Rebuild a board: place, route, fill, DRC, Gerbers + drill (zip for the PCB fab), SVG and PNG previews.
#   ./make-board.sh ../led-distribution-board
set -e
TOOLS="$(cd "$(dirname "$0")" && pwd)"
BOARD="$(cd "$1" && pwd)"
PY="$TOOLS/.venv/bin/python"
NAME=$("$PY" -c "import sys; sys.path.insert(0, '$BOARD'); import parts; print(parts.NAME)")
PCB="$BOARD/$NAME.kicad_pcb"
cd "$TOOLS"
# pcbnew sometimes crashes while rebuilding; just try again.
for i in 1 2 3 4 5; do "$PY" build.py "$BOARD" && break; echo "retry ($i)"; done
"$TOOLS/drc.sh" "$PCB"
OUT="$BOARD/fabrication"
rm -rf "$OUT/gerbers" && mkdir -p "$OUT/gerbers"
kicad-cli pcb export gerbers --layers F.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,Edge.Cuts --use-drill-file-origin -o "$OUT/gerbers/" "$PCB" >/dev/null
kicad-cli pcb export drill --format excellon --drill-origin absolute --excellon-units mm -o "$OUT/gerbers/" "$PCB" >/dev/null
rm -f "$OUT/$NAME-gerbers.zip"
(cd "$OUT/gerbers" && python3 -c "
import zipfile, os
with zipfile.ZipFile('../$NAME-gerbers.zip', 'w', zipfile.ZIP_DEFLATED) as z:
    for f in sorted(os.listdir('.')): z.write(f)
")
mkdir -p "$BOARD/images"
kicad-cli pcb export svg --layers F.Cu,F.Silkscreen,Edge.Cuts --page-size-mode 2 --exclude-drawing-sheet -o "$BOARD/images/front.svg" "$PCB" >/dev/null
kicad-cli pcb export svg --layers B.Cu,Edge.Cuts --mirror --page-size-mode 2 --exclude-drawing-sheet -o "$BOARD/images/back.svg" "$PCB" >/dev/null
"$PY" render.py "$PCB" "$BOARD/images/layout.png" "$NAME"
echo "done: $OUT/$NAME-gerbers.zip"
