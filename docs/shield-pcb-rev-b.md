# Shield PCB, next revision (rev B and later): planned, not up to date

This document collects the **future** state of the shield board: rev B (prepared, not ordered) and the ideas for the revisions after it.
None of it is built. The board that exists is **rev A**, described in `shield-pcb.md` (scope, schematic, ordering, first power-up,
decisions). Rev B and the ideas below can be out of date against rev A and against the firmware; check them before relying on them.

## Rev B (prepared 2026-11-14, not ordered)

Made by `tools/make_shield_rev_b.py` from the rev A board; nothing electrical changes (no part, pad, track or zone
moves). Checked: the BOM, the placement files (`fab/jlcpcb*`, `fab/pcbway`, `shield_positions.csv`) come out the same
as for rev A, the copper, mask, paste and drill gerbers are the same as rev A's plotted by the same KiCad, KiCad's DRC
finds 0 violations (rev A: 53 silkscreen warnings) and 0 unconnected items. The silkscreen:

- **Only what helps the person holding the board**: S V G above the servo header J1 (the cable can be put on the
  wrong way round, which puts the supply on the signal pin), J3 and J4 at the Zero's sockets (square pad = pin 1, for
  the Zero's orientation), a plus at C1 (tantalum), a dot at pin 1 of U1 (visible only without the Zero), "CB SND" and
  "rev B" in the right margin, and the outlines of J2, J3, J4 and JP1.
- **Gone**: the reference labels (R1, C3, ...), the outlines of the small parts (they moved to the fab layer, so the
  assembly drawing keeps them) and the outline of J1, which hung over the board edge. The references stay in the
  schematic, the BOM and the placement files; JLCPCB places the parts from those, not from the silkscreen.
- **Size**: every text is 1.0 mm high with a 0.15 mm stroke (JLCPCB's advice, 1 mm and 0.15 mm; to be checked in their
  rules before the order). The labels of rev A were 0.8 mm / 0.12 mm.
