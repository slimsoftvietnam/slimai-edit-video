"""Look at a music track without hearing it: tempo and beat grid (spectral-flux onsets, autocorrelation), the energy
of every bar, and a log-frequency spectrogram with the bar lines drawn, to find its sections (intro, build, drop,
breakdown, outro) and the bars where it can be cut.

python music_analyse.py TRACK.wav OUT_PREFIX
-> OUT_PREFIX_spec.png and a printed table: bar, time, RMS dB, low / mid / high energy, onset density
"""
import sys
import wave

import numpy as np
from PIL import Image, ImageDraw
from scipy import signal

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
src, prefix = sys.argv[1], sys.argv[2]
w = wave.open(src)
sr = w.getframerate()
ch = w.getnchannels()
x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64).reshape(-1, ch) / 32768
mono = x.mean(1)
dur = len(mono) / sr

# onset envelope: positive spectral flux on a log-magnitude STFT, hop 10 ms
hop = sr // 100
f, t, Z = signal.stft(mono, sr, nperseg=2048, noverlap=2048 - hop, boundary=None)
mag = np.log1p(np.abs(Z) * 100)
flux = np.maximum(0, np.diff(mag, axis=1)).sum(0)
flux = (flux - flux.mean()) / (flux.std() + 1e-9)
env_t = t[1:]

# tempo: autocorrelation of the onset envelope between 70 and 180 BPM
ac = np.correlate(flux, flux, mode="full")[len(flux) - 1:]
lags = np.arange(len(ac)) / 100.0
lo, hi = int(100 * 60 / 180), int(100 * 60 / 70)
best = lo + int(np.argmax(ac[lo:hi]))
bpm = 60.0 / (best / 100.0)
# refine around the peak with parabolic interpolation
if 1 <= best < len(ac) - 1:
    a_, b_, c_ = ac[best - 1], ac[best], ac[best + 1]
    off = 0.5 * (a_ - c_) / (a_ - 2 * b_ + c_ + 1e-12)
    bpm = 60.0 / ((best + off) / 100.0)
beat = 60.0 / bpm
# beat phase: the offset whose comb of beats collects the most flux
phases = np.arange(0, beat, 0.01)
scores = []
for ph in phases:
    idx = ((np.arange(ph, dur, beat)) * 100).astype(int)
    idx = idx[idx < len(flux)]
    scores.append(flux[idx].mean())
phase = phases[int(np.argmax(scores))]
print(f"{src}: {dur:.1f} s, tempo {bpm:.2f} BPM (beat {beat:.3f} s, bar of 4 = {4 * beat:.3f} s), first beat at {phase:.3f} s")

# per-bar table (bars of 4 beats from the phase; the downbeat may be any of the 4, judged from the low end)
bar = 4 * beat
lowb = signal.sosfilt(signal.butter(4, 150, "lowpass", fs=sr, output="sos"), mono)
midb = signal.sosfilt(signal.butter(4, [300, 3000], "bandpass", fs=sr, output="sos"), mono)
highb = signal.sosfilt(signal.butter(4, 5000, "highpass", fs=sr, output="sos"), mono)
# downbeat: which of the 4 beats carries the most low-end energy on average
beat_low = []
for k in range(4):
    vals = []
    tt = phase + k * beat
    while tt + 0.12 < dur:
        s = int(tt * sr)
        vals.append(np.sqrt((lowb[s:s + int(0.12 * sr)] ** 2).mean()))
        tt += bar
    beat_low.append(np.mean(vals))
down = phase + int(np.argmax(beat_low)) * beat
while down - bar >= 0:
    down -= bar
print(f"downbeat grid starts at {down:.3f} s (low-end weight per beat: {', '.join(f'{v:.4f}' for v in beat_low)})")


def db(v):
    return 20 * np.log10(np.sqrt((v ** 2).mean()) + 1e-9)


print(" bar   time    rms   low   mid  high  onsets")
rows = []
tt = down
n = 0
while tt + bar <= dur + 0.01:
    s0, s1 = int(tt * sr), int(min(dur, tt + bar) * sr)
    on = flux[int(tt * 100):int((tt + bar) * 100)]
    rows.append((n, tt, db(mono[s0:s1]), db(lowb[s0:s1]), db(midb[s0:s1]), db(highb[s0:s1]), (on > 1.0).sum()))
    print(f"{n:4d} {tt:6.2f} {rows[-1][2]:6.1f} {rows[-1][3]:5.1f} {rows[-1][4]:5.1f} {rows[-1][5]:5.1f} {rows[-1][6]:5d}")
    tt += bar
    n += 1

# spectrogram with bar lines
fs_, ts_, S = signal.spectrogram(mono, sr, nperseg=4096, noverlap=3072)
S = 10 * np.log10(S + 1e-12)
fl = np.geomspace(30, 16000, 320)
img = np.array([np.interp(fl, fs_, S[:, i]) for i in range(S.shape[1])]).T[::-1]
img = np.clip((img + 110) / 75, 0, 1)
W_, H_ = 1600, 420
im = Image.fromarray((img * 255).astype(np.uint8)).resize((W_, H_)).convert("RGB")
d = ImageDraw.Draw(im)
for (n, tt, *_r) in rows:
    xx = int(tt / dur * W_)
    d.line([(xx, 0), (xx, H_)], fill=(255, 80, 80) if n % 4 == 0 else (90, 90, 160), width=1)
    if n % 4 == 0:
        d.text((xx + 2, 2), str(n), fill=(255, 255, 0))
# energy curve under it
E = np.array([r[2] for r in rows])
curve = Image.new("RGB", (W_, 160), "black")
dc = ImageDraw.Draw(curve)
for (n, tt, rms, *_r) in rows:
    xx = int(tt / dur * W_)
    hh = int(np.clip((rms + 40) / 35, 0, 1) * 150)
    dc.rectangle([xx, 160 - hh, xx + max(2, int(bar / dur * W_) - 2), 160], fill=(80, 200, 140))
out = Image.new("RGB", (W_, H_ + 160))
out.paste(im, (0, 0))
out.paste(curve, (0, H_))
out.save(prefix + "_spec.png")
print("wrote", prefix + "_spec.png")
