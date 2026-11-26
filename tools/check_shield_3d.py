"""Numeric 3D check of the shield board: do the 3D models sit on their pads, how tall is everything, do any parts
collide, does anything stick out of the board, and how much room is under the ESP32-S3-Zero.

Uses KiCad's own Python (it has the pcbnew module) and the STEP models of KiCad's library. The size of a model is taken
from the vertices of its STEP file, so it is a box around the real shape (round parts count a little too big). The
Zero is not on the board; it is added as a plate of 18 x 23.5 x 1.6 mm over the two socket strips.

    "C:\\Program Files\\KiCad\\bin\\python.exe" tools/check_shield_3d.py            report on the console
    "C:\\Program Files\\KiCad\\bin\\python.exe" tools/check_shield_3d.py --md hardware/shield/fab/shield_3d_check.md

Options: --socket-h 8.5 (height of the socket strips),
--male-body 2.5 (thickness of the black plastic of the Zero's own pin header, which sits on the socket).
Not a CAD collision check of the whole assembly: the shapes are boxes, and the Zero's pins and chips are not modelled.
"""
import argparse
import math
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PCB = ROOT / "hardware" / "shield" / "shield.kicad_pcb"
KICAD = Path(os.environ.get("KICAD_DIR", r"C:\Program Files\KiCad"))
MODELS = KICAD / "share" / "kicad" / "3dmodels"
ZERO_W, ZERO_L, ZERO_T = 18.0, 23.5, 1.6
PIN1_FROM_TOP = 1.59           # first pin of the Zero's row, from its USB-C end (docs/shield-pcb.md)
INTENDED_OUT = ("J1",)         # parts that are meant to stick out over the board edge (the servo header)

_cache = {}


def step_file(name):
    name = re.sub(r"\$\{[A-Z0-9_]+\}", str(MODELS).replace("\\", "/"), name)
    p = Path(name)
    if p.suffix.lower() in (".wrl", ".wrz"):
        p = p.with_suffix(".step")
    return p


def step_points(path):
    """The vertices of a STEP file, as a list of (x, y, z) in mm."""
    if path in _cache:
        return _cache[path]
    text = re.sub(r"\s+", " ", path.read_text(errors="ignore"))
    pts = {}
    for m in re.finditer(r"#(\d+) ?= ?CARTESIAN_POINT\('[^']*', ?\(([^)]*)\)\)", text):
        try:
            v = [float(t) for t in m.group(2).split(",")]
        except ValueError:
            continue
        if len(v) == 3:
            pts[m.group(1)] = tuple(v)
    ids = [m.group(1) for m in re.finditer(r"VERTEX_POINT\('[^']*', ?#(\d+)\)", text)]
    use = [pts[i] for i in ids if i in pts] or list(pts.values())
    _cache[path] = use
    return use


def rot(v, rx, ry, rz):
    x, y, z = v
    a = math.radians(rx); y, z = y * math.cos(a) - z * math.sin(a), y * math.sin(a) + z * math.cos(a)
    a = math.radians(ry); x, z = x * math.cos(a) + z * math.sin(a), -x * math.sin(a) + z * math.cos(a)
    a = math.radians(rz); x, y = x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)
    return x, y, z


def world_box(fp, model):
    """Bounding box (x0, y0, z0, x1, y1, z1) of one model in board coordinates (mm, y down like KiCad, z up, 0 = board top)."""
    import pcbnew
    pts = step_points(step_file(model.m_Filename))
    sc, off, ro = model.m_Scale, model.m_Offset, model.m_Rotation
    pos = fp.GetPosition()
    px, py = pcbnew.ToMM(pos.x), pcbnew.ToMM(pos.y)
    a = math.radians(fp.GetOrientationDegrees())
    ca, sa = math.cos(a), math.sin(a)
    out = []
    for p in pts:
        x, y, z = p[0] * sc.x, p[1] * sc.y, p[2] * sc.z
        x, y, z = rot((x, y, z), ro.x, ro.y, -ro.z)
        x, y, z = x + off.x, y + off.y, z + off.z
        fx, fy = x, -y                                   # the model's y runs up the screen, KiCad's runs down
        out.append((px + fx * ca + fy * sa, py - fx * sa + fy * ca, z))
    xs, ys, zs = zip(*out)
    return (min(xs), min(ys), min(zs), max(xs), max(ys), max(zs))


