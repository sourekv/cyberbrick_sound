#include <Arduino.h>

void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println("cyberbrick_sound: boot");
}

void loop() {
  delay(1000);
}
