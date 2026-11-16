<div align="center">

<a href="https://git.io/typing-svg"><img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=28&duration=700&pause=1000&color=E8423F&center=true&vCenter=true&repeat=false&width=500&height=35&lines=COFRE" alt="Typing SVG" /></a>

</div>

# Cofre — REV · 🔴 HARD

- **Status:** ✅ SOLVED — key + combination + MAC reversed offline; server opened on the replayed `/api/step` sequence
- **Points:** 259 (final dynamic value)
- **Flag:** `IDP{L0sT_1n_th3_nUmB3rS_4jd8s4A3}`
- **Attachment:** `ff5278781171c437d89a980957f4587b.zip` (sha256 `ea05de5a1125a97573db86d333c7cd88f8927ab1d472667023f1a8584498e425`) → `Cofre-unsigned.ipa` (iOS, Swift 6 / SwiftUI, Mach-O 64-bit arm64, bundle `com.j3r3mias.cofre`)
- **Prompt:** *"E cofre digital, já abriu?"* ("And a digital safe, opened it yet?")

---

## TL;DR

1. iOS app: a combination safe whose dial is turned by rotating the phone (CoreMotion). Each dialed number is HMAC-signed with an embedded key and sent to a server, which holds the real combination and returns the flag when opened.
2. The HMAC key is embedded but XOR-obfuscated; the combination is a static array in the binary → **`[4, 8, 15, 16, 23, 42]`** (the *Lost* numbers).
3. Recover key + MAC format statically, then replay the `/api/session` → `/api/step` protocol with correct signatures to open the safe server-side.

## Analysis

### Bundle
`Payload/Cofre.app/Cofre` — Swift 6.2 toolchain (`/home/j3r3mias/.../swiftly/toolchains/6.4.1`), CryptoKit. Types: `CofreApp`, `ContentView`, `CofreViewModel`, `CofreAPI`, `MotionSensor`, and core module `CofreCore` (`SafeStateMachine`, `DialMath`, `DialHysteresis`, `RotationTracker`, `RotationDirection`, `ChallengeCombination`, `ProtocolMAC`, `GeneratedConfiguration`).

### Dial math (`CofreCore.DialMath`)
- `positions = 60`, `degreesPerPosition = 6.0`.
- `number(for: heading) = floor(((heading + 3) mod 360) / 6) mod 60` — a 60-notch safe dial (the `+3` snaps to the nearest notch).

### The combination (`CofreCore.ChallengeCombination.values`)
Static `[Int]` storage at `0x1000249b0`; elements (hex) `04 08 0f 10 17 2a`:

> **`[4, 8, 15, 16, 23, 42]`**

### The HMAC key (`GeneratedConfiguration.obfuscatedHMACKey`)
`Cofre.API.init` (`0x100005148`) deobfuscates it with a fixed XOR:

```
x28 = &obfuscatedHMACKey (0x1000240f0); bytes at +0x28 (0x100024118), 32 of them
w19 = 0xA7
loop i in 0..31:  key[i] = obf[i] XOR 0xA7
```

Obfuscated bytes `11 97 92 fd 65 98 67 fd 51 b4 74 8d e8 72 b6 dc f9 2d bd 55 24 0f 5b 37 53 c7 b0 9b 81 b0 ad ec` → **key (raw 32 bytes, used directly as the `SymmetricKey`)**:

```
b630355ac23fc05af613d32a4fd5117b5e8a1af283a8fc90f460173c26170a4b
```

### The MAC (`CofreCore.ProtocolMAC.hex(key:sid:nonce:step:value:direction:)`)
Mangling gives `key: [UInt8]` (raw bytes, **not** a UTF-8 string). The function builds the message by `|`-joined interpolation and HMAC-SHA256s it:

```
message = "<sid>|<nonce>|<step>|<value>|<direction>"
mac     = hex(HMAC_SHA256(key, message))        # lowercase hex
```

`RotationDirection.rawValue`: `0 → "cw"`, `1 → "ccw"`, `2 → "none"`.

### Protocol (`CofreAPI`)
- Base `https://cofre-rev.desafio.<DOMAIN>`, `application/json`, `User-Agent: Cofre/1.0`.
- `POST /api/session` → `Session { sid, nonce }`.
- `POST /api/step`, body keys **`sid`, `i`, `value`, `dir`, `mac`**. The subtle one: `Body.CodingKeys` maps the `step` field to JSON key **`"i"`** (not `"step"`), and `step` is **1-based**. `nonce` is never resent — the server tracks it per session; the MAC binds the client to the right step/nonce.
- `StepReply { ok, open: Bool, flag: String? }`. Server enforces a **10 s rate limit** between steps (`429 "muito rápido: aguarde 10 s entre passos"`).
- Directions **alternate** starting clockwise: `cw, ccw, cw, ccw, cw, ccw` over the six numbers.

Since the app signs with an embedded key, the whole motion UI is bypassable: compute the six MACs and POST them in order (one session, ≥10 s apart).

## What didn't work

| Hypothesis | Result | Why |
|---|---|---|
| `key` is a `String`, SymmetricKey = `Data(key.utf8)` | ✗ | demangling shows `Says5UInt8VG` = `[UInt8]`; XOR output isn't valid UTF-8 → key is raw bytes |
| body key for step is `"step"` | ✗ | `CodingKeys(stringValue:)` matches `"i"` for the step field → any other name = `400 "formato inválido"` |
| `step` 0-based | ✗ | server accepts only `step` starting at **1** |
| hammer convention variants back-to-back | ✗ | `429` rate limit (10 s/step) — must use one session with delays |

## Conclusion

Static analysis yields everything: XOR-deobfuscated 32-byte key, the *Lost* combination, the exact MAC string, the `"i"` JSON remap, 1-based steps, and the alternating cw/ccw directions. One session replaying six signed `/api/step` calls (≥10 s apart, `cw/ccw` alternating) opens the safe and the server returns `IDP{L0sT_1n_th3_nUmB3rS_4jd8s4A3}`.

---

## Appendix — tools

- `solve.py` — `python3 solve.py`: opens one session, then signs and POSTs the six combination numbers to `/api/step` (1-based, `cw/ccw` alternating, ≥11 s apart for the rate limit), learning any step's direction from a rejection and retrying; prints the flag on `open: true`.
