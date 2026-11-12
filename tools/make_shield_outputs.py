"""Manufacturing outputs of the shield board: Gerbers + drill (zip), component positions, BOM, assembly files for
JLCPCB (SMD only, LCSC part numbers) and for PCBWay (every part incl. the through-hole ones, manufacturer part numbers).
Run after tools/make_shield_pcb.py route.

    python3 tools/make_shield_outputs.py             everything (needs kicad-cli on the PATH)
    python3 tools/make_shield_outputs.py --bom-only  only the BOMs and the assembly files, from the existing
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
JLC_BASIC_DIR = FAB / "jlcpcb_basic"
PCBWAY = FAB / "pcbway"

# LCSC part numbers for assembly at JLCPCB, checked on lcsc.com on 2026-11-08 (in stock that day). Check the stock
# again before ordering; a part that ran out needs a replacement with the same value and package.
LCSC = {
    "C1": "C8649",      # Kyocera AVX TAJC107K010RNJ, tantalum 100 uF 10 V, case C (6032) (not the 6.3 V TAJB107K006RNJ C16133: no headroom at 5 V, case B)
    "C2": "C15850",     # Samsung CL21A106KAYNNNE, 10 uF 25 V X5R 0805
    "C3": "C1591",      # Samsung CL10B104KB8NNNC, 100 nF 50 V X7R 0603 (first choice YAGEO CC0603KRX7R9BB104 C14663, out of stock 2026-11-08)
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
    "LED1": "C12624",   # Kento KT-0603G, green 0603 (first choice Everlight 19-217/GHC-YR1S2/3T C72043, out of stock 2026-11-08)
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
# soldered by hand at JLCPCB (not in its files): the Zero's two socket strips and the right-angle servo header.
# PCBWay fits them too (see MPN below).
HAND_SOLDERED = {"J1", "J3", "J4"}

# Manufacturer and part number of every fitted part, for PCBWay (it buys the parts itself, from any distributor).
# The SMD parts are the same as the LCSC ones above. J1/J3/J4 checked on digikey.com on 2026-11-08.
MPN = {
    "C1": ("Kyocera AVX", "TAJC107K010RNJ", "Tantalum capacitor 100 uF 10 V, case C 6032"),
    "C2": ("Samsung Electro-Mechanics", "CL21A106KAYNNNE", "Ceramic capacitor 10 uF 25 V X5R 0805"),
    "C3": ("Samsung Electro-Mechanics", "CL10B104KB8NNNC", "Ceramic capacitor 100 nF 50 V X7R 0603"),
    "C4": ("Samsung Electro-Mechanics", "CL10C101JB8NNNC", "Ceramic capacitor 100 pF 50 V C0G 0603"),
    "D1": ("JSCJ", "B5819W SL", "Schottky diode 40 V 1 A, SOD-123"),
    "F1": ("Ruilon", "SMD1206P050TF/13.2", "PTC resettable fuse 500 mA hold 13.2 V, 1206"),
    "FB1": ("Murata", "BLM18KG601SN1D", "Ferrite bead 600 R @ 100 MHz 1.3 A, 0603"),
    "J1": ("Sullins Connector Solutions", "PRPC003SBAN-M71RC", "Pin header 1x3 2.54 mm, right angle, through hole"),
    "J2": ("JST", "SM02B-SRSS-TB(LF)(SN)", "Connector JST SH 1.0 mm 2-pin, right angle, SMD"),
    "J3": ("Sullins Connector Solutions", "PPTC091LFBN-RC", "Female socket strip 1x9 2.54 mm, straight, through hole, 8.5 mm high"),
    "LED1": ("Kento", "KT-0603G", "LED green 0603"),
    "R1": ("Uni-Royal", "0603WAF1001T5E", "Resistor 1 k 1 % 0603"),
    "R2": ("Uni-Royal", "0603WAF1003T5E", "Resistor 100 k 1 % 0603"),
    "R5": ("Uni-Royal", "0603WAF1004T5E", "Resistor 1 M 1 % 0603"),
    "R6": ("Uni-Royal", "0402WGF330JTCE", "Resistor 33 R 5 % 0402"),
    "TVS1": ("Nexperia", "PESD5V0S1BA", "ESD protection diode 5 V, SOD-323"),
    "U1": ("Analog Devices / Maxim", "MAX98357AETE+T", "I2S class-D amplifier, TQFN-16 3x3"),
}
for _ref, _same in {"C5": "C4", "C6": "C3", "C7": "C3", "D2": "D1", "FB2": "FB1", "J4": "J3", "R3": "R1", "R4": "R2",
                    "R7": "R6", "R8": "R6"}.items():
    MPN[_ref] = MPN[_same]
THROUGH_HOLE = {"J1", "J3", "J4"}

# Rotation corrections for the JLCPCB CPL, in degrees counter-clockwise, added to KiCad's rotation. JLCPCB's part
# models are not always oriented like KiCad's footprints. Found in JLCPCB's placement preview on 2026-11-12 (pin 1 /
# plus side compared with the silkscreen) and checked there with these values: C1 had its plus side at the wrong
# end (180), U1 had pin 1 one corner off (rotated right by 90 = -90). D1, D2, LED1 and J2 were right.
JLC_ROTATION_FIX = {"C1": 180, "U1": -90}

# Second JLCPCB variant with "basic" parts where one exists (no loading fee of about 3 USD per extended part type),
# checked in the JLCPCB parts library on 2026-11-12: ref -> (LCSC, comment). Written to fab/jlcpcb_basic/; the
# default fab/jlcpcb/ keeps the parts above. The other extended parts (C1, F1, J2, TVS1, U1) have no basic equivalent.
JLC_BASIC = {
    "C3": ("C14663", "100n"),                  # YAGEO CC0603KRX7R9BB104, 100 nF 50 V X7R 0603
    "C6": ("C14663", "100n"),
    "C7": ("C14663", "100n"),
    "FB1": ("C14709", "ferrite 120R@100MHz"),  # Murata BLM18PG121SN1D, 120 R @ 100 MHz, 2 A, 0603
    "FB2": ("C14709", "ferrite 120R@100MHz"),
    "LED1": ("C2286", "red"),                  # Kento KT-0603R, red 0603 (no green 0603 among the basic parts)
}


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
    fitted = sorted(r for r in parts if not r.startswith(("MH", "TP", "JP")))
    missing = [r for r in fitted if r not in MPN]
    if missing:
        sys.exit(f"no manufacturer part number for {missing}: add them to MPN in {Path(__file__).name}")

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
    assembled = sorted(r for r in parts if r in LCSC)
    for folder, overrides in ((JLC, {}), (JLC_BASIC_DIR, JLC_BASIC)):
        folder.mkdir(exist_ok=True)
        groups = {}
        for ref in assembled:
            val, fp = parts[ref][0], parts[ref][1]
            lcsc, val = overrides.get(ref, (LCSC[ref], val))
            groups.setdefault((val, fp, lcsc), []).append(ref)
        with open(folder / "shield_bom_jlcpcb.csv", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["Comment", "Designator", "Footprint", "LCSC"])
            for (val, fp, lcsc), refs in sorted(groups.items(), key=lambda kv: kv[1][0]):
                w.writerow([val, ",".join(refs), fp, lcsc])
        with open(folder / "shield_cpl_jlcpcb.csv", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
            for ref in assembled:
                _v, _fp, x, y, rot, side = parts[ref]
                rot = (float(rot) + JLC_ROTATION_FIX.get(ref, 0)) % 360
                w.writerow([ref, f"{float(x):.4f}mm", f"{float(y):.4f}mm", "Top" if side == "top" else "Bottom",
                            f"{rot:g}"])

    # PCBWay turnkey assembly: every fitted part, SMD and through hole, with manufacturer part numbers
    PCBWAY.mkdir(exist_ok=True)
    groups = {}
    for ref in fitted:
        val, fp = parts[ref][0], parts[ref][1]
        groups.setdefault((MPN[ref], val, fp, LCSC.get(ref, ""), ref in THROUGH_HOLE), []).append(ref)
    with open(PCBWAY / "shield_bom_pcbway.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Item #", "Designator", "Qty", "Manufacturer", "Mfg Part #", "Description", "Value", "Package",
                    "Type", "LCSC Part # (alternative source)"])
        rows = sorted(groups.items(), key=lambda kv: kv[1][0])
        for i, ((mpn, val, fp, lcsc, tht), refs) in enumerate(rows, 1):
            w.writerow([i, ",".join(refs), len(refs), mpn[0], mpn[1], mpn[2], val, fp, "THT" if tht else "SMD", lcsc])
    with open(PCBWAY / "shield_centroid_pcbway.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Designator", "Mid X (mm)", "Mid Y (mm)", "Layer", "Rotation"])
        for ref in fitted:
            _v, _fp, x, y, rot, side = parts[ref]
            w.writerow([ref, f"{float(x):.4f}", f"{float(y):.4f}", "Top" if side == "top" else "Bottom",
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
