// Engine sound from sound sets in the data partition (docs/user-sounds.md, include/sound_sets.h).
//
// The BOOT button steps through the sets in /sets/ (in the order of their two-digit index) and the module speaks
// the name of the set (name.wav). The set chosen last is kept in /state.json and comes back after power-up.
// Two types of set:
//   sample   idle.wav and loaded.wav, played faster with the rpm (1.0x..3.0x), blended with the load
//   synth    made in real time: the speaker-tuned grain synth (include/engine_synth2.h, a preset) or the old grain
//            synth (include/engine_synth.h)
// Every set has its own starter (start.wav: cranking only, the engine then catches by itself), horn (horn.wav, a
// loop while the horn is held), shift sound (shift.wav) and EQ ("eq" in set.json, after the engine). The stop is
// automatic: the engine of the set winds down from its rpm (stop_s).
// Without a usable set (no file system, no sets, no PSRAM, every set broken) a fallback compiled into the firmware
// plays: the diesel synth with the synthesised starter and horn of include/engine_events.h; it beeps once.
// Over USB the web page (web/index.html) lists, writes and deletes sets (include/set_link.h); while it talks to the
// module the engine is silent. On the page's "Demo" the module speaks the name of the set and plays a scripted demo
// of about 25 s (demoStep()); BOOT or the receiver's data end it.
// Everything else as in engine_lab: throttle, ignition, horn from the receiver's channel data on GPIO1
// (include/rc_link.h) or the servo pulse, virtual gearbox, reverse without upshifts.
#include <Arduino.h>
#include <math.h>
#include "driver/i2s.h"
#include "config.h"
#include "status_led.h"
#include "gearbox.h"
#include "gear_beep.h"
#include "engine_synth.h"          // old grain synth (engine_pulse)
#include "engine_synth2.h"         // speaker-tuned synth
#include "rc_link.h"
#include "engine_events.h"         // EngineState; StarterSound and HornSound for the fallback
#include "shift_sound.h"           // CC0 shift sound for the fallback
#include "sound_sets.h"
#include "set_link.h"
#if BLE_LINK_ENABLED
#include "ble_link.h"   // prototype, docs/ble-link.md: the protocol of set_link.h over Bluetooth Low Energy
#endif

#define PIN_BOOT_BUTTON 0

static volatile uint32_t riseUs = 0;
static volatile uint32_t widthUs = 0;
static volatile uint32_t lastEdgeMs = 0;

void IRAM_ATTR onEdge() {
  uint32_t now = micros();
  if (digitalRead(PIN_THROTTLE_IN)) {
    riseUs = now;
  } else if (riseUs) {
    uint32_t w = now - riseUs;
    if (w >= PULSE_MIN_US && w <= PULSE_MAX_US) {
      widthUs = w;
      lastEdgeMs = millis();
    }
  }
}

static RcLink rcLink;

static float readPulseThrottle() {
  if (millis() - lastEdgeMs > PULSE_TIMEOUT_MS) return 0.0f;
  int d = (int)widthUs - PULSE_CENTER_US;
  int a = d < 0 ? -d : d;
  if (a < PULSE_DEADBAND_US) return 0.0f;
  float t = (float)(a - PULSE_DEADBAND_US) / (float)(PULSE_RANGE_US - PULSE_DEADBAND_US);
  if (t > 1.0f) t = 1.0f;
  return d < 0 ? -t : t;
}

static bool pulsePresent() { return lastEdgeMs != 0 && millis() - lastEdgeMs <= PULSE_TIMEOUT_MS; }

static bool dataActive() {
#if RC_LINK_ENABLED
  return rcLink.alive(RC_LINK_TIMEOUT_MS);
#else
  return false;
#endif
}

static float readThrottleSigned() {
  if (dataActive()) return rcLink.stick(RcLink::L3, RC_THROTTLE_MID, RC_THROTTLE_DEADZONE);
  return readPulseThrottle();
}

static bool reversing = false;

