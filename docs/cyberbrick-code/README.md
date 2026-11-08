# Code snippets for the CyberBrick receiver

Small MicroPython snippets for the "Code" module of the CyberBrick app, which the receiver runs when an event fires
(see `docs/start-stop-horn.md`, section on the receiver's documented data API). Our own code; it uses only the
documented `rc_module` and standard MicroPython modules, nothing from Bambu is copied or changed on the receiver.
Status: both work on the truck (2026-11-06); `uart_forward.py` is part of the current configuration
(`docs/cyberbrick-config/Truck_with_Engine_Sound_Data.json`).

How to use: in the CyberBrick app, add an event to the receiver (for example a short press of a free button on the
transmitter), set its module to **Code**, paste the snippet as the value, send the configuration and fire the event.
A snippet runs until another snippet is started or the receiver is switched off. The receiver rejects any line
containing `exit`, `quit`, `open`, `eval`, `exec`, `__import__`, `subprocess`, `os.system`, `os.remove` or
`os.rmdir`, even in a comment.

| File | Test | What you should see |
|---|---|---|
| `blink_test.py` | does a snippet run at all | the RGB LED on the receiver (Remote Control Receiver Shield - XA003 XA004) blinks blue about 3 times a second |
| `uart_forward.py` | forward all ten channels over a wire | `uart_probe` on the Zero prints the channels (the green flash of the first version was removed on 2026-11-06) |

## Test 2 wiring (`uart_forward.py` + `uart_probe`)

- The usual servo cable, plugged into the receiver's **PWM4** servo port (S4; GPIO0, unused by the truck) instead of
  PWM2: signal -> about 1 kOhm -> Zero **GPIO1** (the same input as the throttle), GND -> Zero **GND** (connect
  first, disconnect last).
- The **V wire stays disconnected**: the Zero is on USB, the receiver on the model battery
  ([USB power rule](../bringup.md)).
- First plan was the LED2 port (GPIO20), but the pin order of the LED connectors is not marked on the receiver, while
  the servo headers are labelled S / V / G.
- Flash: `pio run -e uart_probe -t upload`, then open the serial monitor (115200). It prints the six sticks
  (0..4095), the four buttons, frames per second (about 50 expected) and checksum errors.

Frame: 23 bytes, 115200 8N1, `A5 5A`, ten uint16 little endian `[L1 L2 L3 R1 R2 R3 K1 K2 K3 K4]`, XOR of the 20
data bytes.

## Results (2026-11-06)

- **Test 1 passed**: a short press of the L Shoulder Button made the RGB LED on the receiver (Remote Control Receiver Shield - XA003 XA004) blink blue. The app
  accepted the hand-written `Truck_Code_Test.json` and showed both snippets.
- **Test 2 passed**: the UART snippet on the PWM4 servo header (GPIO0) delivered frames to `uart_probe` on Zero
  GPIO1, **about 27 frames/s with zero checksum errors** over several thousand frames (the snippet asks every 20 ms;
  new data seems to come at the radio rate). The V wire was disconnected, the Zero on USB.
- Channel order confirmed by moving every control (values 0..4095, rest values of this transmitter in brackets):
  L1 = left shoulder 3-position switch (0 / about 1760 / 4089), L2 = left stick X (about 2130), **L3 = left stick Y,
  the throttle** (about 1830), R1 = right shoulder stick (about 2260), R2 = right stick X, the steering (about 2030),
  R3 = right stick Y (about 2050). All sticks reach 0 and about 4090 at the ends.
- Buttons: **1 = released, 0 = pressed** (K1 read 0 while the L Shoulder Button was held).
- Pitfall: the snippets share the one button. A short press starts the blink snippet and that stops the UART
  snippet (the data stops); a long press starts the UART snippet again. A snippet also stops when the receiver is
  switched off, so after every power-up the long press is needed again.
