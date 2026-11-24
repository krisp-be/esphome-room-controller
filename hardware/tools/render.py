"""Draw a check image of a board (pads, courtyards, tracks, planes) as PNG.

    python render.py <file.kicad_pcb> <out.png> [title]
"""
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon, Rectangle
import nodump  # noqa: F401  (before pcbnew: no crash dumps)
import pcbnew

TM = pcbnew.ToMM


def outlines(sp):
    out = []
    for i in range(sp.OutlineCount()):
        o = sp.Outline(i)
        out.append([(TM(o.CPoint(j).x), TM(o.CPoint(j).y)) for j in range(o.PointCount())])
    return out


def draw(board, png, title=""):
    bb = board.GetBoardEdgesBoundingBox()
    w, h = TM(bb.GetWidth()), TM(bb.GetHeight())
    fig, ax = plt.subplots(figsize=(14, 14 * h / w + 0.6))
    for z in board.Zones():
        if z.GetIsRuleArea() or not z.IsFilled():
            continue
        colour = "#c0392b" if z.GetLayer() == pcbnew.F_Cu else "#2e86c1"
        polys = z.GetFilledPolysList(z.GetLayer())
        for i in range(polys.OutlineCount()):
            pts = polys.Outline(i)
            ax.add_patch(Polygon([(TM(pts.CPoint(j).x), TM(pts.CPoint(j).y)) for j in range(pts.PointCount())],
                                 closed=True, fc=colour, alpha=0.12, ec="none"))
    for t in board.GetTracks():
        if t.GetClass() == "PCB_VIA":
            ax.add_patch(Circle((TM(t.GetPosition().x), TM(t.GetPosition().y)), TM(t.GetWidth()) / 2, fc="#555", ec="k", lw=0.3))
            continue
        colour = "#c0392b" if t.GetLayer() == pcbnew.F_Cu else "#2e86c1"
        ax.plot([TM(t.GetStart().x), TM(t.GetEnd().x)], [TM(t.GetStart().y), TM(t.GetEnd().y)], color=colour,
                lw=TM(t.GetWidth()) * 2.6, solid_capstyle="round", alpha=0.85)
    for fp in board.GetFootprints():
        for pts in outlines(fp.GetCourtyard(pcbnew.F_CrtYd)):
            ax.add_patch(Polygon(pts, closed=True, fill=False, ec="#999", lw=0.6))
        for p in fp.Pads():
            for pts in outlines(p.GetEffectivePolygon()):
                ax.add_patch(Polygon(pts, closed=True, fc="#d4ac0d", ec="k", lw=0.2))
            if p.GetNetname() and p.GetNetname() != "GND":
                ax.text(TM(p.GetPosition().x), TM(p.GetPosition().y) + 1.2, p.GetNetname(), fontsize=3.2, ha="center", color="#333")
        ax.text(TM(fp.GetPosition().x), TM(fp.GetPosition().y) - 1.5, fp.GetReference(), fontsize=6, color="blue", ha="center")
    ax.add_patch(Rectangle((TM(bb.GetX()), TM(bb.GetY())), w, h, fill=False, ec="k", lw=1))
    ax.set_xlim(TM(bb.GetX()) - 3, TM(bb.GetRight()) + 3); ax.set_ylim(TM(bb.GetBottom()) + 3, TM(bb.GetY()) - 3)
    ax.set_aspect("equal"); ax.set_title(title); ax.grid(alpha=0.2)
    fig.tight_layout(); fig.savefig(png, dpi=110); plt.close(fig)


if __name__ == "__main__":
    draw(pcbnew.LoadBoard(sys.argv[1]), sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "")