static float readThrottle() {
  float s = readThrottleSigned() * RC_REVERSE_SIGN;
  if (s < -RC_REVERSE_THRESHOLD) reversing = true;
  else if (s > RC_REVERSE_THRESHOLD) reversing = false;
  return s < 0 ? -s : s;
}

static bool signalPresent() { return dataActive() || pulsePresent(); }

static inline float playLoop(const Clip& c, float& pos, float rate) {
  int idx = (int)pos;
  float frac = pos - idx;
  int next = idx + 1;
  if (next >= (int)c.len) next = 0;
  float s = c.data[idx] + (c.data[next] - c.data[idx]) * frac;
  pos += rate;
  while (pos >= c.len) pos -= c.len;
  return s;
}

static StatusLed statusLed;
static Gearbox gearbox;
static GearBeeper beeper((float)AUDIO_RATE);
static EngineSynth oldSynth;
static EngineSynth2 synth2;
static SpeakerEq setEq;              // the "eq" of the current set (none: passes through)
static EngineState engineState;
static float engGain = 1.0f, engGainPrev = 1.0f;

static SetLibrary library;
static SetLink usbLink;
#if BLE_LINK_ENABLED
static SetLink bleLink;
static BleUart bleUart;
static uint32_t bleWindowMs = 180000;   // prototype: advertising only this long after power-up
static Clip digitClip[10], pinWordClip;     // /voice/d0.wav .. d9.wav and pin.wav (tools/make_voice_digits.py)
static uint32_t pinGapUntil = 0;        // the next clip of the PIN is not started before this (clip length + a short gap)              // /voice/d0.wav .. d9.wav (tools/make_voice_digits.py), speak the PIN
static String blePin;                   // random for every power-up, spoken by the module
static std::vector<int> pinQueue;       // the digits still to speak
static uint32_t pinNextMs = 0;          // when the PIN is spoken again
static bool bleWasConnected = false;
static bool pinSpokenAtStart = false;   // the PIN is spoken once after power-up, again only while a page has connected and has not entered it
static bool bleActive = false;          // started after a real power-up; not after the restart that follows a session
static uint32_t bleRestartAt = 0;       // after the page has left: restart the module then
#endif
static SoundSet cur;                 // the loaded set
static int curIndex = -1;            // index in library.folders; -1 = fallback
static bool fallback = true;

static ClipPlayer namePlayer, shiftPlayer;
static WavStarter wavStarter;
static WavHorn wavHorn;
static StarterSound synthStarter;    // fallback only
static HornSound synthHorn;          // fallback only
static int fallbackShiftPos = -1;

static float duckG = 1.0f;
static inline float duck() {         // engine at 25 % while the name is spoken
  duckG += ((namePlayer.active() ? 0.25f : 1.0f) - duckG) * 0.002f;
  return duckG;
}

static inline float starterSample() { return fallback ? synthStarter.sample() : wavStarter.sample(); }
static inline float hornSample() { return fallback ? synthHorn.sample() : wavHorn.sample(); }
static inline float shiftSample() {
  if (!fallback) return shiftPlayer.next();
  if (fallbackShiftPos < 0) return 0.0f;
  float s = SHIFT_SOUND[fallbackShiftPos] * (1.0f / 32768.0f);
  if (++fallbackShiftPos >= SHIFT_SOUND_LEN) fallbackShiftPos = -1;
  return s;
}
static inline void triggerShift() {
  if (fallback) fallbackShiftPos = 0;
  else shiftPlayer.play(&cur.shiftWav);
}

static inline int16_t mixOut(float s) {
  float v = s * duck() * MASTER_VOLUME + namePlayer.next() * 0.9f + beeper.next();
  v = fmaxf(-1.0f, fminf(32767.0f / 32768.0f, v)) * 32768.0f;
  return (int16_t)v;
}

static inline int16_t outSample(float s, int i, int n) {
  float g = engGainPrev + (engGain - engGainPrev) * ((float)(i + 1) / n);
  return mixOut(s * g + starterSample() + hornSample() + shiftSample() * (SHIFT_SOUND_LEVEL / MASTER_VOLUME));
}

