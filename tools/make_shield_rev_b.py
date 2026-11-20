"""Shield board rev B: the silkscreen of rev A (tag hw-shield-revA, the files ordered at JLCPCB on 2026-11-13) made
for the person holding the board, and the revision in the files. Nothing electrical changes: no part, pad, track or
zone moves, so the BOM and the placement files stay as they were.

What changes:
  - the reference labels go (R1, C3, U1, ...), except J3 and J4 at the Zero's sockets (the Zero's orientation);
  - the outlines of the small parts go from the silkscreen to the fab layer (F.Fab), so the assembly drawing keeps
    them; J2, J3, J4 and JP1 keep theirs, J1's outline (it hangs over the edge) goes;
  - new text, all 1.0 mm high with a 0.15 mm stroke (JLCPCB's advice for silkscreen): S V G below the pads of the servo header
    J1, "+" at C1, "CB SND" and "rev B" in the right margin; a dot at pin 1 of U1;
  - title block of the board: revision B, date, title.

Run with KiCad's own Python (it has the pcbnew module), on the rev A board:

    "C:\\Program Files\\KiCad\\bin\\python.exe" tools/make_shield_rev_b.py

It refuses to run twice (the title block says B afterwards). The board is saved by this KiCad's pcbnew, so the file
format is the one of that version (rev A was written by KiCad 7). Then: tools/make_shield_outputs.py for the
manufacturing files. Decided 2026-11-14, see docs/shield-pcb.md ("Revisions").
"""
import sys
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parent.parent
PCB = ROOT / "hardware" / "shield" / "shield.kicad_pcb"
MM = 1e6

REV = "B"
DATE = "2026-11-14"
LETTER_Y = 105.8                           # S V G: below the J1 pads, not under its plastic body (rev B note of 2026-11-20)
KEEP_REF = {"J3", "J4"}                      # reference labels that stay
KEEP_OUTLINE = {"J2", "J3", "J4", "JP1"}     # outlines that stay on the silkscreen
TEXT_H = 1.0                                 # mm
STROKE = 0.15                                # mm


def main():
    board = pcbnew.LoadBoard(str(PCB))
    tb = board.GetTitleBlock()
    if tb.GetRevision() == REV:
        sys.exit(f"{PCB.name} is already rev {REV}")
    silk = board.GetLayerID("F.SilkS")
    fab = board.GetLayerID("F.Fab")
    edge = board.GetBoardEdgesBoundingBox()

    def vec(x, y):
        return pcbnew.VECTOR2I(int(round(x * MM)), int(round(y * MM)))

    # reference labels
    for fp in board.GetFootprints():
        ref = fp.Reference()
        if fp.GetReference() not in KEEP_REF and ref.GetLayer() == silk:
            ref.SetVisible(False)
        elif fp.GetReference() in KEEP_REF:
            ref.SetTextSize(vec(TEXT_H, TEXT_H))
            ref.SetTextThickness(int(STROKE * MM))

    # outlines of the small parts to the fab layer
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        if ref in KEEP_OUTLINE or ref.startswith(("MH", "TP")):
            continue
        for g in list(fp.GraphicalItems()):
            if g.GetLayer() == silk and isinstance(g, pcbnew.PCB_SHAPE):
                g.SetLayer(fab)

    def text(s, x, y, size=TEXT_H, ang=0, stroke=STROKE):
        t = pcbnew.PCB_TEXT(board)
        t.SetText(s)
        t.SetLayer(silk)
        t.SetTextSize(vec(size, size))
        t.SetTextThickness(int(stroke * MM))
        t.SetPosition(vec(x, y))
        t.SetTextAngleDegrees(ang)
        board.Add(t)

    def dot(x, y, d=0.5):
        g = pcbnew.PCB_SHAPE(board)
        g.SetShape(pcbnew.SHAPE_T_CIRCLE)
        g.SetLayer(silk)
        g.SetFilled(True)
        g.SetStart(vec(x, y))
        g.SetEnd(vec(x + d / 2, y))
        g.SetWidth(0)
        board.Add(g)

    # servo header J1: the letters below the pad row (J1's plastic body covers y 100.05..102.71, so they must not sit there;
    # free strip between the pads, ending at y 105.0, and R1 / F1 from y 106.6); pins 2.54 mm apart, the first at x 111.96
    j1 = board.FindFootprintByReference("J1")
    for pad, letter in zip(sorted(j1.Pads(), key=lambda p: p.GetPosition().x), "SVG"):
        text(letter, pad.GetPosition().x / MM, LETTER_Y)
    # J1's own outline hangs over the board edge: to the fab layer
    for g in list(j1.GraphicalItems()):
        if g.GetLayer() == silk and isinstance(g, pcbnew.PCB_SHAPE):
            g.SetLayer(fab)
    # C1: the plus, beside its plus pad (pad 1)
    text("+", 124.6, 119.9)
    # name and revision in the right margin
    text("CB SND", 126.3, 108.4, ang=90)
    text("rev " + REV, 126.3, 122.8, ang=90)
    # U1 pin 1
    dot(109.5, 121.9)

    tb.SetTitle("Sound shield for the CyberBrick receiver")
    tb.SetRevision(REV)
    tb.SetDate(DATE)
    tb.SetComment(0, "Engine sound module: ESP32-S3-Zero + MAX98357A, throttle from the servo port PWM2")
    tb.SetComment(1, "Rev B: silkscreen only, electrically the same as rev A (tag hw-shield-revA)")
    pcbnew.SaveBoard(str(PCB), board)
    print(f"rev {REV} written to {PCB}")


if __name__ == "__main__":
    main()
