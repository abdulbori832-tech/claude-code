"""Fit scene timings to a voice recording -> timings.json.

usage: python3 align_voice.py voice.(wav|mp3|m4a)

Finds pauses with ffmpeg silencedetect, then picks len(SEGMENTS)-1 of them as
scene boundaries by dynamic programming: each boundary should land near the
point the text proportions predict, and longer pauses are preferred. Works for
TTS output and for a human recording read at any pace.
"""
import json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.environ["SEVEN_NO_TIMINGS"] = "1"
from render_seven import SEGMENTS  # noqa: E402


def silences(path, db=-38, dur=0.22):
    log = subprocess.run(["ffmpeg", "-i", path, "-af", f"silencedetect=n={db}dB:d={dur}", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    st = [float(x) for x in re.findall(r"silence_start: ([-\d.]+)", log)]
    en = [float(x) for x in re.findall(r"silence_end: ([-\d.]+)", log)]
    total = float(re.findall(r"time=(\d+):(\d+):([\d.]+)", log)[-1][2]) + \
        60 * float(re.findall(r"time=(\d+):(\d+):([\d.]+)", log)[-1][1])
    return list(zip(st, en)), total


def main(path):
    sil, total = silences(path)
    speech_start = sil[0][1] if sil and sil[0][0] <= 0.05 else 0.0
    speech_end = sil[-1][0] if sil and sil[-1][1] >= total - 0.05 else total
    inner = [(a, b) for a, b in sil if a > speech_start + 0.3 and b < speech_end - 0.3]
    lens = [len(s[3]) for s in SEGMENTS]
    cum, acc = [], 0
    for L in lens[:-1]:
        acc += L; cum.append(acc / sum(lens))
    span = speech_end - speech_start
    targets = [speech_start + c * span for c in cum]
    K, N = len(targets), len(inner)
    if N < K:
        sys.exit(f"found only {N} pauses for {K} boundaries; read with short pauses between lines")
    INF = 1e18
    cost = [[INF] * N for _ in range(K)]
    back = [[-1] * N for _ in range(K)]
    def c(k, j):
        mid = (inner[j][0] + inner[j][1]) / 2
        return (mid - targets[k]) ** 2 / (0.08 * span) ** 2 - 2.0 * (inner[j][1] - inner[j][0])
    for j in range(N):
        cost[0][j] = c(0, j)
    for k in range(1, K):
        best, bi = INF, -1
        for j in range(N):
            if j - 1 >= 0 and cost[k - 1][j - 1] < best:
                best, bi = cost[k - 1][j - 1], j - 1
            if bi >= 0:
                cost[k][j] = best + c(k, j); back[k][j] = bi
    j = min(range(N), key=lambda x: cost[K - 1][x])
    picks = []
    for k in range(K - 1, -1, -1):
        picks.append(j); j = back[k][j]
    picks.reverse()
    segs, s = [], speech_start
    for j in picks:
        segs.append([round(s, 3), round(inner[j][0], 3)]); s = inner[j][1]
    segs.append([round(s, 3), round(speech_end, 3)])
    json.dump({"source": os.path.basename(path), "segments": segs}, open(os.path.join(HERE, "timings.json"), "w"), indent=1)
    for seg, (a, b) in zip(SEGMENTS, segs):
        print(f"{a:6.2f}-{b:6.2f}  {seg[1]}")


if __name__ == "__main__":
    main(sys.argv[1])
