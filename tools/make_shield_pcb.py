"""Generate the KiCad board of the shield from tools/shield_netlist.py (parts, footprints, nets).

Steps: place real footprints (table PLACE), assign nets, board outline + mounting holes, export for the
Freerouting autorouter, import the routes, add the ground plane, run DRC.

    python3 tools/make_shield_pcb.py place     # placement only (fast), DRC report of courtyards / edge
    python3 tools/make_shield_pcb.py route     # placement + autorouting + ground plane + DRC

Coordinates in PLACE are the mock frame of tools/shield_layout.py (origin = top-left corner of the Zero,
x right, y down, mm); they are shifted to board coordinates (board top-left at 100, 100) when written.
KiCad 7 has no command-line DRC, so the DRC runs through the pcbnew Python module.
"""
import os
import subprocess
import sys
from pathlib import Path

import pcbnew

sys.path.insert(0, str(Path(__file__).parent))
import shield_layout as L  # noqa: E402
import shield_netlist as N  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "hardware" / "shield"
FPLIB = Path("/usr/share/kicad/footprints")
BX0, BY0 = L.ZERO_CX - L.CB_W / 2, L.ZERO_CY - L.CB_H / 2          # board top-left in the mock frame
OX, OY = 100.0, 100.0                                                 # board top-left in KiCad coordinates
mm = pcbnew.FromMM


def P(x, y):
    """mock frame -> KiCad point"""
    return pcbnew.VECTOR2I(mm(OX + x - BX0), mm(OY + y - BY0))


# ref: (x, y, rotation in degrees CCW). Fixed parts here, the rest from tools/place_shield.py (shield_placement.json).
PLACE = {
    "J1": (6.46, 0.9, 90), "C1": (21.0, 12.5, 90), "LED1": (-2.75, 11.8, 90), "R3": (-2.75, 8.6, 90),
    "J3": (L.HDR_X[0], L.PIN_Y[0], 0), "J4": (L.HDR_X[1], L.PIN_Y[0], 0),
    "MH1": (L.CB_HOLES[0][0], L.CB_HOLES[0][1], 0), "MH2": (L.CB_HOLES[1][0], L.CB_HOLES[1][1], 0),
    "MH3": (L.CB_HOLES[2][0], L.CB_HOLES[2][1], 0), "MH4": (L.CB_HOLES[3][0], L.CB_HOLES[3][1], 0),
}
_pl = Path(__file__).with_name("shield_placement.json")
if _pl.exists():
    import json
    for _r, _v in json.loads(_pl.read_text()).items():
        PLACE[_r] = tuple(_v)
# test pads on the bottom side, lower margin
for _k in range(7):
    PLACE[f"TP{_k + 1}"] = (3.4 + 2.0 * _k, 25.9, 0, {"bottom": True})
# the series resistors of the I2S lines are 0402 to fit between the sockets and the amplifier
FOOTPRINT_OVERRIDE = {"R6": "Resistor_SMD:R_0402_1005Metric", "R7": "Resistor_SMD:R_0402_1005Metric", "R8": "Resistor_SMD:R_0402_1005Metric"}


def mounting_hole(d=2.7):
    fp = pcbnew.FOOTPRINT(pcbnew.BOARD())
    pad = pcbnew.PAD(fp)
    pad.SetAttribute(pcbnew.PAD_ATTRIB_NPTH)
    pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
    pad.SetSize(pcbnew.VECTOR2I(mm(d), mm(d)))
    pad.SetDrillSize(pcbnew.VECTOR2I(mm(d), mm(d)))
    pad.SetPosition(pcbnew.VECTOR2I(0, 0))
    fp.Add(pad)
    return fp


def load_fp(spec):
    if spec.startswith("MountingHole:"):
        return mounting_hole()
    lib, name = spec.split(":")
    fp = pcbnew.FootprintLoad(str(FPLIB / f"{lib}.pretty"), name)
    if fp is None:
        raise SystemExit(f"footprint not found: {spec}")
    return fp


