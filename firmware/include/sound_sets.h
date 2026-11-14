#pragma once
// Sound sets in the data partition (LittleFS), for the `engine_sets` firmware. Design: docs/user-sounds.md.
//
//   /sets/NN_description/   NN = index 01..99 (order of the BOOT button), the description is ignored
//     set.json              parameters (name, type, synth/preset or rate..., eq, level, stop_s, gearbox)
//     name.wav start.wav horn.wav shift.wav          every set
//     idle.wav loaded.wav                            sample sets only
//   /state.json             {"set": "<folder>"}: the set chosen last
//
// All WAVs PCM 22 050 Hz, 16 bit, mono. A set is loaded completely into PSRAM when it is chosen (about 0.2-0.6 MB),
// so playback never waits for the flash.
#include <Arduino.h>
#include <LittleFS.h>
#include <vector>
#include <algorithm>
#include "config.h"
#include "engine_lab_data.h"   // LAB_PRESET_NAMES

// ---------------------------------------------------------------- a small JSON reader
// Enough for set.json and state.json: objects, arrays, numbers, strings (no \u escapes), true, false, null.
// Parses the whole text into a tree of values; get("key") on an object, at(i) on an array.
class Json {
 public:
  enum Kind { NUL, BOOL, NUM, STR, ARR, OBJ };
  Kind kind = NUL;
  bool b = false;
  float num = 0.0f;
  String str;
  std::vector<String> keys;
  std::vector<Json> items;

  static bool parse(const String& text, Json& out, String& err) {
    const char* p = text.c_str();
    if (!value(p, out, err)) return false;
    ws(p);
    if (*p) { err = "text after the end"; return false; }
    return true;
  }
  const Json* get(const char* key) const {
    if (kind != OBJ) return nullptr;
    for (size_t i = 0; i < keys.size(); i++) if (keys[i] == key) return &items[i];
    return nullptr;
  }
  size_t size() const { return kind == ARR ? items.size() : 0; }
  const Json& at(size_t i) const { return items[i]; }
  // Typed reads of a member, with a default when it is missing or of another kind.
  float numOr(const char* key, float def) const { const Json* v = get(key); return v && v->kind == NUM ? v->num : def; }
  bool boolOr(const char* key, bool def) const { const Json* v = get(key); return v && v->kind == BOOL ? v->b : def; }
  String strOr(const char* key, const String& def) const { const Json* v = get(key); return v && v->kind == STR ? v->str : def; }

 private:
  static void ws(const char*& p) { while (*p == ' ' || *p == '\n' || *p == '\r' || *p == '\t') p++; }
  static bool value(const char*& p, Json& v, String& err) {
    ws(p);
    if (*p == '{') {
      v.kind = OBJ; p++; ws(p);
      if (*p == '}') { p++; return true; }
      while (true) {
        ws(p);
        Json k;
        if (*p != '"') { err = "key expected"; return false; }
        if (!value(p, k, err)) return false;
        ws(p);
        if (*p != ':') { err = "':' expected"; return false; }
        p++;
        Json item;
        if (!value(p, item, err)) return false;
        v.keys.push_back(k.str);
        v.items.push_back(item);
        ws(p);
        if (*p == ',') { p++; continue; }
        if (*p == '}') { p++; return true; }
        err = "',' or '}' expected"; return false;
      }
    }
    if (*p == '[') {
      v.kind = ARR; p++; ws(p);
      if (*p == ']') { p++; return true; }
      while (true) {
        Json item;
        if (!value(p, item, err)) return false;
        v.items.push_back(item);
        ws(p);
        if (*p == ',') { p++; continue; }
        if (*p == ']') { p++; return true; }
        err = "',' or ']' expected"; return false;
      }
    }
    if (*p == '"') {
      v.kind = STR; p++;
      while (*p && *p != '"') {
        if (*p == '\\' && p[1]) {
          p++;
          v.str += *p == 'n' ? '\n' : *p == 't' ? '\t' : *p;
          p++;
        } else {
          v.str += *p++;
        }
      }
      if (*p != '"') { err = "unterminated string"; return false; }
      p++;
      return true;
    }
    if (!strncmp(p, "true", 4)) { v.kind = BOOL; v.b = true; p += 4; return true; }
    if (!strncmp(p, "false", 5)) { v.kind = BOOL; v.b = false; p += 5; return true; }
    if (!strncmp(p, "null", 4)) { v.kind = NUL; p += 4; return true; }
    char* end;
    double d = strtod(p, &end);
    if (end == p) { err = String("unexpected '") + *p + "'"; return false; }
    v.kind = NUM; v.num = (float)d; p = end;
    return true;
  }
};

