"""Render hardware/shield/shield.kicad_pcb to a PNG (kicad-cli SVG export + Chromium). Usage: render_pcb.py out.png [layers] [px width]"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

root = Path(__file__).resolve().parent.parent
out = Path(sys.argv[1])
layers = sys.argv[2] if len(sys.argv) > 2 else "F.Cu,B.Cu,F.Silkscreen,Edge.Cuts"
width = int(sys.argv[3]) if len(sys.argv) > 3 else 1400
with tempfile.TemporaryDirectory() as d:
    svg = Path(d) / "p.svg"
    subprocess.run(["kicad-cli", "pcb", "export", "svg", "--layers", layers, "--page-size-mode", "2", "--exclude-drawing-sheet",
                    "-o", str(svg), str(root / "hardware/shield/shield.kicad_pcb")], check=True, capture_output=True)
    txt = svg.read_text()
    m = re.search(r'viewBox="([-\d. ]+)"', txt)
    vb = [float(v) for v in m.group(1).split()]
    height = int(width * vb[3] / vb[2])
    txt = re.sub(r'<svg[^>]*>', lambda mm: re.sub(r'(width|height)="[^"]*"', '', mm.group(0)).replace("<svg", f'<svg width="{width}" height="{height}"', 1), txt, count=1)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": width, "height": height})
        pg.set_content(f'<body style="margin:0;background:#1d3a2a">{txt}</body>')
        pg.screenshot(path=str(out))
        b.close()
print(out)