def pad_box(fp):
    import pcbnew
    xs, ys = [], []
    for pad in fp.Pads():
        b = pad.GetBoundingBox()
        xs += [pcbnew.ToMM(b.GetLeft()), pcbnew.ToMM(b.GetRight())]
        ys += [pcbnew.ToMM(b.GetTop()), pcbnew.ToMM(b.GetBottom())]
    return min(xs), min(ys), max(xs), max(ys)


def overlap1(a0, a1, b0, b1):
    return min(a1, b1) - max(a0, b0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--md", help="write the report as Markdown to this file")
    ap.add_argument("--socket-h", type=float, default=8.5)
    ap.add_argument("--male-body", type=float, default=2.5)
    args = ap.parse_args()
    import pcbnew

    board = pcbnew.LoadBoard(str(PCB))
    edge = board.GetBoardEdgesBoundingBox()
    bx0, by0, bx1, by1 = (pcbnew.ToMM(edge.GetLeft()), pcbnew.ToMM(edge.GetTop()),
                          pcbnew.ToMM(edge.GetRight()), pcbnew.ToMM(edge.GetBottom()))
    parts = {}
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        models = list(fp.Models())
        if not models:
            continue
        box = world_box(fp, models[0])
        parts[ref] = dict(box=box, pads=pad_box(fp), model=Path(models[0].m_Filename).name, fp=fp)

    lines = []
    out = lines.append
    out("# Shield 3D check")
    out("")
    out(f"Board {PCB.name}, outline {bx1 - bx0:.2f} x {by1 - by0:.2f} mm. Sizes are boxes around the STEP shapes (mm, z = 0 at the board top).")
    out("")

    # 1. do the models sit on their pads
    out("## 1. Models on their pads (xy)")
    out("")
    out("| Part | Model | Model box x | Model box y | Pads x | Pads y | Result |")
    out("|---|---|---|---|---|---|---|")
    bad = []
    for ref in sorted(parts, key=lambda r: (re.sub(r"\d", "", r), int(re.sub(r"\D", "", r) or 0))):
        p = parts[ref]
        mx0, my0, _, mx1, my1, _ = p["box"]
        qx0, qy0, qx1, qy1 = p["pads"]
        ox = overlap1(mx0, mx1, qx0, qx1)
        oy = overlap1(my0, my1, qy0, qy1)
        # the pads must lie within the model box, give or take 0.6 mm (pads of SMD parts reach out a little)
        ok = qx0 >= mx0 - 0.6 and qx1 <= mx1 + 0.6 and qy0 >= my0 - 0.6 and qy1 <= my1 + 0.6 and ox > 0 and oy > 0
        if not ok:
            bad.append(ref)
        out(f"| {ref} | {p['model']} | {mx0:.2f}..{mx1:.2f} | {my0:.2f}..{my1:.2f} | {qx0:.2f}..{qx1:.2f} | {qy0:.2f}..{qy1:.2f} | {'ok' if ok else 'CHECK'} |")
    out("")
    out("Models that do not cover their pads: " + (", ".join(bad) if bad else "none") + ".")
    out("")

    # 2. heights
    out("## 2. Heights above the board top")
    out("")
    tall = sorted(parts.items(), key=lambda kv: -kv[1]["box"][5])[:8]
    out("| Part | Model | Height (mm) | Lowest point (mm) |")
    out("|---|---|---|---|")
    for ref, p in tall:
        out(f"| {ref} | {p['model']} | {p['box'][5]:.2f} | {p['box'][2]:.2f} |")
    out("")

    # 3. collisions between parts
    out("## 3. Parts that overlap in 3D")
    out("")
    refs = sorted(parts)
    hits = []
    for i, a in enumerate(refs):
        for b in refs[i + 1:]:
            A, B = parts[a]["box"], parts[b]["box"]
            ox = overlap1(A[0], A[3], B[0], B[3])
            oy = overlap1(A[1], A[4], B[1], B[4])
            oz = overlap1(max(A[2], 0), A[5], max(B[2], 0), B[5])
            if ox > 0.05 and oy > 0.05 and oz > 0.05:
                hits.append((a, b, ox, oy, oz))
    if hits:
        out("| A | B | overlap x | y | z (mm) |")
        out("|---|---|---|---|---|")
        for a, b, ox, oy, oz in hits:
            out(f"| {a} | {b} | {ox:.2f} | {oy:.2f} | {oz:.2f} |")
    else:
        out("None (parts above the board top, overlap larger than 0.05 mm in all three directions).")
    out("")

    # 4. outline
    out("## 4. Parts outside the board outline")
    out("")
    outs = []
    for ref, p in sorted(parts.items()):
        b = p["box"]
        over = max(bx0 - b[0], by0 - b[1], b[3] - bx1, b[4] - by1)
        if over > 0.05:
            outs.append((ref, over))
    if outs:
        for ref, over in outs:
            out(f"- {ref}: sticks out by {over:.2f} mm" + (" (meant to: the cable plug)" if ref in INTENDED_OUT else " **check**"))
    else:
        out("None.")
    out("")

    # 5. room under the Zero
    j = [parts[r]["pads"] for r in ("J3", "J4") if r in parts]
    zx0 = min(q[0] for q in j) - 1.38
    zx1 = max(q[2] for q in j) + 1.38
    zy0 = min(q[1] for q in j) - PIN1_FROM_TOP + 0.0
    # the socket pads reach about 0.5 mm over the pin centre; the pin 1 centre is PIN1_FROM_TOP from the Zero's end
    pin1_y = min(parts[r]["fp"].Pads()[0].GetPosition().y for r in ("J3", "J4") if r in parts)
    zy0 = pcbnew.ToMM(pin1_y) - PIN1_FROM_TOP
    zy1 = zy0 + ZERO_L
    out("## 5. Room under the ESP32-S3-Zero")
    out("")
    out(f"The Zero covers x {zx0:.2f}..{zx1:.2f}, y {zy0:.2f}..{zy1:.2f} mm. Its underside is the socket height plus the plastic of its own pin header ({args.male_body} mm), if the header sits on the socket.")
    out("")
    under = []
    for ref, p in sorted(parts.items()):
        if ref in ("J3", "J4"):
            continue
        b = p["box"]
        if overlap1(b[0], b[3], zx0, zx1) > 0 and overlap1(b[1], b[4], zy0, zy1) > 0 and b[5] > 0:
            under.append((ref, b[5]))
    under.sort(key=lambda t: -t[1])
    out("Parts under (or partly under) the Zero, tallest first: " + ", ".join(f"{r} {h:.2f}" for r, h in under) + ".")
    out("")
    out("| Socket strip | Zero underside (mm) | Tallest part under it | Room left (mm) |")
    out("|---|---|---|---|")
    top_h = under[0][1] if under else 0.0
    for name, h in (("8.5 mm", args.socket_h), ("3.5 mm (low strip, short pins)", 3.5)):
        u = h + args.male_body
        out(f"| {name} | {u:.2f} | {top_h:.2f} ({under[0][0] if under else '-'}) | {u - top_h:.2f} |")
    out("")
    out("The 3.5 mm row assumes pins short enough for the plastic to seat on the strip; with the Zero's own pins of about 6 mm the underside stays at about 8.5 mm.")
    out("")

    text = "\n".join(lines)
    print(text)
    if args.md:
        Path(args.md).write_text(text + "\n", encoding="utf-8")
        print("written:", args.md)


if __name__ == "__main__":
    sys.exit(main())
