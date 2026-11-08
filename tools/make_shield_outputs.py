"""Manufacturing outputs of the shield board: Gerbers + drill (zip), component positions, BOM, JLCPCB assembly files.
Run after tools/make_shield_pcb.py route.

    python3 tools/make_shield_outputs.py             everything (needs kicad-cli on the PATH)
    python3 tools/make_shield_outputs.py --bom-only  only the BOMs and the JLCPCB files, from the existing
                                                     fab/shield_positions.csv (no kicad-cli needed)

Output: hardware/shield/fab/ (committed so the files can be inspected; regenerate after any board change).
The footprints in the BOMs come from the board (the positions file), not from the schematic, because the board
generator overrides some of them (R6..R8 are 0402 on the board).
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
POS = FAB / "shield_positions.csv"
JLC = FAB / "jlcpcb"

# LCSC part numbers for assembly at JLCPCB, checked on lcsc.com on 2026-11-08 (in stock that day). Check the stock
# again before ordering; a part that ran out needs a replacement with the same value and package.
LCSC = {
    "C1": "C8649",      # Kyocera AVX TAJC107K010RNJ, tantalum 100 uF 10 V, case C (6032)
    "C2": "C15850",     # Samsung CL21A106KAYNNNE, 10 uF 25 V X5R 0805
    "C3": "C1591",      # Samsung CL10B104KB8NNNC, 100 nF 50 V X7R 0603
    "C4": "C14858",     # Samsung CL10C101JB8NNNC, 100 pF 50 V C0G 0603
    "C5": "C14858",
    "C6": "C1591",
    "C7": "C1591",
    "D1": "C8598",      # JSCJ B5819W SL, Schottky 40 V 1 A, SOD-123
    "D2": "C8598",
    "F1": "C43379",     # Ruilon SMD1206P050TF/13.2, PTC 500 mA hold, 13.2 V, 1206
    "FB1": "C85833",    # Murata BLM18KG601SN1D, 600 R @ 100 MHz, 1.3 A, 0603
    "FB2": "C85833",
    "J2": "C160402",    # JST SM02B-SRSS-TB(LF)(SN), SH 1.0 mm 2-pin, right angle
    "LED1": "C12624",   # Kento KT-0603G, green 0603
    "R1": "C21190",     # Uni-Royal 0603WAF1001T5E, 1 k 0603
    "R2": "C25803",     # Uni-Royal 0603WAF1003T5E, 100 k 0603
    "R3": "C21190",
    "R4": "C25803",
    "R5": "C22935",     # Uni-Royal 0603WAF1004T5E, 1 M 0603
    "R6": "C25105",     # Uni-Royal 0402WGF330JTCE, 33 R 0402
    "R7": "C25105",
    "R8": "C25105",
    "TVS1": "C19224",   # Nexperia PESD5V0S1BA, ESD diode 5 V, SOD-323
    "U1": "C910544",    # Maxim MAX98357AETE+T, TQFN-16 3x3
}
# soldered by hand, not by the assembly service: the Zero's two socket strips and the right-angle servo header
HAND_SOLDERED = {"J1", "J3", "J4"}


def run(*a):
    subprocess.run(a, check=True, capture_output=True)


def board_parts():
    """ref -> (value, footprint, x, y, rotation, side) from the positions file of the board."""
    parts = {}
    with open(POS, newline="") as f:
        for row in csv.DictReader(f):
            parts[row["Ref"]] = (row["Val"], row["Package"], row["PosX"], row["PosY"], row["Rot"], row["Side"])
    return parts


def write_boms():
    parts = board_parts()
    missing = [r for r in parts if r not in LCSC and r not in HAND_SOLDERED and not r.startswith(("MH", "TP", "JP"))]
    if missing:
        sys.exit(f"no LCSC part number for {missing}: add them to LCSC in {Path(__file__).name}")

    # full BOM, grouped by value + footprint + part number
    groups = {}
    for ref, (sym, val, fp, pins, desc) in N.PARTS.items():
        if ref.startswith(("MH", "TP")):
            continue
        board_fp = parts[ref][1] if ref in parts else fp.split(":")[1]
        lcsc = LCSC.get(ref, "hand-soldered" if ref in HAND_SOLDERED else "")
        groups.setdefault((val, board_fp, desc, lcsc), []).append(ref)
    with open(FAB / "shield_bom.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Designators", "Qty", "Value", "Footprint", "LCSC", "Note"])
        for (val, fp, desc, lcsc), refs in sorted(groups.items(), key=lambda kv: kv[1][0]):
            w.writerow([",".join(sorted(refs)), len(refs), val, fp, lcsc, desc])

    # JLCPCB assembly: BOM (Comment, Designator, Footprint, LCSC) and CPL (positions) of the assembled parts only
    JLC.mkdir(exist_ok=True)
    assembled = sorted(r for r in parts if r in LCSC)
    groups = {}
    for ref in assembled:
        val, fp = parts[ref][0], parts[ref][1]
        groups.setdefault((val, fp, LCSC[ref]), []).append(ref)
    with open(JLC / "shield_bom_jlcpcb.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Comment", "Designator", "Footprint", "LCSC"])
        for (val, fp, lcsc), refs in sorted(groups.items(), key=lambda kv: kv[1][0]):
            w.writerow([val, ",".join(refs), fp, lcsc])
    with open(JLC / "shield_cpl_jlcpcb.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        for ref in assembled:
            _v, _fp, x, y, rot, side = parts[ref]
            w.writerow([ref, f"{float(x):.4f}mm", f"{float(y):.4f}mm", "Top" if side == "top" else "Bottom",
                        f"{float(rot):g}"])


def main():
    if "--bom-only" in sys.argv:
        write_boms()
    else:
        if FAB.exists():
            shutil.rmtree(FAB)
        gb = FAB / "gerber"
        gb.mkdir(parents=True)
        layers = "F.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts"
        run("kicad-cli", "pcb", "export", "gerbers", "--layers", layers, "--no-protel-ext", "-o", str(gb), str(PCB))
        run("kicad-cli", "pcb", "export", "drill", "--format", "excellon", "--drill-origin", "absolute",
            "--excellon-units", "mm", "--generate-map", "--map-format", "gerberx2", "-o", str(gb) + "/", str(PCB))
        with zipfile.ZipFile(FAB / "shield_gerbers.zip", "w", zipfile.ZIP_DEFLATED) as z:
            for f in sorted(gb.iterdir()):
                z.write(f, f.name)
        run("kicad-cli", "pcb", "export", "pos", "--format", "csv", "--units", "mm", "--side", "both", "-o", str(POS),
            str(PCB))
        write_boms()
    for p in sorted(FAB.rglob("*")):
        if p.is_file():
            print(p.relative_to(FAB), p.stat().st_size)


if __name__ == "__main__":
    main()
