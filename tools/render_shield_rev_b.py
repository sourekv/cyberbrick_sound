"""Make docs/shield-pcb-rev-b-top.png: the 3D render of the rev B board (top side, the colours of the board stackup)
with the intended "USB-C" label added to the picture only (it is not in the board files).

Usage: python tools/render_shield_rev_b.py

Needs KiCad's kicad-cli and ImageMagick (magick): both are looked for on the PATH, then in their usual Windows folders.
"""
import glob
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PCB = ROOT / "hardware" / "shield" / "shield.kicad_pcb"
OUT = ROOT / "docs" / "shield-pcb-rev-b-top.png"


def program(name, *patterns):
    found = shutil.which(name) or next((m for p in patterns for m in sorted(glob.glob(p), reverse=True)), None)
    if not found:
        raise SystemExit(f"{name} not found")
    return found


def main():
    cli = program("kicad-cli", r"C:\Program Files\KiCad\bin\kicad-cli.exe", r"C:\Program Files\KiCad\*\bin\kicad-cli.exe")
    magick = program("magick", r"C:\Program Files\ImageMagick*\magick.exe")
    with tempfile.TemporaryDirectory() as d:
        raw = Path(d) / "top.png"
        subprocess.run([cli, "pcb", "render", "--side", "top", "--quality", "high", "--width", "1100", "--height", "1100",
                        "--background", "opaque", "--use-board-stackup-colors", "-o", str(raw), str(PCB)], check=True)
        subprocess.run([magick, str(raw), "-font", "Arial", "-pointsize", "34", "-fill", "white", "-gravity", "northwest",
                        "-annotate", "+676+18", "USB-C", "-strip", str(OUT)], check=True)
    print(OUT)


if __name__ == "__main__":
    main()
