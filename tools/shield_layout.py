"""Layout of the sound shield (iteration 2), shared by the 2D mock and the 3D model.

The board has exactly the outline of the ESP32-S3-Zero (18 x 23.5 mm) and sits under it.
The Zero is plugged into two 9-pin female headers on the long edges; everything else lives in the
12.7 mm gap between the two header strips (top side) or on the bottom side (test pads).

Coordinates: mm, origin at the top-left corner of the board seen from above, x to the right,
y downwards. The USB-C port of the Zero is at the top (y = 0). Illustrative placement, not routed:
footprints and heights are typical values, to be replaced by real ones when the schematic is drawn.
"""

BOARD_W, BOARD_H, BOARD_T = 18.0, 23.5, 1.6
HDR_X = (1.38, 16.62)          # centres of the two header strips (15.24 mm = 0.6 in apart)
HDR_H = 8.5                    # female header body height
PIN_Y0, PIN_PITCH = 1.59, 2.54
PIN_Y = [round(PIN_Y0 + PIN_PITCH * i, 2) for i in range(9)]
GAP_X = (HDR_X[0] + 1.27, HDR_X[1] - 1.27)      # free space between the strips: 2.65 .. 15.35

LEFT_PINS = ["5V", "GND", "3V3", "IO1", "IO2", "IO3", "IO4", "IO5", "IO6"]
RIGHT_PINS = ["TX", "RX", "IO13", "IO12", "IO11", "IO10", "IO9", "IO8", "IO7"]

J1_X = (6.46, 9.0, 11.54)      # S, V, G
J1_Y = 1.27
IO1_Y, IO4_Y, IO5_Y, IO6_Y = PIN_Y[3], PIN_Y[6], PIN_Y[7], PIN_Y[8]

# kind: how it is drawn. (x, y) centre, (w, h) footprint box including pads, z = height above the board.
PARTS = [
    dict(ref="J1", kind="hdr_ra", x=9.0, y=1.27, w=7.62, h=2.54, z=2.54,
         name="Input header (S, V, G)",
         desc="3-pin right-angle header at the top edge; the servo cable from PWM2 plugs in from outside. S = throttle copy, V = 5 V, G = ground."),
    dict(ref="R1", kind="chip_r", x=6.46, y=4.7, w=1.5, h=2.8, z=0.5, body=(1.25, 2.0),
         name="Resistor 1 kOhm", desc="Series resistor between the throttle signal and GPIO1."),
    dict(ref="F1", kind="chip_f", x=9.0, y=5.0, w=2.0, h=4.1, z=1.0, body=(1.6, 3.2),
         name="Resettable fuse (PTC)", desc="1206 PTC, about 0.5 A hold. Limits the current drawn from the servo port (the module takes about 0.1 A)."),
    dict(ref="D1", kind="diode", x=9.0, y=9.4, w=1.8, h=4.0, z=1.1, band="bottom",
         name="Reverse-polarity diode", desc="Schottky diode (SOD-123) protecting the module if the servo cable is plugged in the wrong way round."),
    dict(ref="D2", kind="diode", x=4.0, y=5.3, w=1.8, h=4.0, z=1.1, band="top",
         name="5 V OR-ing diode", desc="Keeps USB 5 V and servo-port 5 V from fighting, so both can be connected at the same time."),
    dict(ref="R2", kind="chip_r", x=3.6, y=11.6, w=1.5, h=2.8, z=0.5, body=(1.25, 2.0),
         name="Resistor 100 kOhm", desc="Pull-down on GPIO1, so the input has a defined level when the cable is unplugged."),
    dict(ref="C1", kind="cap_t", x=13.5, y=13.6, w=3.4, h=7.8, z=2.8, body=(3.2, 6.0),
         name="Bulk capacitor 100 uF", desc="Polymer/tantalum 6032 case. Absorbs the current peaks of loud passages so the 5 V rail does not sag."),
    dict(ref="C2", kind="chip_c", x=5.2, y=16.6, w=2.7, h=1.5, z=0.9, body=(2.0, 1.25),
         name="Decoupling 10 uF", desc="Ceramic 0805 close to the amplifier supply pin."),
    dict(ref="C3", kind="chip_c", x=9.0, y=16.6, w=2.7, h=1.5, z=0.6, body=(2.0, 1.25),
         name="Decoupling 100 nF", desc="Ceramic 0805 close to the amplifier supply pin."),
    dict(ref="U1", kind="qfn", x=6.0, y=19.8, w=4.2, h=4.2, z=0.8, body=(3.0, 3.0),
         name="MAX98357A amplifier", desc="I2S class-D amplifier, TQFN-16 3 x 3 mm. Receives BCLK, LRC and DIN from the ESP32 and drives the speaker directly."),
    dict(ref="J2", kind="jst_side", x=12.2, y=21.35, w=4.0, h=4.3, z=3.9,
         name="Speaker connector (JST SH 1.0)", desc="JST SH 1.0 mm 2-pin side-entry connector at the bottom edge, the same type as the CyberBrick motor ports (M1/M2) and button ports. The speaker cable (for example the 2-pin SH cable of a button module) plugs in from outside."),
    # parts in the margin around the Zero (the board is larger than the Zero), so they stay visible from above
    dict(ref="LED1", kind="led", x=-4.1, y=7.94, w=2.2, h=1.2, z=0.6, margin=True,
         name="Power LED", desc="Lights when the servo-port 5 V is present (taken after the reverse-polarity diode D1), so you can see that the cable and the receiver are fine. Hardware only, no firmware needed. Placed beside the Zero because the Zero would hide it."),
    dict(ref="R3", kind="chip_r", x=-1.4, y=7.94, w=2.8, h=1.5, z=0.5, body=(2.0, 1.25), margin=True,
         name="LED resistor 1 kOhm", desc="Series resistor of the power LED (about 3 mA)."),
    dict(ref="J3", kind="hdr_v", x=20.5, y=13.02, w=2.54, h=10.16, z=2.5, margin=True,
         pins=[[20.5, 9.21], [20.5, 11.75], [20.5, 14.29], [20.5, 16.83]], pin_names=["IO12", "IO11", "IO10", "GND"],
         name="Spare GPIO header", desc="1x4 pin header with three free GPIOs (IO12, IO11, IO10) and ground, for later inputs, for example a switch for an engine-stop sound."),
]

