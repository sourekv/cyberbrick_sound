"""Placement of the shield parts by simulated annealing -> tools/shield_placement.json.

Uses the real courtyards of the KiCad footprints. Fixed: the Zero sockets, mounting holes, the input header,
the power LED and its resistor, the bulk capacitor in the right margin, the speaker connector row.
Movable parts must stay inside the free area (gap between the sockets, plus the bottom margin), must not overlap
(courtyards inflated by a routing margin) and are pulled together by the nets (half-perimeter wire length).

    python3 tools/place_shield.py [iterations] [seed]
"""
import json
import math
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import shield_layout as L  # noqa: E402
import shield_netlist as N  # noqa: E402

FPLIB = Path("/usr/share/kicad/footprints")
OUT = Path(__file__).parent / "shield_placement.json"
FOOTPRINT_OVERRIDE = {"R6": "Resistor_SMD:R_0402_1005Metric", "R7": "Resistor_SMD:R_0402_1005Metric", "R8": "Resistor_SMD:R_0402_1005Metric"}
INFL = 0.18                       # routing space around every courtyard
SKIP_NETS = {"GND"}               # ground goes to the plane
WEIGHT = {"+5V": 0.8, "S_IN": 4, "VIN": 4, "VFUSED": 4, "IO1_THR": 3, "5V_ZERO": 4, "IO4_DIN": 3, "IO5_BCLK": 3, "IO6_LRC": 3,
          "DIN": 5, "BCLK": 5, "LRCLK": 5, "OUTP": 6, "OUTN": 6, "SPK_P": 4, "SPK_N": 4, "GAIN": 4, "GAIN_R": 4, "SD_MODE": 4, "SD_R": 4}
# decoupling and EMI capacitors must sit right at the pins they serve: (part, pin, part, pin, weight)
PAIRS = [("C3", "1", "U1", "7", 10), ("C2", "1", "U1", "8", 8), ("C4", "1", "J2", "1", 8), ("C5", "1", "J2", "2", 8),
         ("TVS1", "1", "J1", "1", 6), ("R1", "1", "J1", "1", 4), ("F1", "1", "J1", "2", 4)]


# rough intended position of every movable part (x, y, strength): the circuit blocks from the design sketch.
ANCHOR = {
    "R1": (6.46, 5.0, 3), "TVS1": (4.5, 5.2, 2), "F1": (9.0, 5.2, 3), "D1": (9.0, 10.2, 3), "D2": (4.6, 9.6, 2),
    "R2": (4.0, 11.4, 2), "C6": (12.0, 12.4, 1), "C7": (13.8, 12.4, 1),
    "U1": (7.3, 19.4, 6), "R6": (3.7, 16.9, 8), "R7": (3.7, 19.4, 8), "R8": (3.7, 21.9, 8),
    "C3": (9.8, 16.6, 1), "C2": (5.8, 15.0, 1),
    "FB1": (10.6, 19.3, 1), "FB2": (10.6, 20.7, 1), "C4": (12.6, 18.2, 1), "C5": (14.0, 18.2, 1),
    "R4": (3.4, 25.0, 1), "JP1": (5.6, 25.0, 1), "JP2": (8.0, 25.0, 1), "R5": (10.2, 25.0, 1),
}


def parse_fp(spec):
    lib, name = spec.split(":")
    txt = (FPLIB / f"{lib}.pretty" / f"{name}.kicad_mod").read_text()
    xs, ys = [], []
    for m in re.finditer(r"\(fp_(?:line|rect)\b(.*?)\(layer \"?F\.CrtYd\"?\)", txt, re.S):
        blk = m.group(1)
        if "(fp_" in blk:                      # the match ran over into the next shape: skip it
            blk = blk[blk.rindex("(fp_"):] if False else blk
        mm_ = re.search(r"\(start ([-\d.]+) ([-\d.]+)\)\s*\(end ([-\d.]+) ([-\d.]+)\)", blk)
        if mm_:
            xs += [float(mm_.group(1)), float(mm_.group(3))]
            ys += [float(mm_.group(2)), float(mm_.group(4))]
    if not xs:                    # footprints without a courtyard (mounting hole): use the pads
        for m in re.finditer(r"\(pad \"?[^\"\s]*\"?\s+\w+\s+\w+\s+\(at ([-\d.]+) ([-\d.]+)", txt):
            xs.append(float(m.group(1))); ys.append(float(m.group(2)))
    cy = (min(xs), min(ys), max(xs), max(ys))
    pads = []
    for m in re.finditer(r"\(pad \"?([^\"\s]*)\"?\s+\w+\s+\w+\s+\(at ([-\d.]+) ([-\d.]+)", txt):
        pads.append((m.group(1), float(m.group(2)), float(m.group(3))))
    return cy, pads


