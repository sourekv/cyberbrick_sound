// Prints the width of the incoming servo pulse (microseconds) to serial.
// Measures PIN_THROTTLE_IN; with -DMEASURE_AUX (env pulse_measure_aux) it measures PIN_AUX_IN instead, to check a
// second servo port, for example a CyberBrick button bound to an angle servo (docs/bringup.md).
#include <Arduino.h>
#include "config.h"
#ifdef MEASURE_AUX
#define MEASURE_PIN PIN_AUX_IN
#else
#define MEASURE_PIN PIN_THROTTLE_IN
#endif

static volatile uint32_t riseUs = 0;
static volatile uint32_t widthUs = 0;
static volatile uint32_t lastEdgeMs = 0;
static volatile uint32_t pulseCount = 0;

void IRAM_ATTR onEdge() {
  uint32_t now = micros();
  if (digitalRead(MEASURE_PIN)) {
    riseUs = now;
  } else if (riseUs) {
    widthUs = now - riseUs;
    lastEdgeMs = millis();
    pulseCount++;
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(MEASURE_PIN, INPUT);
  attachInterrupt(digitalPinToInterrupt(MEASURE_PIN), onEdge, CHANGE);
  Serial.printf("pulse_measure: waiting for pulses on GPIO%d\n", MEASURE_PIN);
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
