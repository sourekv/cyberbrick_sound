// Prints the width of the incoming servo pulse (microseconds) to serial.
#include <Arduino.h>
#include "config.h"

static volatile uint32_t riseUs = 0;
static volatile uint32_t widthUs = 0;
static volatile uint32_t lastEdgeMs = 0;
static volatile uint32_t pulseCount = 0;

void IRAM_ATTR onEdge() {
  uint32_t now = micros();
  if (digitalRead(PIN_THROTTLE_IN)) {
    riseUs = now;
  } else if (riseUs) {
    widthUs = now - riseUs;
    lastEdgeMs = millis();
    pulseCount++;
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_THROTTLE_IN, INPUT);
  attachInterrupt(digitalPinToInterrupt(PIN_THROTTLE_IN), onEdge, CHANGE);
  Serial.println("pulse_measure: waiting for pulses");
}

void loop() {
  static uint32_t lastCount = 0, lastMs = 0;
  delay(200);
  uint32_t w = widthUs, c = pulseCount, ms = millis();
  if (ms - lastEdgeMs > PULSE_TIMEOUT_MS) {
    Serial.println("no signal");
  } else {
    float hz = (c - lastCount) * 1000.0f / (ms - lastMs);
    Serial.printf("width %lu us  rate %.1f Hz\n", (unsigned long)w, hz);
  }
  lastCount = c;
  lastMs = ms;
}
