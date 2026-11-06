# CyberBrick app "Code" snippet, test 1: does a snippet run on the receiver at all?
# Blinks the RGB LED on the receiver core (GPIO8) blue, 3 times per second, until another snippet is started.
# Paste the lines below into a receiver event (module "Code"), e.g. a short press of a button, send the
# configuration and press the button. See docs/cyberbrick-code/README.md.
# Our own code (not taken from Bambu); it only uses the documented MicroPython modules.
import time
import neopixel
from machine import Pin
np = neopixel.NeoPixel(Pin(8), 1)
while True:
    np[0] = (0, 0, 40)
    np.write()
    time.sleep(0.15)
    np[0] = (0, 0, 0)
    np.write()
    time.sleep(0.15)