static void useFallback() {
  cur.release();
  fallback = true;
  curIndex = -1;
  synth2.setPreset(0);               // diesel, with its built-in speaker EQ
  setEq.set(nullptr, 0);
  engineState.crankS = 1.1f;
  engineState.stopS = 1.4f;
  beeper.announce(1);
  Serial.println("set: fallback (diesel synth, synthesised starter and horn)");
}

// Loads set i; if it is broken, tries the following ones; with none left, the fallback.
static void selectSet(int i, bool announce = true, bool persist = true) {
  int n = (int)library.folders.size();
  namePlayer.stopNow();
  shiftPlayer.stopNow();
  wavStarter.setClip(nullptr);
  wavHorn.setClip(nullptr);
  for (int k = 0; k < n; k++) {
    int idx = (i + k) % n;
    String err;
    uint32_t t0 = millis();
    if (!library.load(idx, cur, err)) { Serial.printf("set %s: %s\n", library.folders[idx].c_str(), err.c_str()); continue; }
    fallback = false;
    curIndex = idx;
    if (cur.type == SoundSet::SYNTH && cur.synth == SoundSet::SYNTH2) { synth2.setPreset(cur.preset); synth2.setEq(nullptr, 0); }
    if (cur.type == SoundSet::SYNTH && cur.synth == SoundSet::SYNTH_PULSE) oldSynth = EngineSynth();
    setEq.set(cur.eq, cur.eqStages);
    wavStarter.setClip(&cur.startWav);
    wavHorn.setClip(&cur.hornWav);
    engineState.crankS = fmaxf(0.1f, (float)cur.startWav.len / AUDIO_RATE - START_TAIL_S);
    engineState.stopS = fmaxf(0.1f, cur.stopS);
    if (announce) namePlayer.play(&cur.nameWav);
    if (persist) SetLibrary::writeState(cur.folder);   // the page's Play and Demo do not change the start set
    String kind = cur.type == SoundSet::SAMPLE ? "sample" : "synth";
    if (cur.layerCount > 0) kind += ", " + String(cur.layerCount) + " layers";
    Serial.printf("set %s: \"%s\", %s, loaded in %lu ms, %u kB PSRAM free\n", cur.folder.c_str(), cur.name.c_str(),
                  kind.c_str(), (unsigned long)(millis() - t0), (unsigned)(ESP.getFreePsram() / 1024));
    return;
  }
  useFallback();
}

// ---------------------------------------------------------------- the demo (@demo from the web page)
// Time 0 = the name has been spoken. Ignition on (starter, the engine catches), then the throttle profile of
// engine_demo and tools/engine_lab.py (idle, full throttle through the gears, release, two blips, half throttle,
// idle) from 2.5 s, the horn at 17 s, ignition off at 21.5 s, then the wind-down.
static bool demoOn = false;
static float demoT = 0.0f;
static const float DEMO_PROFILE_AT = 2.5f, DEMO_HORN_FROM = 17.0f, DEMO_HORN_TO = 17.8f, DEMO_IGN_OFF = 21.5f;

static float demoProfile(float t) {
  static const float p[][2] = {{0,0},{2,0},{5,1.0f},{7,1.0f},{10,0},{11,0},{11.4f,0.8f},{11.9f,0},
                               {12.4f,0.8f},{12.9f,0},{14,0},{14.1f,0.5f},{16.5f,0.5f},{18,0},{20,0}};
  const int n = sizeof(p) / sizeof(p[0]);
  for (int i = 0; i + 1 < n; i++) {
    if (t >= p[i][0] && t <= p[i + 1][0]) {
      float dt = p[i + 1][0] - p[i][0];
      return dt > 0 ? p[i][1] + (p[i + 1][1] - p[i][1]) * (t - p[i][0]) / dt : p[i + 1][1];
    }
  }
  return 0.0f;
}

