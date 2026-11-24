"""Small grid router (A*/Dijkstra on 2 layers) plus copper planes.

Nets listed in `parts.PLANE_NETS` are not routed: they are copper zones (see `parts.PLANES`).
Every other net is connected pad by pad: the tree grows from the first pad, each time towards the
nearest pad that is not connected yet. Preferred direction: F.Cu horizontal, B.Cu vertical.

Optional isolated islands (`parts.ISLANDS`, `parts.ISOLATED`): nets of island k may only run inside
island k; all other nets stay outside every island, at least `parts.ISO_TRACK` mm away from isolated copper.

The board module is injected by build.py as the module-level name `P`.
"""
import heapq
import math

import numpy as np
import pcbnew
from matplotlib.path import Path as MPath
from scipy.ndimage import binary_dilation, distance_transform_edt

P = None                 # board parts module, set by build.py

G = 0.25                 # grid size (mm)
CLR = 0.25               # minimum copper-to-copper clearance (mm)
EDGE = 0.6               # clearance to the board edge
VIA_D, VIA_DRILL = 0.8, 0.4
VIA_COST = 12.0          # in grid steps
OFF_AXIS = 1.25          # cost factor against the preferred direction of a layer
LAYERS = (pcbnew.F_Cu, pcbnew.B_Cu)
MM = pcbnew.FromMM
TM = pcbnew.ToMM


def islands():
    return getattr(P, "ISLANDS", {}) or {}


