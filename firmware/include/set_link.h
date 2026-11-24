#pragma once
// The USB link of the `engine_sets` firmware: the web page (web/index.html) lists, reads, writes and deletes the
// sound sets in the data partition over the USB serial port (Web Serial). Protocol: docs/user-sounds.md,
// "The USB protocol".
//
// Text lines both ways, binary data as base64, so log lines of the firmware can share the port: the page reads only
// lines that start with '@'. Every command gets exactly one final line, "@ok ..." or "@err <why>", sometimes after
// data lines. The page sends the next command only after that line, which is the flow control (the USB driver drops
// bytes when its receive buffer is full).
//
//   @hello                 @ok cbsound <protocol version>
//   @info                  @ok free=<bytes> total=<bytes> set=<folder or -> psram=<bytes> fw=<version> built=<date> layers=1
//                                           default=<folder the module starts with, or ->
//                                           (fw: include/version.h, for example 0.1.0+115518f)
//                          (layers=1: the firmware plays layered sets, docs/layers-design.md; absent in older firmware)
//   @ls                    @set <bytes> <folder>   (every folder in /sets)          @ok <count>
//   @files <folder>        @file <bytes> <name>    (every file of /sets/<folder>)   @ok <count>
//   @get <path>            @d <base64>  (up to 3072 bytes per line)                 @ok <size> <crc32 hex>
//   @put <size> <path>     @ok              then  @w <base64>  ->  @ok <bytes so far>
//                                           then  @end <crc32 hex>  ->  @ok   (the file is replaced only now)
//   @rm <path>             @ok              (a file, or a set folder with its files)
//   @mv <from> <to>        @ok
//   @select <folder>       @ok              ends the session, plays that set and speaks its name
//   @demo <folder>         @ok              the same, then a demo of about 25 s: starter, idle, through the gears,
//                                           blips, horn, half throttle, stop (no receiver needed)
//   @stop                  @ok              ends the session and silences the name and the demo that are playing
//                                           (the set stays chosen; the engine winds down)
//   @default <folder>      @ok              the set the module starts with after power-up (/state.json); does not
//                                           change what is playing. BOOT on the module changes it too.
//   @volume <0..100>       @ok              the overall volume of the module in percent (60 = the level of before), kept in NVS;
//                                           takes effect when the session ends (the next Test, or at once after @bye)
//   @fwput <size> <crc32 hex>   @ok          starts a firmware update: the image goes into the other app slot
//   @fww <base64>          @ok <bytes so far>   (up to 3072 bytes per line; the first line must be an ESP32-S3 image)
//   @fwend                 @ok              checks size and CRC, makes the new slot the boot slot and restarts the module
//                                           (@err ... and the running firmware stays when anything is wrong)
//   @bye                   @ok              ends the session
//
// Paths are under /sets/. While the page talks to the module (a session: from the first command until @bye,
// @select or 3 s without a command) the engine is silent, the BOOT button is ignored and the firmware does not
// write to the serial port by itself.
#include "version.h"
#include "sound_sets.h"
#include <Arduino.h>
#include <LittleFS.h>
#include <Preferences.h>
#include <Update.h>
#include <vector>

class SetLink {
 public:
  static const int VERSION = 1;
  static const uint32_t SESSION_TIMEOUT_MS = 3000;
  static const size_t RX_BUFFER = 8192;    // > the longest line (@w with 3072 bytes = 4096 base64 characters)
  static const size_t MAX_LINE = 6000;

  // What the session asks of the firmware when it ends (takeEnd()).
  struct End {
    bool ended = false;
    bool changed = false;   // files were written, moved or deleted: rescan, reload the current set
    String select;          // @select, @demo: this folder
    bool demo = false;      // @demo: then play the demo
    bool stop = false;      // @stop: silence the name and the demo
    int volume = -1;        // @volume: the new overall volume in percent, -1 = unchanged
  };

  // Before Serial.begin(). Without attach() the link talks over the USB serial port.
  void begin() { if (io == &Serial) Serial.setRxBufferSize(RX_BUFFER); }

  // The same protocol over another byte stream (the Bluetooth link of docs/ble-link.md).
  void attach(Stream* s) { io = s; }

