"""Controller board v2: netlist and placement (see README.md).

One generic board for every room: whatever a room does not use stays empty.
Coordinates in mm, origin top left, y down (as in KiCad).
Rotation (KiCad, counter-clockwise): 0 = pads of a row footprint run to +x (DIP and pin headers: to +y);
90 = DIP / pin header rows run to +x; -90 = fuse holders run down.
"""

NAME = "controller-board"
LIB = "/usr/share/kicad/footprints/"
URL = "github.com/krisp-be/esphome-room-controller"

# Arduino Nano ESP32 seen from the top with the USB-C to the left (west):
# north and south row, index 0 at the USB end.
NANO_NORTH = ["D12", "D11", "D10", "D9", "D8", "D7", "D6", "D5", "D4", "D3", "D2", "GND", "RST", "D0", "D1"]
NANO_SOUTH = ["D13", "3V3", "B0", "A0", "A1", "A2", "A3", "A4", "A5", "A6", "A7", "VBUS", "B1", "GND", "VIN"]

NANO_NET = {
    # West end of the north row, right below the 74AHCT125: strip data.
    "D12": "D_S1", "D10": "D_S2", "D9": "D_S3", "D11": "D_S4",
    # Rest of the north row heads east: MOSFET outputs and fast inputs.
    "D8": "MOS1", "D7": "MOS2", "D6": "MOS3", "D5": "MOS4",
    "D4": "IN1", "D3": "IN2", "D2": "IN3", "D0": "IN4", "D1": "IN5",
    # South row heads south and east: fans, expander interrupt, I2C.
    "A3": "PWM1", "A7": "PWM2", "A0": "TACH1", "A6": "TACH2",
    "A1": "INT", "A4": "SDA", "A5": "SCL",
    "GND": "GND", "3V3": "+3V3", "VIN": "+9V",
}


def nano_pads(row):
    names = NANO_NORTH if row == "N" else NANO_SOUTH
    return {str(i + 1): NANO_NET.get(n, "") for i, n in enumerate(names)}


WIDTH, HEIGHT = 170.0, 110.0
HOLES = [(3.5, 3.5), (WIDTH - 3.5, 3.5), (3.5, HEIGHT - 3.5), (WIDTH - 3.5, HEIGHT - 3.5)]
HOLE_KEEPOUT = 4.0                 # radius without copper around the mounting holes (M3 head + margin)

X_NANO, Y_NANO = 6.0, 68.5                  # pad 1 of the north row
T_Y = 6.0                                   # terminals, north edge
STRIP_X = [24.0, 42.0, 60.0, 78.0]          # STRIP 1..4
F_TOP = 17.0                                # top pad of the fuse holders (towards the terminal)
S_Y = HEIGHT - 6.0                          # terminals, south edge
OUT_X = [100.0, 114.0, 128.0, 142.0]        # OUT 1..4 (north edge)
IN_X = 164.0                                # IN 1..5 (east edge)
IN_Y = [35.5, 51.1, 66.7, 82.3, 97.9]       # bottom pad of each input terminal
FAN_X = [59.0, 102.0]                       # left edge of the isolated islands (FAN 1, 2)
FAN_Y = 80.0                                # top edge of the islands

R_AX = ("Resistor_THT", "R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal")
R_SHORT = ("Resistor_THT", "R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal")
TERM2 = ("TerminalBlock", "TerminalBlock_bornier-2_P5.08mm")
TERM3 = ("TerminalBlock", "TerminalBlock_bornier-3_P5.08mm")
C_CER = ("Capacitor_THT", "C_Disc_D5.0mm_W2.5mm_P5.00mm")
SCHOTTKY = ("Diode_THT", "D_DO-41_SOD81_P7.62mm_Horizontal")      # 1N5819 or BAT85 (DO-41 holes fit both), pad 1 = cathode
FLYBACK = ("Diode_THT", "D_DO-41_SOD81_P7.62mm_Horizontal")       # 1N5819, pad 1 = cathode
FUSE = ("Fuse", "Fuseholder_Cylinder-5x20mm_Stelvio-Kontek_PTF78_Horizontal_Open")
# Bigger holes: the fuse holder has flat legs of 1.4 x 0.45 mm (1.47 mm diagonal).
DRILLS = {FUSE[1]: 1.8}
MINI560 = ("", "MINI560")                                          # custom footprint in build.py
HDR = "Connector_PinHeader_2.54mm"

