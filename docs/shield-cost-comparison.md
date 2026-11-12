# Shield: price comparison of the manufacturing options

Status: 2026-11-12, 5 assembled boards, top side only, delivery to the Czech Republic. Prices in USD. How to order
each option: `shield-pcb.md` "Ordering at JLCPCB" and "Ordering at PCBWay".

## The three options

| | PCBWay | JLCPCB, original parts | JLCPCB, basic parts |
|---|---|---|---|
| Files | `fab/pcbway/` | `fab/jlcpcb/` | `fab/jlcpcb_basic/` |
| PCB + assembly | 93.00 (PCB 5 + assembly 88) | 54.31 | about 45.0 |
| Parts | **not priced yet**: after PCBWay reviews the BOM (estimate 15-50, J1/J3/J4 included) | included (13.48) | included (about the same) |
| Extended-part loading fee | - | included: 8 part types x 3.09 = 24.72 | included: 5 x 3.09 = 15.45 |
| Shipping | 3.16 (DHL 33.16 minus a 30 USD discount) | DHL about 24, EuroPacket about 11 | DHL about 24, EuroPacket about 11 |
| J1, J3, J4 (servo header, the Zero's sockets) | fitted by PCBWay | buy and solder by hand (about 3-5) | buy and solder by hand (about 3-5) |
| **Total, estimate** | **about 111-146** | **about 82** with DHL, **about 69** with EuroPacket | **about 73** with DHL, **about 60** with EuroPacket |
| Who checks the files | a person at PCBWay, before production | the customer, in the placement preview | the customer, in the placement preview |
| Visible difference | green LED | green LED | **red** LED |

Import VAT (21 %) is added to every option when the parcel enters the EU, so it does not change the order.

## Where the numbers come from

- **PCBWay:** online SMT quote on 2026-11-12 (turnkey, 24 SMD + 3 THT parts). The parts are bought by PCBWay and
  priced only after its BOM review, so its total is still open. The estimate, from the prices on 2026-11-12, for all
  the parts of 5 boards: about 14 USD at LCSC prices (2.79 per board) and about 45 USD at DigiKey prices (9.05 per
  board). Most of it is U1 (LCSC 1.31, DigiKey 3.08 at 10 pieces), C1 (0.46 / 1.14) and the two socket strips J3/J4
  (DigiKey 0.59 each at 10 pieces). PCBWay buys from either kind of source and may add spare parts and minimum
  quantities, hence 15-50 USD.
- **JLCPCB, original parts:** quote in the JLCPCB order form on 2026-11-12 (Economic PCBA), with the parts and the
  loading fee for 8 extended part types (C1, C3/C6/C7, F1, FB1/FB2, J2, LED1, TVS1, U1).
- **JLCPCB, basic parts:** calculated, not quoted: the original quote minus 3 loading fees (C3/C6/C7, FB1/FB2 and
  LED1 become basic parts). The part prices differ by cents. Upload `fab/jlcpcb_basic/` to get the exact price.
- **JLCPCB shipping:** the rates to the Czech Republic shown in the JLCPCB quote form on 2026-11-12 for its default
  5-board PCB: DHL Express 23.52 USD (2-4 business days; also as DDP, duties paid), EuroPacket 11.00 (5-9 days),
  Global Standard Direct Line 7.39 (10-12 days, parcel value up to 150 USD). The assembled boards weigh about 233 g,
  so the real price can be a little higher; the order form shows it once the files are uploaded.
- **J1, J3, J4:** a rough estimate for a right-angle 1x3 header and two socket strips from a local shop.

## What differs between the two JLCPCB options

Only the BOM. The footprints, the positions and the Gerbers are the same, and the part values are not on the
silkscreen. The basic option has:

- C3/C6/C7: YAGEO CC0603KRX7R9BB104 (C14663) instead of Samsung CL10B104KB8NNNC: the same 100 nF X7R 0603.
- FB1/FB2: Murata BLM18PG121SN1D (C14709), 120 R at 100 MHz, 2 A, instead of BLM18KG601SN1D (600 R, 1.3 A). It
  filters the speaker lines a little less; the design allows even 0 R there.
- LED1: red Kento KT-0603R (C2286) instead of the green KT-0603G; no green 0603 LED is a basic part. About 3 mA
  through the 1 k resistor. Check its polarity in the placement preview.

C1, F1, J2, TVS1 and U1 have no basic equivalent.

## Before ordering

- Check the stock of every part on the day of the order.
- JLCPCB: confirm every part in the placement preview (C1 and U1 rotations are already fixed in the files).
- PCBWay: wait for the BOM review and the price of the parts.
