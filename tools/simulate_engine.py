"""Offline simulation of the engine firmware (same algorithm as firmware/src/engine/main.cpp).

Usage: python tools/simulate_engine.py
Writes docs/audio-demo/engine_demo_full.wav and engine_demo_small_speaker.wav.
Keep the constants in sync with firmware/include/config.h and src/engine/main.cpp.
"""
import os, re, wave, struct, math
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "docs", "audio-demo")
s = open(os.path.join(ROOT,"firmware","include","engine_sample.h")).read()
S = [int(x) for x in re.findall(r"-?\d+", s.split("= {")[1])]
N_S = len(S); RATE = 22050; MASTER = 0.35
# throttle profile (seconds, throttle 0..1), same shape as stick movements
prof = [(0,0),(2,0),(5,1.0),(7,1.0),(10,0.0),(11,0.0),(11.4,0.8),(11.9,0.0),(12.4,0.8),(12.9,0.0),(14,0.0),(14.1,0.5),(16.5,0.5),(18,0.0),(20,0.0)]
def throttle(t):
    for (t0,a),(t1,b) in zip(prof,prof[1:]):
        if t0 <= t <= t1: return a + (b-a)*(t-t0)/(t1-t0) if t1>t0 else b
    return 0.0
def render(highpass_hz=None):
    out=[]; pos=0.0; rpm=0.0; n=0
    total=int(20*RATE)
    y1=y2=x1=x2=0.0
    a = math.exp(-2*math.pi*highpass_hz/RATE) if highpass_hz else None
    while n<total:
        target=throttle(n/RATE)           # firmware: once per 128-sample block
        k = 0.02 if target>rpm else 0.008
        rpm += (target-rpm)*k
        rate = 0.7+1.3*rpm
        vol = MASTER*(0.55+0.45*rpm)
        for i in range(128):
            idx=int(pos); fr=pos-idx; nx=idx+1 if idx+1<N_S else 0
            v=(S[idx]+(S[nx]-S[idx])*fr)*vol
            pos+=rate
            if pos>=N_S: pos-=N_S
            if a is not None:  # two one-pole high-passes ~ small-speaker rolloff
                h1=a*(y1+v-x1); x1=v; y1=h1
                h2=a*(y2+h1-x2); x2=h1; y2=h2
                v=h2
            out.append(max(-32768,min(32767,int(v))))
            n+=1
    return out
def save(name,data):
    w=wave.open(name,"wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE)
    w.writeframes(struct.pack("<%dh"%len(data),*data)); w.close()
save(os.path.join(OUT,"engine_demo_full.wav"), render())
save(os.path.join(OUT,"engine_demo_small_speaker.wav"), render(800))
print("ok")
