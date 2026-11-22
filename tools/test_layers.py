#!/usr/bin/env python3
"""Host test of the maths of firmware/include/layers.h (layered sample sets, docs/layers-design.md).

There is no C++ compiler on the development PC, so the two functions of layers.h (layersXfade, layerMix) are ported
here line by line and the properties the firmware relies on are checked on the port. Keep the two in step. The C++
itself is checked by the firmware build and on the module (docs/layers-design.md, "Tests").

    python tools/test_layers.py
"""
import math, sys

def layers_xfade(ratio, xfade):
    w = xfade
    for k in range(len(ratio) - 2):
        gap = 0.5 * (math.log(ratio[k + 2]) - math.log(ratio[k]))
        if gap < w: w = gap
    return max(w, 0.02)

def layer_mix(ratio, r, xfade):
    """returns (a, b, wa, wb, ra, rb); b = -1: only a plays"""
    n = len(ratio)
    lr = math.log(r)
    for k in range(n - 1):
        lc = 0.5 * (math.log(ratio[k]) + math.log(ratio[k + 1]))
        t = (lr - lc) / xfade + 0.5
        if t <= 0: return (k, -1, 1.0, 0.0, r / ratio[k], 1.0)
        if t < 1:
            return (k, k + 1, math.cos(t * math.pi / 2), math.sin(t * math.pi / 2), r / ratio[k], r / ratio[k + 1])
    return (n - 1, -1, 1.0, 0.0, r / ratio[n - 1], 1.0)

fails = 0
def check(c, msg):
    global fails
    if not c: fails += 1; print("FAIL:", msg)

ratio = [1.0, 35.3 / 17.7, 40.8 / 17.7]     # the three layers of the PC prototype (work/layers_demo.py)
xf = layers_xfade(ratio, 0.36)
print("xfade used: %.3f" % xf)
check(0 < xf <= 0.36 + 1e-9, "xfade out of range")

prev = [1.0, 0.0, 0.0]; max_step = 0.0; rmin, rmax = 1e9, 0.0
steps = 2000
for i in range(steps + 1):
    rpm = i / steps; r = 1 + 2 * rpm
    a, b, wa, wb, ra, rb = layer_mix(ratio, r, xf)
    check(0 <= a < 3, "layer a out of range at rpm %.3f" % rpm)
    if b >= 0:
        check(b == a + 1, "not neighbours at rpm %.3f" % rpm)
        check(abs(wa * wa + wb * wb - 1) < 1e-9, "power not constant at rpm %.3f" % rpm)
    else:
        check(wa == 1.0 and wb == 0.0, "solo weights at rpm %.3f" % rpm)
    w = [0.0] * 3; w[a] = wa
    if b >= 0: w[b] = wb
    for k in range(3):
        max_step = max(max_step, abs(w[k] - prev[k])); prev[k] = w[k]
    for wk, rk in ((wa, ra), (wb, rb)):
        if wk > 0.05: rmin = min(rmin, rk); rmax = max(rmax, rk)
print("rates of audible layers %.2f .. %.2f, largest weight step per 1/%d rpm: %.4f" % (rmin, rmax, steps, max_step))
check(max_step < 0.03, "weights jump (%.4f)" % max_step)
check(abs(rmin - 0.60) < 0.03 and abs(rmax - 1.67) < 0.03, "rates differ from the prototype (0.60..1.67 per layer ranges)")

lo = layer_mix(ratio, 1.0, xf); hi = layer_mix(ratio, 3.0, xf)
check(lo[0] == 0 and lo[1] == -1 and abs(lo[4] - 1.0) < 1e-9, "idle should be layer 0 at its own speed")
check(hi[0] == 2 and hi[1] == -1, "full throttle should be the last layer")
print("idle: layer %d at %.2fx, full: layer %d at %.2fx" % (lo[0], lo[4], hi[0], hi[4]))

one = layer_mix([1.0], 2.0, 0.36)
check(one[0] == 0 and one[1] == -1 and abs(one[4] - 2.0) < 1e-9, "one layer")
close = [1.0, 1.2, 1.3]
check(layers_xfade(close, 0.36) <= 0.5 * math.log(1.3) + 1e-9, "xfade limit for close layers")
for r in (0.5, 1.0, 1.1, 1.25, 1.299, 10.0):    # also with the limited width, any r gives valid output
    m = layer_mix(close, r, layers_xfade(close, 0.36)); check(0 <= m[0] < 3, "close layers r=%g" % r)

print("FAILED (%d)" % fails if fails else "all checks passed")
sys.exit(1 if fails else 0)
