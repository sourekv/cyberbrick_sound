"""Interactive BOM of the shield board: one HTML file in which a part clicked in the list lights up on the picture of the
board (and the other way round). For repairs and measuring: rev B has no reference labels on the silkscreen.

Uses InteractiveHtmlBom (https://github.com/openscopeproject/InteractiveHtmlBom, MIT) with KiCad's own Python (it has
the pcbnew module). Install it once into a folder of your choice, then run:

    "C:\Program Files\KiCad\bin\python.exe" -m pip install --target C:\ibom InteractiveHtmlBom
    "C:\Program Files\KiCad\bin\python.exe" tools/make_shield_ibom.py C:\ibom

Output: hardware/shield/fab/shield_ibom.html (committed; regenerate after any board change). Tracks are left out
(--include-tracks makes KiCad 10's pcbnew raise a wxWidgets assert dialog that blocks the run); pads, outlines,
pin 1 marks and the silkscreen are drawn. Made with InteractiveHtmlBom 2.12.0, KiCad 10.0.8 on 2026-11-14.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PCB = ROOT / "hardware" / "shield" / "shield.kicad_pcb"
FAB = ROOT / "hardware" / "shield" / "fab"


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    script = Path(sys.argv[1]) / "InteractiveHtmlBom" / "generate_interactive_bom.py"
    if not script.exists():
        sys.exit(f"{script} not found: install InteractiveHtmlBom there first (see the top of this file)")
    subprocess.run([sys.executable, str(script), str(PCB), "--no-browser", "--dest-dir", str(FAB),
                    "--name-format", "shield_ibom", "--include-nets", "--highlight-pin1", "selected",
                    "--dark-mode"], check=True)


if __name__ == "__main__":
    main()
