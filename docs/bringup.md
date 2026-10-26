# Bring-up plan

Status: written before the hardware arrived. Nothing here has been tested on a real board yet.

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
| Pin order (S/+/-) | |
| + voltage | |
| Signal level | |
| Pulse range (us) | |
| Pulse rate (Hz) | |
| Current draw of module at volume X | |