static bool readJsonFile(const String& path, Json& j, String& err) {
  File f = LittleFS.open(path, "r");
  if (!f) { err = path + ": missing"; return false; }
  String text = f.readString();
  f.close();
  if (!Json::parse(text, j, err)) { err = path + ": " + err; return false; }
  if (j.kind != Json::OBJ) { err = path + ": not an object"; return false; }
  return true;
}

struct Clip {
  int16_t* data = nullptr;
  uint32_t len = 0;
  bool ok() const { return data && len; }
  void release() { if (data) free(data); data = nullptr; len = 0; }
};

// Reads a PCM WAV (22 050 Hz, 16 bit, mono) into PSRAM. On failure err says why.
static bool loadWav(const String& path, Clip& clip, String& err) {
  File f = LittleFS.open(path, "r");
  if (!f) { err = path + ": missing"; return false; }
  uint8_t h[12];
  if (f.read(h, 12) != 12 || memcmp(h, "RIFF", 4) || memcmp(h + 8, "WAVE", 4)) { err = path + ": not a WAV"; return false; }
  bool fmtOk = false;
  while (f.available() >= 8) {
    uint8_t c[8];
    f.read(c, 8);
    uint32_t size = c[4] | (c[5] << 8) | (c[6] << 16) | ((uint32_t)c[7] << 24);
    if (!memcmp(c, "fmt ", 4)) {
      uint8_t fm[16];
      if (size < 16 || f.read(fm, 16) != 16) { err = path + ": bad fmt"; return false; }
      uint16_t format = fm[0] | (fm[1] << 8), ch = fm[2] | (fm[3] << 8), bits = fm[14] | (fm[15] << 8);
      uint32_t rate = fm[4] | (fm[5] << 8) | (fm[6] << 16) | ((uint32_t)fm[7] << 24);
      if (format != 1 || ch != 1 || bits != 16 || rate != AUDIO_RATE) {
        err = path + ": must be PCM 22050 Hz, 16 bit, mono";
        return false;
      }
      fmtOk = true;
      f.seek(f.position() + size - 16 + (size & 1));
    } else if (!memcmp(c, "data", 4)) {
      if (!fmtOk) { err = path + ": data before fmt"; return false; }
      uint32_t n = size / 2;
      if (n == 0) { err = path + ": empty"; return false; }
      int16_t* d = (int16_t*)ps_malloc(n * 2);
      if (!d) { err = path + ": out of memory"; return false; }
      if (f.read((uint8_t*)d, n * 2) != n * 2) { free(d); err = path + ": short read"; return false; }
      clip.release();
      clip.data = d;
      clip.len = n;
      return true;
    } else {
      f.seek(f.position() + size + (size & 1));
    }
  }
  err = path + ": no data chunk";
  return false;
}

struct SoundSet {
  enum Type { SAMPLE, SYNTH } type = SAMPLE;
  enum Synth { SYNTH_PULSE, SYNTH2 } synth = SYNTH2;
  String folder, name;
  int preset = 0;                       // synth2 preset index (LAB_PRESET_NAMES)
  float eq[8][5];
  int eqStages = 0;
  float level = 1.0f, stopS = 1.4f;
  float rateLo = 1.0f, rateHi = 3.0f, loadedRateScale = LOADED_RATE_SCALE, loadedGain = LOADED_GAIN;
  bool gearbox = true;
  Clip nameWav, startWav, hornWav, shiftWav, idleWav, loadedWav;