// One block of the demo: returns the throttle for the gearbox, as engineState.block() does.
static float demoStep(float dt) {
  if (!namePlayer.active()) demoT += dt;                 // starts after the name
  bool started = !namePlayer.active() || demoT > 0.0f;
  bool ign = started && demoT < DEMO_IGN_OFF;
  float throttle = demoT >= DEMO_PROFILE_AT ? demoProfile(demoT - DEMO_PROFILE_AT) : 0.0f;
  if (demoT >= DEMO_IGN_OFF) throttle = 0.0f;
  bool horn = demoT >= DEMO_HORN_FROM && demoT < DEMO_HORN_TO;
  synthHorn.set(horn);
  wavHorn.set(horn);
  float out = fallback ? engineState.block(true, ign, throttle > 0.05f, throttle, dt, gearbox.rpm, synthStarter)
                       : engineState.block(true, ign, throttle > 0.05f, throttle, dt, gearbox.rpm, wavStarter);
  if (demoT > DEMO_IGN_OFF + engineState.stopS + 0.5f) {
    demoOn = false;
    synthHorn.set(false);
    wavHorn.set(false);
    Serial.println("demo: done");
  }
  return out;
}

static bool bootPressed() {
  static bool last = true;
  static uint32_t changedMs = 0;
  static bool stable = true;
  bool now = digitalRead(PIN_BOOT_BUTTON);
  if (now != last) { last = now; changedMs = millis(); }
  if (now != stable && millis() - changedMs > 30) {
    stable = now;
    return !stable;
  }
  return false;
}

void setup() {
  usbLink.begin();
  Serial.begin(115200);
  Serial.println("cyberbrick_sound engine_sets " FW_FULL_VERSION ", built " FW_BUILD);
  statusLed.begin();
  pinMode(PIN_THROTTLE_IN, INPUT);
  pinMode(PIN_BOOT_BUTTON, INPUT_PULLUP);
#if RC_LINK_ENABLED
  rcLink.begin(PIN_THROTTLE_IN);
#endif
  attachInterrupt(digitalPinToInterrupt(PIN_THROTTLE_IN), onEdge, CHANGE);
  synthStarter.begin();
  synthHorn.begin();

  i2s_config_t cfg = {};
  cfg.mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX);
  cfg.sample_rate = AUDIO_RATE;
  cfg.bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT;
  cfg.channel_format = I2S_CHANNEL_FMT_RIGHT_LEFT;
  cfg.communication_format = I2S_COMM_FORMAT_STAND_I2S;
  cfg.intr_alloc_flags = ESP_INTR_FLAG_LEVEL1;
  cfg.dma_buf_count = 6;
  cfg.dma_buf_len = 256;
  cfg.tx_desc_auto_clear = true;
  i2s_pin_config_t pins = {};
  pins.mck_io_num = I2S_PIN_NO_CHANGE;
  pins.bck_io_num = PIN_I2S_BCLK;
  pins.ws_io_num = PIN_I2S_LRC;
  pins.data_out_num = PIN_I2S_DOUT;
  pins.data_in_num = I2S_PIN_NO_CHANGE;
  i2s_driver_install(I2S_NUM_0, &cfg, 0, nullptr);
  i2s_set_pin(I2S_NUM_0, &pins);

  Serial.printf("engine_sets: PSRAM %u kB\n", (unsigned)(ESP.getPsramSize() / 1024));
  if (!psramFound()) {
    Serial.println("sets: no PSRAM (an N8R8 Zero is needed)");
    useFallback();
    return;
  }
  if (!LittleFS.begin(true)) Serial.println("sets: the data partition cannot be mounted or formatted");
  if (library.scan() == 0) { useFallback(); return; }
  int i = library.find(SetLibrary::readState());
  selectSet(i < 0 ? 0 : i);
