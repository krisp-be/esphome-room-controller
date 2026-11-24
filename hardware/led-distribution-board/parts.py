"""LED distribution board: 8 ports, netlist and placement (see README.md).

Power (+24 V, GND) goes to every port in parallel, each through its own PTC.
Data runs in series: IN -> port 1 DI, strip 1, port 1 DO -> port 2 DI ... port 8 DO -> OUT.
One jumper per port bridges DI-DO when the port is empty.

Coordinates in mm, origin top left, y down (as in KiCad).
Rotation (KiCad, counter-clockwise): 0 = pads run to +x; 180 = to -x; 90 = up; -90 = down.
On the screw terminals the wire entry is on the +y side of the footprint (rotation 0 = facing down).
"""

NAME = "led-distribution-board"
LIB = "/usr/share/kicad/footprints/"
URL = "github.com/krisp-be/esphome-room-controller"

WIDTH, HEIGHT = 100.0, 80.0
HOLES = [(32.0, 27.0), (68.0, 27.0), (32.0, 53.0), (68.0, 53.0)]
HOLE_KEEPOUT = 4.0                 # radius without copper around the mounting holes (M3 head + margin)

TERM2 = ("TerminalBlock", "TerminalBlock_bornier-2_P5.08mm")
TERM3 = ("TerminalBlock", "TerminalBlock_bornier-3_P5.08mm")
TERM4 = ("TerminalBlock", "TerminalBlock_bornier-4_P5.08mm")
PTC = ("Capacitor_THT", "C_Disc_D9.0mm_W5.0mm_P5.00mm")          # radial PTC, leads 5.1 mm apart
JUMPER = ("Connector_PinHeader_2.54mm", "PinHeader_1x02_P2.54mm_Vertical")
R_AX = ("Resistor_THT", "R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal")

PITCH = 23.7                       # distance between two ports (terminal 20.7 mm wide + 3 mm)
X_LEFT = [6.73 + k * PITCH for k in range(4)]   # x of the leftmost pin of each port
Y_TOP, Y_BOTTOM = 5.0, HEIGHT - 5.0             # pin row of the terminals
Y_PTC_TOP, Y_PTC_BOTTOM = 14.0, HEIGHT - 14.0


def dnet(k):
    """Data nets: D0 = IN, Dk = after port k, D8 = OUT."""
    return {0: "DATA_IN", 8: "DATA_OUT"}.get(k, f"D{k}")


# ref -> (library, footprint, x, y, rotation, {pad: net}, value); library "" = custom footprint
PARTS = {}
for k in range(8):
    p = k + 1
    top = k < 4
    xl = X_LEFT[k % 4]
    din, dout = dnet(k), dnet(k + 1)
    if top:
        # Wire entry towards the top edge: rotation 180, pad 1 on the right. Left to right: +24 GND DI DO.
        PARTS[f"J{p}"] = (*TERM4, xl + 15.24, Y_TOP, 180,
                          {"4": f"+24V_P{p}", "3": "GND", "2": din, "1": dout}, f"port {p}")
        y_row = Y_PTC_TOP
    else:
        # Wire entry towards the bottom edge: rotation 0, pad 1 on the left. Left to right: +24 GND DI DO.
        PARTS[f"J{p}"] = (*TERM4, xl, Y_BOTTOM, 0,
                          {"1": f"+24V_P{p}", "2": "GND", "3": din, "4": dout}, f"port {p}")
        y_row = Y_PTC_BOTTOM
    # PTC: pad 1 below the +24 pin, pad 2 to the +24 V plane.
    PARTS[f"F{p}"] = (*PTC, xl, y_row, 0, {"1": f"+24V_P{p}", "2": "+24V"}, "PTC 1.1A")
    # DI-DO bridge, horizontal between the DI and DO pins.
    PARTS[f"JP{p}"] = (*JUMPER, xl + 11.43, y_row, 90, {"1": din, "2": dout}, "bridge if empty")

