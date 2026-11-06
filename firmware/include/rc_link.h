// Channel frames from the CyberBrick receiver, sent by the app "Code" snippet docs/cyberbrick-code/uart_forward.py.
// Frame (23 bytes, 115200 8N1): 0xA5 0x5A, ten uint16 little endian [L1 L2 L3 R1 R2 R3 K1 K2 K3 K4], XOR of the
// 20 data bytes. Sticks are 0..4095, buttons 1 = released, 0 = pressed (docs/cyberbrick-code/README.md).
//
// The frames arrive on the same pin as the servo pulse (PIN_THROTTLE_IN): the UART only accepts complete frames
// with a correct checksum, and the pulse interrupt rejects everything that is not a 0.9..2.1 ms pulse, so both can
// listen at once and the firmware uses whichever is alive.
#pragma once
#include <Arduino.h>

class RcLink {
 public:
  static const int CHANNELS = 10;
  enum { L1, L2, L3, R1, R2, R3, K1, K2, K3, K4 };

  void begin(int rxPin, uint32_t baud = 115200) {
    Serial1.begin(baud, SERIAL_8N1, rxPin, -1);
  }

  // Call often (every audio block); returns true when a new frame was accepted.
  bool poll() {
    bool got = false;
    while (Serial1.available()) got |= feed((uint8_t)Serial1.read());
    return got;
  }

  bool alive(uint32_t timeoutMs = 300) const { return lastMs != 0 && millis() - lastMs < timeoutMs; }
  uint16_t get(int i) const { return ch[i]; }
  bool pressed(int k) const { return ch[k] == 0; }   // K1..K4
  uint32_t good = 0, bad = 0;

  // Stick value -1..1 around mid with a dead zone (both in ADC counts), clamped.
  float stick(int i, int mid, int deadzone) const {
    int d = (int)ch[i] - mid;
    int a = d < 0 ? -d : d;
    if (a <= deadzone) return 0.0f;
    float span = (float)((d < 0 ? mid : 4095 - mid) - deadzone);
    float v = (float)(a - deadzone) / span;
    if (v > 1.0f) v = 1.0f;
    return d < 0 ? -v : v;
  }

 private:
  uint8_t frame[23];
  int fill = 0;
  uint16_t ch[CHANNELS] = {2048, 2048, 2048, 2048, 2048, 2048, 1, 1, 1, 1};
  uint32_t lastMs = 0;

  bool feed(uint8_t b) {
    if (fill == 0 && b != 0xA5) return false;
    if (fill == 1 && b != 0x5A) { fill = (b == 0xA5) ? 1 : 0; return false; }
    frame[fill++] = b;
    if (fill < (int)sizeof(frame)) return false;
    fill = 0;
    uint8_t x = 0;
    for (int i = 2; i < 22; i++) x ^= frame[i];
    if (x != frame[22]) { bad++; return false; }
    for (int i = 0; i < CHANNELS; i++) ch[i] = frame[2 + 2 * i] | (frame[3 + 2 * i] << 8);
    good++;
    lastMs = millis();
    return true;
  }
};
