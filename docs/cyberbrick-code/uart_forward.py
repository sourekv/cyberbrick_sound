# CyberBrick app "Code" snippet, test 2: forward the transmitter channels to the sound module over a wire.
# Reads rc_module.rc_slave_data() (documented: [L1, L2, L3, R1, R2, R3, K1, K2, K3, K4], sticks 0..4095,
# buttons 0/1) every 20 ms and sends it from the PWM4 servo port (GPIO0, not used by the truck) as UART 115200 8N1.
# Frame, 23 bytes: 0xA5 0x5A, ten uint16 little endian, XOR of the 20 data bytes.
# RX is put on GPIO9 (the board key, an input with a pull-up anyway) so the UART does not take a used pin.
# Paste the lines below into a receiver event (module "Code"), e.g. a short press of a button.
# The RGB LED on the core flashes green briefly every 50 frames (once a second) while data is sent.
# Our own code (not taken from Bambu); it only uses the documented rc_module and MicroPython modules.
import time
import struct
import neopixel
import rc_module
from machine import UART, Pin
u = UART(1, baudrate=115200, tx=0, rx=9)
np = neopixel.NeoPixel(Pin(8), 1)
n = 0
while True:
    d = rc_module.rc_slave_data()
    if d:
        b = struct.pack('<10H', *d)
        c = 0
        for x in b:
            c ^= x
        u.write(b'\xa5\x5a' + b + bytes([c]))
        n += 1
        np[0] = (0, 30, 0) if n % 50 == 0 else (0, 0, 0)
        np.write()
    time.sleep(0.02)
