"""Narrate a list of paragraphs with a local Piper voice.

Each paragraph is synthesised separately and joined with fixed pauses, so the
scene timings are exact. Writes OUT.wav (48 kHz stereo, deepened + mastered)
and OUT.json ({"segments": [[start, end], ...]} in seconds, incl. lead-in).

usage: python3 tts_piper.py MODEL.onnx TEXT.txt OUT [--len 1.15] [--pitch 0.9] [--pause 0.9]
TEXT.txt: one paragraph per line (blank lines ignored).
"""
import argparse, json, subprocess, wave, io
import numpy as np
from piper import PiperVoice, SynthesisConfig

ap = argparse.ArgumentParser()
ap.add_argument("model"); ap.add_argument("text"); ap.add_argument("out")
ap.add_argument("--len", type=float, default=1.15, help="length scale (>1 = slower)")
ap.add_argument("--pitch", type=float, default=0.9, help="pitch factor (<1 = deeper), tempo kept")
ap.add_argument("--pause", type=float, default=0.9)
ap.add_argument("--lead", type=float, default=0.5)
ap.add_argument("--tail", type=float, default=2.0)
a = ap.parse_args()

voice = PiperVoice.load(a.model)
cfg = SynthesisConfig(length_scale=a.len, noise_scale=0.6, noise_w_scale=0.7)
paras = [l.strip() for l in open(a.text, encoding="utf-8") if l.strip()]
sr = voice.config.sample_rate
chunks, segs, t = [np.zeros(int(a.lead * sr), np.int16)], [], a.lead
for p in paras:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        voice.synthesize_wav(p, w, syn_config=cfg)
    buf.seek(0)
    with wave.open(buf) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), np.int16)
    # trim leading/trailing near-silence so pauses are exact
    nz = np.where(np.abs(x) > 300)[0]
    x = x[max(0, nz[0] - int(0.03 * sr)): nz[-1] + int(0.08 * sr)] if len(nz) else x
    segs.append([round(t, 3), round(t + len(x) / sr, 3)])
    t += len(x) / sr + a.pause
    chunks += [x, np.zeros(int(a.pause * sr), np.int16)]
chunks[-1] = np.zeros(int(a.tail * sr), np.int16)
raw = np.concatenate(chunks)
tmp = a.out + ".raw.wav"
with wave.open(tmp, "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(raw.tobytes())
# deepen (pitch down, tempo preserved), warm EQ, gentle room, loudness
af = (f"asetrate={sr}*{a.pitch},aresample={sr},atempo={1 / a.pitch:.5f},"
      "highpass=f=60,equalizer=f=140:t=q:w=1.2:g=3,equalizer=f=3500:t=q:w=1.5:g=-2,"
      "aecho=0.8:0.6:40|70:0.12|0.07,acompressor=threshold=-20dB:ratio=2.5:attack=8:release=120,"
      "loudnorm=I=-14:TP=-1.5:LRA=9")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-af", af, "-ar", "48000", "-ac", "2", a.out + ".wav"], check=True)
json.dump({"source": f"piper {a.model.split('/')[-1]} len={a.len} pitch={a.pitch}", "segments": segs},
          open(a.out + ".json", "w"), indent=1)
print(f"{a.out}.wav  {t:.1f}s  {len(segs)} segments")