#if BLE_LINK_ENABLED
  // Bluetooth prototype: the name of the module in the advertising, a random PIN spoken with the digit clips. Only after
  // a real power-up: the restart that ends a session (esp_restart) leaves Bluetooth off.
  if (esp_reset_reason() == ESP_RST_SW) Serial.println("ble: off (restart after a Bluetooth session)");
  else {
  bleActive = true;
  for (int d = 0; d < 10; d++) { String err; loadWav("/voice/d" + String(d) + ".wav", digitClip[d], err); }
  { String err; loadWav("/voice/pin.wav", pinWordClip, err); }
  String nm = SetLink::moduleName(), adv = nm.length() ? "CBSound-" + nm : String("CBSound");
  bleUart.begin(adv.c_str());
  bleLink.attach(&bleUart);
  // only digits that sound different on the small speaker: 0 1 2 3 4 6 8 (no 5, 7, 9: five and nine, six and seven run together)
  { static const char ok[] = "0123468"; blePin = ""; for (int k = 0; k < 4; k++) blePin += ok[esp_random() % 7]; }
  bleLink.requireAuth(blePin);
  bleUart.advertise(true);
  pinNextMs = millis() + 6000;            // after the name of the set
  Serial.println("ble: advertising as " + adv + " for 180 s, PIN " + blePin + " (spoken by the module)");
  }
#endif
}

// What a finished session of the web page asks for: rescan and reload, play a set, stop, demo.
static void applyEnd(const SetLink::End& e) {
    if (e.ended && (e.changed || e.select.length()) && psramFound()) {
      String want = e.select.length() ? e.select : (fallback ? String() : cur.folder);
      if (library.scan() == 0) useFallback();
      else {
        int i = library.find(want);
        if (e.select.length() || i < 0) selectSet(i < 0 ? 0 : i, true, false);   // announced, not remembered
        else selectSet(i, false, false);                               // the current set again, with its new files
      }
    }
    if (e.ended && e.stop) {
      demoOn = false;
      namePlayer.stopNow();
      shiftPlayer.stopNow();
      wavStarter.stop();
      synthStarter.stop();
      synthHorn.set(false);
      wavHorn.set(false);
      engineState.silence();      // else the engine would idle on without a receiver
      Serial.println("stop (from the web page)");
    }
    if (e.ended && e.demo) {
      demoOn = true;
      demoT = 0.0f;
      Serial.println("demo: start");
    }
}

