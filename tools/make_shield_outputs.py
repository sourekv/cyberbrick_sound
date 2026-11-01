"""Manufacturing outputs of the shield board: Gerbers + drill (zip), component positions, BOM.
Run after tools/make_shield_pcb.py route.   python3 tools/make_shield_outputs.py
Output: hardware/shield/fab/ (committed so the files can be inspected; regenerate after any board change).
"""
import csv
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import shield_netlist as N  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PCB = ROOT / "hardware" / "shield" / "shield.kicad_pcb"
FAB = ROOT / "hardware" / "shield" / "fab"


def run(*a):
    subprocess.run(a, check=True, capture_output=True)


def main():
    if FAB.exists():
        shutil.rmtree(FAB)
    gb = FAB / "gerber"
    gb.mkdir(parents=True)
    layers = "F.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts"
    run("kicad-cli", "pcb", "export", "gerbers", "--layers", layers, "--no-protel-ext", "-o", str(gb), str(PCB))
    run("kicad-cli", "pcb", "export", "drill", "--format", "excellon", "--drill-origin", "absolute", "--excellon-units", "mm",
        "--generate-map", "--map-format", "gerberx2", "-o", str(gb) + "/", str(PCB))
    with zipfile.ZipFile(FAB / "shield_gerbers.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(gb.iterdir()):
            z.write(f, f.name)
    run("kicad-cli", "pcb", "export", "pos", "--format", "csv", "--units", "mm", "--side", "both", "-o", str(FAB / "shield_positions.csv"), str(PCB))
    # BOM grouped by value + footprint (no distributor numbers: they have to be chosen and checked by the buyer)
    groups = {}
    for ref, (sym, val, fp, pins, desc) in N.PARTS.items():
        if ref.startswith(("MH", "TP")):
            continue
        groups.setdefault((val, fp.split(":")[1], desc), []).append(ref)
    with open(FAB / "shield_bom.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Designators", "Qty", "Value", "Footprint", "Note"])
        for (val, fp, desc), refs in sorted(groups.items(), key=lambda kv: kv[1][0]):
            w.writerow([",".join(sorted(refs)), len(refs), val, fp, desc])
    for p in sorted(FAB.rglob("*")):
        if p.is_file():
            print(p.relative_to(FAB), p.stat().st_size)


if __name__ == "__main__":
    main()
