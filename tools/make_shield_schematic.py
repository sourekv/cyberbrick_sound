"""Generate the KiCad schematic of the shield from tools/shield_netlist.py.

Every pin gets a net label (or a power symbol) right at its end point, so the connectivity is exactly the
netlist and nothing depends on drawn wires. Run:  python3 tools/make_shield_schematic.py
Output: hardware/shield/shield.kicad_sch (+ a minimal project file). Check with kicad-cli (ERC, netlist).
"""
import re
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import shield_netlist as N  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "hardware" / "shield"
SYMDIR = Path("/usr/share/kicad/symbols")
SHEET_UUID = "8d1c2a52-6f0b-4c53-9a7d-5b7a1f3c9e01"


def uid(seed):
    return str(uuid.uuid5(uuid.UUID(SHEET_UUID), seed))


# ---------- library symbols ----------
_lib_cache = {}


def lib_text(nick, name):
    if nick not in _lib_cache:
        _lib_cache[nick] = (SYMDIR / f"{nick}.kicad_sym").read_text(encoding="utf-8")
    s = _lib_cache[nick]
    i = s.index(f'(symbol "{name}"')
    depth, j = 0, i
    while True:
        c = s[j]
        depth += (c == "(") - (c == ")")
        j += 1
        if depth == 0:
            break
    block = s[i:j]
    if "(extends" in block:
        raise SystemExit(f"{nick}:{name} extends another symbol, not supported")
    return block.replace(f'(symbol "{name}"', f'(symbol "{nick}:{name}"', 1)


def lib_pins(block):
    """number -> (x, y, angle) of every pin of the symbol, in symbol coordinates (y up)."""
    pins = {}
    for m in re.finditer(r'\(pin \w+ \w+(?: hide)?\s*\(at ([-\d.]+) ([-\d.]+) (\d+)\)(.*?)\(number "([^"]+)"', block, re.S):
        pins[m.group(5)] = (float(m.group(1)), float(m.group(2)), int(m.group(3)))
    return pins


# ---------- placement (sheet coordinates in mm; A3 = 420 x 297) ----------
# (ref -> x, y, rotation). Two-pin parts are rotated 90 degrees so their pins point left and right.
H = 90
PLACE = {
    # input block
    "J1": (45, 62, 0), "TVS1": (95, 50, 0), "R1": (140, 50, H), "R2": (185, 50, H),
    # power block
    "F1": (45, 105, H), "D1": (90, 105, 0), "D2": (135, 105, 0),
    "C1": (45, 135, H), "C2": (90, 135, H), "C3": (135, 135, H), "C6": (180, 135, H), "C7": (225, 135, H),
    "R3": (45, 165, H), "LED1": (90, 165, 0),
    # Zero sockets
    "J3": (300, 55, 0), "J4": (300, 110, 0),
    # amplifier block
    "R6": (45, 205, H), "R7": (45, 220, H), "R8": (45, 235, H),
    "U1": (150, 222, 0),
    "JP1": (225, 205, 0), "R4": (270, 205, H), "JP2": (225, 230, 0), "R5": (270, 230, H),
    "FB1": (225, 180, H), "FB2": (270, 180, H), "C4": (315, 180, H), "C5": (360, 180, H), "J2": (360, 220, 0),
    # test points and holes
    "TP1": (45, 266, H), "TP2": (80, 266, H), "TP3": (115, 266, H), "TP4": (150, 266, H),
    "TP5": (185, 266, H), "TP6": (220, 266, H), "TP7": (255, 266, H),
    "MH1": (330, 160, 0), "MH2": (350, 160, 0), "MH3": (370, 160, 0), "MH4": (390, 160, 0),
}
TITLES = [
    (30, 30, "Input and protection of the throttle signal"), (30, 90, "Power from the servo port (PWM2)"),
    (285, 30, "ESP32-S3-Zero (plugged into two 9-pin female sockets)"), (30, 190, "Amplifier, I2S series resistors, GAIN and SD_MODE"),
    (210, 170, "Speaker output filter and connector"), (30, 256, "Test pads (bottom side)"), (320, 140, "Mounting holes (2.7 mm, no copper)"),
]


