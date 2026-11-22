"""Run from the repo root after `"C:/Program Files/KiCad/bin/python.exe" tools/extract_board_for_trial.py` (writes work/board_full.json):
    python tools/trial_place_j1.py <YJ in mm> <seed> <iterations> [check]
(check: only the overlaps of the present layout, the calibration).

Trial placement: can the parts of the shield be placed again if J1 moves so that the whole servo plug is inside the board
(the row of pins YJ mm from the edge)?  Only an area and wire length test, no routing."""
import json, math, random, sys
sys.path.insert(0, "tools")
import shield_netlist as N

YJ = float(sys.argv[1]) if len(sys.argv) > 1 else 19.0
SEED = int(sys.argv[2]) if len(sys.argv) > 2 else 1
ITER = int(sys.argv[3]) if len(sys.argv) > 3 else 150000
D = json.load(open("work/board_full.json"))
W, H = D["W"], D["H"]
P = D["parts"]
INFL = 0.02                      # clearance around every courtyard (the real board has hardly any more)

def rot(x, y, a):               # KiCad: positive angle = counter-clockwise on the screen (y down)
    a = math.radians(a); c, s = math.cos(a), math.sin(a)
    return x * c + y * s, -x * s + y * c

def world_box(ref, x, y, a):
    c = P[ref]["crt"]
    pts = [rot(px, py, a) for px, py in ((c[0], c[1]), (c[2], c[1]), (c[2], c[3]), (c[0], c[3]))]
    return (x + min(p[0] for p in pts), y + min(p[1] for p in pts), x + max(p[0] for p in pts), y + max(p[1] for p in pts))

def pad_world(ref, num, x, y, a):
    for n, lx, ly in P[ref]["pads"]:
        if n == num:
            dx, dy = rot(lx, ly, a)
            return x + dx, y + dy
    return x, y

fixed = ["J3", "J4", "J2", "LED1", "R3", "C1"]
movable = [r for r in P if P[r]["side"] == "F" and r not in fixed and not r.startswith(("MH", "TP", "J1"))]
# the keepout of the plug path and of J1 itself (J1 courtyard in its own frame, rotated 90 degrees as it is now)
J1X = 12.01
j1 = world_box("J1", J1X, YJ, P["J1"]["rot"])
keep_plug = (j1[0] - 0.2, 0.0, j1[2] + 0.2, j1[3] + 0.2)      # from the edge of the board to the body of J1
obst = []
for r in fixed:
    obst.append((r,) + world_box(r, P[r]["x"], P[r]["y"], P[r]["rot"]))
for r in P:
    if r.startswith("MH"):
        obst.append((r, P[r]["x"] - 3, P[r]["y"] - 3, P[r]["x"] + 3, P[r]["y"] + 3))
obst.append(("J1+plug",) + keep_plug)
margin = 0.3

nets = N.nets()
W_NET = {"S_IN": 4, "VIN": 4, "VFUSED": 4, "IO1_THR": 3, "5V_ZERO": 4, "+5V": 1.0, "IO4_DIN": 3, "IO5_BCLK": 3, "IO6_LRC": 3,
         "DIN": 5, "BCLK": 5, "LRCLK": 5, "OUTP": 6, "OUTN": 6, "SPK_P": 4, "SPK_N": 4, "GAIN": 4, "GAIN_R": 4, "SD_MODE": 4, "SD_R": 4}
PAIRS = [("C3", "1", "U1", "7", 10), ("C2", "1", "U1", "8", 8), ("C4", "1", "J2", "1", 8), ("C5", "1", "J2", "2", 8),
         ("TVS1", "1", "J1", "1", 6), ("R1", "1", "J1", "1", 4), ("F1", "1", "J1", "2", 4)]

state = {r: [P[r]["x"], P[r]["y"], P[r]["rot"] % 180] for r in movable}
def j1_pad(num):
    i = int(num) - 1
    return J1X + 2.54 * i, YJ
def pos_of(ref, num):
    if ref == "J1":
        return j1_pad(num)
    if ref in state:
        x, y, a = state[ref]; return pad_world(ref, num, x, y, a)
    q = P[ref]; return pad_world(ref, num, q["x"], q["y"], q["rot"])

