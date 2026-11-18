"""Isolate the voice from background music with a UVR MDX-Net ONNX model.

usage: python3 separate_vocals.py model.onnx mix.wav vocals.wav [music.wav]
Input must be 44.1 kHz stereo. Pure numpy STFT, onnxruntime inference.
"""
import sys
import wave
import numpy as np
import onnxruntime as ort

N_FFT, HOP, DIM_F, DIM_T = 7680, 1024, 3072, 256
COMPENSATE = 1.021  # UVR-MDX-NET-Voc_FT
CHUNK = HOP * (DIM_T - 1)
TRIM = N_FFT // 2
GEN = CHUNK - 2 * TRIM
BINS = N_FFT // 2 + 1
WIN = (0.5 - 0.5 * np.cos(2 * np.pi * np.arange(N_FFT) / N_FFT)).astype(np.float32)  # periodic hann


def read_wav(path):
    import subprocess
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "2", "-ar", "44100", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).T.copy()


def write_wav(path, x):
    x = np.clip(x.T, -1, 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(44100)
        w.writeframes((x * 32767).astype(np.int16).tobytes())


def stft(x):  # x: (n, CHUNK) -> (n, BINS, DIM_T) complex, torch center=True reflect
    xp = np.pad(x, ((0, 0), (N_FFT // 2, N_FFT // 2)), mode="reflect")
    idx = np.arange(DIM_T)[:, None] * HOP + np.arange(N_FFT)[None]
    frames = xp[:, idx] * WIN
    return np.fft.rfft(frames, axis=-1).transpose(0, 2, 1)


def istft(spec):  # (n, BINS, DIM_T) -> (n, CHUNK)
    frames = np.fft.irfft(spec.transpose(0, 2, 1), n=N_FFT, axis=-1) * WIN
    L = N_FFT + HOP * (DIM_T - 1)
    out = np.zeros((spec.shape[0], L), np.float64)
    norm = np.zeros(L, np.float64)
    for t in range(DIM_T):
        out[:, t * HOP:t * HOP + N_FFT] += frames[:, t]
        norm[t * HOP:t * HOP + N_FFT] += WIN ** 2
    out /= np.maximum(norm, 1e-8)
    return out[:, N_FFT // 2:N_FFT // 2 + CHUNK]


def to_model(waves):  # (B, 2, CHUNK) -> (B, 4, DIM_F, DIM_T)
    B = waves.shape[0]
    s = stft(waves.reshape(-1, CHUNK))[:, :DIM_F]           # (B*2, F, T)
    s = np.stack([s.real, s.imag], 1).reshape(B, 4, DIM_F, DIM_T)  # ch0 re, ch0 im, ch1 re, ch1 im
    return s.astype(np.float32)


def from_model(spec):  # (B, 4, DIM_F, DIM_T) -> (B, 2, CHUNK)
    B = spec.shape[0]
    full = np.zeros((B, 4, BINS, DIM_T), np.float32)
    full[:, :, :DIM_F] = spec
    full = full.reshape(B * 2, 2, BINS, DIM_T)
    return istft(full[:, 0] + 1j * full[:, 1]).reshape(B, 2, CHUNK)


def separate(sess, mix):
    n = mix.shape[1]
    pad = GEN - n % GEN
    mp = np.concatenate([np.zeros((2, TRIM)), mix, np.zeros((2, pad)), np.zeros((2, TRIM))], 1)
    waves = np.stack([mp[:, i:i + CHUNK] for i in range(0, n + pad, GEN)])
    out = []
    for b in range(0, len(waves), 4):
        w = waves[b:b + 4]
        pos = sess.run(None, {"input": to_model(w)})[0]
        neg = sess.run(None, {"input": to_model(-w)})[0]
        out.append(from_model((pos - neg) * 0.5))  # denoise: average with phase-inverted pass
        print(f"  {min(b + 4, len(waves))}/{len(waves)}", flush=True)
    v = np.concatenate(out)[:, :, TRIM:-TRIM].transpose(1, 0, 2).reshape(2, -1)[:, :n]
    return v * COMPENSATE


if __name__ == "__main__":
    model, src, dst = sys.argv[1:4]
    mix = read_wav(src).astype(np.float64)
    sess = ort.InferenceSession(model, providers=["CPUExecutionProvider"])
    voc = separate(sess, mix)
    write_wav(dst, voc)
    if len(sys.argv) > 4:
        write_wav(sys.argv[4], mix - voc)
    print("done")
