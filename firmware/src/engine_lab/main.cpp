// Engine sound lab: all engine-sound candidates in one firmware, switched with the BOOT button on the Zero.
// The numbers match the preview files rendered by tools/engine_lab.py:
//   1 truck       today's `engine_truck` (CC0 truck loops)
//   2 truck_eq    the same through the speaker EQ
//   3 pulse_old   today's `engine_pulse` synth (preset a_diesel6)
//   4 diesel      new speaker-tuned synth (include/engine_synth2.h)
//   5 petrol4     new, petrol 4-cylinder
//   6 v8          new, cross-plane V8
//   7 v12         new, V12 (six even firings per revolution)
// After every switch the module beeps the number (1..7) of the sound now playing. All sounds share the throttle
// input and the virtual gearbox (except 3, which smooths the RPM itself, as in its own firmware).
// The BOOT button (GPIO0) only matters at power-up/reset; read later it is an ordinary button.
// Throttle: from the receiver's channel data on GPIO1 while frames arrive (include/rc_link.h, the app Code snippet
// docs/cyberbrick-code/uart_forward.py), otherwise from the servo pulse on the same pin.
//
// With -DENGINE_LAB_DEMO=1 (env engine_demo) no receiver is needed: the firmware announces each sound in turn and
// drives it with the same 20 s throttle profile as the previews (idle, full throttle through the gears, release,
// blips, half throttle, idle), then goes on to the next one, forever. BOOT skips to the next sound.
#include <Arduino.h>
#include <math.h>
#include "driver/i2s.h"
#include "config.h"
#include "status_led.h"
#include "gearbox.h"
#include "gear_beep.h"
#include "engine_truck.h"          // CC0, see assets/samples/LICENSE-SAMPLES.md
#include "engine_truck_loaded.h"   // CC0
#include "engine_synth.h"          // old grain synth (engine_pulse)
#include "engine_synth2.h"         // new speaker-tuned synth
#include "rc_link.h"               // channel data over a wire from the receiver Code snippet
#include "engine_events.h"         // start, stop and horn (from the channel data)
#include "shift_sound.h"           // CC0 gear-shift sound (tools/make_shift_sound.py)

// Spoken announcement of the sound number and name, if the locally generated header exists
// (tools/make_voice_prompts.ps1, Piper text-to-speech, English voice en_US-ljspeech); otherwise beeps.
#if __has_include("voice_prompts.h")
#include "voice_prompts.h"
#define HAVE_VOICE 1
#else
#define HAVE_VOICE 0
#endif

#define PIN_BOOT_BUTTON 0
static const int SOUNDS = 7;
static const char* const SOUND_NAMES[SOUNDS] = {"truck", "truck_eq", "pulse_old", "diesel", "petrol4", "v8", "v12"};

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

// Signed -1..1: the sign is the stick direction (see RC_REVERSE_SIGN).
static float readPulseThrottle() {
  if (millis() - lastEdgeMs > PULSE_TIMEOUT_MS) return 0.0f;
  int d = (int)widthUs - PULSE_CENTER_US;
  int a = d < 0 ? -d : d;
  if (a < PULSE_DEADBAND_US) return 0.0f;
  float t = (float)(a - PULSE_DEADBAND_US) / (float)(PULSE_RANGE_US - PULSE_DEADBAND_US);
  if (t > 1.0f) t = 1.0f;
  return d < 0 ? -t : t;
}

static bool pulsePresent() {
  return lastEdgeMs != 0 && millis() - lastEdgeMs <= PULSE_TIMEOUT_MS;
}

// Throttle 0..1 (absolute deflection, both directions): from the receiver's channel data while frames arrive,
// otherwise from the servo pulse. Both come in on the same pin (include/rc_link.h).
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

// Reverse: the stick pushed the reverse way. The direction is kept while the stick is at rest (the truck may still
// roll) and changes only when the stick is pushed past RC_REVERSE_THRESHOLD the other way.
static bool reversing = false;

static float readThrottle() {
  float s = readThrottleSigned() * RC_REVERSE_SIGN;
  if (s < -RC_REVERSE_THRESHOLD) reversing = true;
  else if (s > RC_REVERSE_THRESHOLD) reversing = false;
  return s < 0 ? -s : s;
}

static bool signalPresent() { return dataActive() || pulsePresent(); }

static inline float playLoop(const int16_t* data, int len, float& pos, float rate) {
  int idx = (int)pos;
  float frac = pos - idx;
  int next = idx + 1;
  if (next >= len) next = 0;
  float s = data[idx] + (data[next] - data[idx]) * frac;
  pos += rate;
  if (pos >= len) pos -= len;
  return s;
}

static StatusLed statusLed;
static Gearbox gearbox;
static GearBeeper beeper((float)AUDIO_RATE);
static EngineSynth oldSynth;
static EngineSynth2 synth2;
static SpeakerEq truckEq;
static int sound = 0;
static StarterSound starter;
static HornSound horn;
static EngineState engineState;
static float engGain = 1.0f, engGainPrev = 1.0f;   // engine level from engineState, ramped over each block


