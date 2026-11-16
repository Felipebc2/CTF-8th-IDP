# Inclinação

- **Category:** Rev
- **Points:** 377 (final dynamic value) · 🩸 first blood
- **Description:** "Tente se equilibrar!"
- **Files:** `e1913ed02568f143e356795396bfbd63.zip` (sha256 `22200c0014cc075e7b6966f2ababef24b56eaf00c2f674110f39ddddb0a39e83`) → `Inclinacao.apk` (sha256 `fd966f1314978c8686a319bea478d7ef2678859d5d61842fc2eb39c3455738d5`)
- **Status:** ✅ solved — `IDP{3sp3r0_qU3_nA0_t3nh4_seguR4d0_NA_M40_8df258w89}` (server-issued after holding a real phone at 13.5° / 37.5° for 133.7 s)

## Static findings (jadx, `work/`)

- libGDX tilt game, package `site.idpctf.inclinacao`; no `IDP{` in APK. Server: `<HOST>`.
- `ChallengeClient`: `POST /api/session` (sid + challenge) → `/api/register` (AndroidKeyStore hardware key attestation; emulator/root → 403) → `/api/sample` every 500 ms `{sid, seq, inclCd, rotCd, sig}` signed with the attested key. Response field `reward` = flag, shown by `AndroidLauncher.showReward` ("Parabéns!").
- `logic/HoldRule.isGood`: inclination ∈ **[13.00°, 14.00°)** and rotation ∈ **[37.00°, 38.00°)**, held for **133.7 s** (`HOLD_MS` 133700); gap > 2.5 s between samples breaks the hold.
- `logic/Tilt`: inclination = `atan2(hypot(gx,gy), gz)` (0° = flat, face up); rotation = `atan2(-gx,-gy)` mod 360, raw device axes.
- Sent values come from `SharedGravity.reading()` (raw gravity, 10-sample mean). Recenter (double tap) only affects ball control, not the sample. The HUD ("Inclinação x,x° / Rotação x,x°") shows the same reading as sent, rounded to 0.1°.

## Plan

Real non-rooted Android phone, online. Rest it on a stable wedge until the HUD reads ~**13,5°** / ~**37,5°**, don't touch it for ≥ 134 s, and read the reward dialog.