def build_board():
    board = pcbnew.BOARD()
    nets = {}

    def net(name):
        if name not in nets:
            ni = pcbnew.NETINFO_ITEM(board, name)
            board.Add(ni)
            nets[name] = ni
        return nets[name]

    for ref, (sym, val, fpspec, pins, desc) in N.PARTS.items():
        fpspec = FOOTPRINT_OVERRIDE.get(ref, fpspec)
        fp = load_fp(fpspec)
        fp.SetReference(ref)
        fp.SetValue(val)
        x, y, rot = PLACE[ref][:3]
        opts = PLACE[ref][3] if len(PLACE[ref]) > 3 else {}
        fp.SetPosition(P(x, y))
        fp.SetOrientationDegrees(rot)
        board.Add(fp)
        if opts.get("bottom"):
            fp.Flip(P(x, y), False)
        for pad in fp.Pads():
            num = pad.GetNumber()
            if num in pins and pins[num] is not None:
                pad.SetNet(net(pins[num]))
        fp.Value().SetVisible(False)
        ref_t = fp.Reference()
        ref_t.SetTextSize(pcbnew.VECTOR2I(mm(0.8), mm(0.8)))
        ref_t.SetTextThickness(mm(0.12))
        if ref.startswith(("MH", "TP")):                  # no room for a label: keep it on the fabrication layer only
            ref_t.SetLayer(pcbnew.B_Fab if opts.get("bottom") else pcbnew.F_Fab)
    # outline: rounded rectangle on Edge.Cuts
    r, w, h = 1.5, L.CB_W, L.CB_H
    x0, y0 = OX, OY

    def seg(a, b):
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetStart(pcbnew.VECTOR2I(mm(a[0]), mm(a[1])))
        s.SetEnd(pcbnew.VECTOR2I(mm(b[0]), mm(b[1])))
        s.SetWidth(mm(0.1))
        board.Add(s)

    def arc(c, start, angle):
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_ARC)
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetCenter(pcbnew.VECTOR2I(mm(c[0]), mm(c[1])))
        s.SetStart(pcbnew.VECTOR2I(mm(start[0]), mm(start[1])))
        s.SetArcAngleAndEnd(pcbnew.EDA_ANGLE(angle, pcbnew.DEGREES_T))
        s.SetWidth(mm(0.1))
        board.Add(s)

    seg((x0 + r, y0), (x0 + w - r, y0)); seg((x0 + w, y0 + r), (x0 + w, y0 + h - r))
    seg((x0 + w - r, y0 + h), (x0 + r, y0 + h)); seg((x0, y0 + h - r), (x0, y0 + r))
    arc((x0 + r, y0 + r), (x0, y0 + r), 90); arc((x0 + w - r, y0 + r), (x0 + w - r, y0), 90)
    arc((x0 + w - r, y0 + h - r), (x0 + w, y0 + h - r), 90); arc((x0 + r, y0 + h - r), (x0 + r, y0 + h), 90)
    return board, nets


def ground_plane(board, nets, layer=pcbnew.B_Cu):
    """Solid ground pour over the whole board on the given layer."""
    z = pcbnew.ZONE(board)
    z.SetLayer(layer)
    z.SetNet(nets["GND"])
    z.SetMinThickness(mm(0.2))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(mm(0.25))
    z.SetThermalReliefSpokeWidth(mm(0.3))
    z.SetLocalClearance(mm(0.2))
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    ol = z.Outline()
    ol.NewOutline()
    for x, y in ((OX + 0.2, OY + 0.2), (OX + L.CB_W - 0.2, OY + 0.2), (OX + L.CB_W - 0.2, OY + L.CB_H - 0.2), (OX + 0.2, OY + L.CB_H - 0.2)):
        ol.Append(mm(x), mm(y))
    board.Add(z)


def design_rules(board, nets):
    ds = board.GetDesignSettings()
    ds.SetCopperLayerCount(2)
    ds.m_TrackMinWidth = mm(0.15)
    ds.m_MinClearance = mm(0.15)
    ds.m_ViasMinSize = mm(0.5)
    ds.m_MinThroughDrill = mm(0.3)
    ds.m_CopperEdgeClearance = mm(0.3)
    nc = ds.m_NetSettings.m_DefaultNetClass
    nc.SetClearance(mm(0.2)); nc.SetTrackWidth(mm(0.25)); nc.SetViaDiameter(mm(0.6)); nc.SetViaDrill(mm(0.3))


def write_project():
    """Design rules live in the project file in KiCad 7; they are what the DRC and the fab checks use."""
    import json
    pro = OUT / "shield.kicad_pro"
    d = json.loads(pro.read_text()) if pro.exists() else {"meta": {"filename": "shield.kicad_pro", "version": 1}}
    ds = d.setdefault("board", {}).setdefault("design_settings", {})
    ds["rules"] = {"min_clearance": 0.15, "min_track_width": 0.15, "min_via_diameter": 0.5, "min_through_hole_diameter": 0.3,
                   "min_copper_edge_clearance": 0.3, "min_hole_clearance": 0.25, "min_hole_to_hole": 0.25,
                   "min_silk_clearance": 0.0, "min_text_height": 0.8, "min_text_thickness": 0.12}
    ds["defaults"] = {"board_outline_line_width": 0.1, "copper_line_width": 0.25, "silk_line_width": 0.12, "silk_text_size_h": 0.8,
                      "silk_text_size_v": 0.8, "silk_text_thickness": 0.12, "fab_line_width": 0.1, "courtyard_line_width": 0.05}
    ns = d.setdefault("net_settings", {"meta": {"version": 3}, "net_colors": None})
    ns["classes"] = [{"name": "Default", "clearance": 0.2, "track_width": 0.25, "via_diameter": 0.6, "via_drill": 0.3,
                      "diff_pair_width": 0.2, "diff_pair_gap": 0.25, "diff_pair_via_gap": 0.25, "wire_width": 6, "bus_width": 12,
                      "line_style": 0, "microvia_diameter": 0.3, "microvia_drill": 0.1, "pcb_color": "rgba(0, 0, 0, 0.000)",
                      "schematic_color": "rgba(0, 0, 0, 0.000)"}]
    pro.write_text(json.dumps(d, indent=2))


