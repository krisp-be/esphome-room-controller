"""Build a board (.kicad_pcb) from its parts.py: placement, nets, outline, holes, tracks, planes.

    python build.py <board-dir>             # place + route + fill + save
    python build.py <board-dir> --place     # place only (quick check)

<board-dir>/parts.py describes the board (see led-distribution-board/parts.py for an example).
The output is <board-dir>/<parts.NAME>.kicad_pcb.
"""
import importlib.util
import sys
from pathlib import Path

import pcbnew

import router

MM = pcbnew.FromMM


def v(x, y):
    return pcbnew.VECTOR2I(MM(x), MM(y))


def load_parts(board_dir):
    spec = importlib.util.spec_from_file_location("parts", Path(board_dir) / "parts.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# --- custom footprints -------------------------------------------------------------------------

def pad_tht(fp, number, x, y, d=1.8, drill=1.0, shape="round"):
    p = pcbnew.PAD(fp)
    p.SetNumber(number)
    p.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
    p.SetShape(pcbnew.PAD_SHAPE_RECTANGLE if shape == "square" else pcbnew.PAD_SHAPE_CIRCLE)
    p.SetSize(v(d, d))
    p.SetDrillSize(v(drill, drill))
    p.SetLayerSet(pcbnew.PAD.PTHMask())
    fp.Add(p)
    p.SetFPRelativePosition(v(x, y))
    return p


def rectangle(fp, x0, y0, x1, y1, layer, width=0.12):
    for (a, b), (c, d) in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
        s = pcbnew.PCB_SHAPE(fp)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetLayer(layer)
        s.SetWidth(MM(width))
        fp.Add(s)
        s.SetStart(v(a, b)); s.SetEnd(v(c, d))
        s.Move(fp.GetPosition())   # SetStart/End are absolute; the footprint is still at 0,0


def label(fp, t, x, y, layer=pcbnew.F_SilkS, h=1.0):
    s = pcbnew.PCB_TEXT(fp)
    s.SetText(t)
    s.SetLayer(layer)
    s.SetTextSize(v(h, h))
    s.SetTextThickness(MM(h * 0.15))
    fp.Add(s)
    s.SetFPRelativePosition(v(x, y))


def custom_footprint(board, name):
    fp = pcbnew.FOOTPRINT(board)
    if name == "MINI560":
        # Placeholder: module about 30 x 18 mm, input (IN+, GND) left, output (OUT+, GND) right,
        # two holes at 2.54 mm each. MEASURE the real module and adjust.
        pad_tht(fp, "1", 2.0, 7.73, shape="square")
        pad_tht(fp, "2", 2.0, 10.27)
        pad_tht(fp, "3", 28.0, 7.73, shape="square")
        pad_tht(fp, "4", 28.0, 10.27)
        rectangle(fp, 0, 0, 30, 18, pcbnew.F_SilkS)
        rectangle(fp, -0.25, -0.25, 30.25, 18.25, pcbnew.F_CrtYd, 0.05)
        label(fp, "IN+", 5.2, 7.73, h=0.9); label(fp, "OUT", 24.8, 7.73, h=0.9)
    elif name == "SIP4":
        # Hi-Link HLK-1D0505A / B0505S: 1 GND, 2 VIN | 3 0V, 4 +VO, pitch 2.54. CHECK the datasheet.
        for i in range(4):
            pad_tht(fp, str(i + 1), 2.54 * i, 0, d=1.7, drill=0.9, shape="square" if i == 0 else "round")
        rectangle(fp, -2.0, -3.0, 9.6, 3.0, pcbnew.F_SilkS)
        rectangle(fp, -2.25, -3.25, 9.85, 3.25, pcbnew.F_CrtYd, 0.05)
    else:
        raise ValueError(name)
    return fp


# --- board -------------------------------------------------------------------------------------

def build_board(P):
    board = pcbnew.BOARD()
    ds = board.GetDesignSettings()
    ds.SetCopperLayerCount(2)
    nc = ds.m_NetSettings.m_DefaultNetClass
    nc.SetClearance(MM(0.25)); nc.SetTrackWidth(MM(0.3)); nc.SetViaDiameter(MM(0.8)); nc.SetViaDrill(MM(0.4))
    ds.m_MinResolvedSpokes = 1
    ds.m_TrackMinWidth = MM(0.2); ds.m_ViasMinSize = MM(0.6); ds.m_MinThroughDrill = MM(0.3)

    nets = {}

    def net(name):
        if name not in nets:
            n = pcbnew.NETINFO_ITEM(board, name)
            board.Add(n)
            nets[name] = n
        return nets[name]

    for ref, (lib, name, x, y, rot, pads, value) in P.PARTS.items():
        fp = pcbnew.FootprintLoad(P.LIB + lib + ".pretty", name) if lib else custom_footprint(board, name)
        fp.SetReference(ref)
        fp.SetValue(value)
        fp.Value().SetVisible(False)
        if ref.startswith("J"):
            fp.Reference().SetVisible(False)   # terminals have their own silkscreen labels
        board.Add(fp)
        fp.SetOrientationDegrees(rot)
        fp.SetPosition(v(x, y))
        for number, netname in pads.items():
            if not netname:
                continue
            for p in fp.Pads():
                if p.GetNumber() == number:
                    p.SetNet(net(netname))
    w, h = P.WIDTH, P.HEIGHT
    for (a, b), (c, d) in (((0, 0), (w, 0)), ((w, 0), (w, h)), ((w, h), (0, h)), ((0, h), (0, 0))):
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(MM(0.1))
        s.SetStart(v(a, b)); s.SetEnd(v(c, d))
        board.Add(s)
    for t, x, y, rot, height in P.TEXTS:
        s = pcbnew.PCB_TEXT(board)
        s.SetText(t); s.SetLayer(pcbnew.F_SilkS)
        s.SetTextSize(v(height, height)); s.SetTextThickness(MM(height * 0.15))
        s.SetPosition(v(x, y)); s.SetTextAngleDegrees(rot)
        board.Add(s)
    for i, (x, y) in enumerate(P.HOLES, 1):
        fp = pcbnew.FootprintLoad(P.LIB + "MountingHole.pretty", "MountingHole_3.2mm_M3")
        fp.SetReference(f"H{i}"); fp.Reference().SetVisible(False)
        board.Add(fp); fp.SetPosition(v(x, y))
    return board


def main():
    board_dir = Path(sys.argv[1]).resolve()
    P = load_parts(board_dir)
    router.P = P
    out = board_dir / f"{P.NAME}.kicad_pcb"
    board = build_board(P)
    if "--place" not in sys.argv:
        # Nets that fail move to the front and the whole board is routed again.
        best = None
        keep = [board]   # keep old boards alive: pcbnew sometimes crashes when they are freed
        for attempt in range(8):
            failed = router.route(board, verbose=False)
            if best is None or len(failed) < len(best[1]):
                best = (board, failed)
            if not failed:
                break
            print(f"attempt {attempt + 1}: {len(failed)} failed, retrying with priority", flush=True)
            for name, _ in failed:
                if name in P.PRIORITY:
                    P.PRIORITY.remove(name)
                P.PRIORITY.insert(0, name)
            board = build_board(P)
            keep.append(board)
        board, failed = best
        if failed:
            print("best attempt, still not routed:", failed)
        router.planes(board)
    pcbnew.SaveBoard(str(out), board)
    if "--place" not in sys.argv:
        router.fill(out)
    print("saved:", out)


if __name__ == "__main__":
    main()
