"""Spring-themed opening audio: filtered build -> drop at the cut, cinematic impact,
title thud, sparkle chime glissando, riser -> impact + crash, whooshes, pops, ticks.
SFX go through a synthetic stereo reverb. Output 48 kHz stereo WAV."""
import sys, wave
import numpy as np

SR = 48000
DUR = float(sys.argv[2]) if len(sys.argv) > 2 else 4.06
CUT = 2.1
N = int(SR * DUR)
rng = np.random.default_rng(11)
t_all = np.arange(N) / SR
mus = np.zeros((N, 2)); sfx = np.zeros((N, 2)); dry = np.zeros((N, 2))


def put(buf, sig, at, gain=1.0, pan=0.0):
    i = int(at * SR); j = min(N, i + len(sig))
    if j <= i or i < 0: return
    s = sig[: j - i] * gain
    buf[i:j, 0] += s * np.sqrt(0.5 * (1 - pan)) * 1.414
    buf[i:j, 1] += s * np.sqrt(0.5 * (1 + pan)) * 1.414


def lp(x, fc):
    """one-pole low-pass with (optionally time-varying) cutoff"""
    fc = np.broadcast_to(np.asarray(fc, float), x.shape)
    a = np.exp(-2 * np.pi * fc / SR); y = np.empty_like(x); prev = 0.0
    for k in range(len(x)):
        prev = (1 - a[k]) * x[k] + a[k] * prev; y[k] = prev
    return y


def hp(x, fc): return x - lp(x, fc)
def midi(n): return 440 * 2 ** ((n - 69) / 12)
def env_adsr(n, a, r):
    tt = np.arange(n) / SR; return np.minimum(1, tt / a) * np.exp(-tt * r)


