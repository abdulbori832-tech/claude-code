"""Word timings for captions and editing: python voice_words.py voice.(mp3|wav) out_dir
Writes out_dir/voice.wav (48 kHz mono, +0.1 s lead-in) and out_dir/words.json [{w,s,e}]."""
import json, os, subprocess, sys
import numpy as np
from faster_whisper import WhisperModel

src, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", src, "-af", "adelay=100", "-ar", "48000", "-ac", "1", os.path.join(out, "voice.wav")], check=True)
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(out, "voice.wav"), "-ar", "16000", "-ac", "1", "-f", "f32le", "-"], capture_output=True).stdout
audio = np.frombuffer(raw, np.float32)
model = WhisperModel("small.en", device="cpu", compute_type="int8")
segs, _ = model.transcribe(audio, word_timestamps=True, language="en")
words = [{"w": w.word.strip(), "s": round(w.start, 3), "e": round(w.end, 3)} for s in segs for w in s.words]
json.dump(words, open(os.path.join(out, "words.json"), "w"), indent=0)
print(f"{len(words)} words, {len(audio) / 16000:.1f} s")
print(" ".join(f'{w["w"]}@{w["s"]}' for w in words))
