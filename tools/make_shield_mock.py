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
S = 34.0                      # px per mm
MX, MY = 150, 260
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


def build_svg():
    o = []
    o.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">')
    o.append(f'<rect width="{W}" height="{H}" fill="{BG}"/>')
    o.append(text(-MX / S + 0.4, -7.2, "Sound shield, top view", 20, weight=600, mono=False))
    o.append(text(-MX / S + 0.4, -6.4, f"{L.BOARD_W:g} x {L.BOARD_H:g} mm = outline of the ESP32-S3-Zero, which sits on top of it", 13, fill=MUTED, mono=False))

    # protruding plugs (outside the board): servo plug at the top, speaker plug at the bottom
    o.append(rect(5.3, -6.0, 12.7, 0.0, fill="none", stroke=MUTED, stroke_width=1.2, stroke_dasharray="5 4"))
    o.append(text(9.0, -3.0, "servo cable from PWM2", 12, "middle", fill=MUTED))
    o.append(rect(9.25, L.BOARD_H, 15.15, L.BOARD_H + 5.0, fill="none", stroke=MUTED, stroke_width=1.2, stroke_dasharray="5 4"))
    o.append(text(12.2, L.BOARD_H + 2.5, "speaker plug", 12, "middle", fill=MUTED))
    # USB-C of the Zero (above, for orientation)
    o.append(rect(4.53, -0.15, 13.47, 7.15, fill="none", stroke="#8d949c", stroke_width=1.2, stroke_dasharray="2 4"))
    o.append(text(9.0, 7.7, "USB-C of the Zero (above)", 11, "middle", fill="#8d949c"))

    # board
    o.append(rect(0, 0, L.BOARD_W, L.BOARD_H, fill=GREEN, stroke=GREEN_D, stroke_width=2, rx=4))
    # header strips
    for hx in L.HDR_X:
        o.append(rect(hx - 1.27, 0.32, hx + 1.27, 23.18, fill="#1c1c1e", opacity="0.85", rx=2))
    for i, y in enumerate(L.PIN_Y):
        for hx in L.HDR_X:
            o.append(f'<circle cx="{X(hx):.1f}" cy="{Y(y):.1f}" r="{0.62 * S / 2 + 3:.1f}" fill="#d8b04a"/>')
        o.append(text(L.HDR_X[0] - 1.5, y, L.LEFT_PINS[i], 11, "end", fill=MUTED))
        o.append(text(L.HDR_X[1] + 1.5, y, L.RIGHT_PINS[i], 11, "start", fill=MUTED))

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
            o.append(rect(x0 + 0.6, y0 + 2.4, x1 - 0.6, y1, fill="#cfc8b4", stroke="none"))
            for px in (10.7, 12.7):
                o.append(f'<circle cx="{X(px):.1f}" cy="{Y(18.6):.1f}" r="{0.55 * S / 2:.1f}" fill="#d8b04a"/>')
            o.append(text(10.7, 17.95, "+", 12, "middle", 700)); o.append(text(12.7, 17.95, "-", 12, "middle", 700))
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
        if p["ref"] in ("R1", "F1", "D1", "D2", "R2", "C1"):
            o.append(text(p["x"], y0 - 0.45 if p["ref"] != "C1" else y0 - 0.45, p["ref"], 12, "middle", 700, "#f4f4ee"))
    for ref, x, y in (("U1", 6.0, 17.35), ("C2", 5.2, 15.35), ("C3", 9.0, 15.35), ("J2", 12.2, 23.9)):
        pass
    o.append(text(6.0, 22.35, "U1", 12, "middle", 700, "#f4f4ee"))
    o.append(text(5.2, 15.45, "C2", 12, "middle", 700, "#f4f4ee"))
    o.append(text(9.0, 15.55, "C3", 12, "middle", 700, "#f4f4ee"))
    o.append(text(12.2, 21.3, "J2", 12, "middle", 700, "#1b2530"))
    o.append(text(9.0, 0.5, "J1", 12, "middle", 700, "#fff"))

    # legend below
    ly = L.BOARD_H + 6.2
    o.append(text(0, ly, "Top side (between the header strips)", 13, weight=600, mono=False))
    items = [("#ff7a6b", "5 V (servo V, through F1, D1)"), ("#ffb347", "throttle S to GPIO1"),
             ("#6ec1ff", "I2S to the amplifier"), ("#ececec", "speaker")]
    for i, (c, t) in enumerate(items):
        yy = ly + 1.05 * (i + 1)
        o.append(f'<line x1="{X(0):.1f}" x2="{X(1.4):.1f}" y1="{Y(yy):.1f}" y2="{Y(yy):.1f}" stroke="{c}" stroke-width="{0.35 * S:.1f}" stroke-linecap="round"/>')
        o.append(text(1.9, yy, t, 12, fill=FG, mono=False))
    yy = ly + 1.05 * 5
    o.append(f'<line x1="{X(0):.1f}" x2="{X(1.4):.1f}" y1="{Y(yy):.1f}" y2="{Y(yy):.1f}" stroke="#ff7a6b" stroke-width="{0.35 * S:.1f}" stroke-dasharray="6 5" stroke-linecap="round"/>')
    o.append(text(1.9, yy, "hop on the bottom layer (under the S trace)", 12, fill=FG, mono=False))
    o.append(text(9.0, ly, "Bottom side: GND plane, 7 test pads (5V, 3V3, GND, IO1, BCLK, LRC, DIN)", 11, "start", fill=MUTED, mono=False))
    o.append("</svg>")
    return "\n".join(o)


def build_3d():
    tpl = (Path(__file__).parent / "shield-3d.template.html").read_text(encoding="utf-8")
    data = dict(
        board=dict(w=L.BOARD_W, h=L.BOARD_H, t=L.BOARD_T), hdrX=L.HDR_X, hdrH=L.HDR_H, pinY=L.PIN_Y,
        leftPins=L.LEFT_PINS, rightPins=L.RIGHT_PINS, j1x=L.J1_X, j1y=L.J1_Y, parts=L.PARTS, nets=L.NETS,
        gndVias=L.GND_VIAS, hopVias=L.HOP_VIAS, tp=L.TP, tpNames=L.TP_NAMES,
    )
    return tpl.replace("/*LAYOUT_JSON*/null", json.dumps(data))


def main():
    if not L.check():
        sys.exit(1)
    svg = build_svg()
    (ROOT / "docs" / "shield-mock.svg").write_text(svg, encoding="utf-8")
    (ROOT / "docs" / "shield-3d.html").write_text(build_3d(), encoding="utf-8")
    print("wrote docs/shield-mock.svg and docs/shield-3d.html")
    if "--png" in sys.argv:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
            pg.goto("file://" + str(ROOT / "docs" / "shield-mock.svg"))
            pg.screenshot(path=str(ROOT / "docs" / "shield-mock.png"))
            b.close()
        print("wrote docs/shield-mock.png")


if __name__ == "__main__":
    main()
