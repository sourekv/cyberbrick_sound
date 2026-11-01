"""Electrical definition of the sound shield: the single source for the schematic and the board.

Every part has a KiCad symbol, a footprint and a pin -> net map. Pin numbers follow the KiCad library
symbols (Device:R pins 1/2, diodes and LED: 1 = cathode, 2 = anode, C_Polarized: 1 = plus, ...).
MAX98357A pinout verified against the datasheet (TQFN-16): 1 DIN, 2 GAIN_SLOT, 3/11/15 GND, 4 SD_MODE,
7/8 VDD, 9 OUTP, 10 OUTN, 14 LRCLK, 16 BCLK, 5/6/12/13 N.C., exposed pad (17) to ground.

None means "deliberately not connected" (gets a no-connect flag in the schematic).
"""

NC = None
FP_R = "Resistor_SMD:R_0603_1608Metric"
FP_C = "Capacitor_SMD:C_0603_1608Metric"

# ref: (symbol, value, footprint, {pin: net}, description)
PARTS = {
    # ---- input and protection ----
    "J1": ("Connector_Generic:Conn_01x03", "Servo input S-V-G", "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Horizontal",
           {"1": "S_IN", "2": "VIN", "3": "GND"}, "Right-angle male header, throttle copy from PWM2"),
    "TVS1": ("Device:D_TVS", "ESD diode 5 V", "Diode_SMD:D_SOD-323", {"1": "S_IN", "2": "GND"}, "Optional ESD protection of the throttle signal"),
    "R1": ("Device:R", "1k", FP_R, {"1": "S_IN", "2": "IO1_THR"}, "Series resistor to GPIO1"),
    "R2": ("Device:R", "100k", FP_R, {"1": "IO1_THR", "2": "GND"}, "Pull-down on GPIO1"),
    # ---- power ----
    "F1": ("Device:Polyfuse", "0.5A PTC", "Fuse:Fuse_1206_3216Metric", {"1": "VIN", "2": "VFUSED"}, "Resettable fuse"),
    "D1": ("Device:D_Schottky", "Schottky 1A", "Diode_SMD:D_SOD-123", {"1": "+5V", "2": "VFUSED"}, "Reverse-polarity protection"),
    "D2": ("Device:D_Schottky", "Schottky 1A", "Diode_SMD:D_SOD-123", {"1": "5V_ZERO", "2": "+5V"}, "OR-ing: servo 5 V and USB 5 V can both be connected"),
    "C1": ("Device:C_Polarized", "100u", "Capacitor_Tantalum_SMD:CP_EIA-6032-28_Kemet-C", {"1": "+5V", "2": "GND"}, "Bulk capacitor"),
    "C2": ("Device:C", "10u", "Capacitor_SMD:C_0805_2012Metric", {"1": "+5V", "2": "GND"}, "Amplifier supply decoupling"),
    "C3": ("Device:C", "100n", FP_C, {"1": "+5V", "2": "GND"}, "Amplifier supply decoupling"),
    "C6": ("Device:C", "100n", FP_C, {"1": "+5V", "2": "GND"}, "General decoupling"),
    "C7": ("Device:C", "100n", FP_C, {"1": "+5V", "2": "GND"}, "General decoupling"),
    "R3": ("Device:R", "1k", FP_R, {"1": "+5V", "2": "LED_A"}, "Power LED resistor (about 3 mA)"),
    "LED1": ("Device:LED", "green", "LED_SMD:LED_0603_1608Metric", {"1": "GND", "2": "LED_A"}, "Power LED"),
    # ---- ESP32-S3-Zero on two 9-pin female headers (left: 5V GND 3V3 IO1..IO6, right: TX RX IO13..IO7) ----
    "J3": ("Connector_Generic:Conn_01x09", "Zero left: 5V GND 3V3 IO1 IO2 IO3 IO4 IO5 IO6",
           "Connector_PinSocket_2.54mm:PinSocket_1x09_P2.54mm_Vertical",
           {"1": "5V_ZERO", "2": "GND", "3": "+3V3", "4": "IO1_THR", "5": NC, "6": NC, "7": "IO4_DIN", "8": "IO5_BCLK", "9": "IO6_LRC"},
           "Socket for the left pin row of the ESP32-S3-Zero"),
    "J4": ("Connector_Generic:Conn_01x09", "Zero right: TX RX IO13..IO7 (unused)",
           "Connector_PinSocket_2.54mm:PinSocket_1x09_P2.54mm_Vertical",
           {str(i): NC for i in range(1, 10)}, "Socket for the right pin row of the ESP32-S3-Zero (no signals used)"),
    # ---- I2S series resistors ----
    "R6": ("Device:R", "33R", FP_R, {"1": "IO4_DIN", "2": "DIN"}, "Series resistor DIN (can be 0R)"),
    "R7": ("Device:R", "33R", FP_R, {"1": "IO5_BCLK", "2": "BCLK"}, "Series resistor BCLK (can be 0R)"),
    "R8": ("Device:R", "33R", FP_R, {"1": "IO6_LRC", "2": "LRCLK"}, "Series resistor LRC (can be 0R)"),
    # ---- amplifier ----
    "U1": ("Audio:MAX98357A", "MAX98357AETE+", "Package_DFN_QFN:TQFN-16-1EP_3x3mm_P0.5mm_EP1.23x1.23mm",
           {"1": "DIN", "2": "GAIN", "3": "GND", "4": "SD_MODE", "5": NC, "6": NC, "7": "+5V", "8": "+5V",
            "9": "OUTP", "10": "OUTN", "11": "GND", "12": NC, "13": NC, "14": "LRCLK", "15": "GND", "16": "BCLK", "17": "GND"},
           "I2S class-D amplifier"),
    "JP1": ("Jumper:SolderJumper_2_Open", "GAIN 15 dB", "Jumper:SolderJumper-2_P1.3mm_Open_Pad1.0x1.5mm",
            {"1": "GAIN", "2": "GAIN_R"}, "Open: GAIN floating = 9 dB. Bridged: 100k to ground = 15 dB"),
    "R4": ("Device:R", "100k", FP_R, {"1": "GAIN_R", "2": "GND"}, "GAIN resistor"),
    "JP2": ("Jumper:SolderJumper_2_Bridged", "SD_MODE (L+R)/2", "Jumper:SolderJumper-2_P1.3mm_Bridged_Pad1.0x1.5mm",
            {"1": "SD_MODE", "2": "SD_R"}, "Bridged by default; cut open = amplifier in shutdown"),
    "R5": ("Device:R", "1M", FP_R, {"1": "+5V", "2": "SD_R"}, "SD_MODE pull-up: with the internal 100k pull-down gives (L+R)/2"),
    # ---- speaker output ----
    "FB1": ("Device:FerriteBead", "ferrite 600R@100MHz", "Inductor_SMD:L_0603_1608Metric", {"1": "OUTP", "2": "SPK_P"}, "Speaker output filter (can be 0R)"),
    "FB2": ("Device:FerriteBead", "ferrite 600R@100MHz", "Inductor_SMD:L_0603_1608Metric", {"1": "OUTN", "2": "SPK_N"}, "Speaker output filter (can be 0R)"),
    "C4": ("Device:C", "100p", FP_C, {"1": "SPK_P", "2": "GND"}, "EMI capacitor at the speaker connector"),
    "C5": ("Device:C", "100p", FP_C, {"1": "SPK_N", "2": "GND"}, "EMI capacitor at the speaker connector"),
    "J2": ("Connector_Generic:Conn_01x02", "Speaker JST SH 1.0", "Connector_JST:JST_SH_SM02B-SRSS-TB_1x02-1MP_P1.00mm_Horizontal",
           {"1": "SPK_P", "2": "SPK_N"}, "Speaker connector, same type as the CyberBrick motor ports"),
}