FAN_REF = {1: dict(iso_dc="U5", opto="U7", pwm="J6", led="R5", pu="R6", c="C9", bridge="W1", term="J19", rt="R15", dt="D5",
                  vsel="JP6"),
           2: dict(iso_dc="U10", opto="U11", pwm="J9", led="R7", pu="R8", c="C10", bridge="W2", term="J20", rt="R16", dt="D6",
                  vsel="JP7")}


def fan(k, x0):
    """FAN k: fast optocoupler (6N137) with its own isolated 5 V; terminal PWM/GNDiso inside the island,
    terminal V+/GND/TACH outside. Wire bridge W{k} ties GNDiso to GND (computer fan).
    Jumper JP{5 + k} selects V+ on the fan terminal: 1-2 = 12 V (default), 2-3 = 24 V (24 V fans only)."""
    iso, v5, out = f"GNDISO{k}", f"+5VISO{k}", f"PWM_OUT{k}"
    r = FAN_REF[k]
    return {
        r["iso_dc"]: ("", "SIP4", x0 - 3.81, 84.0, 0, {"1": "GND", "2": "+5V", "3": iso, "4": v5}, "HLK-1D0505A"),
        r["opto"]: ("Package_DIP", "DIP-8_W7.62mm_Socket", x0 - 3.81, 89.5, 0,
                    {"2": f"OPTO{k}_A", "3": "GND", "5": iso, "6": out, "7": v5, "8": v5}, "6N137"),
        r["pwm"]: (*TERM2, x0 + 6.5, S_Y, 0, {"1": out, "2": iso}, f"FAN {k} PWM"),
        r["led"]: (*R_SHORT, x0 - 8.5, 97.0, 90, {"1": f"PWM{k}", "2": f"OPTO{k}_A"}, "180"),
        r["pu"]: (*R_SHORT, x0 + 12.5, 97.0, 90, {"1": out, "2": v5}, "2k2"),
        r["c"]: (*C_CER, x0 + 8.0, 95.0, 90, {"1": iso, "2": v5}, "100n"),
        r["bridge"]: (*R_SHORT, x0 - 6.0, 101.0, 0, {"1": "GND", "2": iso}, "GND bridge"),
        r["term"]: (*TERM3, x0 - 22.0, S_Y, 0, {"1": f"FAN{k}_V", "2": "GND", "3": f"TACH{k}_IN"}, f"FAN {k}"),
        r["vsel"]: (HDR, "PinHeader_1x03_P2.54mm_Vertical", x0 - 22.5, 88.0, 0,
                    {"1": "+12V", "2": f"FAN{k}_V", "3": "+24V"}, f"FAN {k} V: 12V | 24V"),
        r["rt"]: (*R_SHORT, x0 - 19.0, 96.0, 90, {"1": f"TACH{k}_IN", "2": f"TACH{k}"}, "1k"),
        r["dt"]: (*SCHOTTKY, x0 - 15.0, 96.0, 90, {"1": "+3V3", "2": f"TACH{k}"}, "1N5819"),
    }


def mosfet(k, x):
    """OUT k: terminal +24V_M / OUTk, flyback diode, logic-level MOSFET, gate and pull-down resistor."""
    return {
        f"J{13 + k}": (*TERM2, x, T_Y, 0, {"1": "+24V_M", "2": f"OUT{k}"}, f"OUT {k}"),
        f"D{k}": (*FLYBACK, x, 15.5, 0, {"1": "+24V_M", "2": f"OUT{k}"}, "1N5819"),
        f"Q{k}": ("Package_TO_SOT_THT", "TO-220-3_Vertical", x + 1.0, 24.0, 0,
                  {"1": f"G{k}", "2": f"OUT{k}", "3": "GND"}, "IRLZ44N"),
        f"R{19 + k}": (*R_SHORT, x + 1.0, 36.0, 90, {"1": f"MOS{k}", "2": f"G{k}"}, "100"),
        f"R{23 + k}": (*R_SHORT, x + 5.0, 36.0, 90, {"1": "GND", "2": f"G{k}"}, "10k"),
    }