# nets: pts are board coordinates; layer 'top' or 'bot'
NETS = [
    dict(net="S", color="#ffb347", pts=[[6.46, 1.27], [6.46, 3.8]]),
    dict(net="S", color="#ffb347", pts=[[6.46, 5.6], [6.46, IO1_Y], [HDR_X[0], IO1_Y]]),
    dict(net="V", color="#ff7a6b", pts=[[9.0, 1.27], [9.0, 3.35]]),
    dict(net="V", color="#ff7a6b", pts=[[9.0, 6.65], [9.0, 7.9]]),
    # 5 V rail after D1: to the Zero via D2 (hop under the S trace), to the bulk cap and to the amplifier
    dict(net="5V", color="#ff7a6b", pts=[[9.0, 10.9], [13.5, 10.9], [13.5, 10.6]]),
    dict(net="5V", color="#ff7a6b", pts=[[9.0, 10.9], [9.0, 12.2], [5.0, 12.2], [5.0, 10.2]]),
    dict(net="5V", color="#ff7a6b", layer="bot", pts=[[5.0, 10.2], [5.0, 8.2]]),
    dict(net="5V", color="#ff7a6b", pts=[[5.0, 8.2], [4.0, 8.2], [4.0, 6.9]]),
    dict(net="5V", color="#ff7a6b", pts=[[4.0, 3.7], [4.0, PIN_Y[0]], [HDR_X[0], PIN_Y[0]]]),
    dict(net="5V", color="#ff7a6b", pts=[[11.0, 10.9], [11.0, 15.3], [7.15, 15.3], [7.15, 18.05]]),
    dict(net="5V", color="#ff7a6b", pts=[[6.2, 16.6], [7.15, 16.6]]),
    dict(net="5V", color="#ff7a6b", pts=[[7.15, 16.6], [8.0, 16.6]]),
    # I2S
    dict(net="DIN", color="#6ec1ff", pts=[[HDR_X[0], IO4_Y], [3.4, IO4_Y], [3.4, 19.3], [4.25, 19.3]]),
    dict(net="BCLK", color="#6ec1ff", pts=[[HDR_X[0], IO5_Y], [3.0, IO5_Y], [3.0, 19.8], [4.25, 19.8]]),
    dict(net="LRC", color="#6ec1ff", pts=[[HDR_X[0], IO6_Y], [3.6, IO6_Y], [3.6, 20.3], [4.25, 20.3]]),
    # speaker
    dict(net="SPK+", color="#ececec", pts=[[7.75, 19.7], [11.7, 19.7]]),
    dict(net="SPK-", color="#ececec", pts=[[7.75, 20.3], [12.7, 20.3], [12.7, 19.7]]),
    # pull-down tap
    dict(net="S", color="#ffb347", pts=[[3.6, IO1_Y], [3.6, 10.6]]),
    # power LED, from the 5 V rail between D2 and the hop
    dict(net="5V", color="#ff7a6b", pts=[[4.0, 7.94], [-0.2, 7.94]]),
    dict(net="5V", color="#ff7a6b", pts=[[-2.6, 7.94], [-3.25, 7.94]]),
    dict(net="GND", color="#9aa7b4", pts=[[-4.95, 7.94], [-4.95, 9.0], [-4.2, 9.0]]),
    # spare GPIO header
    dict(net="IO12", color="#d6a8ff", pts=[[HDR_X[1], PIN_Y[3]], [20.5, PIN_Y[3]]]),
    dict(net="IO11", color="#d6a8ff", pts=[[HDR_X[1], PIN_Y[4]], [20.5, PIN_Y[4]]]),
    dict(net="IO10", color="#d6a8ff", pts=[[HDR_X[1], PIN_Y[5]], [20.5, PIN_Y[5]]]),
    dict(net="GND", color="#9aa7b4", pts=[[20.5, PIN_Y[6]], [20.5, 18.9]]),
]
# GND vias (GND plane on the bottom layer) and the hop vias
GND_VIAS = [[3.6, 13.4], [4.2, 15.5], [10.4, 15.6], [13.5, 17.2], [6.0, 19.8], [14.6, 9.9], [-4.2, 9.0], [20.5, 18.9]]
HOP_VIAS = [[5.0, 10.2], [5.0, 8.2]]