# test points on the bottom side
for _i, _n in enumerate(["+5V", "+3V3", "GND", "IO1_THR", "IO5_BCLK", "IO6_LRC", "IO4_DIN"], start=1):
    PARTS[f"TP{_i}"] = ("Connector:TestPoint", {"+5V": "5V", "+3V3": "3V3", "IO1_THR": "IO1", "IO5_BCLK": "BCLK", "IO6_LRC": "LRC",
                        "IO4_DIN": "DIN"}.get(_n, _n), "TestPoint:TestPoint_Pad_D1.0mm", {"1": _n}, "Test pad")

# mounting holes (no copper, so a metal screw cannot short anything)
for _i in range(1, 5):
    PARTS[f"MH{_i}"] = ("Mechanical:MountingHole", "M2.5", "MountingHole:MountingHole_2.7mm_M2.5", {}, "Mounting hole 2.7 mm")

# ---- parts that will carry a PWR_FLAG in the schematic (the power nets are fed from connectors) ----
PWR_FLAG_NETS = ["+5V", "GND"]
POWER_SYMBOLS = {"GND": "power:GND", "+5V": "power:+5V", "+3V3": "power:+3V3"}


def nets():
    """net name -> sorted list of 'REF.pin'."""
    out = {}
    for ref, (_s, _v, _f, pins, _d) in PARTS.items():
        for pin, net in pins.items():
            if net is not None:
                out.setdefault(net, []).append(f"{ref}.{pin}")
    return {k: sorted(v) for k, v in sorted(out.items())}


if __name__ == "__main__":
    for n, p in nets().items():
        print(f"{n:10s}", " ".join(p))