  // Bluetooth prototype (docs/ble-link.md): until `@auth <pin>` only @hello and @info are answered. After 3 wrong PINs
  // the link is locked for good (until restart). The USB link never calls this.
  void requireAuth(const String& p) { authRequired = true; authed = false; pin = p; badPins = 0; locked = false; }
  void resetAuth() { authed = false; badPins = 0; }
  bool isAuthed() const { return !authRequired || authed; }
  bool isLocked() const { return locked; }
  // After a firmware update has been written: the main loop restarts the module when this is true (the reply has gone first).
  bool restartDue() const { return restartAt && millis() > restartAt; }
  bool changedSinceStart() const { return everChanged; }   // a set was written, moved or deleted, or the name changed

  // The overall volume in percent (NVS, so that uploadfs does not erase it); 60 = the level the firmware had before it was adjustable.
  static int moduleVolume() {
    Preferences pr; pr.begin("cbsound", true);
    int v = pr.getInt("volume", 60);
    pr.end();
    return v < 0 ? 0 : v > 100 ? 100 : v;
  }

  // The name of the module (for several modules): NVS, so that uploadfs does not erase it. Empty = not set.
  static String moduleName() {
    Preferences pr; pr.begin("cbsound", true);
    String n = pr.getString("name", "");
    pr.end();
    return n;
  }

  // Reads and runs the commands that have arrived. Returns true while a session is active.
  bool poll(const String& currentSet) {
    cur = currentSet;
    while (io->available()) {
      int c = io->read();
      if (c < 0) break;
      if (c == '\r') continue;
      if (c == '\n') {
        if (overflow) reply("@err line too long");
        else if (line.length() && line[0] == '@') { lastMs = millis(); active = true; run(line); lastMs = millis(); }   // after a slow command (erasing the app slot takes seconds) the session has not timed out
        line = "";
        overflow = false;
        continue;
      }
      if (line.length() < MAX_LINE) line += (char)c;
      else overflow = true;
    }
    if (active && millis() - lastMs > SESSION_TIMEOUT_MS) finish();
    return active;
  }

  // Once after a session has ended: what to do now.
  End takeEnd() { End e = end; end = End(); return e; }

 private:
  Stream* io = &Serial;
  bool authRequired = false, authed = false, locked = false, everChanged = false;
  bool fwOn = false, fwFirst = true;
  uint32_t fwSize = 0, fwDone = 0, fwCrc = 0, fwWant = 0, restartAt = 0;
  int badPins = 0;
  String pin;
  String line, cur;
  bool overflow = false, active = false;
  uint32_t lastMs = 0;
  End end;
  // the file being written by @put
  File wf;
  String wPath, wTmp;
  uint32_t wSize = 0, wDone = 0, wCrc = 0;

  void finish() {
    abortPut();
    abortFw();
    active = false;
    end.ended = true;
  }

  void reply(const String& s) { io->print(s); io->print('\n'); }

  static bool pathOk(const String& p) {
    return p.startsWith("/sets/") && p.length() > 6 && p.length() < 80 && p.indexOf("..") < 0 && p.indexOf("//") < 0 &&
           !p.endsWith("/") && p.indexOf(' ') < 0;
  }

