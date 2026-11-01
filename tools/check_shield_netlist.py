"""Compare the connectivity KiCad extracts from the schematic with tools/shield_netlist.py."""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import shield_netlist as N  # noqa: E402

sch = Path(__file__).resolve().parent.parent / "hardware" / "shield" / "shield.kicad_sch"
with tempfile.TemporaryDirectory() as d:
    out = Path(d) / "n.net"
    subprocess.run(["kicad-cli", "sch", "export", "netlist", "--format", "kicadsexpr", "-o", str(out), str(sch)], check=True)
    text = out.read_text()
text = text[text.index("(nets"):]
got = {}
for blk in text.split("(net (code")[1:]:
    name = re.search(r'\(name "([^"]*)"\)', blk).group(1).lstrip("/")
    nodes = sorted(f"{r}.{p}" for r, p in re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)', blk) if not r.startswith("#"))
    if not name.startswith("unconnected") and nodes:
        got[name] = nodes
want = N.nets()
bad = 0
for k in sorted(set(want) | set(got)):
    if want.get(k) != got.get(k):
        bad += 1
        print("DIFF", k, "\n  want", want.get(k), "\n  got ", got.get(k))
print(f"{len(want)} nets intended, {len(got)} found, {bad} differences")
sys.exit(1 if bad else 0)