#ifndef ENGINE_LAB_DEMO
#define ENGINE_LAB_DEMO 0
#endif
#if ENGINE_LAB_DEMO
static const float DEMO_SECONDS = 20.0f;
static uint32_t demoSamples = 0;   // samples played of the profile of the current sound
// Same profile as tools/engine_lab.py PROFILE: (time s, throttle 0..1)
static float demoThrottle(float t) {
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
#endif

// Plays one spoken prompt; the engine is turned down while it speaks (duck()).
class VoicePlayer {
 public:
  void say(int i) {
#if HAVE_VOICE
    if (i >= 0 && i < VOICE_PROMPTS) { clip = i; pos = 0; }
#endif
  }
  float next() {
#if HAVE_VOICE
    if (clip < 0) return 0.0f;
    float s = VOICE_DATA[clip][pos] * (1.0f / 32768.0f);
    if (++pos >= VOICE_LEN[clip]) clip = -1;
    return s;
#else
    return 0.0f;
#endif
  }
  bool speaking() const { return clip >= 0; }
  // Engine gain factor, smoothed: 0.25 while speaking, 1 otherwise.
  float duck() {
    g += ((clip >= 0 ? 0.25f : 1.0f) - g) * 0.002f;
    return g;
  }
 private:
  int clip = -1;
  uint32_t pos = 0;
  float g = 1.0f;
};
static VoicePlayer voice;

// Gear-shift sound: a short CC0 recording (include/shift_sound.h), started on every upshift, during the torque cut of
// the virtual gearbox. With every engine sound (owner's choice, 2026-11-08; first tried on the V8 only).
class ShiftPlayer {
 public:
  void trigger() { pos = 0; }
  float next() {
    if (pos < 0) return 0.0f;
    float s = SHIFT_SOUND[pos] * (1.0f / 32768.0f);
    if (++pos >= SHIFT_SOUND_LEN) pos = -1;
    return s;
  }
 private:
  int pos = -1;
};
static ShiftPlayer shift;
static bool shiftSoundFor(int) { return true; }   // all sounds

// Voice (or beeps) mixed over the engine sample s (both in -1..1 before MASTER_VOLUME is applied to s).
static inline int16_t mixOut(float s) {
  float v = s * voice.duck() * MASTER_VOLUME + voice.next() * 0.9f + beeper.next();
  v = fmaxf(-1.0f, fminf(32767.0f / 32768.0f, v)) * 32768.0f;
  return (int16_t)v;
}

// Engine sample s with the engine level and the start/stop/horn sounds, then voice and beeps.
static inline int16_t outSample(float s, int i, int n) {
  float g = engGainPrev + (engGain - engGainPrev) * ((float)(i + 1) / n);
  return mixOut(s * g + starter.sample() + horn.sample() + shift.next() * (SHIFT_SOUND_LEVEL / MASTER_VOLUME));
}

static void selectSound(int s) {
  sound = s;
  if (sound >= 3) synth2.setPreset(sound - 3);
  truckEq = SpeakerEq();
#if ENGINE_LAB_DEMO
  gearbox = Gearbox();        // every sound starts from rest
  oldSynth = EngineSynth();
  demoSamples = 0;
#endif
#if HAVE_VOICE
  if (sound < VOICE_PROMPTS) voice.say(sound);
  else beeper.announce(sound + 1);   // no spoken prompt for this sound yet (regenerate voice_prompts.h)
#else
  beeper.announce(sound + 1);
#endif
  Serial.printf("sound %d: %s\n", sound + 1, SOUND_NAMES[sound]);
}

// Debounced press of the BOOT button (active low); true once per press.
static bool bootPressed() {
  static bool last = true;
  static uint32_t changedMs = 0;
  static bool stable = true;
  bool now = digitalRead(PIN_BOOT_BUTTON);
  if (now != last) { last = now; changedMs = millis(); }
  if (now != stable && millis() - changedMs > 30) {
    stable = now;
    return !stable;   // went low = pressed
  }
  return false;
}

void setup() {
  Serial.begin(115200);
  statusLed.begin();
  pinMode(PIN_THROTTLE_IN, INPUT);
  pinMode(PIN_BOOT_BUTTON, INPUT_PULLUP);
#if RC_LINK_ENABLED
  rcLink.begin(PIN_THROTTLE_IN);
#endif
  attachInterrupt(digitalPinToInterrupt(PIN_THROTTLE_IN), onEdge, CHANGE);
  starter.begin();
  horn.begin();

  i2s_config_t cfg = {};
  cfg.mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX);
  cfg.sample_rate = AUDIO_RATE;
  cfg.bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT;
  cfg.channel_format = I2S_CHANNEL_FMT_RIGHT_LEFT;  // same sample on both channels
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
#if ENGINE_LAB_DEMO
  Serial.println("engine_demo: plays all sounds in turn, BOOT skips to the next");
#else
  Serial.println("engine_lab: BOOT switches the sound (1..7)");
#endif
  selectSound(0);
}

