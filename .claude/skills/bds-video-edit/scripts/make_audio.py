"""Synthesize original background music + SFX (pop, whoosh, tick, riser, impact, ding)
timed to the video's text/transition events. Output: 44.1kHz stereo WAV."""
import os, sys, wave
import numpy as np

SR = 44100
DUR = float(os.environ.get("VIDEO_DUR", "6.17"))
N = int(SR * DUR)
rng = np.random.default_rng(7)
t_all = np.arange(N) / SR
L = np.zeros(N); R = np.zeros(N)


def add(sig, at, gain=1.0, pan=0.0):
    i = int(at * SR)
    j = min(N, i + len(sig))
    if j <= i:
        return
    s = sig[: j - i] * gain
    L[i:j] += s * (1 - max(0, pan)); R[i:j] += s * (1 + min(0, pan))


def onepole_lp(x, fc):
    a = np.exp(-2 * np.pi * np.asarray(fc) / SR)
    y = np.zeros_like(x); prev = 0.0
    a = np.broadcast_to(a, x.shape)
    for k in range(len(x)):
        prev = (1 - a[k]) * x[k] + a[k] * prev
        y[k] = prev
    return y


def midi(n):
    return 440 * 2 ** ((n - 69) / 12)


# ---------- music: warm pad + pluck arpeggio + soft beat (120 bpm) ----------
BEAT = 0.5
chords = [[53, 57, 60, 64], [55, 59, 62, 67], [52, 55, 59, 62], [57, 60, 64, 67]]  # Fmaj7 G6 Em7 Am7
CH = 1.5
pad = np.zeros(N)
for ci, ch in enumerate(chords):
    s, e = int(ci * CH * SR), min(N, int((ci + 1) * CH * SR + 0.3 * SR))
    tt = np.arange(e - s) / SR
    env = np.minimum(1, tt / 0.25) * np.minimum(1, np.maximum(0, (e - s) / SR - tt) / 0.3)
    for n in ch:
        for det in (-0.08, 0.08):
            f = midi(n + det)
            pad[s:e] += env * (2 * ((tt * f) % 1) - 1) * 0.05
pad = onepole_lp(pad, 1400)
# pumping (sidechain feel) on each beat
pump = 0.55 + 0.45 * np.minimum(1, (t_all % BEAT) / 0.22)
pad *= pump
L += pad; R += pad

for k in range(int(DUR / (BEAT / 2))):  # 8th-note pluck arpeggio
    at = k * BEAT / 2
    ch = chords[min(3, int(at / CH))]
    n = ch[[0, 2, 1, 3, 2, 3, 1, 2][k % 8]] + 12
    tt = np.arange(int(0.35 * SR)) / SR
    sig = np.sin(2 * np.pi * midi(n) * tt) * np.exp(-tt * 12) * 0.09
    sig += np.sin(4 * np.pi * midi(n) * tt) * np.exp(-tt * 20) * 0.03
    add(sig, at, pan=0.35 if k % 2 else -0.35)

for b in range(int(DUR / BEAT)):
    tt = np.arange(int(0.3 * SR)) / SR
    kick = np.sin(2 * np.pi * (45 * tt + 60 * (1 - np.exp(-tt * 30)) / 30)) * np.exp(-tt * 9) * 0.32
    add(kick, b * BEAT)
    hat = rng.standard_normal(int(0.05 * SR)); hat = np.diff(hat, prepend=0) * np.exp(-np.arange(len(hat)) / SR * 80) * 0.035
    add(hat, b * BEAT + BEAT / 2)

# ---------- SFX ----------
def pop(f0=900):
    tt = np.arange(int(0.12 * SR)) / SR
    return np.sin(2 * np.pi * (f0 * tt - 2500 * tt ** 2)) * np.exp(-tt * 40) * 0.5

def tick():
    tt = np.arange(int(0.04 * SR)) / SR
    return np.sin(2 * np.pi * 2400 * tt) * np.exp(-tt * 120) * 0.18

def whoosh(d=0.55, up=True):
    n = int(d * SR); tt = np.arange(n) / SR
    noise = rng.standard_normal(n)
    fc = 300 + 5000 * (tt / d if up else 1 - tt / d) ** 2
    lp = onepole_lp(noise, fc); hp = lp - onepole_lp(lp, 200)
    env = np.sin(np.pi * tt / d) ** 2
    return hp * env * 0.5

def riser(d=0.75):
    n = int(d * SR); tt = np.arange(n) / SR
    f = 200 * (8 ** (tt / d))
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.12
    noise = rng.standard_normal(n); noise = noise - onepole_lp(noise, 1000 + 6000 * tt / d)
    return (tone + noise * 0.12) * (tt / d) ** 2

def impact():
    tt = np.arange(int(0.9 * SR)) / SR
    boom = np.sin(2 * np.pi * (38 * tt + 80 * (1 - np.exp(-tt * 15)) / 15)) * np.exp(-tt * 4) * 0.6
    crack = rng.standard_normal(len(tt)) * np.exp(-tt * 35) * 0.25
    return boom + onepole_lp(crack, 3000)

def ding(f=1318.5):
    tt = np.arange(int(1.6 * SR)) / SR
    s = sum(a * np.sin(2 * np.pi * f * m * tt) * np.exp(-tt * d) for a, m, d in
            [(0.3, 1, 3), (0.12, 2.76, 5), (0.07, 5.4, 8), (0.05, 2, 4)])
    return s

def shimmer(d=0.4):
    tt = np.arange(int(d * SR)) / SR
    return sum(np.sin(2 * np.pi * f * tt) for f in (2637, 3136, 3951)) * np.exp(-tt * 6) * (tt < d) * 0.04

add(impact(), 0.0, 0.8); add(shimmer(0.6), 0.05, 1.5)          # hook title slam
add(whoosh(0.5), 1.1, 0.9, pan=-0.3)                            # light leak 1
add(whoosh(0.3), 1.6, 0.7, pan=0.3)                             # SA BAN smear
add(pop(800), 1.95, 0.5)
for i in range(8): add(tick(), 1.5 + i * 0.12, 0.6, pan=(i % 2 - 0.5) * 0.6)
add(riser(0.5), 2.45, 0.8); add(impact(), 3.05, 0.6)           # red tint -> white flash
add(whoosh(0.3), 3.3, 0.7, pan=0.3)                             # VIEW SONG smear
add(pop(1100), 3.7, 0.8); add(shimmer(), 3.72)                  # glass card
add(whoosh(0.5), 4.55, 0.9, pan=-0.3)                           # light leak 2
add(whoosh(0.3), 5.0, 0.7, pan=0.3)                             # BANG GIA smear
add(pop(900), 5.62, 0.9); add(ding(), 5.7, 0.9)                 # LUU VIDEO
# duck music under the impact, master fade-out, normalise
fade = np.minimum(1, np.maximum(0, (DUR - t_all) / 0.45))
L *= fade; R *= fade
peak = max(np.abs(L).max(), np.abs(R).max())
L, R = L / peak * 0.89, R / peak * 0.89
data = (np.stack([L, R], 1) * 32767).astype(np.int16)
with wave.open(sys.argv[1], "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(data.tobytes())
