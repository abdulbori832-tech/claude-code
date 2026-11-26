"""Draft voice for testing a script's pacing (NOT the final voice): python draft_voice.py script.txt out.wav [voice]
Needs: pip install kokoro-onnx, and the two model files next to this script:
  kokoro-v1.0.onnx, voices-v1.0.bin  (github.com/thewh1teagle/kokoro-onnx, releases 'model-files-v1.0')."""
import os, sys
import soundfile as sf
from kokoro_onnx import Kokoro

here = os.path.dirname(os.path.abspath(__file__))
k = Kokoro(os.path.join(here, "kokoro-v1.0.onnx"), os.path.join(here, "voices-v1.0.bin"))
a, sr = k.create(open(sys.argv[1]).read().strip(), voice=sys.argv[3] if len(sys.argv) > 3 else "am_michael", speed=0.92, lang="en-us")
sf.write(sys.argv[2], a, sr)
print(f"{len(a) / sr:.1f} s")