def drc(board, path, show=("courtyards_overlap", "clearance", "copper_edge_clearance", "hole_clearance", "shorting_items", "items_not_allowed", "pth_inside_courtyard", "padstack")):
    import collections
    import re
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.WriteDRCReport(board, str(path), pcbnew.EDA_UNITS_MILLIMETRES, True)
    txt = Path(path).read_text()
    blocks = re.split(r"\n(?=\[)", txt)
    cnt = collections.Counter()
    for blk in blocks:
        m = re.match(r"\[(\w+)\]", blk)
        if not m:
            continue
        cnt[m.group(1)] += 1
        if m.group(1) in show:
            lines = [ln.strip() for ln in blk.splitlines()]
            print(lines[0], "|", " | ".join(l for l in lines[2:] if l.startswith("@"))[:230])
    print("DRC summary:", dict(cnt))


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "place"
    board, nets = build_board()
    design_rules(board, nets)
    OUT.mkdir(parents=True, exist_ok=True)
    write_project()
    out = OUT / "shield.kicad_pcb"
    if mode == "route":
        route(board, out, nets)
    ground_plane(board, nets)
    ground_plane(board, nets, pcbnew.F_Cu)
    board.Save(str(out))
    print("wrote", out)
    write_project()                                    # pcbnew rewrites the project file with default rules on save
    board = pcbnew.LoadBoard(str(out))                 # the zone filler is only stable on a board loaded from file
    design_rules(board, nets)
    drc(board, OUT / "drc.rpt")
    board.Save(str(out))                               # now with the filled ground pour


def route(board, out, nets_by_name):
    dsn = OUT / "shield.dsn"
    ses = OUT / "shield.ses"
    pcbnew.ExportSpecctraDSN(board, str(dsn))
    jar = os.environ.get("FREEROUTING_JAR", "freerouting.jar")
    subprocess.run(["xvfb-run", "-a", "java", "-jar", jar, "-de", str(dsn), "-do", str(ses), "-mp", "30"], check=True, timeout=900)
    import_ses(board, ses, nets_by_name)


def import_ses(board, ses_path, nets):
    """Read the routes of a Freerouting session file (KiCad 7's Python API cannot import it without a GUI)."""
    import re
    txt = Path(ses_path).read_text()
    res = float(re.search(r"\(routes\s+\(resolution um (\d+)\)", txt).group(1))     # units per micrometre
    layers = {"F.Cu": pcbnew.F_Cu, "B.Cu": pcbnew.B_Cu}

    def pt(x, y):
        return pcbnew.VECTOR2I(int(round(float(x) / res * 1000)), int(round(-float(y) / res * 1000)))

    body = txt[txt.index("(network_out"):]
    n_tr = n_via = 0
    for m in re.finditer(r"\(net (\S+)\s(.*?)(?=\n      \(net |\Z)", body, re.S):
        name, blk = m.group(1).strip('"'), m.group(2)
        ni = nets[name]
        for w in re.finditer(r"\(path (\S+) (\d+)\s+([-\d\s]+?)\)", blk):
            lay, width, coords = w.group(1), int(w.group(2)), w.group(3).split()
            pts = [pt(coords[i], coords[i + 1]) for i in range(0, len(coords), 2)]
            for a, b in zip(pts, pts[1:]):
                t = pcbnew.PCB_TRACK(board)
                t.SetStart(a); t.SetEnd(b); t.SetLayer(layers[lay]); t.SetNet(ni)
                t.SetWidth(int(round(width / res * 1000)))
                board.Add(t); n_tr += 1
        for v in re.finditer(r'\(via "[^"]*" ([-\d]+) ([-\d]+)', blk):
            via = pcbnew.PCB_VIA(board)
            via.SetPosition(pt(v.group(1), v.group(2)))
            via.SetNet(ni)
            via.SetViaType(pcbnew.VIATYPE_THROUGH)
            via.SetWidth(mm(0.6)); via.SetDrill(mm(0.3))
            via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            board.Add(via); n_via += 1
    print("imported", n_tr, "track segments,", n_via, "vias")


if __name__ == "__main__":
    main()