def rot_xy(x, y, deg):
    t = math.radians(deg)
    return x * math.cos(t) + y * math.sin(t), -x * math.sin(t) + y * math.cos(t)


class Part:
    def __init__(self, ref, fpspec, fixed, pos, rot=0, region=None, rots=(0, 90)):
        self.ref, self.fixed, self.rots = ref, fixed, rots
        self.cy, self.pads = parse_fp(fpspec)
        self.x, self.y = pos
        self.rot = rot
        self.region = region
        self.nets = N.PARTS[ref][3]

    def box(self, x=None, y=None, rot=None, infl=0.0):
        x = self.x if x is None else x
        y = self.y if y is None else y
        rot = self.rot if rot is None else rot
        c = [rot_xy(px, py, rot) for px in (self.cy[0], self.cy[2]) for py in (self.cy[1], self.cy[3])]
        return (x + min(a for a, b in c) - infl, y + min(b for a, b in c) - infl, x + max(a for a, b in c) + infl, y + max(b for a, b in c) + infl)

    def pad_xy(self, num, x=None, y=None, rot=None):
        x = self.x if x is None else x
        y = self.y if y is None else y
        rot = self.rot if rot is None else rot
        for n, px, py in self.pads:
            if n == num:
                a, b = rot_xy(px, py, rot)
                return x + a, y + b
        return None


def inter(a, b):
    w = min(a[2], b[2]) - max(a[0], b[0])
    h = min(a[3], b[3]) - max(a[1], b[1])
    return w * h if w > 0 and h > 0 else 0.0


def circle_box(c, r):
    return (c[0] - r, c[1] - r, c[0] + r, c[1] + r)


def setup():
    parts = {}
    fixed = {
        "J1": (6.46, 0.9, 90), "J3": (L.HDR_X[0], L.PIN_Y[0], 0), "J4": (L.HDR_X[1], L.PIN_Y[0], 0),
        "C1": (21.0, 12.5, 90), "LED1": (-2.75, 11.8, 90), "R3": (-2.75, 8.6, 90),
    }
    for i, h in enumerate(L.CB_HOLES, 1):
        fixed[f"MH{i}"] = (h[0], h[1], 0)
    for ref, (sym, val, fp, pins, d) in N.PARTS.items():
        if ref.startswith("TP"):
            continue
        fp = FOOTPRINT_OVERRIDE.get(ref, fp)
        if ref in fixed:
            x, y, r = fixed[ref]
            parts[ref] = Part(ref, fp, True, (x, y), r)
        elif ref == "J2":
            parts[ref] = Part(ref, fp, False, (12.6, 23.6), 0, region="j2", rots=(0,))
        else:
            parts[ref] = Part(ref, fp, False, ANCHOR[ref][:2], 0, rots=(0, 90, 180, 270) if ref == "U1" else (0, 90))
    return parts


def allowed(p, x, y, rot):
    """True when the movable part is inside the free area."""
    b = p.box(x, y, rot)
    if p.region == "j2":
        return 5.0 <= b[0] and b[2] <= 15.6 and b[3] <= L.BOARD_H + 3.25 - 0.35
    gap = (L.GAP_X[0] + 0.05, 0.4, L.GAP_X[1] - 0.05, L.BOARD_H + 0.0)
    if b[0] >= gap[0] and b[2] <= gap[2] and b[1] >= gap[1] and b[3] <= gap[3]:
        return True
    # bottom margin strip below the Zero
    if b[0] >= 0.6 and b[2] <= 17.4 and b[1] >= L.BOARD_H + 0.1 and b[3] <= L.BOARD_H + 3.25 - 0.35:
        return True
    # left and right margin strips beside the Zero (between the corner hole rings)
    if b[1] >= 2.9 and b[3] <= 20.7:
        if b[0] >= -5.15 and b[2] <= -0.6:
            return True
        if b[0] >= 18.4 and b[2] <= 23.15:
            return True
    return False