void loop() {
  static float pos = 0.0f, posLoaded = 0.0f, load = 0.0f, prevGain = 1.0f;
  static uint32_t lastPrint = 0;
  const int N = 128;
  int16_t buf[N * 2];  // interleaved L,R

  if (bootPressed()) selectSound((sound + 1) % SOUNDS);
#if RC_LINK_ENABLED
  rcLink.poll();
#endif

#if ENGINE_LAB_DEMO
  float target = 0.0f;
  if (!voice.speaking() && !beeper.active()) {   // the profile starts after the announcement
    float t = (float)demoSamples / AUDIO_RATE;
    if (t >= DEMO_SECONDS) selectSound((sound + 1) % SOUNDS);
    else { target = demoThrottle(t); demoSamples += N; }
  }
  statusLed.update(true, target);
#else
  float target = readThrottle();
  statusLed.update(signalPresent(), target);
#endif
  const float dt = (float)N / AUDIO_RATE;
#if RC_LINK_ENABLED && !ENGINE_LAB_DEMO
  {
    bool data = dataActive();
    int ignDev = (int)rcLink.get(RcLink::L1) - RC_IGNITION_MID;
    bool ignNow = ignDev > RC_IGNITION_BAND || ignDev < -RC_IGNITION_BAND;   // end positions = ON, middle = OFF
    static bool ignition = false, ignCand = false;
    static uint32_t ignSinceMs = 0;
    if (ignNow != ignCand) { ignCand = ignNow; ignSinceMs = millis(); }
    if (ignCand != ignition && millis() - ignSinceMs >= RC_IGNITION_SETTLE_MS) ignition = ignCand;
    int hornDev = (int)rcLink.get(RcLink::R1) - RC_HORN_REST;
    horn.set(data && (hornDev > RC_HORN_THRESHOLD || hornDev < -RC_HORN_THRESHOLD));
    target = engineState.block(rcLink.alive(RC_STATE_HOLD_MS), ignition, target > 0.05f, target, dt, gearbox.rpm,
                               starter);
  }
#else
  target = engineState.block(false, false, true, target, dt, gearbox.rpm, starter);   // demo: always running
#endif
  {
    static int lastGear = 0;
    // reversing: one gear only, so no upshift (and no shift sound); the rpm still spans the whole range of gear 1
    gearbox.update(reversing ? target * (0.98f / GEAR_COUNT) : target, dt);
    if (gearbox.gear > lastGear && shiftSoundFor(sound)) shift.trigger();
    lastGear = gearbox.gear;
  }
  engineState.apply(gearbox.rpm, gearbox.gain);
  engGainPrev = engGain;
  engGain = engineState.gain;
  const float rpm = gearbox.rpm, gain = gearbox.gain;

  if (sound <= 1) {
    float rate = 1.0f + 2.0f * rpm;
    float vol = 0.55f + 0.45f * rpm;
    load += (target - load) * 0.04f;
    const float wIdle = cosf(load * 1.5707963f), wLoaded = sinf(load * 1.5707963f);
    for (int i = 0; i < N; i++) {
      float s = wIdle * playLoop(ENGINE_SAMPLE, ENGINE_SAMPLE_LEN, pos, rate)
              + wLoaded * LOADED_GAIN * playLoop(ENGINE_LOADED, ENGINE_LOADED_LEN, posLoaded, rate * LOADED_RATE_SCALE);
      float g = prevGain + (gain - prevGain) * ((float)(i + 1) / N);
      s = s * vol * g * (1.0f / 32768.0f);
      if (sound == 1) s = truckEq.run(s) * 1.6f;   // EQ removes energy; 1.6 brings the level back
      buf[2 * i] = buf[2 * i + 1] = outSample(s, i, N);
    }
  } else if (sound == 2) {
    oldSynth.block(target);
    for (int i = 0; i < N; i++) buf[2 * i] = buf[2 * i + 1] = outSample(oldSynth.sample(), i, N);
  } else {
    synth2.block(target, gearbox);
    for (int i = 0; i < N; i++) buf[2 * i] = buf[2 * i + 1] = outSample(synth2.sample(), i, N);
  }
  prevGain = gain;
  size_t written;
  i2s_write(I2S_NUM_0, buf, sizeof(buf), &written, portMAX_DELAY);

  if (millis() - lastPrint > 500) {
    lastPrint = millis();
    static const char* const ST[] = {"OFF", "CRANK", "RUN", "STOP"};
    Serial.printf("%s L1 %u R1 %u  ", ST[engineState.state], rcLink.get(RcLink::L1), rcLink.get(RcLink::R1));
    Serial.printf("sound %d %s  %s  L3 %u  pulse %lu us  throttle %.2f %s  rpm %.2f  gear %d  frames %lu, %lu bad\n",
                  sound + 1, SOUND_NAMES[sound], dataActive() ? "DATA " : "PULSE", rcLink.get(RcLink::L3),
                  (unsigned long)widthUs, target, reversing ? "REV" : "FWD", rpm, gearbox.gear + 1,
                  (unsigned long)rcLink.good,
                  (unsigned long)rcLink.bad);
  }
}
