#!/usr/bin/env python3
"""Generate the shield mock (docs/shield-mock.svg + .png) and the 3D viewer (docs/shield-3d.html)
from the layout in tools/shield_layout.py.

    python3 tools/make_shield_mock.py            # SVG + 3D page
    python3 tools/make_shield_mock.py --png      # also render the PNG (needs playwright + chromium)
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import shield_layout as L

ROOT = Path(__file__).resolve().parent.parent
S = 34.0                      # px per mm (set per figure)
MX, MY = 150, 260             # pixel position of the board origin (set per figure)
W = int(L.BOARD_W * S + 2 * MX)
H = int(L.BOARD_H * S + MY + 420)

BG, FG, MUTED = "#ffffff", "#1b2530", "#5c6b7a"
GREEN, GREEN_D = "#2f8f4e", "#1d6b36"


def X(x): return MX + x * S
def Y(y): return MY + y * S


def rect(x0, y0, x1, y1, **kw):
    attrs = " ".join(f'{k.replace("_", "-")}="{v}"' for k, v in kw.items())
    return f'<rect x="{X(x0):.1f}" y="{Y(y0):.1f}" width="{(x1 - x0) * S:.1f}" height="{(y1 - y0) * S:.1f}" {attrs}/>'


def text(x, y, s, size=13, anchor="start", weight=500, fill=FG, mono=True, rot=None):
    fam = "ui-monospace,Menlo,Consolas,monospace" if mono else "system-ui,sans-serif"
    tr = f' transform="rotate({rot} {X(x):.1f} {Y(y):.1f})"' if rot else ""
    return (f'<text x="{X(x):.1f}" y="{Y(y):.1f}" font-family="{fam}" font-size="{size}" font-weight="{weight}" '
            f'text-anchor="{anchor}" dominant-baseline="middle" fill="{fill}"{tr}>{s}</text>')


def circle(cx, cy, r, **kw):
    attrs = " ".join(f'{k.replace("_", "-")}="{v}"' for k, v in kw.items())
    return f'<circle cx="{X(cx):.1f}" cy="{Y(cy):.1f}" r="{r * S:.1f}" {attrs}/>'


def board_elems(vid):
    """Board outline (union of shapes, with an outline) and the mounting holes of a variant."""
    v = L.VARIANT[vid]
    out = []
    for stage in ("edge", "fill"):
        for sh in v["shapes"]:
            kw = dict(fill=GREEN_D, stroke=GREEN_D, stroke_width=4) if stage == "edge" else dict(fill=GREEN, stroke="none")
            if sh[0] == "rect":
                _, x0, y0, x1, y1, rad = sh
                out.append(rect(x0, y0, x1, y1, rx=rad * S, **kw))
            else:
                out.append(circle(sh[1], sh[2], sh[3], **kw))
    for hx, hy, d in v["holes"]:
        out.append(circle(hx, hy, L.CB_RING_D / 2, fill="#d8b04a", stroke="#9a7a2a", stroke_width=1))
        out.append(circle(hx, hy, d / 2, fill=BG, stroke="#9a7a2a", stroke_width=1))
    return out


def dim_line(x0, y0, x1, y1, label, off=(0, -0.5), rot=None):
    """Dimension line between two points (mm) with arrow heads and a label."""
    o = [f'<line x1="{X(x0):.1f}" y1="{Y(y0):.1f}" x2="{X(x1):.1f}" y2="{Y(y1):.1f}" stroke="#c0392b" stroke-width="1.3"/>']
    for (a, b, c, d) in ((x0, y0, x1, y1), (x1, y1, x0, y0)):
        import math
        ang = math.atan2(Y(d) - Y(b), X(c) - X(a)) if False else math.atan2(Y(d) - Y(b), X(c) - X(a))
        px, py = X(a), Y(b)
        for da in (0.35, -0.35):
            o.append(f'<line x1="{px:.1f}" y1="{py:.1f}" x2="{px + 11 * math.cos(ang + da):.1f}" y2="{py + 11 * math.sin(ang + da):.1f}" stroke="#c0392b" stroke-width="1.3"/>')
    o.append(text((x0 + x1) / 2 + off[0], (y0 + y1) / 2 + off[1], label, 13, "middle", 600, "#c0392b", rot=rot))
    return o


def panel(vid, title, sub, tx_px=None):
    """One top view of the shield for the given board variant."""
    o = []
    tx = (tx_px - MX) / S if tx_px is not None else -MX / S + 0.4
    o.append(text(tx, -7.2 if tx_px is None else -10.5, title, 20, weight=600, mono=False))
    o.append(text(tx, -6.4 if tx_px is None else -9.7, sub, 13, fill=MUTED, mono=False))

    # board
    o += board_elems(vid)
    # protruding plugs (outside the board): servo plug at the top, speaker plug at the bottom
    o.append(rect(5.3, -6.0, 12.7, 0.0, fill="none", stroke=MUTED, stroke_width=1.2, stroke_dasharray="5 4"))
    o.append(text(9.0, -3.0, "servo cable from PWM2", 12, "middle", fill=MUTED))
    o.append(rect(10.2, L.BOARD_H, 14.2, L.BOARD_H + 5.0, fill="none", stroke=MUTED, stroke_width=1.2, stroke_dasharray="5 4"))
    o.append(text(12.2, L.BOARD_H + 2.5, "speaker plug", 12, "middle", fill=MUTED))
    # USB-C of the Zero (above, for orientation)
    o.append(rect(4.53, -0.15, 13.47, 7.15, fill="none", stroke="#8d949c", stroke_width=1.2, stroke_dasharray="2 4"))
    o.append(text(9.0, 7.7, "USB-C of the Zero (above)", 11, "middle", fill="#8d949c"))

    # header strips
    for hx in L.HDR_X:
        o.append(rect(hx - 1.27, 0.32, hx + 1.27, 23.18, fill="#1c1c1e", opacity="0.85", rx=2))
    for i, y in enumerate(L.PIN_Y):
        for hx in L.HDR_X:
            o.append(f'<circle cx="{X(hx):.1f}" cy="{Y(y):.1f}" r="{0.62 * S / 2 + 3:.1f}" fill="#d8b04a"/>')
        o.append(text(L.HDR_X[0] - 1.5, y, L.LEFT_PINS[i], 11, "end", fill="#d9efe0"))
        o.append(text(L.HDR_X[1] + 1.5, y, L.RIGHT_PINS[i], 11, "start", fill="#d9efe0"))

    # traces
    for n in L.NETS:
        bot = n.get("layer") == "bot"
        pts = " ".join(f"{X(a):.1f},{Y(b):.1f}" for a, b in n["pts"])
        o.append(f'<polyline points="{pts}" fill="none" stroke="{n["color"]}" stroke-width="{0.35 * S:.1f}" '
                 f'stroke-linejoin="round" stroke-linecap="round"' + (' stroke-dasharray="6 5" opacity="0.8"' if bot else "") + "/>")
    for vx, vy in L.GND_VIAS + L.HOP_VIAS:
        o.append(f'<circle cx="{X(vx):.1f}" cy="{Y(vy):.1f}" r="{0.45 * S / 2 + 2:.1f}" fill="#d8b04a"/>')
        o.append(f'<circle cx="{X(vx):.1f}" cy="{Y(vy):.1f}" r="{0.2 * S / 2:.1f}" fill="{GREEN_D}"/>')

    # parts
    for p in L.PARTS:
        x0, y0, x1, y1 = p["x"] - p["w"] / 2, p["y"] - p["h"] / 2, p["x"] + p["w"] / 2, p["y"] + p["h"] / 2
        k = p["kind"]
        if k == "hdr_ra":
            o.append(rect(x0, y0, x1, y1, fill="#222", stroke="#000", stroke_width=1))
            for px in L.J1_X:
                o.append(f'<circle cx="{X(px):.1f}" cy="{Y(L.J1_Y):.1f}" r="{0.45 * S:.1f}" fill="#d8b04a"/>')
            for px, nm in zip(L.J1_X, "SVG"):
                o.append(text(px, -0.9, nm, 13, "middle", 700))
        elif k == "jst_side":
            o.append(rect(x0, y0, x1, y1, fill="#ece6d6", stroke="#7a7466", stroke_width=1.2))
            o.append(rect(x0 + 0.5, y0 + 1.7, x1 - 0.5, y1, fill="#cfc8b4", stroke="none"))
            for px, py in L.J2_PADS:
                o.append(f'<circle cx="{X(px):.1f}" cy="{Y(py):.1f}" r="{0.5 * S / 2:.1f}" fill="#d8b04a"/>')
            o.append(text(L.J2_PADS[0][0], L.J2_PADS[0][1] - 0.9, "+", 12, "middle", 700)); o.append(text(L.J2_PADS[1][0], L.J2_PADS[1][1] - 0.9, "-", 12, "middle", 700))
        elif k == "led":
            o.append(rect(p["x"] - 0.8, p["y"] - 0.4, p["x"] + 0.8, p["y"] + 0.4, fill="#59e06f", stroke="#1f7a33", stroke_width=1))
            o.append(rect(p["x"] - 1.1, p["y"] - 0.45, p["x"] - 0.7, p["y"] + 0.45, fill="#c9ced4", stroke="none"))
            o.append(rect(p["x"] + 0.7, p["y"] - 0.45, p["x"] + 1.1, p["y"] + 0.45, fill="#c9ced4", stroke="none"))
            o.append(rect(x0, y0, x1, y1, fill="none", stroke="#f4f4ee", stroke_width=0.8, stroke_dasharray="3 3"))
        elif k == "hdr_v":
            o.append(rect(x0, y0, x1, y1, fill="#222", stroke="#000", stroke_width=1))
            for (px, py), nm in zip(p["pins"], p["pin_names"]):
                o.append(circle(px, py, 0.35, fill="#d8b04a"))
                o.append(text(px + 1.7, py, nm, 11, "start", fill="#d9efe0"))
        elif k == "qfn":
            bx0, by0, bx1, by1 = p["x"] - 1.5, p["y"] - 1.5, p["x"] + 1.5, p["y"] + 1.5
            o.append(rect(x0, y0, x1, y1, fill="none", stroke="#f4f4ee", stroke_width=1, stroke_dasharray="3 3"))
            o.append(rect(bx0, by0, bx1, by1, fill="#1c1c1e", stroke="#000", stroke_width=1))
            o.append(f'<circle cx="{X(bx0 + 0.35):.1f}" cy="{Y(by0 + 0.35):.1f}" r="3" fill="#888"/>')
        elif k == "cap_t":
            bw, bh = p["body"]
            o.append(rect(p["x"] - bw / 2, p["y"] - bh / 2, p["x"] + bw / 2, p["y"] + bh / 2, fill="#e0a85b", stroke="#8a5a1c", stroke_width=1))
            o.append(rect(p["x"] - bw / 2, p["y"] - bh / 2, p["x"] + bw / 2, p["y"] - bh / 2 + 0.9, fill="#3a2a10", stroke="none"))
            o.append(rect(x0, y0, x1, y1, fill="none", stroke="#f4f4ee", stroke_width=0.8, stroke_dasharray="3 3"))
        else:                                    # chip parts and diodes
            bw, bh = p.get("body", (p["w"], p["h"]))
            col = {"chip_r": "#2a2a2a", "chip_c": "#d6b77e", "chip_f": "#e3cf5e", "diode": "#1c1c1e"}[k]
            o.append(rect(p["x"] - bw / 2, p["y"] - bh / 2, p["x"] + bw / 2, p["y"] + bh / 2, fill=col, stroke="#000", stroke_width=0.8))
            o.append(rect(x0, y0, x1, y1, fill="none", stroke="#f4f4ee", stroke_width=0.8, stroke_dasharray="3 3"))
            if k == "diode":
                yb = p["y"] + bh / 2 - 0.5 if p["band"] == "bottom" else p["y"] - bh / 2
                o.append(rect(p["x"] - bw / 2, yb, p["x"] + bw / 2, yb + 0.5, fill="#c9ced4", stroke="none"))
        # reference label
        lx = x1 + 0.25 if p["ref"] not in ("J1", "J2", "U1", "C2", "C3") else None
        if p["ref"] in ("R1", "F1", "D1", "D2", "R2", "C1", "LED1", "R3", "J3"):
            o.append(text(p["x"], y0 - 0.45 if p["ref"] != "C1" else y0 - 0.45, p["ref"], 12, "middle", 700, "#f4f4ee"))
    for ref, x, y in (("U1", 6.0, 17.35), ("C2", 5.2, 15.35), ("C3", 9.0, 15.35), ("J2", 12.2, 23.9)):
        pass
    o.append(text(6.0, 22.35, "U1", 12, "middle", 700, "#f4f4ee"))
    o.append(text(5.2, 15.45, "C2", 12, "middle", 700, "#f4f4ee"))
    o.append(text(9.0, 15.55, "C3", 12, "middle", 700, "#f4f4ee"))
    o.append(text(12.2, 22.3, "J2", 12, "middle", 700, "#1b2530"))
    o.append(text(9.0, 0.5, "J1", 12, "middle", 700, "#fff"))

    return o


def legend():
    o = []
    ly = L.BOARD_H + 6.2
    o.append(text(0, ly, "Top side (between the header strips)", 13, weight=600, mono=False))
    items = [("#ff7a6b", "5 V (servo V, through F1, D1)"), ("#ffb347", "throttle S to GPIO1"),
             ("#6ec1ff", "I2S to the amplifier"), ("#ececec", "speaker"),
             ("#d6a8ff", "spare GPIO to J3"), ("#9aa7b4", "ground (to the bottom plane)")]
    for i, (c, t) in enumerate(items):
        yy = ly + 1.05 * (i + 1)
        o.append(f'<line x1="{X(0):.1f}" x2="{X(1.4):.1f}" y1="{Y(yy):.1f}" y2="{Y(yy):.1f}" stroke="{c}" stroke-width="{0.35 * S:.1f}" stroke-linecap="round"/>')
        o.append(text(1.9, yy, t, 12, fill=FG, mono=False))
    yy = ly + 1.05 * 7
    o.append(f'<line x1="{X(0):.1f}" x2="{X(1.4):.1f}" y1="{Y(yy):.1f}" y2="{Y(yy):.1f}" stroke="#ff7a6b" stroke-width="{0.35 * S:.1f}" stroke-dasharray="6 5" stroke-linecap="round"/>')
    o.append(text(1.9, yy, "hop on the bottom layer (under the S trace)", 12, fill=FG, mono=False))
    o.append(text(9.0, ly, "Bottom side: GND plane, 7 test pads (5V, 3V3, GND, IO1, BCLK, LRC, DIN)", 11, "start", fill=MUTED, mono=False))
    return o


def wrap(w, h, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">'
            f'<rect width="{w}" height="{h}" fill="{BG}"/>\n' + "\n".join(body) + "\n</svg>")


def build_svg():
    """Top view of the shield on the CyberBrick-sized board, with dimensions and legend."""
    global S, MX, MY
    S, MY = 28.0, 330
    MX = 130 + 5.5 * S
    body = panel("cb", "Sound shield, top view",
                 f"{L.CB_W:g} x {L.CB_H:g} mm, same size and mounting holes as the CyberBrick receiver shield; the ESP32-S3-Zero sits in the middle", tx_px=130)
    # the Zero outline, dashed
    body.append(rect(0, 0, L.BOARD_W, L.BOARD_H, fill="none", stroke="#f4f4ee", stroke_width=1, stroke_dasharray="2 5", opacity="0.9"))
    hx0, hx1 = L.CB_HOLES[0][0], L.CB_HOLES[1][0]
    hy0, hy1 = L.CB_HOLES[0][1], L.CB_HOLES[2][1]
    body += dim_line(hx0, -7.0, hx1, -7.0, f"{L.CB_DX:.1f}", off=(0, -0.55))
    body += dim_line(25.3, hy0, 25.3, hy1, f"{L.CB_DY:.1f}", off=(0.9, 0), rot=-90)
    body.append(text(hx0 - 0.2, hy0 - 3.9, f"hole {L.CB_HOLE_D:g} mm", 12, "middle", 600, "#c0392b"))
    body += legend()
    ny = L.BOARD_H + 6.2 + 1.05 * 9
    body.append(text(0.0, ny, "Hole spacing 23.0 x 24.0 mm from the CAD model of a CyberBrick receiver test housing (matches the manufacturer's image).",
                     12, "start", fill=MUTED, mono=False))
    body.append(text(0.0, ny + 0.9, "Hole diameter 2.7 mm from the manufacturer's image. Verify both with calipers on the real receiver.",
                     12, "start", fill=MUTED, mono=False))
    clr = ((L.CB_DX / 2 - L.BOARD_W / 2) ** 2 + (L.CB_DY / 2 - L.BOARD_H / 2) ** 2) ** 0.5 - 2.25
    body.append(text(0.0, ny + 1.8, f"A screw head of 4.5 mm leaves only {clr:.2f} mm to the corner of the Zero; use a low or countersunk head.",
                     12, "start", fill=MUTED, mono=False))
    w = int(130 * 2 + L.CB_W * S)
    h = int(MY + (ny + 3.1) * S)
    return wrap(w, h, body), w, h


def build_3d():
    tpl = (Path(__file__).parent / "shield-3d.template.html").read_text(encoding="utf-8")
    data = dict(
        board=dict(x0=L.ZERO_CX - L.CB_W / 2, y0=L.ZERO_CY - L.CB_H / 2, w=L.CB_W, h=L.CB_H, t=L.BOARD_T),
        zero=dict(w=L.BOARD_W, l=L.BOARD_H), holes=L.CB_HOLES, ringD=L.CB_RING_D, hdrX=L.HDR_X, hdrH=L.HDR_H, pinY=L.PIN_Y,
        leftPins=L.LEFT_PINS, rightPins=L.RIGHT_PINS, j1x=L.J1_X, j1y=L.J1_Y, parts=L.PARTS, nets=L.NETS,
        j2Pads=L.J2_PADS, gndVias=L.GND_VIAS, hopVias=L.HOP_VIAS, tp=L.TP, tpNames=L.TP_NAMES,
    )
    return tpl.replace("/*LAYOUT_JSON*/null", json.dumps(data))


def main():
    if not L.check():
        sys.exit(1)
    svg, w, h = build_svg()
    (ROOT / "docs" / "shield-mock.svg").write_text(svg, encoding="utf-8")
    (ROOT / "docs" / "shield-3d.html").write_text(build_3d(), encoding="utf-8")
    print("wrote docs/shield-mock.svg and docs/shield-3d.html")
    if "--png" in sys.argv:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
            pg.goto("file://" + str(ROOT / "docs" / "shield-mock.svg"))
            pg.screenshot(path=str(ROOT / "docs" / "shield-mock.png"))
            b.close()
        print("wrote docs/shield-mock.png")


if __name__ == "__main__":
    main()
