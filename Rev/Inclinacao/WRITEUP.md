<div align="center">

<a href="https://git.io/typing-svg"><img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=28&duration=700&pause=1000&color=E8423F&center=true&vCenter=true&repeat=false&width=500&height=35&lines=INCLINA%C3%87%C3%83O" alt="Typing SVG" /></a>

</div>

# Inclinação — REV · 🟡 MEDIUM

- **Status:** ✅ SOLVED — I read the hold rule from the APK statically, then the flag was issued by the server after physical play on a real phone
- **Points:** 377 (final dynamic value) · 🩸 first blood
- **Flag:** `IDP{3sp3r0_qU3_nA0_t3nh4_seguR4d0_NA_M40_8df258w89}`
- **Attachment:** `e1913ed02568f143e356795396bfbd63.zip` (sha256 `22200c0014cc075e7b6966f2ababef24b56eaf00c2f674110f39ddddb0a39e83`) → `Inclinacao.apk` (sha256 `fd966f1314978c8686a319bea478d7ef2678859d5d61842fc2eb39c3455738d5`; Android, Kotlin + libGDX, R8-obfuscated)
- **Prompt:** *"Tente se equilibrar!"* ("Try to balance yourself!")

---

## TL;DR

1. `Inclinacao.apk` is a libGDX tilt game in which you steer a ball along an endless track with side paths. The track and the distance counter are a decoy.
2. The flag is not in the APK. The app streams signed `(inclination, rotation)` samples of the **phone** to the server, and the signing key is hardware-attested. The server returns a `reward` once the phone has been held at **13°–14° inclination and 37°–38° rotation for 133.7 s** (the numbers spell 1337).
3. I propped a real, non-rooted phone on a wedge until the HUD read about 13.5° / 37.5° and left it untouched for about 2:15. The "Parabéns!" dialog then showed the flag.

## Analysis

### Triage

```
Inclinacao.apk
├── classes.dex            444 KB   (app + libGDX + kotlinx, R8-minified)
├── lib/*/libgdx*.so                (stock libGDX natives, no custom JNI)
├── assets/sounds/{fall,pipe,success,water}.wav
└── assets/textures/ball.png
```

There is no `IDP{` string in the dex, the resources or the assets. `jadx -d work dist/Inclinacao.apk` shows that the app package is `site.idpctf.inclinacao`, and that `BuildConfig.SERVER_URL` points to `<HOST>`. So the flag comes from a server.

### Protocol (`ApiClient`, `ChallengeClient`, `AttestedKey`)

| Endpoint | Body | Purpose |
|---|---|---|
| `POST /api/session` | `{}` | returns `sid` and a 32-byte `challenge` |
| `POST /api/register` | `{sid, chain}` | sends the certificate chain of an AndroidKeyStore key generated with `challenge` as the attestation challenge. The server rejects emulators and rooted devices with 403 *"atestação rejeitada"* |
| `POST /api/sample` | `{sid, seq, incl_cd, rot_cd, sig}` | sent every 500 ms. `sig` is computed with the attested key over `sid\|seq\|inclCd\|rotCd`. The response may carry `reward` |

`AndroidLauncher.showReward` shows `reward` in a dialog titled "Parabéns!" with a "Copiar" button.

The sample contains **only** the two angles. Ball position, distance and the track never leave the device, so playing the track is irrelevant. Forging samples, for example from a patched APK or an emulator with a spoofed sensor, fails because each sample has to be signed by a key attested by real hardware.

### The hold rule (`logic/HoldRule`)

```java
public static final long HOLD_MS = 133700;      // 133.7 s
public static final long MAX_GAP_MS = 2500;     // a gap of more than 2.5 s between samples resets the hold
public static final long MIN_SAMPLE_INTERVAL_MS = 300;
public static final int TARGET_INCL_CD = 1300;  // centi-degrees, so 13.00°
public static final int TARGET_ROT_CD = 3700;   // 37.00°
public static final int WINDOW_CD = 100;        // 1.00°

public final boolean isGood(int i, int i2) {
    int i3 = i - 1300;
    return i3 >= 0 && i3 < 100 && Math.floorMod(i2 + (-3700), FULL_TURN_CD) < 100;
}
```

The window is one-sided: inclination must be in **[13.00°, 14.00°)** and rotation in **[37.00°, 38.00°)**. The client ships this rule, and the server enforces the same check on the signed samples. 13 / 37 / 133.7 is a "1337" nod.

### What the angles mean (`logic/Tilt`, `GravitySensor`, `SharedGravity`)

- The input is the raw device-frame gravity vector from `TYPE_GRAVITY`, or from a low-pass-filtered accelerometer when that sensor is missing. It is then averaged over 10 samples (`GravityFilter`).
- `inclination = atan2(hypot(gx, gy), gz)` in degrees. 0° means the phone lies flat, face up.
- `rotation = atan2(-gx, -gy)` mod 360, i.e. the direction of the tilt in the screen plane.
- Double-tap "recentralizar" only re-zeroes the ball control (`TiltControl`). The sampled values come from `SharedGravity.reading()`, which recentering does not touch.
- The HUD's "Inclinação x,x° / Rotação x,x°" (`LevelDisplay`) is built from the same reading, rounded to 0.1°. It is therefore a direct readout of what the server receives.
- Sampling stops only in `AndroidLauncher.onPause`, i.e. when the app goes to the background or the screen turns off. Neither the in-game pause nor the ball falling stops it.

### Solve

1. I installed the original APK (`adb install`) on a real, non-rooted Android phone with network access.
2. I disabled the screen auto-lock.
3. I propped the phone on a wedge on a table and adjusted it until the HUD read about **13.5°** inclination and **37.5°** rotation, the middle of both windows.
4. I left it untouched for about 2:15, longer than 133.7 s. The ball fell off the track, which doesn't matter.
5. The "Parabéns!" dialog showed `IDP{3sp3r0_qU3_nA0_t3nh4_seguR4d0_NA_M40_8df258w89}` ("hope you weren't holding it in your hand").

## What didn't work

| Hypothesis | Result | Why |
|---|---|---|
| Flag hidden in dex, resources or assets | ✗ | no `IDP{`, no encrypted blob. The flag only exists server-side |
| Play the track far enough (≈ 950 m played) | ✗ | distance is never sent to the server. The track is a decoy |
| Offline derivation / patched APK / emulator | ✗ (not attempted against the server) | samples are signed by a hardware-attested key, so the server rejects emulators and root |

## Conclusion

This is a "rev to learn the rules" challenge. Static analysis can't produce the flag, but it gives the exact physical condition: a 1°-wide window on two angles, held for 133.7 s, which is nearly impossible by hand while playing. The decompiled HUD code proves that the on-screen readout is the same value the server checks, so a phone resting on a wedge solves it.

---

## Appendix — tools

- `jadx -d work dist/Inclinacao.apk`: decompile. The key files are `site/idpctf/inclinacao/{ApiClient,ChallengeClient,AttestedKey,AndroidLauncher}.java` and `logic/{HoldRule,Tilt,LevelDisplay}.java`.
- There is no solve script: the flag is issued by the server after physical play.