class Grid:
    def __init__(self, board):
        self.board = board
        self.nx = int(math.ceil(P.WIDTH / G))
        self.ny = int(math.ceil(P.HEIGHT / G))
        self.copper = np.full((2, self.ny, self.nx), -1, dtype=np.int32)   # net code per cell, -2 = blocked
        self.padcopper = np.full((self.ny, self.nx), -1, dtype=np.int32)   # net code of plated-through pads
        self.core = np.full((self.ny, self.nx), -1, dtype=np.int32)        # net code around pad centres (0.3 mm)
        xs = (np.arange(self.nx) + 0.5) * G
        ys = (np.arange(self.ny) + 0.5) * G
        self.X, self.Y = np.meshgrid(xs, ys)
        for fp in board.GetFootprints():
            for p in fp.Pads():
                code = p.GetNetCode() if p.GetNetCode() > 0 else -2
                layers = [0, 1] if p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH) else [0]
                sp = p.GetEffectivePolygon()
                for i in range(sp.OutlineCount()):
                    o = sp.Outline(i)
                    pts = [(TM(o.CPoint(j).x), TM(o.CPoint(j).y)) for j in range(o.PointCount())]
                    self._polygon(pts, code, layers)
                    if len(layers) == 2:
                        self._polygon_pth(pts, code)
                c = p.GetPosition()
                sj, si = self._box(TM(c.x) - 0.4, TM(c.y) - 0.4, TM(c.x) + 0.4, TM(c.y) + 0.4)
                kb = self.core[sj, si]
                kb[(self.X[sj, si] - TM(c.x)) ** 2 + (self.Y[sj, si] - TM(c.y)) ** 2 <= 0.3 ** 2] = code
                if p.GetDrillSize().x > 0:     # holes (also NPTH mounting holes) block both layers
                    self._circle(TM(c.x), TM(c.y), TM(p.GetDrillSize().x) / 2 + 0.2, code, [0, 1])
        for x, y in P.HOLES:                   # no copper under the screw head (and the standoff)
            self._circle(x, y, P.HOLE_KEEPOUT, -2, [0, 1])
        self.edgemask = (self.X < EDGE) | (self.Y < EDGE) | (self.X > P.WIDTH - EDGE) | (self.Y > P.HEIGHT - EDGE)
        # island masks
        self.island_mask = {}
        for k, (x0, y0, x1, y1) in islands().items():
            self.island_mask[k] = (self.X > x0) & (self.X < x1) & (self.Y > y0) & (self.Y < y1)
        self.any_island = np.zeros((self.ny, self.nx), bool)
        for m in self.island_mask.values():
            self.any_island |= m
        self.channel = np.zeros((self.ny, self.nx), bool)
        for kx0, ky0, kx1, ky1 in getattr(P, "GND_CHANNELS", []):
            self.channel |= (self.X > kx0) & (self.X < kx1) & (self.Y > ky0) & (self.Y < ky1)
        gnd = board.FindNet("GND")
        self.gnd_code = gnd.GetNetCode() if gnd else -99
        iso = getattr(P, "ISOLATED", {}) or {}
        self.iso_codes = [board.FindNet(n).GetNetCode() for n in iso if board.FindNet(n)]

    def iso_distance(self, layer):
        """Distance (mm) to the nearest isolated copper or island area; huge when there are no islands."""
        if not self.island_mask:
            return np.full((self.ny, self.nx), 1e9)
        m = np.isin(self.copper[layer], self.iso_codes) | self.any_island
        return distance_transform_edt(~m) * G

    def _box(self, x0, y0, x1, y1):
        i0 = max(int(x0 / G) - 1, 0); i1 = min(int(x1 / G) + 2, self.nx)
        j0 = max(int(y0 / G) - 1, 0); j1 = min(int(y1 / G) + 2, self.ny)
        return slice(j0, j1), slice(i0, i1)

    def _polygon(self, pts, code, layers):
        a = np.array(pts)
        sj, si = self._box(a[:, 0].min(), a[:, 1].min(), a[:, 0].max(), a[:, 1].max())
        cells = np.column_stack([self.X[sj, si].ravel(), self.Y[sj, si].ravel()])
        inside = MPath(a).contains_points(cells, radius=1e-6).reshape(self.X[sj, si].shape)
        inside = binary_dilation(inside)   # conservative: do not miss corners and edges
        for layer in layers:
            block = self.copper[layer, sj, si]
            block[inside] = code

    def _polygon_pth(self, pts, code):
        a = np.array(pts)
        sj, si = self._box(a[:, 0].min(), a[:, 1].min(), a[:, 0].max(), a[:, 1].max())
        cells = np.column_stack([self.X[sj, si].ravel(), self.Y[sj, si].ravel()])
        inside = MPath(a).contains_points(cells).reshape(self.X[sj, si].shape)
        block = self.padcopper[sj, si]
        block[inside] = code

    def _circle(self, x, y, r, code, layers):
        sj, si = self._box(x - r, y - r, x + r, y + r)
        inside = (self.X[sj, si] - x) ** 2 + (self.Y[sj, si] - y) ** 2 <= r * r
        for layer in layers:
            block = self.copper[layer, sj, si]
            block[inside] = code

    def track(self, x0, y0, x1, y1, w, code, layer):
        r = w / 2
        sj, si = self._box(min(x0, x1) - r, min(y0, y1) - r, max(x0, x1) + r, max(y0, y1) + r)
        px, py = self.X[sj, si], self.Y[sj, si]
        dx, dy = x1 - x0, y1 - y0
        L2 = dx * dx + dy * dy
        t = np.clip(((px - x0) * dx + (py - y0) * dy) / L2, 0, 1) if L2 > 0 else 0
        d2 = (px - x0 - t * dx) ** 2 + (py - y0 - t * dy) ** 2
        block = self.copper[layer, sj, si]
        rr = r + G * 0.5
        block[d2 <= rr * rr] = code

    def free(self, code, w, island):
        """Per layer: may the centre of a track (width w) of net `code` lie here? island = k or None."""
        out = []
        for layer in range(2):
            other = (self.copper[layer] != -1) & (self.copper[layer] != code)
            d = distance_transform_edt(~other) * G
            ok = (d >= w / 2 + CLR + G * 1.0) & ~self.edgemask
            if island is not None:
                ok &= self.island_mask[island]
            elif self.island_mask:
                ok &= ~self.any_island & (self.iso_distance(layer) >= P.ISO_TRACK + w / 2)
            if code != self.gnd_code:
                ok &= ~self.channel
            out.append(ok)
        dvia = []
        for layer in range(2):
            other = (self.copper[layer] != -1) & (self.copper[layer] != code)
            dvia.append(distance_transform_edt(~other) * G)
        via_ok = (np.minimum(dvia[0], dvia[1]) >= VIA_D / 2 + CLR + G * 1.0) & ~self.edgemask
        if code != self.gnd_code:
            via_ok &= ~self.channel
        if island is not None:
            via_ok &= self.island_mask[island]
        elif self.island_mask:
            via_ok &= ~self.any_island & (np.minimum(self.iso_distance(0), self.iso_distance(1))
                                          >= P.ISO_TRACK + VIA_D / 2)
        own = []
        for layer in range(2):
            other = (self.copper[layer] != -1) & (self.copper[layer] != code)
            d = distance_transform_edt(~other) * G
            own.append(((self.copper[layer] == code) & (d >= w / 2 + CLR + G * 1.0)) | (self.core == code))
        self.pth = self.padcopper == code
        return out, via_ok, own


DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]


def search(g, source, target, free, via_ok, own):
    """Dijkstra/A* from all source cells to a target cell. source/target: lists of (layer, j, i)."""
    ny, nx = g.ny, g.nx
    targetset = set(target)
    tj = np.array([d[1] for d in target]); ti = np.array([d[2] for d in target])
    cj, ci = tj.mean(), ti.mean()

    def h(j, i):
        return 0.9 * math.hypot(j - cj, i - ci)

    best, prev, pq = {}, {}, []
    for s in source:
        best[s] = 0.0
        heapq.heappush(pq, (h(s[1], s[2]), 0.0, s))
    while pq:
        f, cost, s = heapq.heappop(pq)
        if cost > best.get(s, 1e18):
            continue
        if s in targetset:
            path = [s]
            while path[-1] in prev:
                path.append(prev[path[-1]])
            return path[::-1]
        layer, j, i = s
        for di, dj in DIRS:
            i2, j2 = i + di, j + dj
            if not (0 <= i2 < nx and 0 <= j2 < ny):
                continue
            if not (free[layer][j2, i2] or own[layer][j2, i2]):
                continue
            if di and dj and not ((free[layer][j, i2] or own[layer][j, i2]) and (free[layer][j2, i] or own[layer][j2, i])):
                continue
            step = 1.4142 if (di and dj) else 1.0
            if (layer == 0 and dj and not di) or (layer == 1 and di and not dj):
                step *= OFF_AXIS
            n = (layer, j2, i2)
            c2 = cost + step
            if c2 < best.get(n, 1e18):
                best[n] = c2; prev[n] = s
                heapq.heappush(pq, (c2 + h(j2, i2), c2, n))
        if via_ok[j, i] or g.pth[j, i]:
            n = (1 - layer, j, i)
            c2 = cost + (0.5 if g.pth[j, i] else VIA_COST)
            if (free[1 - layer][j, i] or own[1 - layer][j, i]) and c2 < best.get(n, 1e18):
                best[n] = c2; prev[n] = s
                heapq.heappush(pq, (c2 + h(j, i), c2, n))
    return None


def pad_cells(g, p):
    c = p.GetPosition()
    x, y = TM(c.x), TM(c.y)
    sj, si = g._box(x - 0.4, y - 0.4, x + 0.4, y + 0.4)
    jj, ii = np.nonzero((g.X[sj, si] - x) ** 2 + (g.Y[sj, si] - y) ** 2 <= 0.3 ** 2)
    layers = (0, 1) if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH else (0,)
    return [(layer, int(j + sj.start), int(i + si.start)) for layer in layers for j, i in zip(jj, ii)]


def simplify(path):
    """Grid cells -> list of (layer, [points in mm]) per layer run, without points on straight runs."""
    runs, cur = [], [path[0]]
    for c in path[1:]:
        if c[0] != cur[-1][0]:
            runs.append(cur)
            cur = [c]
        else:
            cur.append(c)
    runs.append(cur)
    out = []
    for run in runs:
        pts = [(c[2], c[1]) for c in run]
        short = [pts[0]]
        for k in range(1, len(pts) - 1):
            a, b, c = short[-1], pts[k], pts[k + 1]
            if (b[0] - a[0]) * (c[1] - b[1]) != (b[1] - a[1]) * (c[0] - b[0]):
                short.append(b)
        if len(pts) > 1:
            short.append(pts[-1])
        out.append((run[0][0], [((i + 0.5) * G, (j + 0.5) * G) for i, j in short]))
    return out