def rot_pt(px, py, rot):
    """Pin end (symbol coordinates, y up) -> offset in sheet coordinates (y down) for a symbol rotated CCW by rot."""
    if rot == 0:
        return px, -py
    if rot == 90:
        return -py, -px
    if rot == 180:
        return -px, py
    if rot == 270:
        return py, px
    raise ValueError(rot)


def esc(s):
    return s.replace("\\", "\\\\").replace('"', '\\"')


def build():
    used = {}
    libs = []
    body = []
    flags = []
    counters = {"pwr": 0}
    labelled = {}                                    # (x, y) -> net, so stacked pins get one label

    def lib_for(sym):
        nick, name = sym.split(":")
        if sym not in used:
            used[sym] = lib_text(nick, name)
            libs.append(used[sym])
        return used[sym]

    for pow_sym in N.POWER_SYMBOLS.values():
        lib_for(pow_sym)
    lib_for("power:PWR_FLAG")

    def eff(hide=False, size=1.27):
        return f"(effects (font (size {size} {size})){' hide' if hide else ''})"

    for ref, (sym, val, fp, pins, desc) in N.PARTS.items():
        block = lib_for(sym)
        lp = lib_pins(block)
        x, y, rot = PLACE[ref]
        ext = max([abs(v[1]) for v in lp.values()] + [2.54]) if rot == 0 else max([abs(v[0]) for v in lp.values()] + [1.0]) + 2.5
        ext = ext + 3.5 if rot == 0 else 5.5
        ang = 90 if rot == 90 else 0                            # keep field text horizontal on rotated symbols
        ext_top = ext_bot = ext
        if ref.startswith(("TP", "MH")):
            ext_top, ext_bot = 4.5, (7 if ref.startswith("TP") else 4.5)
        if ref == "U1":
            ext_top, ext_bot = 26, 24
        pin_uuids = "".join(f'\n    (pin "{n}" (uuid {uid(ref + n)}))' for n in sorted(lp, key=lambda k: (len(k), k)))
        body.append(
            f'  (symbol (lib_id "{sym}") (at {x} {y} {rot}) (unit 1) (in_bom yes) (on_board yes) (dnp no)\n'
            f'    (uuid {uid(ref)})\n'
            f'    (property "Reference" "{ref}" (at {x} {y - ext_top} {ang}) {eff()})\n'
            f'    (property "Value" "{esc(val)}" (at {x} {y + ext_bot} {ang}) {eff()})\n'
            f'    (property "Footprint" "{fp}" (at {x} {y} 0) {eff(True)})\n'
            f'    (property "Datasheet" "~" (at {x} {y} 0) {eff(True)}){pin_uuids}\n'
            f'    (instances (project "shield" (path "/{SHEET_UUID}" (reference "{ref}") (unit 1))))\n  )')
        for pn, (px, py, pa) in lp.items():
            if pn not in pins:
                continue
            net = pins[pn]
            dx, dy = rot_pt(px, py, rot)
            sx, sy = round(x + dx, 2), round(y + dy, 2)
            if net is None:
                flags.append(f'  (no_connect (at {sx} {sy}) (uuid {uid("nc" + ref + pn)}))')
                continue
            if (sx, sy) in labelled:
                if labelled[(sx, sy)] != net:
                    raise SystemExit(f"{ref}.{pn}: stacked pins with different nets at {sx},{sy}")
                continue
            labelled[(sx, sy)] = net
            out_angle = (pa + 180 + rot) % 360                     # direction away from the symbol body
            if net in N.POWER_SYMBOLS:
                counters["pwr"] += 1
                pn_ref = f"#PWR{counters['pwr']:02d}"
                psym = N.POWER_SYMBOLS[net]
                base = 270 if net == "GND" else 90                    # direction the library graphic extends
                prot = (out_angle - base) % 360
                import math
                ox, oy = round(5.5 * math.cos(math.radians(out_angle)), 2), round(-5.5 * math.sin(math.radians(out_angle)), 2)
                vis = " hide" if ref.startswith(("TP", "J3")) else ""
                body.append(
                    f'  (symbol (lib_id "{psym}") (at {sx} {sy} {prot}) (unit 1) (in_bom yes) (on_board yes) (dnp no)\n'
                    f'    (uuid {uid(pn_ref)})\n'
                    f'    (property "Reference" "{pn_ref}" (at {sx} {sy} 0) {eff(True)})\n'
                    f'    (property "Value" "{net}" (at {round(sx + ox, 2)} {round(sy + oy, 2)} {90 if prot in (90, 270) else 0}) {eff(bool(vis))})\n'
                    f'    (property "Footprint" "" (at {sx} {sy} 0) {eff(True)})\n'
                    f'    (property "Datasheet" "" (at {sx} {sy} 0) {eff(True)})\n'
                    f'    (pin "1" (uuid {uid(pn_ref + "p")}))\n'
                    f'    (instances (project "shield" (path "/{SHEET_UUID}" (reference "{pn_ref}") (unit 1))))\n  )')
                if net in N.PWR_FLAG_NETS and ref.startswith("TP"):
                    counters["pwr"] += 1
                    fl = f"#FLG{counters['pwr']:02d}"
                    body.append(
                        f'  (symbol (lib_id "power:PWR_FLAG") (at {sx} {sy} 0) (unit 1) (in_bom yes) (on_board yes) (dnp no)\n'
                        f'    (uuid {uid(fl)})\n'
                        f'    (property "Reference" "{fl}" (at {sx} {sy} 0) {eff(True)})\n'
                        f'    (property "Value" "PWR_FLAG" (at {sx + 6} {sy} 0) {eff(True)})\n'
                        f'    (property "Footprint" "" (at {sx} {sy} 0) {eff(True)})\n'
                        f'    (property "Datasheet" "~" (at {sx} {sy} 0) {eff(True)})\n'
                        f'    (pin "1" (uuid {uid(fl + "p")}))\n'
                        f'    (instances (project "shield" (path "/{SHEET_UUID}" (reference "{fl}") (unit 1))))\n  )')
            else:
                just = "right" if out_angle == 180 else "left"
                body.append(f'  (label "{net}" (at {sx} {sy} {out_angle}) {eff()[:-1]} (justify {just} bottom)) (uuid {uid("lb" + ref + pn)}))')
    texts = [f'  (text "{esc(t)}" (at {x} {y} 0) (effects (font (size 2.5 2.5) bold) (justify left bottom)) (uuid {uid("t" + t)}))'
             for x, y, t in TITLES]
    notes = [
        "Notes: MAX98357A needs a supported sample rate (8, 16, 32, 44.1, 48 kHz ...); 22.05 kHz is not listed in the datasheet.",
        "JP1 open = gain 9 dB. JP2 bridged = (L+R)/2 mix. FB1, FB2, R6-R8 and TVS1 are optional (0R / not fitted is allowed).",
    ]
    texts += [f'  (text "{esc(t)}" (at 30 {280 + 4 * i} 0) (effects (font (size 1.8 1.8)) (justify left bottom)) (uuid {uid("n" + str(i))}))'
              for i, t in enumerate(notes)]
    sch = ('(kicad_sch (version 20230121) (generator eeschema)\n'
           f'  (uuid {SHEET_UUID})\n  (paper "A3")\n'
           '  (title_block (title "Sound shield for the CyberBrick receiver") (date "2026-11-01") (rev "A")\n'
           '    (comment 1 "Engine sound module: ESP32-S3-Zero + MAX98357A, throttle from the servo port PWM2"))\n'
           '  (lib_symbols\n' + "\n".join(libs) + '\n  )\n' + "\n".join(body + flags + texts) + '\n'
           '  (sheet_instances (path "/" (page "1")))\n)\n')
    return sch


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "shield.kicad_sch").write_text(build(), encoding="utf-8")
    pro = OUT / "shield.kicad_pro"
    if not pro.exists():
        pro.write_text('{\n  "meta": {"filename": "shield.kicad_pro", "version": 1}\n}\n', encoding="utf-8")
    print("wrote", OUT / "shield.kicad_sch")


if __name__ == "__main__":
    main()
