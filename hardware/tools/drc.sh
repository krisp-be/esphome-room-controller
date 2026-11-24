#!/bin/bash
# Run the KiCad DRC (errors and warnings) and print a summary. Exits non-zero on any finding.
#   ./drc.sh board.kicad_pcb
PCB="$1"
OUT="$(mktemp --suffix=.json)"
kicad-cli pcb drc --format json --severity-all -o "$OUT" "$PCB" >/dev/null 2>&1
python3 - "$OUT" <<'PY'
import json, sys
from collections import Counter
d = json.load(open(sys.argv[1]))
v = d["violations"]; u = d.get("unconnected_items", [])
print("DRC findings:", dict(Counter(x["type"] for x in v)) or "none", "| unconnected:", len(u))
for x in v:
    print("  ", x["type"], "|", " / ".join(i["description"] for i in x["items"]))
sys.exit(1 if v or u else 0)
PY
