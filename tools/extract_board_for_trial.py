import json, math
import pcbnew
b = pcbnew.LoadBoard("hardware/shield/shield.kicad_pcb")
e = b.GetBoardEdgesBoundingBox()
x0, y0 = pcbnew.ToMM(e.GetLeft()), pcbnew.ToMM(e.GetTop())
mm = pcbnew.ToMM
out = {"W": mm(e.GetWidth()), "H": mm(e.GetHeight()), "parts": {}}
for f in b.GetFootprints():
    ref = f.GetReference()
    pos = f.GetPosition()
    ang = f.GetOrientationDegrees()
    # courtyard bbox in the footprint's own frame: take it at the footprint's current orientation and un-rotate
    crt = f.GetCourtyard(pcbnew.F_CrtYd) if f.GetLayer() == pcbnew.F_Cu else f.GetCourtyard(pcbnew.B_CrtYd)
    bb = crt.BBox() if crt.OutlineCount() else f.GetBoundingBox(False)
    cb = [mm(bb.GetLeft()) - mm(pos.x), mm(bb.GetTop()) - mm(pos.y), mm(bb.GetRight()) - mm(pos.x), mm(bb.GetBottom()) - mm(pos.y)]
    # pads in the local frame (un-rotate the world offset by the orientation)
    a = math.radians(ang)
    pads = []
    for p in f.Pads():
        dx, dy = mm(p.GetPosition().x) - mm(pos.x), mm(p.GetPosition().y) - mm(pos.y)
        lx = dx * math.cos(a) - dy * math.sin(a)
        ly = dx * math.sin(a) + dy * math.cos(a)
        pads.append([p.GetNumber(), round(lx, 4), round(ly, 4)])
    # courtyard in the local frame: un-rotate the bbox corners
    cs = []
    for (cx, cy) in ((cb[0], cb[1]), (cb[2], cb[1]), (cb[2], cb[3]), (cb[0], cb[3])):
        cs.append((cx * math.cos(a) - cy * math.sin(a), cx * math.sin(a) + cy * math.cos(a)))
    lb = [min(c[0] for c in cs), min(c[1] for c in cs), max(c[0] for c in cs), max(c[1] for c in cs)]
    out["parts"][ref] = {"x": mm(pos.x) - x0, "y": mm(pos.y) - y0, "rot": ang, "side": "F" if f.GetLayer() == pcbnew.F_Cu else "B",
                         "crt": [round(v, 3) for v in lb], "pads": pads, "val": f.GetValue()}
json.dump(out, open("work/board_full.json", "w"), indent=0)
print(len(out["parts"]), "parts", out["W"], out["H"])
for r in ("J1", "U1", "R2", "C2"):
    p = out["parts"][r]; print(r, p["x"], p["y"], p["rot"], p["crt"], p["pads"][:2])