# Inputs on the left (wire to the left, pads run down), output on the right (wire to the right, pads run up).
PARTS.update({
    "J9": (*TERM2, 5.0, 24.0, -90, {"1": "+24V", "2": "GND"}, "24V in"),
    "J10": (*TERM3, 5.0, 40.0, -90, {"1": "+24V_IN", "2": "GND", "3": "DATA_IN"}, "IN"),
    "J11": (*TERM3, 95.0, 50.16, 90, {"3": "+24V_OUT", "2": "GND", "1": "DATA_OUT"}, "OUT"),
    "JP9": (*JUMPER, 14.0, 40.0, 0, {"1": "+24V_IN", "2": "+24V"}, "24V via IN"),
    "JP10": (*JUMPER, 86.0, 40.0, 0, {"1": "+24V_OUT", "2": "+24V"}, "24V to OUT"),
    "C1": ("Capacitor_THT", "CP_Radial_D8.0mm_P3.50mm", 15.5, 25.0, 0, {"1": "+24V", "2": "GND"}, "47u/50V"),
    "R1": (*R_AX, 12.0, 33.0, 0, {"1": "+24V", "2": "LED_A"}, "4k7"),
    "D1": ("LED_THT", "LED_D3.0mm", 27.54, 33.0, 180, {"1": "GND", "2": "LED_A"}, "LED 24V"),
})

# Track widths per net (mm); everything else DEFAULT_WIDTH.
WIDTHS = {**{f"+24V_P{p}": 1.5 for p in range(1, 9)}, "+24V_IN": 1.2, "+24V_OUT": 1.2}
DEFAULT_WIDTH = 0.4

# Nets laid as planes instead of routed: (net, layer, polygon); layer "F" or "B".
_edge = [(0.3, 0.3), (WIDTH - 0.3, 0.3), (WIDTH - 0.3, HEIGHT - 0.3), (0.3, HEIGHT - 0.3)]
PLANES = [("+24V", "F", _edge), ("GND", "B", _edge)]
PLANE_NETS = {n for n, _, _ in PLANES}

PRIORITY = [dnet(k) for k in range(9)]   # routed first
LAST = []

# Silkscreen (F.SilkS): (text, x, y, rotation, height)
TEXTS = []
for k in range(8):
    xl = X_LEFT[k % 4]
    top = k < 4
    y_hint = 17.6 if top else HEIGHT - 17.6
    y_pins = 10.6 if top else HEIGHT - 10.6
    TEXTS += [
        (f"{k + 1}", xl - 3.6, y_pins + (0.6 if top else -0.6), 0, 2.0),
        ("+24", xl, y_pins, 0, 0.9), ("GND", xl + 5.08, y_pins, 0, 0.9),
        ("DI", xl + 10.16, y_pins, 0, 0.9), ("DO", xl + 15.24, y_pins, 0, 0.9),
        ("bridge=empty", xl + 12.7, y_hint, 0, 0.9),
    ]
TEXTS += [
    ("24V IN", 10.5, 19.5, 0, 1.0), ("+", 10.5, 24.0, 0, 1.0), ("-", 10.5, 29.08, 0, 1.0),
    ("IN", 5.0, 35.0, 0, 1.2),
    ("+24", 10.8, 40.0, 0, 0.8), ("GND", 10.8, 45.08, 0, 0.8), ("DATA", 11.2, 50.16, 0, 0.8),
    ("24V via IN", 17.0, 47.5, 0, 0.9),
    ("OUT", 95.0, 35.0, 0, 1.2),
    ("+24", 89.2, 40.0, 0, 0.8), ("GND", 89.2, 45.08, 0, 0.8), ("DATA", 88.8, 50.16, 0, 0.8),
    ("24V to OUT", 83.0, 47.5, 0, 0.9),
    ("LED DISTRIBUTION BOARD 8x", 50.0, 36.0, 0, 1.6),
    ("24 V - PTC per port - v1 2026-11", 50.0, 39.5, 0, 1.0),
    (URL, 50.0, 44.5, 0, 1.0),
]