def fast_input(k, y):
    """IN k: terminal V/GND/SIG, supply jumper 3V3-V-5V, 1k series resistor and BAT85 clamp to 3.3 V."""
    return {
        f"J{21 + k}": (*TERM3, IN_X, y, 90, {"1": f"VIN{k}", "2": "GND", "3": f"IN{k}_IN"}, f"IN {k}"),
        f"JP{k}": (HDR, "PinHeader_1x03_P2.54mm_Vertical", 157.5, y - 7.6, 0,
                   {"1": "+3V3", "2": f"VIN{k}", "3": "+5V"}, f"IN {k} supply"),
        f"R{27 + k}": (*R_SHORT, 150.3, y - 1.0, 90, {"1": f"IN{k}_IN", "2": f"IN{k}"}, "1k"),
        f"D{6 + k}": (*SCHOTTKY, 153.8, y - 1.0, 90, {"1": "+3V3", "2": f"IN{k}"}, "1N5819"),
    }


# MCP23017 (DIP-28, rotation 90): bottom row pin 1..14 west to east, top row pin 15..28 east to west.
MCP_X, MCP_Y = 112.0, 60.0
MCP = {**{str(1 + i): f"IOB{i}" for i in range(8)}, "9": "+3V3", "10": "GND", "12": "SCL", "13": "SDA",
       "15": "GND", "16": "GND", "17": "GND", "18": "+3V3", "20": "INT",
       **{str(21 + i): f"IOA{i}" for i in range(8)}}
# IO A header (above, rotation 90): odd pins = IO west to east A7..A0, even pins = GND (north row).
HDR_A = {**{str(2 * j + 1): f"IOA{7 - j}" for j in range(8)}, **{str(2 * j + 2): "GND" for j in range(8)}}
# IO B header (below, rotation -90): odd pins = IO east to west B7..B0, even pins = GND (south row).
HDR_B = {**{str(2 * j + 1): f"IOB{7 - j}" for j in range(8)}, **{str(2 * j + 2): "GND" for j in range(8)}}

