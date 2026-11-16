<div align="center">

<a href="https://git.io/typing-svg"><img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=28&duration=700&pause=1000&color=E8423F&center=true&vCenter=true&repeat=false&width=500&height=35&lines=ZOOM" alt="Typing SVG" /></a>

</div>

# Zoom — REV · 🟢 EASY

- **Status:** ✅ SOLVED — flag recovered statically from the APK, no device needed
- **Points:** 184 (final dynamic value)
- **Flag:** `IDP{zOOOOOOm_dOs_MaiS_cHaTos}`
- **Attachment:** `35e0e2c898cc0035a1595e5a3a7c9558.zip` (sha256 `e0e7cba1f83c286e6810469f3cc4cc5b10cc70312b3b0d70ffb38ce3b8e01fcb`) → `Zoom.apk` (Android, Kotlin + Jetpack Compose, R8-obfuscated)
- **Prompt:** *"Em uma galáxia muito muito distante."* ("In a galaxy far far away.")

---

## TL;DR

1. `Zoom.apk` is a Compose "game": a 31 MB video of a galaxy that zooms in one step per pinch-out gesture. After **1337** consecutive pinches it shows the flag.
2. The flag isn't computed or fetched. It's a compile-time constant, `BuildConfig.FLAG_ROT13`, that only goes through ROT13.
3. `strings` on `classes.dex` (or jadx) gives `VQC{mBBBBBBz_qBf_ZnvF_pUnGbf}`, and ROT13 turns it into the flag.

## Analysis

### Unpacking

```
Zoom.apk
├── classes.dex          2.6 MB   (app + androidx/media3)
├── res/gy.mp4          31.1 MB   (the galaxy zoom video, R8-renamed)
├── res/X0.mp3           0.9 MB   (background music loop)
└── lib/*/libandroidx.graphics.path.so   (stock Compose, no custom native code)
```

The media files are huge, but there's no custom `.so`, so all the logic has to be in the dex.

### Quick strings

`strings -a classes.dex | grep -i flag` already gives away the design: `FLAG_ROT13`, `FlagOverlay`, and the package `site.idpctf.zoom` (`FrameSeeker`, `ZoomGame`, ...).

### Decompiled app (jadx)

`site/idpctf/zoom/BuildConfig.java`:

```java
public static final String FLAG_ROT13 = "VQC{mBBBBBBz_qBf_ZnvF_pUnGbf}";
public static final int START_COUNT = 1337;
```

The constant is read in one place only, `ZoomScreenKt.FlagOverlay`:

```java
objJ = Rot13.INSTANCE.apply(BuildConfig.FLAG_ROT13);   // shown in a Text() + copied to clipboard
```

`logic/Rot13.apply` looks odd after R8 (`(c - 'T') % 26 + 'a'`, `(c - '4') % 26 + 'A'`), but `'T' = 'a' - 13` and `'4' = 'A' - 13`, so it's plain ROT13. Digits and `{_}` pass through unchanged.

### The intended path (what we skipped)

- `ZoomGame(frameCount, total = 1337, startCount = 1337)` maps the remaining count onto a frame index of `gy.mp4` (`FrameTarget.base/target`), so every pinch advances the zoom into the galaxy.
- `PinchDetector` counts a pinch only when the distance between the two fingers grows to **1.5×** its minimum since arming (`log(span/min)/ln 1.5` is the progress bar). After that the fingers must close back to ≤ 0.7× before the next pinch can arm.
- `ZoomGame.onPointers(emptyList)` calls `reset()`: lifting every finger sends the counter back to 1337.
- `ZoomContent` shows `Header(remaining)` while `remaining > 0`, and `FlagOverlay` once it reaches 0.

So the "legit" solve is 1337 pinch-outs in a row without ever lifting both fingers. The flag text makes fun of exactly that: *"zOOOOOOm dOs MaiS cHaTos"* ("the most annoying zoom").

## What didn't work

| Hypothesis | Result | Why |
|---|---|---|
| Flag rendered in a frame of `gy.mp4` / spectrogram in `X0.mp3` | not needed | the media is just scenery, the flag is a dex constant |
| Encrypted payload / runtime class loading | ✗ | no crypto or `DexClassLoader` in `site.idpctf.zoom`, only ROT13 |

## Conclusion

The flag sits in the APK, protected only by ROT13 and a 1337-gesture grind. It's the same lesson as Legibilidade: `strings` before anything else. The R8 obfuscation and the 31 MB video are there to slow you down, not to protect anything.

---

## Appendix — tools

- `solve.py` — `python3 solve.py [zip]`: opens the challenge zip → `Zoom.apk` → `classes.dex`, finds `VQC{...}` and prints the ROT13 decode. Standard library only.
- `jadx -d out Zoom.apk` — decompilation used for the analysis (`out/` is not committed).