  void release() {
    nameWav.release(); startWav.release(); hornWav.release(); shiftWav.release(); idleWav.release();
    loadedWav.release();
  }
};

class SetLibrary {
 public:
  std::vector<String> folders;          // sorted, one per index

  // Mounts the file system and lists /sets. Returns the number of sets found.
  int scan() {
    folders.clear();
    if (!LittleFS.begin(false)) { Serial.println("sets: no file system in the data partition (pio run -t uploadfs)"); return 0; }
    File root = LittleFS.open("/sets");
    if (!root || !root.isDirectory()) { Serial.println("sets: no /sets folder"); return 0; }
    std::vector<String> all;
    for (File f = root.openNextFile(); f; f = root.openNextFile()) {
      String n = baseName(f.name());
      if (!f.isDirectory()) continue;
      if (n.length() < 2 || !isDigit(n[0]) || !isDigit(n[1])) { Serial.printf("sets: %s skipped (no index)\n", n.c_str()); continue; }
      all.push_back(n);
    }
    std::sort(all.begin(), all.end(), [](const String& a, const String& b) { return a < b; });
    for (const String& n : all) {
      if (!folders.empty() && folders.back().substring(0, 2) == n.substring(0, 2)) {
        Serial.printf("sets: %s skipped (index %s used by %s)\n", n.c_str(), n.substring(0, 2).c_str(), folders.back().c_str());
        continue;
      }
      folders.push_back(n);
    }
    Serial.printf("sets: %d found\n", (int)folders.size());
    return (int)folders.size();
  }

  int find(const String& folder) const {
    for (size_t i = 0; i < folders.size(); i++) if (folders[i] == folder) return (int)i;
    return -1;
  }

  // Loads set i completely (parameters and WAVs). On failure the set is released and err says why.
  bool load(int i, SoundSet& s, String& err) {
    s.release();
    s = SoundSet();
    s.folder = folders[i];
    String dir = "/sets/" + s.folder + "/";
    Json j;
    if (!readJsonFile(dir + "set.json", j, err)) return false;
    s.name = j.strOr("name", s.folder);
    String type = j.strOr("type", "sample");
    if (type == "synth") {
      s.type = SoundSet::SYNTH;
      String synth = j.strOr("synth", "synth2");
      if (synth == "pulse") s.synth = SoundSet::SYNTH_PULSE;
      else if (synth == "synth2") {
        s.synth = SoundSet::SYNTH2;
        String p = j.strOr("preset", "diesel");
        s.preset = -1;
        for (int k = 0; k < LAB_PRESETS; k++) if (p == LAB_PRESET_NAMES[k]) s.preset = k;
        if (s.preset < 0) { err = dir + "set.json: unknown preset " + p; return false; }
      } else { err = dir + "set.json: unknown synth " + synth; return false; }
    } else if (type != "sample") { err = dir + "set.json: unknown type " + type; return false; }
    if (const Json* eq = j.get("eq")) {
      for (size_t k = 0; k < eq->size(); k++) {
        const Json& st = eq->at(k);
        if (s.eqStages >= 8 || st.size() != 5) { err = dir + "set.json: eq must be up to 8 stages of 5 numbers"; return false; }
        for (int m = 0; m < 5; m++) s.eq[s.eqStages][m] = st.at(m).num;
        s.eqStages++;
      }
    }
    s.level = j.numOr("level", 1.0f);
    s.stopS = j.numOr("stop_s", 1.4f);
    s.gearbox = j.boolOr("gearbox", true);
    if (const Json* rate = j.get("rate")) {
      if (rate->size() == 2) { s.rateLo = rate->at(0).num; s.rateHi = rate->at(1).num; }
    }
    s.loadedRateScale = j.numOr("loaded_rate_scale", LOADED_RATE_SCALE);
    s.loadedGain = j.numOr("loaded_gain", LOADED_GAIN);

    bool ok = loadWav(dir + "name.wav", s.nameWav, err) && loadWav(dir + "start.wav", s.startWav, err) &&
              loadWav(dir + "horn.wav", s.hornWav, err) && loadWav(dir + "shift.wav", s.shiftWav, err);
    if (ok && s.type == SoundSet::SAMPLE)
      ok = loadWav(dir + "idle.wav", s.idleWav, err) && loadWav(dir + "loaded.wav", s.loadedWav, err);
    if (!ok) s.release();
    return ok;
  }

