"""The colour of the shield board in its KiCad file: the physical stackup (Board Setup > Physical Stackup) with the
solder mask colour of rev B, blue like the ESP32-S3-Zero on top of it (decided 2026-11-27; rev A is green).

KiCad uses the colour in its 3D view (with the board stackup colours switched on) and writes it into the gerber job
file; the gerbers and the drill file do not change. The colour of a real board is chosen in the order form.

tools/make_shield_rev_b.py calls set_stackup() after it has written the board. On a rev B board it can also be run
alone, with any Python (running it again only sets the colour):

    python tools/shield_stackup.py
"""
import re
from pathlib import Path

PCB = Path(__file__).resolve().parent.parent / "hardware" / "shield" / "shield.kicad_pcb"
# A custom blue (RRGGBBAA): KiCad's own "Blue" looks violet in the 3D view; this one is close to the blue of the Zero and
# lets the tracks show through.
MASK = "#0A2F80F2"
SILK = "White"

# 2 layers, 1.6 mm in all: mask 0.01 + copper 0.035 + core 1.51 + copper 0.035 + mask 0.01
STACKUP = f"""(stackup
(layer "F.SilkS" (type "Top Silk Screen") (color "{SILK}"))
(layer "F.Paste" (type "Top Solder Paste"))
(layer "F.Mask" (type "Top Solder Mask") (color "{MASK}") (thickness 0.01))
(layer "F.Cu" (type "copper") (thickness 0.035))
(layer "dielectric 1" (type "core") (thickness 1.51) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))
(layer "B.Cu" (type "copper") (thickness 0.035))
(layer "B.Mask" (type "Bottom Solder Mask") (color "{MASK}") (thickness 0.01))
(layer "B.Paste" (type "Bottom Solder Paste"))
(layer "B.SilkS" (type "Bottom Silk Screen") (color "{SILK}"))
(copper_finish "None")
(dielectric_constraints no)
)"""


def set_stackup(path=PCB):
    text = Path(path).read_bytes().decode("utf-8")
    nl = "\r\n" if "\r\n" in text else "\n"
    if "(stackup" in text:
        # KiCad's own layout: one item per line, the colour after the type of the layer
        new, n = re.subn(r'(\(type "(?:Top|Bottom) Solder Mask"\)\s*\(color ")[^"]*(")', rf"\g<1>{MASK}\g<2>", text)
        if n != 2:
            raise SystemExit(f"{path}: the stackup has no two mask colours to set; use KiCad's Board Setup")
    else:
        lines = STACKUP.split("\n")
        block = [lines[0]] + ["\t" + x for x in lines[1:-1]] + [lines[-1]]
        new, n = re.subn(r"(\n\t\(setup)(\r?\n)", lambda m: m.group(1) + m.group(2) + "".join("\t\t" + x + nl for x in block),
                         text, count=1)
        if n != 1:
            raise SystemExit(f"{path}: no (setup section found")
    Path(path).write_bytes(new.encode("utf-8"))
    print(f"solder mask {MASK} set in {path}")


if __name__ == "__main__":
    if '(rev "B")' not in PCB.read_text(encoding="utf-8"):
        raise SystemExit(f"{PCB.name} is not rev B; rev A is green")
    set_stackup()