J2_PADS = [[11.7, 19.7], [12.7, 19.7]]       # signal pads of J2 (1.0 mm pitch), + and -

# test pads on the bottom side
TP_NAMES = ["5V", "3V3", "GND", "IO1", "BCLK", "LRC", "DIN"]
TP = [[round(3.4 + 2.0 * k, 2), 22.7] for k in range(7)]

LABELS = [
    dict(text="J1", x=9.0, y=-0.0, kind="ref"),
]


# Mounting holes matching the CyberBrick receiver shield (XA004, 29 x 30 mm).
# Four corner holes, diameter 2.7 mm and copper ring about 5.7 mm (read from the manufacturer's product image of the
# receiver shield XA004, reference only, not stored here). The spacing is exactly 23.0 x 24.0 mm according to the
# CAD model of the community "CyberBrick Remote Control Receiver Test Housing" (MakerWorld 1237405), whose four
# heat-set insert holes (3.1 mm) are at +-11.5 / +-12.0 mm from the centre; the image gives 23.2 x 24.2 mm, i.e. the
# same within the reading error. Still VERIFY with calipers on the real receiver before ordering.
CB_W, CB_H = 29.0, 30.0
CB_HOLE_D, CB_RING_D = 2.7, 5.7
CB_DX, CB_DY = 23.0, 24.0                       # hole spacing
ZERO_CX, ZERO_CY = BOARD_W / 2, BOARD_H / 2     # centre of the Zero; the CyberBrick pattern is centred on it
CB_HOLES = [[round(ZERO_CX + sx * CB_DX / 2, 2), round(ZERO_CY + sy * CB_DY / 2, 2), CB_HOLE_D]
            for sy in (-1, 1) for sx in (-1, 1)]


# Outline shapes are a union of ("rect", x0, y0, x1, y1, corner radius) and ("circle", cx, cy, r),
# in the same coordinates as the parts (origin = top-left corner of the Zero).
VARIANTS = [
    dict(id="cb", name="CyberBrick size", short="29 x 30 mm like the CyberBrick receiver shield, its four holes",
         shapes=[("rect", ZERO_CX - CB_W / 2, ZERO_CY - CB_H / 2, ZERO_CX + CB_W / 2, ZERO_CY + CB_H / 2, 1.5)],
         holes=CB_HOLES),
]
VARIANT = {v["id"]: v for v in VARIANTS}


def bounds(outline):
    xs = [p[0] for p in outline]; ys = [p[1] for p in outline]
    return min(xs), min(ys), max(xs), max(ys)


def _circle_hits_rect(cx, cy, r, box):
    nx = min(max(cx, box[0]), box[2]); ny = min(max(cy, box[1]), box[3])
    return (cx - nx) ** 2 + (cy - ny) ** 2 < r * r


def check():
    """Print overlaps between part footprints and violations of the gap / board outline / holes."""
    ok = True
    bx0, by0, bx1, by1 = bounds([[sh[1], sh[2]] for sh in VARIANT["cb"]["shapes"]] + [[sh[3], sh[4]] for sh in VARIANT["cb"]["shapes"]])
    boxes = {p["ref"]: (p["x"] - p["w"] / 2, p["y"] - p["h"] / 2, p["x"] + p["w"] / 2, p["y"] + p["h"] / 2) for p in PARTS}
    for p in PARTS:
        r = p["ref"]; x0, y0, x1, y1 = boxes[r]
        if p.get("margin"):
            if x0 < bx0 + 0.2 or x1 > bx1 - 0.2 or y0 < by0 + 0.2 or y1 > by1 - 0.2:
                print("outside the board:", r); ok = False
            if x1 > 0 and x0 < BOARD_W and y1 > 0 and y0 < BOARD_H:
                print("margin part under the Zero:", r); ok = False
            for hx, hy, _ in CB_HOLES:
                if _circle_hits_rect(hx, hy, CB_RING_D / 2 + 0.2, boxes[r]):
                    print("margin part touches a mounting hole:", r); ok = False
        elif x0 < GAP_X[0] - 1e-6 or x1 > GAP_X[1] + 1e-6 or y0 < -1e-6 or y1 > BOARD_H + 1e-6:
            print("outside gap/board:", r, [round(v, 2) for v in (x0, y0, x1, y1)]); ok = False
    refs = list(boxes)
    for i, a in enumerate(refs):
        for b in refs[i + 1:]:
            A, B = boxes[a], boxes[b]
            if A[0] < B[2] and B[0] < A[2] and A[1] < B[3] and B[1] < A[3]:
                print("overlap:", a, b); ok = False
    print("layout ok" if ok else "layout has problems")
    return ok


if __name__ == "__main__":
    check()
