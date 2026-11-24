# Hardware

| Board | Size | What it does |
|---|---|---|
| [controller-board](controller-board) | about 170 × 110 mm | The brain: Arduino Nano ESP32 with ESPHome, 4 LED strip outputs, 2 fan channels, 4 MOSFET outputs, 5 sensor inputs, I/O expander, 433 MHz receiver socket. One per room. |
| [led-distribution-board](led-distribution-board) | 100 × 80 mm | Splits one strip output into 8 ports: power in parallel (PTC per port), data in series. Chainable. |

Both are simple 2-layer through-hole boards: easy to solder by hand and cheap to order
(PCBWay, JLCPCB, …: minimum order is usually 5 boards, which is enough for a few rooms).

## Tools

The boards are not drawn by hand: each board folder has a `parts.py` with the placement and the
netlist, and the scripts in [`tools`](tools) turn that into a routed KiCad board, run the design
rule check and export the Gerbers.

| File | What |
|---|---|
| `tools/build.py` | builds `<board>.kicad_pcb` from `parts.py`: footprints, nets, outline, holes, routing, planes |
| `tools/router.py` | small 2-layer grid router (A*), copper planes, keep-outs, optional isolated islands |
| `tools/render.py` | check image (PNG) of a board |
| `tools/drc.sh` | KiCad DRC with a short summary |
| `tools/make-board.sh` | all of the above + Gerbers, drill file, zip, SVG and PNG images |

Requirements: KiCad 8 (for `pcbnew` and `kicad-cli`) and Python 3 with numpy, scipy and matplotlib:

```bash
cd hardware/tools
python3 -m venv --system-site-packages .venv
.venv/bin/pip install numpy scipy matplotlib
./make-board.sh ../led-distribution-board
```

The `.kicad_pcb` files open in KiCad for inspection or manual changes, but a rebuild overwrites them:
make permanent changes in `parts.py`.