def boxes():
    return {r: world_box(r, *state[r]) for r in movable}

def overlap(a, b):
    ox = min(a[2], b[2]) - max(a[0], b[0]) + 2 * INFL
    oy = min(a[3], b[3]) - max(a[1], b[1]) + 2 * INFL
    return ox * oy if ox > 0 and oy > 0 else 0.0

def cost(detail=False):
    bx = boxes()
    ov = 0.0; n_ov = 0
    refs = list(bx)
    for i, r in enumerate(refs):
        b = bx[r]
        if b[0] < margin or b[1] < margin or b[2] > W - margin or b[3] > H - margin:
            ov += 5.0 + abs(min(b[0] - margin, 0)) + abs(min(b[1] - margin, 0)); n_ov += 1
        for o in obst:
            v = overlap(b, o[1:])
            if v > 0: ov += 1.0 + v; n_ov += 1
        for s in refs[i + 1:]:
            v = overlap(b, bx[s])
            if v > 0: ov += 1.0 + v; n_ov += 1
    wl = 0.0
    for net, pins in nets.items():
        if net == "GND": continue
        pts = []
        for pr in pins:
            ref, num = pr.split(".")
            if ref in P and P[ref]["side"] == "F":
                pts.append(pos_of(ref, num))
        if len(pts) > 1:
            xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
            wl += W_NET.get(net, 2) * ((max(xs) - min(xs)) + (max(ys) - min(ys)))
    for a, na, b, nb, w in PAIRS:
        pa, pb = pos_of(a, na), pos_of(b, nb)
        wl += w * math.hypot(pa[0] - pb[0], pa[1] - pb[1])
    if detail: return ov, n_ov, wl
    return ov * 300 + wl

random.seed(SEED)
if len(sys.argv) > 4 and sys.argv[4] == "check":
    ov, n_ov, wl = cost(True); print("CURRENT layout (YJ=%.1f): overlaps %d, penalty %.2f" % (YJ, n_ov, ov))
    bx = boxes()
    refs = list(bx)
    for i, r in enumerate(refs):
        for o in obst:
            v = overlap(bx[r], o[1:])
            if v > 0: print("  ", r, "x", o[0], round(v, 2))
        for q in refs[i+1:]:
            v = overlap(bx[r], bx[q])
            if v > 0: print("  ", r, "x", q, round(v, 2))
        b = bx[r]
        if b[0] < margin or b[1] < margin or b[2] > W - margin or b[3] > H - margin: print("  ", r, "outside", [round(t,1) for t in b])
    sys.exit()
# the parts that sit in the keepout start at a random free spot
for r in movable:
    b = world_box(r, *state[r])
    if overlap(b, keep_plug) > 0:
        state[r][0] = random.uniform(2, W - 2); state[r][1] = random.uniform(2, H - 2)
cur = cost(); best = cur; best_state = {k: v[:] for k, v in state.items()}
T0 = 30.0
for it in range(ITER):
    T = T0 * (1 - it / ITER) ** 2 + 0.02
    r = random.choice(movable); old = state[r][:]
    k = random.random()
    if k < 0.7:
        s = 3.0 * (1 - it / ITER) + 0.15
        state[r][0] += random.gauss(0, s); state[r][1] += random.gauss(0, s)
    elif k < 0.85:
        state[r][2] = 90 - state[r][2] if state[r][2] in (0, 90) else 0
    else:
        o = random.choice(movable)
        if o != r: state[r][0], state[r][1], state[o][0], state[o][1] = state[o][0], state[o][1], state[r][0], state[r][1]
    c = cost()
    if c < cur or random.random() < math.exp((cur - c) / T):
        cur = c
        if c < best: best = c; best_state = {k2: v[:] for k2, v in state.items()}
    else:
        state[r] = old
state = best_state
ov, n_ov, wl = cost(True)
print("YJ=%.1f seed=%d: overlaps %d (penalty %.2f), weighted wire length %.0f" % (YJ, SEED, n_ov, ov, wl))
json.dump({"YJ": YJ, "state": state, "ov": ov, "n_ov": n_ov, "wl": wl}, open("work/trial_%g_%d.json" % (YJ, SEED), "w"))