  void run(const String& l) {
    int sp = l.indexOf(' ');
    String cmd = sp < 0 ? l : l.substring(0, sp);
    String arg = sp < 0 ? String() : l.substring(sp + 1);
    if (locked) return reply("@err locked");
    if (authRequired && !authed && cmd != "@hello" && cmd != "@info" && cmd != "@auth") return reply("@err auth");
    if (cmd == "@auth") {
      if (!authRequired || arg == pin) { authed = true; return reply("@ok"); }
      if (++badPins >= 3) locked = true;
      return reply("@err wrong pin");
    }
    if (cmd == "@name") {
      bool ok = arg.length() >= 1 && arg.length() <= 8;
      for (size_t i = 0; ok && i < arg.length(); i++) { char c = arg[i]; ok = isAlphaNumeric(c) || c == '_' || c == '-'; }
      if (!ok) return reply("@err name: 1 to 8 letters, digits, - or _");
      Preferences pr; pr.begin("cbsound", false); pr.putString("name", arg); pr.end();
      everChanged = true;
      return reply("@ok restart the module to advertise the new name");
    }
    if (cmd == "@volume") {
      int v = arg.toInt();
      if (arg.length() == 0 || v < 0 || v > 100) return reply("@err usage: @volume <0..100>");
      Preferences pr; pr.begin("cbsound", false); pr.putInt("volume", v); pr.end();
      end.volume = v;
      return reply("@ok");
    }
    if (cmd == "@fww") return fwWrite(arg);
    if (cmd == "@fwend") return fwEnd();
    if (fwOn) abortFw();                    // any other command abandons an unfinished firmware transfer
    if (cmd == "@fwput") return fwPut(arg);
    if (cmd == "@w") return write(arg);
    if (cmd == "@end") return endPut(arg);
    if (wf) abortPut();                    // any other command abandons an unfinished @put
    if (cmd == "@hello") return reply(String("@ok cbsound ") + VERSION);
    if (cmd == "@info") return info();
    if (cmd == "@ls") return ls();
    if (cmd == "@files") return files(arg);
    if (cmd == "@get") return get(arg);
    if (cmd == "@put") return put(arg);
    if (cmd == "@rm") return rm(arg);
    if (cmd == "@mv") return mv(arg);
    if (cmd == "@select" || cmd == "@demo") {
      if (!LittleFS.exists("/sets/" + arg)) return reply("@err no such set");
      reply("@ok");
      end.select = arg;
      end.demo = cmd == "@demo";
      return finish();
    }
    if (cmd == "@stop") { reply("@ok"); end.stop = true; return finish(); }
    if (cmd == "@default") {
      if (!LittleFS.exists("/sets/" + arg)) return reply("@err no such set");
      SetLibrary::writeState(arg);
      return reply("@ok");
    }
    if (cmd == "@bye") { reply("@ok"); return finish(); }
    reply("@err unknown command " + cmd);
  }

  void info() {
    size_t total = LittleFS.totalBytes(), used = LittleFS.usedBytes();
    reply(String("@ok free=") + (unsigned)(total - used) + " total=" + (unsigned)total + " set=" +
          (cur.length() ? cur : String("-")) + " psram=" + (unsigned)ESP.getFreePsram() + " fw=" FW_FULL_VERSION
          " built=" FW_BUILD " layers=1 fwupdate=1 volume=" + moduleVolume() + " name=" + moduleName() + " auth=" + (authRequired ? (authed ? "ok" : "need") : "no") + " default=" + (SetLibrary::readState().length() ? SetLibrary::readState() : String("-")));
  }

  static uint32_t folderBytes(File dir) {
    uint32_t n = 0;
    for (File f = dir.openNextFile(); f; f = dir.openNextFile()) if (!f.isDirectory()) n += f.size();
    return n;
  }

  static String baseName(const char* p) {
    String s(p);
    int k = s.lastIndexOf('/');
    return k >= 0 ? s.substring(k + 1) : s;
  }

  void ls() {
    File root = LittleFS.open("/sets");
    int n = 0;
    if (root && root.isDirectory()) {
      for (File f = root.openNextFile(); f; f = root.openNextFile()) {
        if (!f.isDirectory()) continue;
        String name = baseName(f.name());
        File d = LittleFS.open("/sets/" + name);
        reply(String("@set ") + (unsigned)folderBytes(d) + " " + name);
        n++;
      }
    }
    reply(String("@ok ") + n);
  }

  void files(const String& folder) {
    File d = LittleFS.open("/sets/" + folder);
    if (!d || !d.isDirectory()) return reply("@err no such set");
    int n = 0;
    for (File f = d.openNextFile(); f; f = d.openNextFile()) {
      if (f.isDirectory()) continue;
      reply(String("@file ") + (unsigned)f.size() + " " + baseName(f.name()));
      n++;
    }
    reply(String("@ok ") + n);
  }

