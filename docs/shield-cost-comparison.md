# Shield: price comparison of the manufacturing options

**Chosen on 2026-11-12: JLCPCB with basic parts** (`shield-pcb.md` "Decided").

Status: 2026-11-12 (import charges added 2026-11-13), 5 assembled boards, top side only, delivery to the Czech Republic. Prices in USD. How to order
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

Import charges (VAT, customs duty, clearance fees) are added to every option when the parcel enters the EU; see
"Import charges" below.

## Import charges

Since the EU customs reform (1 July 2026; JLCPCB "EU Tax Reform July 2026 - Client FAQ", read on 2026-11-13), a
private (B2C) parcel up to 150 EUR pays, with or without DDP:

- **VAT 21 %** on the goods and the shipping.
- **Temporary customs duty: 3 EUR per HS code.** The boards are most likely one HS code, so 3 EUR.
- **EU handling fee (UHF): 2 EUR** per customs declaration line, since 1 November 2026.
- **Carrier's duty & tax disbursement fee** when the carrier advances the duty and VAT: DHL in the Czech Republic
  2 % of the advanced amount, **at least 400 CZK** (UPS at least 416 CZK, FedEx at least 364 CZK).

**DDP shipping** (DHL Express (DDP) or FedEx Express (DDP) in the JLCPCB order form): JLCPCB calculates, collects
and pays all of this with the order, the disbursement fee included (possibly at a discount from its carrier
contracts), so nothing is paid at the door. Without DDP the carrier collects it on delivery. With Global Standard
Direct Line, JLCPCB collects only the VAT in advance (IOSS); the 3 EUR duty is paid on import. Whether the Czech
post charges its own fee for EuroPacket is not known.

**Recommended: DHL Express (DDP):** fastest, everything paid up front, no surprise at the door. EuroPacket is about
33 USD cheaper, but slower and with the duty paid on delivery.

## Grand total

Everything paid for 5 finished boards, with the import charges above. J1/J3/J4 for the JLCPCB options are bought
locally with VAT already in the price. Not included: what all options need anyway (the ESP32-S3-Zero, the servo
cable and the speaker, `shield-pcb.md` "Needed besides the board"). Approximate rates: 5 EUR (duty + UHF) = about
6 USD, 400 CZK = about 18 USD.

| | Order | Shipping | Parts not in the order | VAT 21 % | Duty + UHF | Clearance fee | **Grand total** | Per board |
|---|---|---|---|---|---|---|---|---|
| PCBWay, DHL (parts 15-50) | 108.00-143.00 | 3.16 | - | 23.34-30.69 | about 6 | about 18 | **about 159-201** | 32-40 |
| JLCPCB original, DHL DDP | 54.31 | 23.52 | 3-5 | 16.34 | about 6 | up to about 18 | **about 121-123** | about 24 |
| JLCPCB original, EuroPacket | 54.31 | 11.00 | 3-5 | 13.72 | about 6 | not known | **about 88-90** | about 18 |
| JLCPCB basic, DHL DDP | about 45.04 | 23.52 | 3-5 | 14.40 | about 6 | up to about 18 | **about 110-112** | about 22 |
| JLCPCB basic, EuroPacket | about 45.04 | 11.00 | 3-5 | 11.77 | about 6 | not known | **about 77-79** | about 16 |

The PCBWay order is the PCB and assembly (93.00) plus its parts estimate; the JLCPCB order already holds the parts.
The DDP clearance fee is the carrier's minimum and may be lower through JLCPCB. The cheapest option (JLCPCB basic
parts, EuroPacket) costs about half of PCBWay but needs the three through-hole parts soldered by hand and a red
power LED.

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
