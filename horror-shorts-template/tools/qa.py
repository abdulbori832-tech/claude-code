"""Quick check of a finished short: python qa.py video.mp4
Reports size/fps/length, loudness, black frames, frozen spans (12+ identical frames)."""
import subprocess, sys
import numpy as np

v = sys.argv[1]
info = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height,r_frame_rate:format=duration", "-of", "compact", v], capture_output=True, text=True).stdout
print(info.strip())
loud = subprocess.run(["ffmpeg", "-hide_banner", "-i", v, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
print("LOUDNESS", [l.strip() for l in loud.splitlines() if l.strip().startswith(("I:", "Peak:"))][-2:])
W, H = 108, 192
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", v, "-vf", f"scale={W}:{H}", "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True).stdout
fr = np.frombuffer(raw, np.uint8).reshape(-1, H, W).astype(np.float32)
mean = fr.mean((1, 2)); diff = np.abs(np.diff(fr, axis=0)).mean((1, 2))
black = np.where(mean < 3)[0]
print("FRAMES", len(fr), "| fully black frames:", len(black), "(fine if planned, e.g. a blackout ending)")
frozen, run = [], 0
for i, d in enumerate(diff):
    run = run + 1 if d < 0.05 else 0
    if run == 12: frozen.append(i - 11)
print("FROZEN spans:", frozen or "none")