# ================= MUSIC (C major, 120 bpm, bright spring) =================
BEAT = 0.5
C2, C3, TURN, CTA, END = 4.0, 13.1667, 21.0, 27.9, DUR
BUILD2 = (C3 - 1.0, C3)                      # filter closes, drums drop out, then 2nd drop
OUTRO = 29.6                                 # drums stop, pad rings out
PROG = [[48, 55, 60, 64, 67], [43, 55, 59, 62, 67], [45, 57, 60, 64, 69], [41, 57, 60, 65, 69]]   # C G Am F
def chord_at(t):
    if t < CUT: return [53, 57, 60, 64, 67]                     # Fmaj9 intro
    return PROG[int((t - CUT) // 2.0) % 4]
def in_build(t): return t < CUT or BUILD2[0] <= t < BUILD2[1]
def drums_on(t): return CUT <= t < OUTRO and not (BUILD2[0] <= t < BUILD2[1])

# pad, chord changes every 2 s (intro 0-CUT)
bounds = [0.0, CUT] + [CUT + 2.0 * k for k in range(1, 20) if CUT + 2.0 * k < DUR] + [DUR]
pad = np.zeros(N)
for s0, s1 in zip(bounds[:-1], bounds[1:]):
    i, j = int(s0 * SR), min(N, int(s1 * SR) + int(0.25 * SR))
    tt = np.arange(j - i) / SR
    e = np.minimum(1, tt / 0.12) * np.minimum(1, np.maximum(0, (j - i) / SR - tt) / 0.25)
    for n in chord_at(s0 + 1e-3)[1:]:
        for det in (-0.07, 0.07):
            f = midi(n + det); pad[i:j] += e * (2 * ((tt * f) % 1) - 1) * 0.035
cutoff = np.full(N, 5200.0)
m = t_all < CUT; cutoff[m] = 500 + 3500 * (t_all[m] / CUT) ** 2
m = (t_all >= BUILD2[0]) & (t_all < BUILD2[1]); cutoff[m] = 700 + 4500 * ((t_all[m] - BUILD2[0]) / 1.0) ** 2
m = t_all >= OUTRO; cutoff[m] = 5200 - 3800 * np.minimum(1, (t_all[m] - OUTRO) / 1.2)
pad = lp(pad, cutoff)
pump = np.where([drums_on(x) for x in t_all[::480]], 1, 0).repeat(480)[:N].astype(float)
pump = 1 - pump * (0.55 - 0.55 * np.minimum(1, (t_all % BEAT) / 0.2))
mus[:, 0] += pad * pump; mus[:, 1] += pad * pump

arp_pat = [0, 2, 4, 3, 1, 3, 4, 2]
for k in range(int(DUR / (BEAT / 2))):
    at = k * BEAT / 2
    if at >= OUTRO + 0.5: break
    n = chord_at(at)[1:][arp_pat[k % 8] % 4] + 12
    nn = int(0.4 * SR); tt = np.arange(nn) / SR
    sig = (np.sin(2 * np.pi * midi(n) * tt) + 0.35 * np.sin(4 * np.pi * midi(n) * tt) * np.exp(-tt * 18)) * np.exp(-tt * 10) * 0.07
    if in_build(at):
        x = at / CUT if at < CUT else (at - BUILD2[0]) / 1.0
        sig = lp(sig, 900 + 3000 * x ** 2); g = 0.45 + 0.55 * x
    else: g = 1.0
    put(mus, sig, at, g, pan=0.4 if k % 2 else -0.4)

for b in range(int(DUR / BEAT) + 1):
    at = b * BEAT
    if not drums_on(at): continue
    nn = int(0.35 * SR); tt = np.arange(nn) / SR
    put(mus, np.sin(2 * np.pi * (42 * tt + 90 * (1 - np.exp(-tt * 28)) / 28)) * np.exp(-tt * 8) * 0.5, at)
    if b % 2 == 1:
        nz = rng.standard_normal(int(0.18 * SR)); put(mus, hp(nz, 900) * np.exp(-np.arange(len(nz)) / SR * 22) * 0.18, at)
    hat = hp(rng.standard_normal(int(0.05 * SR)), 7000) * np.exp(-np.arange(int(0.05 * SR)) / SR * 70) * 0.06
    put(mus, hat, at + BEAT / 2, pan=0.3)
for s0, s1 in zip(bounds[1:-1], bounds[2:]):              # bass under drums
    nn = int((s1 - s0) * SR); tt = np.arange(nn) / SR
    f = midi(chord_at(s0 + 1e-3)[0] - 12 if chord_at(s0 + 1e-3)[0] > 44 else chord_at(s0 + 1e-3)[0])
    on = np.array([drums_on(s0 + x) for x in tt[::480]]).repeat(480)[:nn]
    bass = np.sin(2 * np.pi * f * tt) * 0.22 * np.minimum(1, tt / 0.01) * (0.5 + 0.5 * np.minimum(1, (tt % BEAT) / 0.2)) * on
    put(mus, bass, s0)

# ================= SFX =================
def impact(big=1.0):
    nn = int(1.6 * SR); tt = np.arange(nn) / SR
    sub = np.sin(2 * np.pi * (32 * tt + 70 * (1 - np.exp(-tt * 9)) / 9)) * np.exp(-tt * 2.6) * 0.9
    body = np.sin(2 * np.pi * 95 * tt) * np.exp(-tt * 14) * 0.35
    crack = lp(rng.standard_normal(nn), 4500) * np.exp(-tt * 30) * 0.5
    return (sub + body + crack) * big


def crash():
    nn = int(1.8 * SR); tt = np.arange(nn) / SR
    return hp(rng.standard_normal(nn), 5000) * np.exp(-tt * 2.8) * 0.16


def whoosh(d=0.5, up=True):
    nn = int(d * SR); tt = np.arange(nn) / SR
    fc = 300 + 6000 * ((tt / d) if up else (1 - tt / d)) ** 2
    return hp(lp(rng.standard_normal(nn), fc), 200) * np.sin(np.pi * tt / d) ** 2 * 0.55


def thud():
    nn = int(0.5 * SR); tt = np.arange(nn) / SR
    return np.sin(2 * np.pi * (55 * tt + 40 * (1 - np.exp(-tt * 20)) / 20)) * np.exp(-tt * 9) * 0.6


def bell(f, amp=0.12):
    nn = int(1.4 * SR); tt = np.arange(nn) / SR
    return sum(a * np.sin(2 * np.pi * f * m * tt) * np.exp(-tt * d) for a, m, d in
               [(1, 1, 3.5), (0.4, 2.0, 5), (0.25, 3.01, 7), (0.12, 4.2, 9)]) * amp * np.minimum(1, tt / 0.003)


def pop(f0=900):
    tt = np.arange(int(0.12 * SR)) / SR
    return np.sin(2 * np.pi * (f0 * tt - 2400 * tt ** 2)) * np.exp(-tt * 40) * 0.45


def tick():
    tt = np.arange(int(0.035 * SR)) / SR
    return np.sin(2 * np.pi * 2600 * tt) * np.exp(-tt * 130) * 0.14


def riser(d):
    nn = int(d * SR); tt = np.arange(nn) / SR
    f = 180 * (10 ** (tt / d))
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.1
    nz = hp(rng.standard_normal(nn), 800 + 5000 * tt / d) * 0.14
    return (tone + nz) * (tt / d) ** 2.2


def tier_sfx(t0):
    put(sfx, whoosh(0.3), t0 + .1, 0.7, pan=0.4); put(dry, pop(1000), t0 + .45, 0.45)
def tick_line(t0, n):
    for i in range(n): put(dry, tick(), t0 + i * 0.12, 0.6, pan=(i % 2 - .5) * .6)

put(sfx, impact(1.0), 0.0); put(sfx, crash(), 0.0, 0.7)                     # hook slam
put(sfx, whoosh(0.35, up=False), 0.02, 0.6)
put(dry, thud(), 0.33, 0.8)                                                  # title lands
for i, n in enumerate([84, 86, 88, 91, 93, 96, 98, 100]):                    # sparkle on MÙA XUÂN
    put(sfx, bell(midi(n), 0.07), 0.45 + i * 0.045, pan=-0.5 + i / 7)
put(sfx, whoosh(0.4), 0.42, 0.5, pan=-0.3)
put(dry, pop(800), 0.35, 0.5); put(dry, pop(950), 0.95, 0.5); tick_line(0.5, 8)
put(sfx, riser(0.65), CUT - 0.65, 0.9); put(sfx, whoosh(0.5), 1.85, 0.8, pan=0.3)
put(sfx, impact(0.7), CUT); put(sfx, crash(), CUT, 0.9)                      # DROP 1
tier_sfx(CUT + .1); tick_line(CUT + .15, 6)
put(sfx, whoosh(0.5), 3.75, 0.8, pan=-0.3); tier_sfx(C2 + .15); tick_line(C2 + .2, 7)
put(sfx, whoosh(0.45, up=False), 7.6, 0.5)
put(dry, pop(1100), 8.1, 0.7)                                                # glass card
for i, n in enumerate([88, 91, 96]): put(sfx, bell(midi(n), 0.06), 8.12 + i * 0.06, pan=0.3)
tick_line(8.1, 7)
put(sfx, riser(1.0), C3 - 1.0, 1.0); put(sfx, impact(0.9), C3); put(sfx, crash(), C3, 1.0)   # DROP 2
tier_sfx(C3 + .25); tick_line(C3 + .3, 7)
put(sfx, whoosh(0.5), TURN - .25, 0.8, pan=0.3); tier_sfx(TURN + .2); tick_line(TURN + .25, 7)
put(sfx, whoosh(0.5), 27.65, 0.8, pan=-0.3); tier_sfx(27.9); tick_line(27.95, 7)
put(dry, pop(900), 29.7, 0.9); put(sfx, bell(midi(88), 0.18), 29.75); put(sfx, bell(midi(95), 0.09), 29.77)  # LƯU VIDEO ding
put(sfx, whoosh(0.5), DUR - 0.6, 0.5)

# ================= reverb (stereo FFT convolution) =================
ir_n = int(1.6 * SR); ti = np.arange(ir_n) / SR
ir = np.stack([lp(rng.standard_normal(ir_n), 6000) * np.exp(-ti * 3.8) for _ in range(2)], 1)
ir[:int(0.012 * SR)] = 0; ir /= np.abs(ir).sum(0) ** 0.5 * 6
L = 1 << int(np.ceil(np.log2(N + ir_n)))
wet = np.stack([np.fft.irfft(np.fft.rfft(sfx[:, c], L) * np.fft.rfft(ir[:, c], L), L)[:N] for c in range(2)], 1)

# sidechain-duck the music under the big impacts
duck = np.ones(N)
for at in (0.0, CUT, C3):
    i = int(at * SR); k = np.arange(min(N - i, int(0.6 * SR)))
    duck[i:i + len(k)] *= 0.35 + 0.65 * (k / len(k)) ** 0.7
mix = mus * duck[:, None] * 0.9 + sfx + dry + wet * 0.55
mix *= np.minimum(1, (DUR - t_all) / 0.3)[:, None]
mix = np.tanh(mix / np.abs(mix).max() * 1.6) / np.tanh(1.6) * 0.92                 # soft-clip glue
with wave.open(sys.argv[1], "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
