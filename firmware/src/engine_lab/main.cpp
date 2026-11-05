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

static float readThrottle() {
  if (millis() - lastEdgeMs > PULSE_TIMEOUT_MS) return 0.0f;
  int d = (int)widthUs - PULSE_CENTER_US;
  if (d < 0) d = -d;
  if (d < PULSE_DEADBAND_US) return 0.0f;
  float t = (float)(d - PULSE_DEADBAND_US) / (float)(PULSE_RANGE_US - PULSE_DEADBAND_US);
  return t > 1.0f ? 1.0f : t;
}

static bool signalPresent() {
  return lastEdgeMs != 0 && millis() - lastEdgeMs <= PULSE_TIMEOUT_MS;
}

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

// Voice (or beeps) mixed over the engine sample s (both in -1..1 before MASTER_VOLUME is applied to s).
static inline int16_t mixOut(float s) {
  float v = s * voice.duck() * MASTER_VOLUME + voice.next() * 0.9f + beeper.next();
  v = fmaxf(-1.0f, fminf(32767.0f / 32768.0f, v)) * 32768.0f;
  return (int16_t)v;
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
  attachInterrupt(digitalPinToInterrupt(PIN_THROTTLE_IN), onEdge, CHANGE);

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
  gearbox.update(target, (float)N / AUDIO_RATE);
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
      buf[2 * i] = buf[2 * i + 1] = mixOut(s);
    }
  } else if (sound == 2) {
    oldSynth.block(target);
    for (int i = 0; i < N; i++) buf[2 * i] = buf[2 * i + 1] = mixOut(oldSynth.sample());
  } else {
    synth2.block(target, gearbox);
    for (int i = 0; i < N; i++) buf[2 * i] = buf[2 * i + 1] = mixOut(synth2.sample());
  }
  prevGain = gain;
  size_t written;
  i2s_write(I2S_NUM_0, buf, sizeof(buf), &written, portMAX_DELAY);

  if (millis() - lastPrint > 500) {
    lastPrint = millis();
    Serial.printf("sound %d %s  pulse %lu us  throttle %.2f  rpm %.2f  gear %d\n", sound + 1, SOUND_NAMES[sound],
                  (unsigned long)widthUs, target, rpm, gearbox.gear + 1);
  }
}
