// UART probe: receives the channel frames that the CyberBrick receiver sends with the app "Code" snippet
// docs/cyberbrick-code/uart_forward.py and prints them on the USB serial console.
// Frame (23 bytes, 115200 8N1): 0xA5 0x5A, ten uint16 little endian [L1 L2 L3 R1 R2 R3 K1 K2 K3 K4], XOR of the
// 20 data bytes. Wiring: the usual servo cable from the receiver PWM4 port (signal = GPIO0) -> ~1 kOhm -> Zero GPIO1, GND -> GND. Nothing else:
// the V wire stays disconnected while the Zero is on USB (docs/bringup.md, USB power rule).
// Prints the latest channels, frames per second and checksum errors twice a second; the status LED shows green
// while frames arrive and red when none came for 0.5 s.
#include <Arduino.h>
#include "config.h"
#include "status_led.h"

#define PIN_UART_RX 1   // the same input as the throttle servo signal, so the existing servo cable can be used
static const uint32_t BAUD = 115200;

static StatusLed statusLed;
static uint8_t frame[23];
static int fill = 0;
static uint16_t ch[10];
static uint32_t good = 0, bad = 0, lastGoodMs = 0;

static void feed(uint8_t b) {
  if (fill == 0 && b != 0xA5) return;
  if (fill == 1 && b != 0x5A) { fill = (b == 0xA5) ? 1 : 0; return; }
  frame[fill++] = b;
  if (fill < (int)sizeof(frame)) return;
  fill = 0;
  uint8_t x = 0;
  for (int i = 2; i < 22; i++) x ^= frame[i];
  if (x != frame[22]) { bad++; return; }
  for (int i = 0; i < 10; i++) ch[i] = frame[2 + 2 * i] | (frame[3 + 2 * i] << 8);
  good++;
  lastGoodMs = millis();
}

void setup() {
  Serial.begin(115200);
  statusLed.begin();
  Serial1.begin(BAUD, SERIAL_8N1, PIN_UART_RX, -1);
  Serial.println("uart_probe: waiting for frames on GPIO1 (115200 8N1)");
}

void loop() {
  static uint32_t lastPrint = 0, goodAtPrint = 0;
  while (Serial1.available()) feed((uint8_t)Serial1.read());
  bool alive = lastGoodMs && millis() - lastGoodMs < 500;
  statusLed.update(alive, alive ? 0.3f : 0.0f);
  if (millis() - lastPrint >= 500) {
    uint32_t dt = millis() - lastPrint;
    lastPrint = millis();
    float fps = (good - goodAtPrint) * 1000.0f / dt;
    goodAtPrint = good;
    if (alive) {
      Serial.printf("L1 %4u L2 %4u L3 %4u R1 %4u R2 %4u R3 %4u  K %u%u%u%u  | %.0f frames/s, errors %lu\n",
                    ch[0], ch[1], ch[2], ch[3], ch[4], ch[5], ch[6], ch[7], ch[8], ch[9], fps, (unsigned long)bad);
    } else {
      Serial.printf("no frames (good %lu, errors %lu)\n", (unsigned long)good, (unsigned long)bad);
    }
  }
}