# ref -> (library, footprint, x, y, rotation, {pad: net}, value); library "" = custom footprint
PARTS = {
    # --- Nano ESP32 on two female headers (rows 15.24 mm apart)
    "U1A": ("Connector_PinSocket_2.54mm", "PinSocket_1x15_P2.54mm_Vertical", X_NANO, Y_NANO, 90, nano_pads("N"), "Nano ESP32 north"),
    "U1B": ("Connector_PinSocket_2.54mm", "PinSocket_1x15_P2.54mm_Vertical", X_NANO, Y_NANO + 15.24, 90, nano_pads("S"), "Nano ESP32 south"),
    # --- 24 V in and strip outputs (north edge)
    "J1": (*TERM2, 10.5, T_Y, 0, {"1": "+24V", "2": "GND"}, "24V in"),
    **{f"J{i + 1}": (*TERM3, x, T_Y, 0, {"1": f"+24V_S{i}", "2": "GND", "3": f"DATA{i}"}, f"STRIP {i}")
       for i, x in enumerate(STRIP_X, 1)},
    # --- fuses, vertical below the terminals (pad 1 at the top, towards the terminal); F5 for the OUT terminals
    **{f"F{i}": (*FUSE, x, F_TOP, -90, {"1": f"+24V_S{i}", "2": "+24V"}, "2A") for i, x in enumerate(STRIP_X, 1)},
    "F5": (*FUSE, 92.0, F_TOP, -90, {"1": "+24V_M", "2": "+24V"}, "4A"),
    # --- 24 V decoupling
    "C1": ("Capacitor_THT", "CP_Radial_D6.3mm_P2.50mm", 5.0, 21.0, 90, {"1": "+24V", "2": "GND"}, "47u/50V"),
    "C2": ("Capacitor_THT", "CP_Radial_D6.3mm_P2.50mm", 12.5, 21.0, 90, {"1": "+24V", "2": "GND"}, "47u/50V"),
    "C3": (*C_CER, 6.0, 30.0, 0, {"1": "+24V", "2": "GND"}, "100n"),
    # --- step-down modules, standing on pin headers (custom footprint, MEASURE the pads); position = top right
    "U3": (*MINI560, 68.5, 45.0, -90, {"1": "+24V", "2": "GND", "3": "+5V", "4": "GND"}, "Mini560 5V"),
    "U2": (*MINI560, 87.25, 45.0, -90, {"1": "+24V", "2": "GND", "3": "+9V", "4": "GND"}, "Mini560 9V"),
    "U8": (*MINI560, 106.0, 45.0, -90, {"1": "+24V", "2": "GND", "3": "+12V", "4": "GND"}, "Mini560 12V"),
    "C4": ("Capacitor_THT", "CP_Radial_D8.0mm_P3.50mm", 46.5, 83.0, 0, {"1": "+5V", "2": "GND"}, "220u/25V"),
    "C7": ("Capacitor_THT", "CP_Radial_D8.0mm_P3.50mm", 89.0, 83.0, 0, {"1": "+12V", "2": "GND"}, "220u/25V"),
    # --- level shifter 74AHCT125 (DIP-14 in a socket)
    "U4": ("Package_DIP", "DIP-14_W7.62mm_Socket", 5.0, 56.0, 90, {
        "1": "GND", "2": "D_S1", "3": "BUF1", "4": "GND", "5": "D_S2", "6": "BUF2", "7": "GND",
        "8": "BUF3", "9": "D_S3", "10": "GND", "11": "BUF4", "12": "D_S4", "13": "GND", "14": "+5V"}, "74AHCT125"),
    "C5": (*C_CER, 5.0, 44.0, 0, {"1": "+5V", "2": "GND"}, "100n"),
    # series resistors in the data lines (east of the pull-downs), pad 2 up
    **{f"R{i}": (*R_AX, 36.0 + 3.0 * (i - 1), 56.5, 90, {"1": f"BUF{i}", "2": f"DATA{i}"}, "220") for i in range(1, 5)},
    # pull-downs on the U4 inputs (east of U4)
    **{f"R{9 + i}": (*R_AX, 24.0 + 3.0 * (i - 1), 56.5, 90, {"1": f"D_S{i}", "2": "GND"}, "10k") for i in range(1, 5)},
    # --- MOSFET outputs (north east)
    **{ref: p for k, x in enumerate(OUT_X, 1) for ref, p in mosfet(k, x).items()},
    # --- fan channels with isolated islands (south edge)
    **fan(1, FAN_X[0]),
    **fan(2, FAN_X[1]),
    # --- fast inputs (east edge)
    **{ref: p for k, y in enumerate(IN_Y, 1) for ref, p in fast_input(k, y).items()},
    # --- I/O expander MCP23017 with two headers and the 433 MHz receiver
    "U9": ("Package_DIP", "DIP-28_W7.62mm_Socket", MCP_X, MCP_Y, 90, MCP, "MCP23017"),
    "J18": (HDR, "PinHeader_2x08_P2.54mm_Vertical", MCP_X, 46.0, 90, HDR_A, "IO A"),
    "J12": (HDR, "PinHeader_2x08_P2.54mm_Vertical", MCP_X + 7 * 2.54, 71.0, -90, HDR_B, "IO B"),
    # 433 MHz receiver between the MCP and IO B (measured pin order): pad 1..7 = VT, D0, D1, D2, D3, VDD, GND
    # on B3..B7. The module is 28.3 mm wide: its 4 unpinned pads (ST, LED, GND, ANT) overhang past VT (west).
    "U6": ("Connector_PinSocket_2.54mm", "PinSocket_1x07_P2.54mm_Vertical", MCP_X + 3 * 2.54, 66.0, 90,
           {"1": "IOB3", "2": "IOB4", "3": "IOB5", "4": "IOB6", "5": "IOB7", "6": "+3V3", "7": "GND"}, "433 MHz receiver"),
    "C8": (*C_CER, 139.0, 64.0, 0, {"1": "+3V3", "2": "GND"}, "100n"),
    # power for the relay module and other modules on the IO headers
    "J7": (HDR, "PinHeader_1x04_P2.54mm_Vertical", 139.0, 71.0, 90,
           {"1": "+5V", "2": "+5V", "3": "+3V3", "4": "GND"}, "MODULES"),
    # --- I²C out (south west) with pull-ups
    "J11": (*TERM2, 12.0, S_Y, 0, {"1": "+3V3", "2": "GND"}, "I2C power"),
    "J13": (*TERM2, 23.0, S_Y, 0, {"1": "SDA", "2": "SCL"}, "I2C"),
    "R33": (*R_SHORT, 28.5, 97.0, 90, {"1": "SDA", "2": "+3V3"}, "4k7"),
    "R34": (*R_SHORT, 31.5, 97.0, 90, {"1": "SCL", "2": "+3V3"}, "4k7"),
}

