"""Placeholder sound effects + ambience + BGM, synthesised in pure Python (no numpy).

    python3 Tools/Audio/gen_sfx.py <out_dir>

Writes 16-bit mono WAVs. Import them into /Game/Project/Audio (asset names = file names). Replacing an asset with
a real recording of the same name keeps every blueprint hook working.
"""
import math
import random
import struct
import sys
import wave

SR = 32000
OUT = sys.argv[1] if len(sys.argv) > 1 else '.'
TAU = 2 * math.pi


def write(name, s, peak=0.9):
    m = max(1e-6, max(abs(x) for x in s))
    k = peak / m
    with wave.open(f'{OUT}/{name}.wav', 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(b''.join(struct.pack('<h', int(max(-1, min(1, x * k)) * 32767)) for x in s))
    print(name, round(len(s) / SR, 2), 's')


def n(sec):
    return int(sec * SR)


def env(i, a, d, total):
    """attack a, exponential decay constant d (seconds), i in samples"""
    t = i / SR
    if t < a:
        return t / a
    return math.exp(-(t - a) / d)


def lp(s, c):
    """one-pole low-pass, c in 0..1 (smaller = darker)"""
    y, out = 0.0, []
    for x in s:
        y += c * (x - y)
        out.append(y)
    return out


def hp(s, c):
    lo = lp(s, c)
    return [a - b for a, b in zip(s, lo)]


def noise(k, seed=1):
    r = random.Random(seed)
    return [r.uniform(-1, 1) for _ in range(k)]


def mix(*tracks):
    L = max(len(t) for t in tracks)
    return [sum(t[i] for t in tracks if i < len(t)) for i in range(L)]


def fade(s, fi=0.005, fo=0.02):
    a, b = n(fi), n(fo)
    s = list(s)
    for i in range(min(a, len(s))):
        s[i] *= i / a
    for i in range(min(b, len(s))):
        s[-1 - i] *= i / b
    return s


# ---------------------------------------------------------------- fox footstep: soft dirt/stone tap
def step(seed):
    k = n(0.14)
    ns = lp(noise(k, seed), 0.25)
    thump = [math.sin(TAU * 95 * i / SR) * env(i, 0.002, 0.025, k) for i in range(k)]
    grit = [x * env(i, 0.001, 0.03, k) for i, x in enumerate(hp(noise(k, seed + 9), 0.3))]
    return fade(mix([x * env(i, 0.002, 0.04, k) for i, x in enumerate(ns)], [t * 0.6 for t in thump], [g * 0.25 for g in grit]))


# ---------------------------------------------------------------- hit: punchy thump + crunchy noise + falling tone
def hit():
    k = n(0.55)
    body = [math.sin(TAU * (140 * math.exp(-i / SR * 8) + 45) * i / SR) * env(i, 0.001, 0.12, k) for i in range(k)]
    crunch = [x * env(i, 0.001, 0.06, k) for i, x in enumerate(lp(noise(k, 3), 0.5))]
    zap = [math.sin(TAU * (900 * math.exp(-i / SR * 6)) * i / SR) * env(i, 0.001, 0.15, k) * 0.25 for i in range(k)]
    return fade(mix(body, [c * 0.7 for c in crunch], zap))


# ---------------------------------------------------------------- box pick up: whoosh up + light knock
def pick():
    k = n(0.28)
    wh = lp(noise(k, 5), 0.15)
    out = []
    for i in range(k):
        t = i / k
        out.append(wh[i] * math.sin(math.pi * t) * 0.8 + math.sin(TAU * (300 + 500 * t) * i / SR) * 0.15 * math.sin(math.pi * t))
    return fade(out)


# ---------------------------------------------------------------- box drop: heavy wooden thud
def drop():
    k = n(0.45)
    body = [math.sin(TAU * (110 * math.exp(-i / SR * 5) + 55) * i / SR) * env(i, 0.001, 0.09, k) for i in range(k)]
    wood = [math.sin(TAU * 420 * i / SR) * env(i, 0.001, 0.035, k) * 0.35 for i in range(k)]
    dust = [x * env(i, 0.005, 0.12, k) * 0.35 for i, x in enumerate(lp(noise(k, 7), 0.2))]
    return fade(mix(body, wood, dust))


# ---------------------------------------------------------------- enemy (rock beast) footstep: deep rumble stomp
def enemy_step(seed):
    k = n(0.5)
    body = [math.sin(TAU * (70 * math.exp(-i / SR * 4) + 35) * i / SR) * env(i, 0.004, 0.16, k) for i in range(k)]
    rubble = [x * env(i, 0.003, 0.1, k) * 0.6 for i, x in enumerate(lp(noise(k, seed), 0.12))]
    return fade(mix(body, rubble))


# ---------------------------------------------------------------- glitch: bit-crushed stutter bursts
def glitch(sec, seed, bright):
    r = random.Random(seed)
    k = n(sec)
    out = [0.0] * k
    i = 0
    while i < k:
        seg = n(r.uniform(0.02, 0.09))
        kind = r.random()
        f = r.choice([220, 330, 440, 660, 880, 1320]) * bright
        hold, v = r.randint(4, 40), 0.0
        for j in range(seg):
            if i + j >= k:
                break
            if kind < 0.35:        # square buzz
                x = 1.0 if math.sin(TAU * f * j / SR) > 0 else -1.0
            elif kind < 0.65:      # sample-and-hold noise (bit crush)
                if j % hold == 0:
                    v = r.uniform(-1, 1)
                x = v
            elif kind < 0.8:       # silence gap
                x = 0.0
            else:                  # fast sweep
                x = math.sin(TAU * (f * (1 + 3 * j / seg)) * j / SR)
            out[i + j] = x * 0.6
        i += seg
    q = 1 / 8                      # quantise (bit crush)
    out = [round(x / q) * q for x in out]
    return fade(out, 0.002, 0.05)


# ---------------------------------------------------------------- dialogue: fox = soft paper/wood "pip", system = digital chirp
def dlg_fox():
    k = n(0.12)
    a = [math.sin(TAU * 660 * i / SR) * env(i, 0.003, 0.03, k) for i in range(k)]
    b = [math.sin(TAU * 990 * i / SR) * env(i, 0.003, 0.02, k) * 0.4 for i in range(k)]
    p = [x * env(i, 0.001, 0.015, k) * 0.3 for i, x in enumerate(hp(noise(k, 11), 0.5))]
    return fade(mix(a, b, p))


def dlg_sys():
    k = n(0.16)
    out = []
    for i in range(k):
        t = i / SR
        f = 1200 if t < 0.05 else 1800
        sq = 1.0 if math.sin(TAU * f * t) > 0 else -1.0
        out.append(sq * 0.35 * (1 if t < 0.045 or 0.06 < t < 0.13 else 0))
    return fade(lp(out, 0.4), 0.001, 0.01)


# ---------------------------------------------------------------- lift: motor hum + chain rattle, then clunk
def lift():
    k = n(1.6)
    out = []
    r = random.Random(13)
    for i in range(k):
        t = i / SR
        e = min(1, t / 0.15) * (1 if t < 1.35 else max(0, (1.45 - t) / 0.1))
        hum = (math.sin(TAU * 60 * t) + 0.5 * math.sin(TAU * 120 * t) + 0.25 * math.sin(TAU * 180 * t)) * 0.4
        rat = r.uniform(-1, 1) * (0.5 + 0.5 * math.sin(TAU * 14 * t)) * 0.25
        out.append((hum + rat) * e)
    clunk = [0.0] * n(1.42) + [math.sin(TAU * 90 * i / SR) * env(i, 0.001, 0.06, 0) for i in range(n(0.18))]
    return fade(mix(lp(out, 0.35), clunk))


# ---------------------------------------------------------------- rotating bridge: stone grinding + click
def bridge():
    k = n(1.1)
    g = lp(noise(k, 17), 0.06)
    out = []
    for i in range(k):
        t = i / SR
        e = min(1, t / 0.1) * (1 if t < 0.85 else max(0, (0.95 - t) / 0.1))
        out.append(g[i] * e * (0.7 + 0.3 * math.sin(TAU * 23 * t)) * 1.6)
    click = [0.0] * n(0.9) + [math.sin(TAU * 260 * i / SR) * env(i, 0.001, 0.05, 0) for i in range(n(0.2))]
    return fade(mix(out, click))


# ---------------------------------------------------------------- gate: wooden creak
def gate():
    k = n(0.8)
    out = []
    ph = 0.0
    for i in range(k):
        t = i / SR
        f = 180 + 70 * math.sin(TAU * 1.3 * t) + 20 * math.sin(TAU * 7 * t)
        ph += TAU * f / SR
        saw = (ph / math.pi) % 2 - 1
        e = min(1, t / 0.05) * max(0, 1 - t / 0.8)
        out.append(saw * e * 0.5)
    return fade(lp(out, 0.25))


# ---------------------------------------------------------------- portal / reveal shimmer (fox look stage change)
def shimmer():
    k = n(1.4)
    out = [0.0] * k
    for f, d in [(880, 0), (1320, 0.08), (1760, 0.16), (2640, 0.24)]:
        o = n(d)
        for i in range(k - o):
            out[i + o] += math.sin(TAU * f * i / SR) * env(i, 0.01, 0.35, k) * 0.25
    return fade(out)


# ---------------------------------------------------------------- ambience loop: wind + sparse birds (20 s, seamless)
def ambience():
    sec = 20
    k = n(sec)
    w = lp(noise(k, 21), 0.02)
    out = []
    for i in range(k):
        t = i / SR
        sw = 0.6 + 0.4 * math.sin(TAU * t / sec * 2) * math.sin(TAU * t / sec * 3 + 1)
        out.append(w[i] * sw * 3.0)
    r = random.Random(23)
    for _ in range(9):
        st = r.uniform(0.5, sec - 1.5)
        base = r.uniform(2600, 4200)
        for c in range(r.randint(2, 4)):
            o = n(st + c * 0.13)
            L = n(0.09)
            for i in range(L):
                if o + i < k:
                    tt = i / L
                    out[o + i] += math.sin(TAU * (base + 900 * math.sin(math.pi * tt)) * i / SR) * math.sin(math.pi * tt) * 0.12
    # seamless loop: crossfade the last second into the first
    X = n(1.0)
    for i in range(X):
        a = i / X
        out[i] = out[i] * a + out[k - X + i] * (1 - a)
    return out[:k - X]


# ---------------------------------------------------------------- BGM: gentle storybook loop (pentatonic, 32 bars-ish)
def bgm():
    bpm = 84
    beat = 60 / bpm
    bars = 16
    k = n(bars * 4 * beat)
    out = [0.0] * k
    # chord roots (C major-ish, soft): C Am F G
    prog = [(48, [0, 4, 7]), (45, [0, 3, 7]), (41, [0, 4, 7]), (43, [0, 4, 7])]
    hz = lambda m: 440 * 2 ** ((m - 69) / 12)

    def note(start, dur, f, amp, bright=1.0, dec=0.6):
        o, L = n(start), n(dur)
        for i in range(L):
            if o + i >= k:
                break
            t = i / SR
            e = min(1, t / 0.01) * math.exp(-t / dec)
            v = math.sin(TAU * f * t) + 0.3 * bright * math.sin(TAU * 2 * f * t) + 0.1 * bright * math.sin(TAU * 3 * f * t)
            out[o + i] += v * e * amp

    r = random.Random(31)
    penta = [0, 2, 4, 7, 9]
    for bar in range(bars):
        root, tri = prog[bar % 4]
        t0 = bar * 4 * beat
        # pad: held chord, soft
        for iv in tri:
            note(t0, 4 * beat, hz(root + 12 + iv), 0.05, 0.3, 2.5)
        # bass
        note(t0, 2 * beat, hz(root - 12 + 12), 0.12, 0.2, 0.8)
        note(t0 + 2 * beat, 2 * beat, hz(root + 7), 0.08, 0.2, 0.8)
        # plucked melody (music-box), 8th notes with rests
        for s in range(8):
            if r.random() < 0.55:
                m = 72 + penta[r.randrange(5)] + (12 if r.random() < 0.2 else 0)
                note(t0 + s * beat / 2, beat * 1.5, hz(m), 0.07, 1.0, 0.35)
    # tail wrap for a seamless loop
    X = n(1.5)
    for i in range(X):
        out[i] += out[k - X + i] if k - X + i < k else 0
    return out


if __name__ == '__main__':
    for v in range(3):
        write(f'SFX_FoxStep_0{v + 1}', step(100 + v), 0.6)
        write(f'SFX_EnemyStep_0{v + 1}', enemy_step(200 + v), 0.8)
    write('SFX_Hit', hit())
    write('SFX_BoxPick', pick(), 0.6)
    write('SFX_BoxDrop', drop())
    write('SFX_GlitchScreen', glitch(1.2, 41, 1.0), 0.6)
    write('SFX_GlitchObject', glitch(0.8, 43, 1.6), 0.55)
    write('SFX_DlgFox', dlg_fox(), 0.45)
    write('SFX_DlgSystem', dlg_sys(), 0.4)
    write('SFX_Lift', lift(), 0.75)
    write('SFX_BridgeRotate', bridge(), 0.75)
    write('SFX_Gate', gate(), 0.6)
    write('SFX_Shimmer', shimmer(), 0.6)
    write('AMB_Wilds_Loop', ambience(), 0.35)
    write('BGM_Storybook_Loop', bgm(), 0.5)
