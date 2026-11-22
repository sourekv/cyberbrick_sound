#pragma once
// The Bluetooth Low Energy link (docs/ble-link.md): the protocol of set_link.h over a Nordic-UART-like
// GATT service, so that the web page can reach the module through Web Bluetooth. Only built in the environment
// engine_sets (-DBLE_LINK_ENABLED=1, the default there). Access is protected by the PIN of SetLink (@auth); the service is
// advertising only during a window after power-up.
//
//   service  6E400001-B5A0-F393-E0A9-E50E24DCCA9E
//   RX       6E400002-...   the page writes the protocol lines here (write, write without response)
//   TX       6E400003-...   the module sends the replies here (notify)
//
// BleUart is a Stream, so SetLink (attach()) runs on it unchanged. Lines of the protocol are up to about 4 kB, a
// notification carries at most MTU - 3 bytes, so a reply is cut into several notifications and put together again by
// the page. The MTU is whatever the central negotiates (BLEDevice::setMTU asks for 517).
#include <Arduino.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>

class BleUart : public Stream, public BLEServerCallbacks, public BLECharacteristicCallbacks {
 public:
  static constexpr const char* SERVICE = "6E400001-B5A0-F393-E0A9-E50E24DCCA9E";
  static constexpr const char* RX_UUID = "6E400002-B5A0-F393-E0A9-E50E24DCCA9E";
  static constexpr const char* TX_UUID = "6E400003-B5A0-F393-E0A9-E50E24DCCA9E";
  static const size_t RX_SIZE = 8192;

  void begin(const char* name) {
    BLEDevice::init(name);
    BLEDevice::setMTU(517);
    server = BLEDevice::createServer();
    server->setCallbacks(this);
    BLEService* svc = server->createService(SERVICE);
    tx = svc->createCharacteristic(TX_UUID, BLECharacteristic::PROPERTY_NOTIFY);
    tx->addDescriptor(new BLE2902());
    BLECharacteristic* rx = svc->createCharacteristic(RX_UUID, BLECharacteristic::PROPERTY_WRITE | BLECharacteristic::PROPERTY_WRITE_NR);
    rx->setCallbacks(this);
    svc->start();
    BLEAdvertising* adv = BLEDevice::getAdvertising();
    adv->addServiceUUID(SERVICE);
    adv->setScanResponse(true);
    started = true;
  }
  void advertise(bool on) {
    if (!started) return;
    if (on) BLEDevice::startAdvertising(); else BLEDevice::getAdvertising()->stop();
    advertising = on;
  }
  bool isAdvertising() const { return advertising && !connected; }
  bool isConnected() const { return connected; }
  int mtu() const { return mtuNow; }

  // ---- Stream (the reading side is what SetLink polls, the writing side what it replies)
  int available() override { return (int)((head + RX_SIZE - tail) % RX_SIZE); }
  int read() override {
    if (head == tail) return -1;
    uint8_t c = rxBuf[tail];
    tail = (tail + 1) % RX_SIZE;
    return c;
  }
  int peek() override { return head == tail ? -1 : rxBuf[tail]; }
  size_t write(uint8_t c) override { return write(&c, 1); }
  size_t write(const uint8_t* data, size_t n) override {
    for (size_t i = 0; i < n; i++) {
      out += (char)data[i];
      if (data[i] == '\n') sendOut();            // a protocol line is complete: send it
    }
    return n;
  }
  void flush() override { sendOut(); }

  // ---- callbacks (the BLE task)
  void onConnect(BLEServer* s) override { connected = true; advertising = false; Serial.println("ble: connected"); }
  void onDisconnect(BLEServer* s) override {
    connected = false; mtuNow = 23; head = tail = 0;
    Serial.println("ble: disconnected");
  }
  void onMtuChanged(BLEServer* s, esp_ble_gatts_cb_param_t* param) override { mtuNow = param->mtu.mtu; Serial.printf("ble: MTU %d\n", mtuNow); }
  void onWrite(BLECharacteristic* c) override {
    std::string v = c->getValue();
    for (char ch : v) {
      size_t next = (head + 1) % RX_SIZE;
      if (next == tail) break;                    // full: the page sends the next command only after the reply, so this should not happen
      rxBuf[head] = (uint8_t)ch; head = next;
    }
  }

 private:
  BLEServer* server = nullptr;
  BLECharacteristic* tx = nullptr;
  volatile bool connected = false, started = false, advertising = false;
  volatile int mtuNow = 23;
  uint8_t rxBuf[RX_SIZE];
  volatile size_t head = 0, tail = 0;
  String out;

  void sendOut() {
    if (!out.length()) return;
    if (!connected) { out = ""; return; }
    const size_t chunk = (size_t)max(20, min(512, (int)mtuNow - 3));
    size_t sent = 0;
    while (sent < out.length() && connected) {
      size_t n = min(chunk, (size_t)out.length() - sent);
      tx->setValue((uint8_t*)out.c_str() + sent, n);
      tx->notify();
      sent += n;
      delay(6);                                   // let the stack send before the next one; the page needs the whole line anyway
    }
    out = "";
  }
};