# Track widths per net (mm); everything else DEFAULT_WIDTH.
WIDTHS = {"+24V": 1.5, **{f"+24V_S{i}": 1.2 for i in range(1, 5)}, "+24V_M": 1.2,
          **{f"OUT{i}": 1.0 for i in range(1, 5)}, "+12V": 0.8, "FAN1_V": 0.8, "FAN2_V": 0.8, "+5V": 0.8, "+9V": 0.6, "+3V3": 0.5,
          **{f"+5VISO{k}": 0.5 for k in (1, 2)}}
DEFAULT_WIDTH = 0.3

# Isolated islands (x0, y0, x1, y1) on the south edge and their nets.
ISLANDS = {k: (x, FAN_Y, x + 16.0, HEIGHT) for k, x in enumerate(FAN_X, 1)}
ISOLATED = {n: k for k in ISLANDS for n in (f"GNDISO{k}", f"+5VISO{k}", f"PWM_OUT{k}")}
ISO_TRACK = 1.5    # minimum distance of ordinary tracks to isolated copper
ISO_PLANE = 2.0    # distance of the GND plane to an island


def _gnd_outline():
    w, h, m = WIDTH, HEIGHT, ISO_PLANE
    pts = [(0.3, 0.3), (w - 0.3, 0.3), (w - 0.3, h - 0.3)]
    for k, (x0, y0, x1, y1) in sorted(ISLANDS.items(), key=lambda e: -e[1][0]):
        pts += [(x1 + m, h - 0.3), (x1 + m, y0 - m), (x0 - m, y0 - m), (x0 - m, h - 0.3)]
    return pts + [(0.3, h - 0.3)]


# Nets laid as planes instead of routed: (net, layer, polygon); layer "F" or "B".
PLANES = [("GND", "F", _gnd_outline()), ("GND", "B", _gnd_outline())]
for _k, (_x0, _y0, _x1, _y1) in ISLANDS.items():
    _iso = [(_x0 + 0.2, _y0 + 0.2), (_x1 - 0.2, _y0 + 0.2), (_x1 - 0.2, HEIGHT - 0.3), (_x0 + 0.2, HEIGHT - 0.3)]
    PLANES += [(f"GNDISO{_k}", "F", _iso), (f"GNDISO{_k}", "B", _iso)]
PLANE_NETS = {n for n, _, _ in PLANES}
PLANE_THERMAL = True   # thermal reliefs: easier hand soldering on the GND planes