void loop() {
  static float pos = 0.0f, posLoaded = 0.0f, load = 0.0f, prevGain = 1.0f, plainRpm = 0.0f;
  static uint32_t lastPrint = 0;
  const int N = 128;
  int16_t buf[N * 2];

  bool talking = usbLink.poll(fallback ? String() : cur.folder);   // the web page is talking to the module: silent
#if BLE_LINK_ENABLED
  if (bleActive) {
    // before the PIN has been entered the link does not silence the engine: the spoken PIN would be cut into pieces
    const bool bleSession = bleLink.poll(fallback ? String() : cur.folder);
    talking = (bleSession && bleLink.isAuthed()) || talking;
    if (bleUart.isAdvertising() && millis() > bleWindowMs) { bleUart.advertise(false); bleActive = false; Serial.println("ble: nobody came in the 3 minutes, advertising off"); }
  }
#endif
  if (usbLink.restartDue()
#if BLE_LINK_ENABLED
      || bleLink.restartDue()
#endif
  ) {                                      // a firmware update has been written (@fwend)
    Serial.println("firmware updated: restarting");
    delay(100);
    ESP.restart();
  }
  if (talking) {
    vTaskDelay(1);
    return;
  }
  applyEnd(usbLink.takeEnd());
#if BLE_LINK_ENABLED
  if (bleRestartAt && millis() > bleRestartAt) ESP.restart();
  if (bleActive) applyEnd(bleLink.takeEnd());
  if (bleActive) {
    // the PIN: once after power-up, and again (every 40 s) only while a page is connected and has not entered it
    const bool needPin = (bleUart.isAdvertising() && !pinSpokenAtStart) || (bleUart.isConnected() && !bleLink.isAuthed());
    if (needPin && pinQueue.empty() && millis() > pinNextMs && !namePlayer.active() && !demoOn && !bleLink.isLocked()) {
      pinQueue.push_back(-1);                                   // "Pin."
      for (char c : blePin) pinQueue.push_back(c - '0');        // the digits in a row
      pinQueue.push_back(-2);                                   // a pause
      for (char c : blePin) pinQueue.push_back(c - '0');        // and once more: a digit that is missed the first time is heard again
      pinSpokenAtStart = true;
      Serial.println("ble: speaking the PIN");
    }
    if (!pinQueue.empty() && !namePlayer.active() && millis() >= pinGapUntil) {
      int d = pinQueue.front();
      pinQueue.erase(pinQueue.begin());
      if (d == -2) pinGapUntil = millis() + 700;
      else {
        const Clip& cl = d == -1 ? pinWordClip : digitClip[d];
        if (cl.ok()) {
          namePlayer.play(&cl);
          pinGapUntil = millis() + (uint32_t)(cl.len * 1000ULL / AUDIO_RATE) + 160;   // the clip and a short gap
        }
      }
      if (pinQueue.empty()) { pinNextMs = millis() + 40000; Serial.println("ble: PIN spoken"); }
    }
    bool c = bleUart.isConnected();
    if (c && !bleWasConnected) pinNextMs = millis() + 500;      // a page has connected: the PIN now
    if (bleWasConnected && !c) {          // the page left
      bleLink.resetAuth(); pinQueue.clear();
      if (bleLink.changedSinceStart()) {  // something was written, deleted or renamed: a restart loads it, Bluetooth stays off
        bleUart.advertise(false); bleActive = false; bleRestartAt = millis() + 1500;
        Serial.println("ble: the page left after a change, restarting in 1.5 s (Bluetooth stays off after it)");
      } else if (millis() < bleWindowMs) {   // nothing changed: the page may connect again until the 3 minutes are over
        bleUart.advertise(true);
        Serial.println("ble: the page left, nothing changed, advertising goes on until the window is over");
      } else { bleUart.advertise(false); bleActive = false; Serial.println("ble: the page left, the window is over, advertising off"); }
    }
    bleWasConnected = c;
    if (bleLink.isLocked() && bleUart.isAdvertising()) { bleUart.advertise(false); Serial.println("ble: locked after 3 wrong PINs"); }
  }
#endif
  if (bootPressed()) {
    demoOn = false;
    if (!library.folders.empty()) selectSet(fallback ? 0 : curIndex + 1);
  }
#if RC_LINK_ENABLED
  rcLink.poll();
#endif

  if (demoOn && dataActive()) { demoOn = false; Serial.println("demo: ended by the receiver"); }
  float target = readThrottle();
  statusLed.update(signalPresent() || demoOn, target);
  const float dt = (float)N / AUDIO_RATE;
  if (demoOn) {
    target = demoStep(dt);
  } else {
#if RC_LINK_ENABLED
  {
    bool data = dataActive();
    int ignDev = (int)rcLink.get(RcLink::L1) - RC_IGNITION_MID;
    bool ignNow = ignDev > RC_IGNITION_BAND || ignDev < -RC_IGNITION_BAND;
    static bool ignition = false, ignCand = false;
    static uint32_t ignSinceMs = 0;
    if (ignNow != ignCand) { ignCand = ignNow; ignSinceMs = millis(); }
    if (ignCand != ignition && millis() - ignSinceMs >= RC_IGNITION_SETTLE_MS) ignition = ignCand;
    int hornDev = (int)rcLink.get(RcLink::R1) - RC_HORN_REST;
    bool hornOn = data && (hornDev > RC_HORN_THRESHOLD || hornDev < -RC_HORN_THRESHOLD);
    synthHorn.set(hornOn);
    wavHorn.set(hornOn);
    bool alive = rcLink.alive(RC_STATE_HOLD_MS);
    if (fallback) target = engineState.block(alive, ignition, target > 0.05f, target, dt, gearbox.rpm, synthStarter);
    else target = engineState.block(alive, ignition, target > 0.05f, target, dt, gearbox.rpm, wavStarter);
  }
#else
  target = engineState.block(false, false, true, target, dt, gearbox.rpm, wavStarter);
#endif
  }
  {
    static int lastGear = 0;
    if (fallback || cur.gearbox) {
      gearbox.update(reversing ? target * (0.98f / GEAR_COUNT) : target, dt);
      if (gearbox.gear > lastGear) triggerShift();
      lastGear = gearbox.gear;
    } else {                         // "gearbox": false: the rpm follows the throttle, no shifts
      plainRpm += (target - plainRpm) * fminf(1.0f, dt * 6.0f);
      gearbox.rpm = plainRpm;
      gearbox.speed = target;
      gearbox.gain = 1.0f;
      gearbox.gear = 0;
      lastGear = 0;
    }
  }
  engineState.apply(gearbox.rpm, gearbox.gain);
  engGainPrev = engGain;
  engGain = engineState.gain;
  const float rpm = gearbox.rpm, gain = gearbox.gain;
  const float level = fallback ? 1.0f : cur.level;

  if (!fallback && cur.type == SoundSet::SAMPLE && cur.layerCount > 0) {
    // layered set (docs/layers-design.md): at most two neighbouring layers, each played at the rate that brings it to
    // the pitch of the sets without layers, crossfaded with equal power; no loaded blend in this version
    static float layerPos[LAYERS_MAX] = {0};
    const float r = fmaxf(0.1f, cur.rateLo + (cur.rateHi - cur.rateLo) * rpm);
    const LayerMix m = layerMix(cur.layerRatio, cur.layerCount, r, cur.xfade);
    const float vol = 0.55f + 0.45f * rpm;
    for (int i = 0; i < N; i++) {
      float s = m.wa * playLoop(cur.layerClip[m.a], layerPos[m.a], m.ra);
      if (m.b >= 0) s += m.wb * playLoop(cur.layerClip[m.b], layerPos[m.b], m.rb);
      float g = prevGain + (gain - prevGain) * ((float)(i + 1) / N);
      s = setEq.run(s * vol * g * (1.0f / 32768.0f)) * level;
      buf[2 * i] = buf[2 * i + 1] = outSample(s, i, N);
    }
  } else if (!fallback && cur.type == SoundSet::SAMPLE) {
    float rate = fmaxf(0.1f, cur.rateLo + (cur.rateHi - cur.rateLo) * rpm);
    float vol = 0.55f + 0.45f * rpm;
    load += (target - load) * 0.04f;
    const float wIdle = cosf(load * 1.5707963f), wLoaded = sinf(load * 1.5707963f);
    for (int i = 0; i < N; i++) {
      float s = wIdle * playLoop(cur.idleWav, pos, rate)
              + wLoaded * cur.loadedGain * playLoop(cur.loadedWav, posLoaded, rate * cur.loadedRateScale);
      float g = prevGain + (gain - prevGain) * ((float)(i + 1) / N);
      s = setEq.run(s * vol * g * (1.0f / 32768.0f)) * level;
      buf[2 * i] = buf[2 * i + 1] = outSample(s, i, N);
    }
  } else if (!fallback && cur.synth == SoundSet::SYNTH_PULSE) {
    oldSynth.block(target);
    for (int i = 0; i < N; i++) buf[2 * i] = buf[2 * i + 1] = outSample(setEq.run(oldSynth.sample()) * level, i, N);
  } else {
    synth2.block(target, gearbox);
    for (int i = 0; i < N; i++) buf[2 * i] = buf[2 * i + 1] = outSample(setEq.run(synth2.sample()) * level, i, N);
  }
  prevGain = gain;
  size_t written;
  i2s_write(I2S_NUM_0, buf, sizeof(buf), &written, portMAX_DELAY);

  if (millis() - lastPrint > 500) {
    lastPrint = millis();
    static const char* const ST[] = {"OFF", "CRANK", "RUN", "STOP"};
    Serial.printf("%s  set %s  %s  throttle %.2f %s  rpm %.2f  gear %d  frames %lu, %lu bad\n", ST[engineState.state],
                  fallback ? "fallback" : cur.folder.c_str(), dataActive() ? "DATA " : "PULSE", target,
                  reversing ? "REV" : "FWD", rpm, gearbox.gear + 1, (unsigned long)rcLink.good,
                  (unsigned long)rcLink.bad);
  }
}
