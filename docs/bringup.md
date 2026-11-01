# Bring-up plan

Status: PWM2 throttle copy verified on the real receiver (see the measurements table). The engine firmware with the real throttle is the next test.

## 1. Measurements on the CyberBrick receiver (multimeter, before connecting anything)
Record results in the table at the bottom.
- [ ] Servo port connector type (standard 3-pin 2.54 mm header?) and number of servo ports
- [ ] Pin order of a servo port. The CyberBrick app's board view labels each servo port S, V, G (signal, +, GND), 4 ports S1-S4 (GPIO 3, 2, 1, 0 per the official code) on two 2x3 headers. Confirm on the real board: find GND by continuity to the battery negative or a motor-port ground, then measure the other two against it with the receiver powered
- [ ] Voltage on the + pin (expected 5 V)
- [ ] Signal pin: idle voltage and, with the throttle channel mapped in the CyberBrick app, whether it is a 3.3 V or 5 V pulse (a multimeter shows only the average; if it reads well above ~0.5 V average it is probably active; if unsure, assume 5 V and use a divider)
- [ ] Update the CyberBrick app/firmware first so receiver and transmitter match
- [ ] In the app: the stock model maps the L stick to the DC motor port M1 (throttle) and R stick to a servo (steering). Try adding a continuous-rotation servo device on a free servo port (e.g. S2) and assign it the L stick too, so a copy of the throttle appears on a servo port. Then map the throttle stick to a servo channel and limit range to 1.0-2.0 ms if possible

## 1b. Planned CyberBrick app mapping (app side confirmed, hardware side untested)
The stock model drives the motor on M1 from the L Stick (channel Y, module "Throttle", direction Negative) and steering on PWM1.
In the app (Truck -> Channel Binding for the L Stick) a second row can be added for the same channel:
- Truck: add an Angular Servo, it is created as **PWM2 (Angular)** on servo port 2.
- Channel Binding, L Stick: **Y -> PWM2 (Angular), Negative** (same as Throttle). The app accepts two modules on one channel.
- PWM2 parameters: **Speed 100 %, Min angle 45 deg, Max angle 135 deg, Midpoint offset 0 deg**. From the official code an angle servo outputs about 0.5 ms at 0 deg, 1.5 ms at 90 deg and 2.5 ms at 180 deg, so 45-135 deg should give about 1.0-2.0 ms.
- Nothing is sent to the device until "Send to Device". Verify with `pulse_measure`: about 1000-2000 us, 1500 us at stick centre.
- The L Stick self-centres; the firmware uses |pulse - 1500|, so forward and reverse both raise the engine sound.

## 2. Wiring (breadboard) - pins from `firmware/include/config.h`
Verify GPIO labels against the silkscreen on the Waveshare board first.

| Waveshare ESP32-S3-Zero | MAX98357A module |
|---|---|
| GPIO4 | DIN |
| GPIO5 | BCLK |
| GPIO6 | LRC |
| 5V (USB) | VIN |
| GND | GND |

| CyberBrick servo port | ESP32-S3-Zero |
|---|---|
| signal | 1 kΩ resistor -> GPIO1 |
| GND | GND |
| + (5 V) | NOT connected for the first tests |

Speaker: to the MAX98357A + / - terminals.

Rules:
- First tests: board powered from USB (or a powerbank), only signal + GND from the receiver.
- Never connect USB and the servo port's 5 V at the same time.
- Never put 7.4 V on any board pin.
- If the signal is 5 V, use a divider (for example 1.8 kΩ in series, 3.3 kΩ to GND) before GPIO1.

### Stage 2: powering the module from the servo port
Only after stage 1 works. See `docs/wiring-stage2.png` (source `.svg`): unplug USB, connect the servo port's V pin to the board's 5V pin, measure the voltage and the current (multimeter in series) before relying on it, and lower `MASTER_VOLUME` if the receiver resets. Reflash only with the V wire removed.

Test-tone wiring only (no CyberBrick yet): `docs/wiring-test-tone.png`.

## 3. Test order
1. `pio run -e test_tone -t upload` - expect a steady 440 Hz tone. Checks amplifier and speaker.
2. `pio run -e pulse_measure -t upload` - move the stick, expect about 1000-2000 us at about 50 Hz.
3. `pio run -e engine -t upload` - engine sound follows the throttle.
Tune `config.h`: `PULSE_CENTER_US`, `PULSE_RANGE_US`, `MASTER_VOLUME`.

## 4. Measurements table

| Item | Result |
|---|---|
| Servo connector | |
| Number of servo ports | |
| Pin order (S/+/-) | S, V, G in a row; S is the leftmost pin, G the rightmost (PWM2 = lower row of the left header) |
| + voltage | 4.94 V on the servo port V pin (receiver on battery, no load; battery itself 7.1 V) |
| Signal level | about 3.3 V (multimeter average on 200 mV range: 0.15 / 0.23 / 0.31 V at 1.0 / 1.5 / 2.0 ms) |
| Pulse range (us) | 977 .. 1973 with L Stick Y bound to PWM2 (45..135 deg); at rest 1445..1465 (duty steps of about 20 us) |
| Pulse rate (Hz) | 50.0, measured on GPIO1 via 1 kOhm with `pulse_measure` |
| Current draw of module at volume X | MASTER_VOLUME 0.6, ESP32-S3-Zero + MAX98357A + 40 mm speaker powered from the PWM2 V pin: about 57 mA idle, about 105 mA at full throttle in either direction (multimeter average, 1 A range). Receiver stayed stable, motor kept responding |

## Second input: button as a servo on another port (engine start / stop)
Decision 2026-11-01: engine start and stall sounds will be controlled through a second servo-type input, because it is more general than sniffing the radio link (any button, switch or stick of the transmitter can be bound to an output in the CyberBrick app). The transmitter has four digital button ports K1-K4 (momentary button module: short press, long press, press and release; several values can be added and they cycle with each press) and the receiver has four servo ports.
Test before any firmware depends on it:
1. In the CyberBrick app add a second angle servo (a free port, for example **PWM3**, servo port 3) and bind a button (K1) to it with two values, for example 135 deg and 45 deg, cycling with each press.
2. Connect the signal pin (S) of that servo port through a 1 kOhm resistor to **GPIO2** of the Zero (left header, pin 5; `PIN_AUX_IN` in `config.h`). Ground is common with the PWM2 cable; no power is needed from this port.
3. Flash `pio run -e pulse_measure_aux -t upload` and watch the serial monitor: the width should change with every press and stay there (about 1.0 ms / 2.0 ms, see the PWM2 measurements above). Note the values and whether the pulse keeps running after the press, and whether the throttle copy on PWM2 is unaffected.
Open: whether the app accepts a button bound to an angle servo with fixed angles, and whether the receiver keeps the pulse running without a servo plugged in (it does for PWM2).