  void get(const String& path) {
    if (!pathOk(path)) return reply("@err bad path");
    File f = LittleFS.open(path, "r");
    if (!f || f.isDirectory()) return reply("@err missing");
    static uint8_t buf[3072];
    uint32_t crc = 0, size = 0;
    while (true) {
      int n = f.read(buf, sizeof(buf));
      if (n <= 0) break;
      crc = crc32(crc, buf, n);
      size += n;
      reply("@d " + b64enc(buf, n));
    }
    char tail[40];
    snprintf(tail, sizeof(tail), "@ok %u %08x", (unsigned)size, (unsigned)crc);
    reply(tail);
  }

  void put(const String& arg) {
    int sp = arg.indexOf(' ');
    if (sp < 0) return reply("@err usage: @put <size> <path>");
    uint32_t size = (uint32_t)arg.substring(0, sp).toInt();
    String path = arg.substring(sp + 1);
    if (!pathOk(path) || path.indexOf('/', 6) < 0) return reply("@err bad path");
    size_t total = LittleFS.totalBytes(), used = LittleFS.usedBytes();
    if (size + 16384 > total - used) return reply("@err no space");
    String dir = path.substring(0, path.lastIndexOf('/'));
    if (!LittleFS.exists("/sets")) LittleFS.mkdir("/sets");
    if (!LittleFS.exists(dir)) LittleFS.mkdir(dir);
    wPath = path;
    wTmp = path + ".tmp";
    wf = LittleFS.open(wTmp, "w");
    if (!wf) return reply("@err cannot create " + wTmp);
    wSize = size;
    wDone = 0;
    wCrc = 0;
    reply("@ok");
  }

  void write(const String& b64) {
    if (!wf) return reply("@err no @put");
    static uint8_t buf[3200];
    int n = b64dec(b64, buf, sizeof(buf));
    if (n < 0 || wDone + n > wSize) { abortPut(); return reply("@err bad data"); }
    if (wf.write(buf, n) != (size_t)n) { abortPut(); return reply("@err write failed (full?)"); }
    wCrc = crc32(wCrc, buf, n);
    wDone += n;
    reply(String("@ok ") + (unsigned)wDone);
  }

  void endPut(const String& crcHex) {
    if (!wf) return reply("@err no @put");
    wf.close();
    uint32_t want = (uint32_t)strtoul(crcHex.c_str(), nullptr, 16);
    if (wDone != wSize || want != wCrc) {
      LittleFS.remove(wTmp);
      return reply(wDone != wSize ? "@err short file" : "@err crc mismatch");
    }
    if (LittleFS.exists(wPath)) LittleFS.remove(wPath);
    if (!LittleFS.rename(wTmp, wPath)) { LittleFS.remove(wTmp); return reply("@err rename failed"); }
    end.changed = true; everChanged = true;
    reply("@ok");
  }

  // ---- firmware update over the link (docs/ble-link.md): the image is written into the other app slot by the Update library,
  // and the slot becomes the boot slot only when the size and the CRC are right. A running firmware is never touched.
  void fwPut(const String& arg) {
    int sp = arg.indexOf(' ');
    if (sp < 0) return reply("@err usage: @fwput <size> <crc32 hex>");
    uint32_t size = (uint32_t)arg.substring(0, sp).toInt();
    uint32_t want = (uint32_t)strtoul(arg.substring(sp + 1).c_str(), nullptr, 16);
    if (size < 100000 || size > 0x180000) return reply("@err firmware size (100 kB to 1.5 MB)");
    if (!Update.begin(size, U_FLASH)) return reply(String("@err cannot start the update: ") + Update.errorString());
    fwOn = true; fwFirst = true; fwSize = size; fwDone = 0; fwCrc = 0; fwWant = want;
    reply("@ok");
  }

  void fwWrite(const String& b64) {
    if (!fwOn) return reply("@err no @fwput");
    static uint8_t buf[3200];
    int n = b64dec(b64, buf, sizeof(buf));
    if (n < 0 || fwDone + n > fwSize) { abortFw(); return reply("@err bad data"); }
    if (fwFirst) {                           // an ESP32 image starts with 0xE9, the chip id (9 = ESP32-S3) is at offset 12
      if (n < 16 || buf[0] != 0xE9 || buf[12] != 0x09 || buf[13] != 0x00) { abortFw(); return reply("@err not an ESP32-S3 firmware image"); }
      fwFirst = false;
    }
    if (Update.write(buf, n) != (size_t)n) { abortFw(); return reply("@err write failed"); }
    fwCrc = crc32(fwCrc, buf, n);
    fwDone += n;
    reply(String("@ok ") + (unsigned)fwDone);
  }