# Routed first (short connections in a tight area); GND pads the plane cannot reach get a track.
PRIORITY = ["GND", "IOB0", "IOB1", "IOB2", "IOB3", "IOB4", "IOB5", "IOB6", "IOB7", "D_S1", "D_S2", "D_S3", "D_S4", "BUF1", "BUF2", "BUF3", "BUF4"]
LAST = []
GND_TRACKS = {("U4", n) for n in ("1", "4", "7", "10", "13")} | {("C5", "2"), ("U5", "1"), ("U10", "1"), ("C7", "2"), ("U1A", "12"), ("U1B", "14")} | {(u, n) for u in ("U2", "U3", "U8") for n in ("2", "4")}
# GND pads that surely sit on the main plane: GND_TRACKS pads are routed to the nearest of these
# (not to a pad that may sit in a loose piece of plane).
GND_ANCHORS = ({("J1", "2"), ("J11", "2"), ("C1", "2"), ("C2", "2"), ("C3", "2"), ("U9", "10"), ("U6", "7"), ("J7", "4")}
               | {(f"J{i}", "2") for i in (2, 3, 4, 5, 19, 20, 22, 23, 24, 25, 26)}
               | {(f"Q{k}", "3") for k in range(1, 5)} | {(f"R{k}", "1") for k in range(24, 28)}
               | {(f"R{k}", "2") for k in range(10, 14)}
               | {(j, str(n)) for j in ("J18", "J12") for n in range(2, 17, 2)})
# Areas where only GND may run (between the pin rows of U4, for the OE pins).
GND_CHANNELS = []

# Silkscreen (F.SilkS): (text, x, y, rotation, height)
TEXTS = [
    ("24V IN  +  -", 13.0, 12.6, 0, 1.0),
    *[(f"STRIP {i}: +24  GND  DATA", x + 5.08, 12.6, 0, 0.9) for i, x in enumerate(STRIP_X, 1)],
    *[(f"OUT {k}: +24  -", x + 2.54, 11.6, 0, 0.8) for k, x in enumerate(OUT_X, 1)],
    *[(f"IN {k}: V GND SIG", IN_X - 7.0, y - 5.08, 90, 0.8) for k, y in enumerate(IN_Y, 1)],
    *[("3V3 / V / 5V", 157.5 - 2.6, y - 5.08, 90, 0.6) for y in IN_Y],
    *[(f"FAN {k}: V+ GND TACH", x - 16.9, S_Y - 5.4, 0, 0.7) for k, x in enumerate(FAN_X, 1)],
    *[("FAN V: 12V | 24V", x - 24.7, 90.54, 90, 0.6) for x in FAN_X],
    *[("12V", x - 20.6, 88.0, 0, 0.55) for x in FAN_X],
    *[("24V", x - 20.6, 93.08, 0, 0.55) for x in FAN_X],
    *[("24V = 24V fans only!", x - 17.0, 85.2, 0, 0.6) for x in FAN_X],
    *[("PWM GNDiso", x + 9.0, S_Y - 5.4, 0, 0.7) for x in FAN_X],
    *[(f"ISOLATED {k}", x + 8.0, FAN_Y + 2.0, 0, 0.8) for k, x in enumerate(FAN_X, 1)],
    *[("GND bridge: PC fan only", x - 2.2, 103.2, 0, 0.55) for x in FAN_X],
    ("I2C 3V3 GND", 14.5, S_Y - 5.4, 0, 0.7),
    ("SDA SCL", 25.5, S_Y - 5.4, 0, 0.7),
    ("IO A: A7 ............ A0", 120.9, 49.3, 0, 0.8),
    ("IO B: B0 ............ B7", 120.9, 76.8, 0, 0.8),
    ("433: VT D0 D1 D2 D3 3V3 GND", 127.5, 68.4, 0, 0.6),
    ("MODULES 5V 5V 3V3 GND", 142.8, 73.4, 0, 0.6),
    ("ESPHOME ROOM CONTROLLER v2", 15.5, 89.0, 0, 1.1),
    ("24 V - Nano ESP32 - 2026-11", 15.5, 91.6, 0, 0.8),
    (URL, 15.5, 93.8, 0, 0.75),
]