- **Files**: the title block says rev B (board and schematic) and the gerbers carry `Revision: B`. The board is saved
  by KiCad 10 (rev A: KiCad 7), so it opens in KiCad 10 or newer. `tools/make_shield_pcb.py` still generates the
  rev A board; to rebuild rev B run it, then `tools/make_shield_rev_b.py`, then `tools/make_shield_outputs.py`
  (with KiCad's `kicad-cli` on the PATH). The interactive BOM comes from `tools/make_shield_ibom.py`.
- **Parts, decided 2026-11-14: if rev B is ordered, try to fit the ideal parts**, that is the files of the full BOM
  in `fab/jlcpcb/` (green LED C12624, Samsung 100 nF C1591, ferrites 600 R C85833), not the basic-parts variant of
  rev A; the differences are in `shield-bom-compare.md`. Costs about 9 USD more in loading fees; check the stock of
  those parts at LCSC again before ordering (the first choices were out of stock on 2026-11-08), and the placement
  preview as for rev A. It is a try, not a must: if the rev A parts prove fine at the first power-up (red LED, 120 R ferrites), or the extra
  cost is not worth it, the basic-parts variant stays. If one ideal part is not available, fall back to its basic
  equivalent and record it.
- **Done 2026-11-20, from a note on the first boards: the S V G labels of rev B were covered by the connector.** `make_shield_rev_b.py` puts them at y 101.9 mm, which is under the black plastic body of the right-angle header J1 (it lies on the board from y 100.05 to 102.71), so once J1 is soldered, and with the cable plugged in, the letters cannot be seen. Fixed in `make_shield_rev_b.py` (`LETTER_Y`), in the board and in the gerbers of `fab/` (regenerated, DRC 0 violations, 0 unconnected; only the silkscreen layer changed): the letters are now in the free strip between the pad row of J1 (y 104.15, pads end at about 105.0) and R1/F1 (from y 106.6), for example y 105.8 mm with 1.0 mm text, still above the three pins' x positions (111.96, 114.50, 117.04); check the DRC and that the text does not touch the pads or R1/F1. Rev A has no S V G letters at all (only the outline of J1).
- Before ordering: look at the gerber preview once (JLCPCB's or KiCad's viewer) and check the text sizes against
  JLCPCB's current silkscreen rules; then the tag `hw-shield-revB`.

## Next revision (after rev B)

Collected for the version after rev B (the silkscreen of rev B is done, see "Revisions" in `shield-pcb.md`):

- Whatever the first assembled boards (rev A) show at power-up.
- **Optional, only if two revisions need different firmware**: a board ID the firmware can read, for example a
  resistor divider on one of the spare pins IO10..IO12 read by the ADC. Not needed while the pins stay the same.

## Ideas and open points for a later revision

- **To consider (2026-11-22, from the photo of the first working board): the servo connector deeper under the Zero.** On the rev A board the right-angle header J1 is at the USB-C end of the Zero, and from above the servo plug looks as if it stood against the USB-C connector. It does not get in its way: the servo plug sits on the shield (about 3 mm tall) and the Zero is 8.5 mm above the board on its sockets, with the USB-C connector higher still (the lower edge of a USB-C plug about 10 mm above the board), so the two plugs are on **different levels**. The way it is now, with the servo plug outside the board on the long pins of J1 that stick out of the edge, is the **intended variant** (the board stays at the size of the receiver shield and the plug does not need any room among the parts); the idea below is an alternative to it, not a repair. It makes it possible to move J1 **in the same plane, deeper into the board, under the Zero**: the servo plug then sits under the Zero's overhang, the USB-C cable goes in above it, and nothing gets in the way. Open points for a revision: the input protection (F1, R1, TVS1, D1, D2) sits in the strip before J1 at y 7 to 12 mm and would have to move, the plug needs about 8 mm along the row and a free path from the board edge to the header, the cable must still run out under the Zero to the receiver's S4, and the S V G labels (rev B) move with it: they go **to the edge of the board**, at the start of the plug's path, not beside the pins. With the plug pushed in they are hidden, but they tell **what the correct orientation of the cable is** before it is pushed in (S, V, G from left to right, the S wire, the one with the colour mark, on the S side; the square pad of the S pin is the first); the colour mark on the S wire stays. Other ways considered and not preferred: the connector to the side (the strips beside the Zero are about 5.5 mm and hold the mounting holes, LED1 and C1) or vertically up (it would still stand in front of the USB-C opening, and it adds height). Not decided; consider it for rev C or a rev B that is not ordered yet (rev B is only the silkscreen so far).

- **Direction for the servo connector in a later revision (2026-11-22, not drawn yet): the holes of J1 moved inward.** The labels S V G stay at the edge of the board as they are (the plug seats about 5 mm behind them, so they are not covered). Only the **holes of J1** move: so far inward that the **whole plug is inside the outline of the board**, with the row of pins about **19 mm from the edge** (first thought 15 mm, the owner prefers 19; the long pins run towards the edge, the plug about 9 mm long covers them, so it ends about 8.5 mm behind the labels), and only the cable passes the edge. The plug is about 8.5 mm wide and the room between the socket strips of the Zero is 12.7 mm, so it goes between them; it is 3 mm tall under the Zero, which is 8.5 mm above the board. The price is the room: the plug covers the strip from y 8.5 to 17.5 mm and the body of J1 is at y 17.7 to 20.3 mm, so everything that sits there now moves: F1, R1, TVS1, D1, D2, C2, C6, C7, R6 and **the amplifier U1** (y 18.4 to 21.3 mm, x 9.7 to 12.6 mm, which the body of J1 would overlap). The input section and the amplifier area are laid out again; the S V G labels (rev B) keep their place. A sketch (not a KiCad change): `work/j1_deeper.png` on the owner's computer, not in the repository.

- **Area test of that direction (2026-11-22): with the board and the parts as they are, it does not fit.** `tools/trial_place_j1.py` (data from `tools/extract_board_for_trial.py`) places the 22 movable parts again by simulated annealing, inside the outline, outside the sockets, the mounting holes, the fixed parts and a keepout for the plug (from the edge of the board to the body of J1, about 8.7 mm wide). It is a courtyard test only, without routing; calibrated with the real board (0 overlaps at the present J1 position, and the annealing finds 0 overlaps there too). Result for the row of J1 pins at 6 mm: 4 overlaps left; 8 and 10 mm: 9; 12 mm: 15; **19 mm: 23 to 26**. The reason: the keepout of the plug takes a strip 8.7 mm wide out of the 12.7 mm between the socket rows, and the 22 parts need about 141 mm² of courtyards. To make a deeper J1 possible something has to give: parts on the bottom side (JLCPCB can fit both sides, for a fee), smaller passives (0402) and fewer optional parts (the jumpers JP1, JP2 with R4, R5 and the three 33 Ohm resistors R6 to R8 can be dropped or made links, about 40 mm²), a bigger board (it would no longer be the size of the receiver shield), or a shallower J1. 19 mm would need all of that and the whole amplifier area laid out again.

- **Marking the USB side of the Zero (2026-11-22, an idea for the silkscreen):** instead of J3 and J4 (the names of the socket strips, which tell nothing to the user) write **USB** on the board at the end where the Zero's USB-C connector is, so that the Zero is fitted the right way round without counting pins. The square pad of pin 1 stays. Not done on rev B yet.

- **Open (noted 2026-11-15): fitting J1/J3/J4 at JLCPCB for a large series.** Not decided, only looked at. JLCPCB offers through-hole assembly (wave/selective or hand soldering); the fee figures found are second-hand and from 2024-25 (roughly 3.50 USD fixed plus about 0.02 USD per joint), so take the real number from the order quote. LCSC has 1x9, 8.5 mm female strips: C2897372 (HCTL PM254-1-09-Z-8.5, about 8000 in stock, looks like the best match), C22373895 (Hong Cheng, gold), C7509520 (CONNFLY DS1023-1x9SF11, gold), C225506 (CJT A2541HWV-9P); price and pin length not checked. Risk: with the Zero plugged in the two strips are held parallel, the service has no Zero to do that, so they may stand a little crooked; try a few boards first. The small run (5 boards) keeps the hand-cut GME strips. Other strips looked at and not chosen: Preci-Dip 801-87-007-10-001101 (7 positions, 7 mm, precision contacts) and an eBay lot of 24 PPTC091LFBN-RC from Canada (about 815 CZK with shipping).
