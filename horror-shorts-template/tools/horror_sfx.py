"""Horror sound bed + mix. Usage: python horror_sfx.py cues.json voice.wav out_mix.wav
cues.json: {"duration": s, "drone": [a,b], "hum": [a,b], "steps": [a,b], "flicker": [[a,b],...], "heartbeat": [a,b],
            "ticks": [t,...], "paper": [t,...], "beep": [t,...], "riser": [a,b], "impact": t, "sting": t}
Everything is synthesised here: no third-party sound files, no licences to worry about."""
import json, os, sys, subprocess, tempfile, numpy as np
from scipy.io import wavfile
from scipy.signal import butter, lfilter, fftconvolve

SR = 48000
rng = np.random.default_rng(7)
cues = json.load(open(sys.argv[1]))
N = int(cues["duration"] * SR)
L = np.zeros(N); R = np.zeros(N)

def put(sig, t, gain=1.0, pan=0.0):
    i = int(t * SR)
    if i >= N: return
    s = sig[: N - i] * gain
    L[i:i + len(s)] += s * (1 - max(0, pan)); R[i:i + len(s)] += s * (1 + min(0, pan))
def bp(x, lo, hi, o=2): b, a = butter(o, [lo / (SR / 2), hi / (SR / 2)], "band"); return lfilter(b, a, x)
def lp(x, hi, o=2): b, a = butter(o, hi / (SR / 2)); return lfilter(b, a, x)
def hp(x, lo, o=2): b, a = butter(o, lo / (SR / 2), "high"); return lfilter(b, a, x)
def tt(d): return np.arange(int(d * SR)) / SR
def fade(x, a=0.05, b=0.3):
    n = len(x); e = np.ones(n); ia, ib = int(a * SR), int(b * SR)
    e[:ia] = np.linspace(0, 1, ia); e[n - ib:] = np.linspace(1, 0, ib); return x * e

if "drone" in cues:  # detuned low saws + wind
    a, b = cues["drone"]; t = tt(b - a)
    d = sum(((t * f) % 1 - 0.5) for f in (43.6, 44.1, 65.4, 87.6)) * 0.25
    d = lp(d, 220) + lp(rng.standard_normal(len(t)), 400) * 0.25 * (0.6 + 0.4 * np.sin(2 * np.pi * 0.13 * t))
    put(fade(d, 1.5, 0.8), a, 0.35)
if "hum" in cues:  # fluorescent 120 Hz hum
    a, b = cues["hum"]; t = tt(b - a)
    h = np.sin(2 * np.pi * 120 * t) * 0.6 + np.sign(np.sin(2 * np.pi * 240 * t)) * 0.05
    put(fade(h, 0.5, 0.02), a, 0.035)
for a, b in cues.get("flicker", []):  # electrical crackle bursts
    t0 = a
    while t0 < b:
        c = hp(rng.standard_normal(int(0.03 * SR)), 1500) * np.exp(-tt(0.03) * 120)
        put(c, t0, 0.5, rng.uniform(-0.5, 0.5)); t0 += rng.uniform(0.04, 0.16)
if "steps" in cues:
    a, b = cues["steps"]; t0 = a
    while t0 < b:
        s = lp(rng.standard_normal(int(0.18 * SR)), 900) * np.exp(-tt(0.18) * 28) + np.sin(2 * np.pi * 70 * tt(0.18)) * np.exp(-tt(0.18) * 35)
        put(s, t0, 0.5, -0.2); t0 += 0.52
if "heartbeat" in cues:
    a, b = cues["heartbeat"]; t0 = a; per = 0.95
    while t0 < b:
        for k, g in ((0, 1.0), (0.17, 0.7)):
            beat = np.sin(2 * np.pi * 52 * tt(0.22)) * np.exp(-tt(0.22) * 18)
            put(beat, t0 + k, 0.9 * g)
        t0 += per; per = max(0.48, per * 0.93)
for t0 in cues.get("ticks", []):
    k = bp(rng.standard_normal(int(0.05 * SR)), 2500, 6000) * np.exp(-tt(0.05) * 90)
    put(k, t0, 0.6)
for t0 in cues.get("paper", []):
    p = bp(rng.standard_normal(int(0.5 * SR)), 2000, 7000) * (np.abs(np.sin(2 * np.pi * 9 * tt(0.5))) ** 2) * np.exp(-tt(0.5) * 4)
    put(p, t0, 0.25)
for t0 in cues.get("beep", []):
    put(fade(np.sign(np.sin(2 * np.pi * 1760 * tt(0.12))) * 0.3, 0.005, 0.02), t0, 0.12)
    put(fade(np.sign(np.sin(2 * np.pi * 1760 * tt(0.12))) * 0.3, 0.005, 0.02), t0 + 0.2, 0.12)
if "riser" in cues:  # dissonant string swell
    a, b = cues["riser"]; t = tt(b - a); env = (t / t[-1]) ** 2
    r = sum(np.sin(2 * np.pi * f * t * (1 + 0.06 * t / t[-1])) for f in (311.1, 329.6, 466.2, 493.9)) * env
    r += hp(rng.standard_normal(len(t)), 3000) * env * 0.6
    put(r, a, 0.12)
if "impact" in cues:  # boom + metallic screech
    t0 = cues["impact"]; t = tt(2.5)
    boom = np.sin(2 * np.pi * np.cumsum(40 + 80 * np.exp(-t * 6)) / SR) * np.exp(-t * 2.2)
    boom += lp(rng.standard_normal(len(t)), 300) * np.exp(-t * 6) * 0.8
    scr = bp(rng.standard_normal(int(1.2 * SR)), 1800, 4200) * np.exp(-tt(1.2) * 3) * (1 + 0.5 * np.sin(2 * np.pi * 31 * tt(1.2)))
    put(boom, t0, 1.0); put(scr, t0, 0.35, 0.3); put(scr[::-1] * 0 + scr, t0 + 0.01, 0.35, -0.3)
if "sting" in cues:
    t0 = cues["sting"]; t = tt(3.0)
    s = sum(np.sin(2 * np.pi * f * t) for f in (55, 58.3, 82.4)) * np.exp(-t * 1.2)
    put(s, t0, 0.5)

bed = np.stack([L, R], 1)
# voice with a short dark room reverb
sr, v = wavfile.read(sys.argv[2]); v = v.astype(np.float64) / 32768.0
if v.ndim > 1: v = v.mean(1)
ir_t = tt(0.9); ir = rng.standard_normal(len(ir_t)) * np.exp(-ir_t * 7); ir = lp(ir, 3000); ir /= np.abs(ir).sum() / 6
wet = fftconvolve(v, ir)[: len(v)]
voice = v + wet * 0.18
voice = np.pad(voice, (0, max(0, N - len(voice))))[:N]
mix = bed + np.stack([voice, voice], 1) * 1.0
mix /= max(1e-9, np.abs(mix).max()) / 0.9
tmp = os.path.join(tempfile.gettempdir(), "_hmix.wav")
wavfile.write(tmp, SR, (mix * 32767).astype(np.int16))
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", tmp, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "48000", sys.argv[3]], check=True)
print("mix written", sys.argv[3])