  static String readState() {
    Json j;
    String err;
    if (!readJsonFile("/state.json", j, err)) return "";
    return j.strOr("set", "");
  }

  static void writeState(const String& folder) {
    if (readState() == folder) return;   // spares the flash
    File f = LittleFS.open("/state.json", "w");
    if (!f) return;
    f.print("{\"set\": \"" + folder + "\"}\n");
  }

 private:
  static String baseName(const char* p) {
    String s(p);
    int k = s.lastIndexOf('/');
    return k >= 0 ? s.substring(k + 1) : s;
  }
};

// ---------------------------------------------------------------- players

// One-shot: plays a clip once.
class ClipPlayer {
 public:
  void play(const Clip* c) { clip = c; pos = 0; }
  void stopNow() { clip = nullptr; }
  bool active() const { return clip != nullptr; }
  float next() {
    if (!clip) return 0.0f;
    float s = clip->data[pos] * (1.0f / 32768.0f);
    if (++pos >= clip->len) clip = nullptr;
    return s;
  }
 private:
  const Clip* clip = nullptr;
  uint32_t pos = 0;
};

// start.wav as the starter of EngineState (start(), stop()). The engine catches when the clip enters its last
// START_TAIL_S (EngineState::crankS = length - START_TAIL_S), the tail plays out under the catching engine. stop()
// before that (ignition back to OFF while cranking) fades the starter out over 0.12 s.
static const float START_TAIL_S = 0.12f;
class WavStarter {
 public:
  void setClip(const Clip* c) { clip = c; on = false; }
  void start() { if (clip && clip->ok()) { pos = 0; on = true; fade = 1.0f; stopping = false; } }
  void stop() {
    if (on && clip->len - pos > (uint32_t)(START_TAIL_S * AUDIO_RATE)) stopping = true;
  }
  bool active() const { return on; }
  float sample() {
    if (!on) return 0.0f;
    float s = clip->data[pos] * (1.0f / 32768.0f);
    if (++pos >= clip->len) { on = false; return s; }
    if (stopping) { fade -= 1.0f / (0.12f * AUDIO_RATE); if (fade <= 0.0f) { on = false; return 0.0f; } }
    return s * fade;
  }
 private:
  const Clip* clip = nullptr;
  uint32_t pos = 0;
  float fade = 1.0f;
  bool on = false, stopping = false;
};

// horn.wav as a loop while the horn control is held: 25 ms attack with the pitch settling from 5 % low (the air
// pressure building up, as HornSound does), 120 ms release.
class WavHorn {
 public:
  void setClip(const Clip* c) { clip = c; env = 0.0f; }
  void set(bool h) { held = h; }
  float sample() {
    if (!clip || !clip->ok()) return 0.0f;
    const float dt = 1.0f / AUDIO_RATE;
    if (held) { if (env == 0.0f) { blat = 0.0f; pos = 0.0f; } env += dt / 0.025f; if (env > 1.0f) env = 1.0f; }
    else { env -= dt / 0.12f; if (env < 0.0f) env = 0.0f; }
    if (env == 0.0f) return 0.0f;
    blat += dt;
    float rate = 1.0f - 0.05f * expf(-blat / 0.06f);
    int i = (int)pos;
    float fr = pos - i;
    int nx = i + 1 < (int)clip->len ? i + 1 : 0;
    float s = clip->data[i] + (clip->data[nx] - clip->data[i]) * fr;
    pos += rate;
    if (pos >= clip->len) pos -= clip->len;
    return s * (1.0f / 32768.0f) * env;
  }
 private:
  const Clip* clip = nullptr;
  bool held = false;
  float env = 0.0f, blat = 0.0f, pos = 0.0f;
};
