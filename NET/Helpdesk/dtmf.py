#!/usr/bin/env python3
# Measure dual-tone bursts in a WAV and map to DTMF. Usage: python3 -I dtmf.py call.wav
import sys, wave, struct
import numpy as np

path = sys.argv[1]
w = wave.open(path, 'rb')
sr = w.getframerate(); n = w.getnframes(); ch = w.getnchannels()
raw = w.readframes(n)
x = np.frombuffer(raw, dtype=np.int16).astype(float)
if ch > 1:
    x = x[::ch]
x /= (np.abs(x).max() or 1)

# Energy envelope to split bursts from silence
win = int(0.02 * sr)                      # 20 ms frames
env = np.array([np.sqrt(np.mean(x[i:i+win]**2)) for i in range(0, len(x)-win, win)])
thr = env.max() * 0.15
active = env > thr

# Group consecutive active frames into segments
segs = []
i = 0
while i < len(active):
    if active[i]:
        j = i
        while j < len(active) and active[j]:
            j += 1
        if (j - i) >= 3:                  # >= ~60 ms to count as a tone
            segs.append((i*win, j*win))
        i = j
    else:
        i += 1

DTMF = {(697,1209):'1',(697,1336):'2',(697,1477):'3',(697,1633):'A',
        (770,1209):'4',(770,1336):'5',(770,1477):'6',(770,1633):'B',
        (852,1209):'7',(852,1336):'8',(852,1477):'9',(852,1633):'C',
        (941,1209):'*',(941,1336):'0',(941,1477):'#',(941,1633):'D'}
LOW = [697,770,852,941]; HIGH=[1209,1336,1477,1633]
def nearest(f, cands): return min(cands, key=lambda c: abs(c-f))

out = []
for a,b in segs:
    seg = x[a:b] * np.hanning(b-a)
    sp = np.abs(np.fft.rfft(seg))
    fr = np.fft.rfftfreq(len(seg), 1/sr)
    band = (fr > 300) & (fr < 2000)
    idx = np.where(band)[0]
    order = idx[np.argsort(sp[idx])[::-1]]
    # pick two dominant peaks that are well separated
    peaks = []
    for k in order:
        if all(abs(fr[k]-fr[p])>150 for p in peaks):
            peaks.append(k)
        if len(peaks)==2: break
    f1,f2 = sorted(fr[p] for p in peaks)
    lo = nearest(f1, LOW); hi = nearest(f2, HIGH)
    ch_ = DTMF.get((lo,hi), '?')
    out.append((a/sr, f1, f2, lo, hi, ch_))

print(f"sr={sr} segments={len(segs)}")
for t,f1,f2,lo,hi,c in out:
    print(f"t={t:5.2f}s  tones=({f1:6.1f},{f2:6.1f})  snap=({lo},{hi})  -> {c}")
print("DTMF string:", ''.join(c for *_,c in out))
