# Shield 3D check

Board shield.kicad_pcb, outline 29.10 x 30.10 mm. Sizes are boxes around the STEP shapes (mm, z = 0 at the board top).

## 1. Models on their pads (xy)

| Part | Model | Model box x | Model box y | Pads x | Pads y | Result |
|---|---|---|---|---|---|---|
| C1 | CP_EIA-6032-28_Kemet-C.wrl | 124.90..128.10 | 112.75..118.75 | 125.33..127.67 | 112.25..119.25 | ok |
| C2 | C_0805_2012Metric.wrl | 111.20..112.45 | 114.67..116.67 | 111.11..112.56 | 114.22..117.12 | ok |
| C3 | C_0603_1608Metric.wrl | 114.23..115.83 | 118.40..119.20 | 113.81..116.25 | 118.33..119.28 | ok |
| C4 | C_0603_1608Metric.wrl | 115.59..117.19 | 120.25..121.05 | 115.17..117.61 | 120.17..121.12 | ok |
| C5 | C_0603_1608Metric.wrl | 118.57..119.37 | 120.93..122.53 | 118.50..119.44 | 120.50..122.95 | ok |
| C6 | C_0603_1608Metric.wrl | 116.99..117.79 | 114.83..116.43 | 116.92..117.86 | 114.41..116.86 | ok |
| C7 | C_0603_1608Metric.wrl | 118.83..119.63 | 114.89..116.49 | 118.75..119.70 | 114.47..116.92 | ok |
| D1 | D_SOD-123.wrl | 116.36..117.96 | 109.37..113.17 | 116.56..117.76 | 109.17..113.37 | ok |
| D2 | D_SOD-123.wrl | 109.46..113.26 | 110.77..112.37 | 109.26..113.46 | 110.97..112.17 | ok |
| F1 | Fuse_1206_3216Metric.wrl | 114.18..117.38 | 106.63..108.23 | 113.75..117.81 | 106.56..108.31 | ok |
| FB1 | L_0603_1608Metric.wrl | 114.80..116.40 | 122.07..122.87 | 114.38..116.83 | 122.00..122.94 | ok |
| FB2 | L_0603_1608Metric.wrl | 117.55..119.15 | 118.05..118.85 | 117.12..119.58 | 117.97..118.92 | ok |
| J1 | PinHeader_1x03_P2.54mm_Horizontal.wrl | 110.69..118.31 | 94.11..104.47 | 111.11..117.89 | 103.30..105.00 | ok |
| J2 | JST_SH_SM02B-SRSS-TB_1x02-1MP_P1.00mm_Horizontal.wrl | 115.00..119.00 | 124.38..129.32 | 114.60..119.40 | 124.08..129.62 | ok |
| J3 | PinSocket_1x09_P2.54mm_Vertical.wrl | 105.61..108.15 | 103.57..126.43 | 106.03..107.73 | 103.99..126.01 | ok |
| J4 | PinSocket_1x09_P2.54mm_Vertical.wrl | 120.85..123.39 | 103.57..126.43 | 121.27..122.97 | 103.99..126.01 | ok |
| LED1 | LED_0603_1608Metric.wrl | 102.35..103.15 | 114.25..115.85 | 102.28..103.22 | 113.83..116.28 | ok |
| R1 | R_0603_1608Metric.wrl | 110.75..112.35 | 106.67..107.47 | 110.33..112.78 | 106.59..107.55 | ok |
| R2 | R_0603_1608Metric.wrl | 109.33..110.13 | 113.77..115.37 | 109.25..110.20 | 113.34..115.80 | ok |
| R3 | R_0603_1608Metric.wrl | 102.35..103.15 | 111.05..112.65 | 102.28..103.22 | 110.62..113.08 | ok |
| R4 | R_0603_1608Metric.wrl | 107.17..108.77 | 127.88..128.68 | 106.75..109.19 | 127.81..128.75 | ok |
| R5 | R_0603_1608Metric.wrl | 111.10..112.70 | 125.53..126.33 | 110.67..113.12 | 125.45..126.41 | ok |
| R6 | R_0402_1005Metric.wrl | 113.40..113.90 | 115.95..116.95 | 113.33..113.97 | 115.67..117.23 | ok |
| R7 | R_0402_1005Metric.wrl | 109.22..109.72 | 122.73..123.73 | 109.15..109.79 | 122.45..124.01 | ok |
| R8 | R_0402_1005Metric.wrl | 109.23..109.73 | 124.95..125.95 | 109.16..109.80 | 124.67..126.23 | ok |
| TVS1 | D_SOD-323.wrl | 110.27..112.77 | 108.48..109.73 | 110.17..112.87 | 108.89..109.33 | ok |
| U1 | TQFN-16-1EP_3x3mm_P0.5mm_EP1.6x1.6mm.step | 109.59..112.59 | 118.34..121.34 | 109.24..112.94 | 117.99..121.69 | ok |

Models that do not cover their pads: none.

## 2. Heights above the board top

| Part | Model | Height (mm) | Lowest point (mm) |
|---|---|---|---|
| J4 | PinSocket_1x09_P2.54mm_Vertical.wrl | 8.50 | -3.10 |
| J3 | PinSocket_1x09_P2.54mm_Vertical.wrl | 8.50 | -3.10 |
| J2 | JST_SH_SM02B-SRSS-TB_1x02-1MP_P1.00mm_Horizontal.wrl | 2.96 | 0.00 |
| C1 | CP_EIA-6032-28_Kemet-C.wrl | 2.80 | -0.00 |
| J1 | PinHeader_1x03_P2.54mm_Horizontal.wrl | 2.54 | -3.00 |
| D1 | D_SOD-123.wrl | 1.26 | -0.00 |
| D2 | D_SOD-123.wrl | 1.26 | -0.00 |
| C2 | C_0805_2012Metric.wrl | 1.25 | 0.00 |

## 3. Parts that overlap in 3D

None (parts above the board top, overlap larger than 0.05 mm in all three directions).

## 4. Parts outside the board outline

- J1: sticks out by 5.84 mm (meant to: the cable plug)

## 5. Room under the ESP32-S3-Zero

The Zero covers x 104.65..124.35, y 103.25..126.75 mm. Its underside is the socket height plus the plastic of its own pin header (2.5 mm), if the header sits on the socket.

Parts under (or partly under) the Zero, tallest first: J2 2.96, J1 2.54, D1 1.26, D2 1.26, C2 1.25, TVS1 1.11, C3 0.80, C4 0.80, C5 0.80, C6 0.80, C7 0.80, FB1 0.80, FB2 0.80, U1 0.78, F1 0.55, R1 0.45, R2 0.45, R5 0.45, R6 0.35, R7 0.35, R8 0.35.

| Socket strip | Zero underside (mm) | Tallest part under it | Room left (mm) |
|---|---|---|---|
| 8.5 mm | 11.00 | 2.96 (J2) | 8.04 |
| 3.5 mm (low strip, short pins) | 6.00 | 2.96 (J2) | 3.04 |

The 3.5 mm row assumes pins short enough for the plastic to seat on the strip; with the Zero's own pins of about 6 mm the underside stays at about 8.5 mm.