  void fwEnd() {
    if (!fwOn) return reply("@err no @fwput");
    if (fwDone != fwSize) { abortFw(); return reply("@err short image"); }
    if (fwCrc != fwWant) { abortFw(); return reply("@err crc mismatch"); }
    bool ok = Update.end();
    fwOn = false;
    if (!ok) return reply(String("@err ") + Update.errorString());
    reply("@ok restarting with the new firmware");
    restartAt = millis() + 1200;             // after the reply has been sent
  }

  void abortFw() {
    if (!fwOn) return;
    Update.abort();
    fwOn = false;
  }

  void abortPut() {
    if (!wf) return;
    wf.close();
    LittleFS.remove(wTmp);
  }

  void rm(const String& path) {
    if (!pathOk(path)) return reply("@err bad path");
    File f = LittleFS.open(path);
    if (!f) return reply("@err missing");
    if (f.isDirectory()) {
      std::vector<String> names;
      for (File g = f.openNextFile(); g; g = f.openNextFile()) names.push_back(baseName(g.name()));
      f.close();
      for (const String& n : names) LittleFS.remove(path + "/" + n);
      if (!LittleFS.rmdir(path)) return reply("@err cannot remove the folder");
    } else {
      f.close();
      if (!LittleFS.remove(path)) return reply("@err cannot remove");
    }
    end.changed = true; everChanged = true;
    reply("@ok");
  }

  void mv(const String& arg) {
    int sp = arg.indexOf(' ');
    String from = sp < 0 ? arg : arg.substring(0, sp), to = sp < 0 ? String() : arg.substring(sp + 1);
    if (!pathOk(from) || !pathOk(to)) return reply("@err bad path");
    if (!LittleFS.exists(from)) return reply("@err missing");
    if (LittleFS.exists(to)) return reply("@err target exists");
    if (!LittleFS.rename(from, to)) return reply("@err rename failed");
    end.changed = true; everChanged = true;
    reply("@ok");
  }

  // ------------------------------------------------------------ helpers
  static uint32_t crc32(uint32_t crc, const uint8_t* p, size_t n) {   // the zlib CRC-32
    crc = ~crc;
    while (n--) {
      crc ^= *p++;
      for (int k = 0; k < 8; k++) crc = (crc >> 1) ^ (0xEDB88320u & (0u - (crc & 1u)));
    }
    return ~crc;
  }

  static String b64enc(const uint8_t* p, size_t n) {
    static const char T[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    String s;
    s.reserve((n + 2) / 3 * 4);
    for (size_t i = 0; i < n; i += 3) {
      uint32_t v = (uint32_t)p[i] << 16 | (i + 1 < n ? p[i + 1] << 8 : 0) | (i + 2 < n ? p[i + 2] : 0);
      s += T[v >> 18 & 63];
      s += T[v >> 12 & 63];
      s += i + 1 < n ? T[v >> 6 & 63] : '=';
      s += i + 2 < n ? T[v & 63] : '=';
    }
    return s;
  }

  static int b64val(char c) {
    if (c >= 'A' && c <= 'Z') return c - 'A';
    if (c >= 'a' && c <= 'z') return c - 'a' + 26;
    if (c >= '0' && c <= '9') return c - '0' + 52;
    if (c == '+') return 62;
    if (c == '/') return 63;
    return -1;
  }

  // Returns the number of bytes, or -1 for bad input.
  static int b64dec(const String& s, uint8_t* out, size_t cap) {
    size_t n = 0;
    uint32_t acc = 0;
    int bits = 0;
    for (size_t i = 0; i < s.length(); i++) {
      char c = s[i];
      if (c == '=') break;
      int v = b64val(c);
      if (v < 0) return -1;
      acc = acc << 6 | v;
      bits += 6;
      if (bits >= 8) {
        bits -= 8;
        if (n >= cap) return -1;
        out[n++] = (uint8_t)(acc >> bits);
      }
    }
    return (int)n;
  }
};