def route(board, verbose=True):
    g = Grid(board)
    iso = getattr(P, "ISOLATED", {}) or {}
    gnd_tracks = getattr(P, "GND_TRACKS", set())
    nets = {}
    anchors = {}   # plane nets: pads that the plane reaches; GND_TRACKS pads are routed to the nearest one
    for fp in board.GetFootprints():
        for p in fp.Pads():
            n = p.GetNetname()
            if n in P.PLANE_NETS:
                if (fp.GetReference(), p.GetNumber()) in gnd_tracks:
                    nets.setdefault(n, []).append(p)      # plane pads that the plane cannot reach
                else:
                    sure = getattr(P, "GND_ANCHORS", None)   # optional: only these pads count as on the main plane
                    if sure is None or (fp.GetReference(), p.GetNumber()) in sure:
                        anchors.setdefault(n, []).append(p)
            elif n:
                nets.setdefault(n, []).append(p)
    order = sorted(nets, key=lambda n: (n in P.LAST, n not in P.PRIORITY, -P.WIDTHS.get(n, 0.3), len(nets[n])))
    failed = []
    for name in order:
        pads = nets[name]
        plane = name in P.PLANE_NETS and anchors.get(name)
        if len(pads) < (1 if plane else 2):
            continue
        code = pads[0].GetNetCode()
        w = P.WIDTHS.get(name, P.DEFAULT_WIDTH)
        island = iso.get(name)
        free, via_ok, own = g.free(code, w, island)
        cells = [pad_cells(g, p) for p in pads]
        if plane:
            # each listed pad gets its own track to the nearest plane-connected pad of the same net
            tree = [c for p in anchors[name] for c in pad_cells(g, p)]
            todo = list(range(len(pads)))
        else:
            tree = list(cells[0])
            todo = list(range(1, len(pads)))
        netitem = board.FindNet(name)
        while todo:
            bj = np.array([c[1] for c in tree]); bi = np.array([c[2] for c in tree])

            def dist(k):
                c = cells[k][len(cells[k]) // 2]
                return np.min((bj - c[1]) ** 2 + (bi - c[2]) ** 2)
            k = min(todo, key=dist)
            path = search(g, tree, cells[k], free, via_ok, own)
            todo.remove(k)
            if path is None:
                failed.append((name, pads[k].GetParentFootprint().GetReference() + "." + pads[k].GetNumber()))
                continue
            for layer, pts in simplify(path):
                for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
                    t = pcbnew.PCB_TRACK(board)
                    t.SetStart(pcbnew.VECTOR2I(MM(x0), MM(y0))); t.SetEnd(pcbnew.VECTOR2I(MM(x1), MM(y1)))
                    t.SetWidth(MM(w)); t.SetLayer(LAYERS[layer]); t.SetNet(netitem)
                    board.Add(t)
                    g.track(x0, y0, x1, y1, w, code, layer)
            for a, b in zip(path, path[1:]):
                if a[0] != b[0] and not g.pth[a[1], a[2]]:
                    x, y = (a[2] + 0.5) * G, (a[1] + 0.5) * G
                    via = pcbnew.PCB_VIA(board)
                    via.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
                    via.SetWidth(MM(VIA_D)); via.SetDrill(MM(VIA_DRILL)); via.SetNet(netitem)
                    board.Add(via)
                    g._circle(x, y, VIA_D / 2, code, [0, 1])
            tree += path
            free, via_ok, own = g.free(code, w, island)
        if verbose:
            print(f"  {name:10s} {len(pads)} pads", flush=True)
    if failed:
        print("NOT ROUTED:", failed)
    return failed


def planes(board):
    """Zones from P.PLANES (net, layer "F"/"B", polygon), pads fully connected (high current)
    unless P.PLANE_THERMAL is set,
    plus copper keep-outs around the mounting holes."""
    for name, layer, pts in P.PLANES:
        z = pcbnew.ZONE(board)
        z.SetLayer(pcbnew.F_Cu if layer == "F" else pcbnew.B_Cu)
        z.SetNet(board.FindNet(name))
        z.SetLocalClearance(MM(0.4))
        z.SetMinThickness(MM(0.25))
        if getattr(P, "PLANE_THERMAL", False):
            z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
            z.SetThermalReliefGap(MM(0.4)); z.SetThermalReliefSpokeWidth(MM(0.5))
        else:
            z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
        o = z.Outline(); o.NewOutline()
        for x, y in pts:
            o.Append(MM(x), MM(y))
        board.Add(z)
    for x, y in P.HOLES:
        z = pcbnew.ZONE(board)
        z.SetIsRuleArea(True)
        z.SetDoNotAllowCopperPour(True); z.SetDoNotAllowTracks(True); z.SetDoNotAllowVias(True)
        z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
        z.SetLayerSet(pcbnew.LSET.AllCuMask())
        o = z.Outline(); o.NewOutline()
        for k in range(24):
            a = 2 * math.pi * k / 24
            o.Append(MM(x + P.HOLE_KEEPOUT * math.cos(a)), MM(y + P.HOLE_KEEPOUT * math.sin(a)))
        board.Add(z)


def fill(path):
    """Fill zones on a freshly loaded board (filling a board built in Python crashes)."""
    b = pcbnew.LoadBoard(str(path))
    b.BuildConnectivity()
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(str(path), b)