def cost(parts, detail=False):
    refs = list(parts)
    ov = 0.0
    boxes = {r: parts[r].box(infl=INFL) for r in refs}
    for i, a in enumerate(refs):
        for b in refs[i + 1:]:
            if parts[a].fixed and parts[b].fixed:
                continue
            ov += inter(boxes[a], boxes[b])
    wl = 0.0
    nets = {}
    for ref, p in parts.items():
        for pin, net in p.nets.items():
            if net is None or net in SKIP_NETS:
                continue
            xy = p.pad_xy(pin)
            if xy:
                nets.setdefault(net, []).append(xy)
    for net, pts in nets.items():
        if len(pts) < 2:
            continue
        xs = [a for a, b in pts]; ys = [b for a, b in pts]
        wl += WEIGHT.get(net, 1.0) * ((max(xs) - min(xs)) + (max(ys) - min(ys)))
    for r, (ax, ay, k) in ANCHOR.items():
        wl += k * math.hypot(parts[r].x - ax, parts[r].y - ay)
    for a, pa, b, pb, w in PAIRS:
        pa_, pb_ = parts[a].pad_xy(pa), parts[b].pad_xy(pb)
        wl += w * math.hypot(pa_[0] - pb_[0], pa_[1] - pb_[1])
    # keep out of the corner hole rings
    ring = 0.0
    for h in L.CB_HOLES:
        hb = circle_box(h, L.CB_RING_D / 2 + 0.05)
        for r in refs:
            if not parts[r].fixed and not r.startswith("MH"):
                ring += inter(boxes[r], hb)
    if detail:
        return ov, wl, ring
    return 400 * ov + 400 * ring + wl


def anneal(parts, iters, seed):
    random.seed(seed)
    mov = [r for r, p in parts.items() if not p.fixed]
    # start: scatter inside the gap until the area constraint holds
    for r in mov:
        p = parts[r]
        if p.region == "j2":
            p.x, p.y, p.rot = 11.5, 23.6, 0
            continue
        for _ in range(2000):
            ax, ay, _k = ANCHOR[r]
            p.x, p.y, p.rot = ax + random.gauss(0, 0.6), ay + random.gauss(0, 0.6), random.choice(p.rots)
            if allowed(p, p.x, p.y, p.rot):
                break
    cur = cost(parts)
    best = cur
    best_state = {r: (parts[r].x, parts[r].y, parts[r].rot) for r in mov}
    for it in range(iters):
        t = 3.0 * (1 - it / iters) ** 2 + 0.02
        r = random.choice(mov)
        p = parts[r]
        old = (p.x, p.y, p.rot)
        s = random.choice((0.15, 0.5, 1.5))
        if random.random() < 0.1:
            nx, ny, nr = p.x, p.y, random.choice(p.rots)
        else:
            nx, ny, nr = p.x + random.gauss(0, s), p.y + random.gauss(0, s), p.rot
        if p.region == "j2":
            ny = 23.6
        nx, ny = round(nx, 2), round(ny, 2)
        if not allowed(p, nx, ny, nr):
            continue
        p.x, p.y, p.rot = nx, ny, nr
        c = cost(parts)
        if c < cur or random.random() < math.exp((cur - c) / t):
            cur = c
            if c < best:
                best, best_state = c, {k: (parts[k].x, parts[k].y, parts[k].rot) for k in mov}
        else:
            p.x, p.y, p.rot = old
    for r, (x, y, rot) in best_state.items():
        parts[r].x, parts[r].y, parts[r].rot = x, y, rot
    return best


def main():
    iters = int(sys.argv[1]) if len(sys.argv) > 1 else 40000
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    random.seed(seed)
    parts = setup()
    best = anneal(parts, iters, seed)
    ov, wl, ring = cost(parts, True)
    print(f"cost {best:.1f}  overlap {ov:.3f} mm2  hole rings {ring:.3f}  weighted wire length {wl:.1f}")
    out = {r: [p.x, p.y, p.rot] for r, p in parts.items() if not p.fixed}
    OUT.write_text(json.dumps(out, indent=1, sort_keys=True))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
