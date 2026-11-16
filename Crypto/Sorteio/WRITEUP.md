<div align="center">

<a href="https://git.io/typing-svg"><img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=28&duration=700&pause=1000&color=E8423F&center=true&vCenter=true&repeat=false&width=500&height=35&lines=SORTEIO" alt="Typing SVG" /></a>

</div>

# Sorteio — CRYPTO · 🟡 MEDIUM

- **Status:** ✅ SOLVED — full mechanism recovered; flag captured live in the in-person test window by scheduling the turn around a precomputed winning second.
- **Points:** 323 (final dynamic value)
- **Flag:** `IDP{s0rt3_n40_3x1st3_VTF7GD46DA4K}` (per-team secret, not in the binary; obtained live by winning)
- **Attachment / Target:** `IDP-Sorteios-Especiais-...-instalador.exe` (NSIS installer wrapping a .NET 10 / WPF desktop app) · `https://sorteio-crypto.desafio.<DOMAIN>`
- **Prompt:** *"Para testar a solução, o time precisa agendar um horário. ... Cada janela tem 5 minutos. ... A próxima janela só pode começar 30 minutos depois do fim da anterior."*

---

## TL;DR

1. The attachment is a Nullsoft (NSIS) installer for a **.NET 10 WPF** app. The draw logic lives in a tiny `IdpSorteios.Core.dll` (13 KB, shipped **with PDBs**).
2. The draw is `number = (new Random(seed).Next() % 1000) + 1`, with **`seed = (int) DateTimeOffset.UtcNow.ToUnixTimeSeconds()`** — a `System.Random` seeded by the **wall-clock second**. `.NET`'s *seeded* `Random(int)` is the deterministic legacy (Knuth subtractive) PRNG, identical on every platform → fully reproducible offline.
3. **You win when the draw returns `42`.** After every draw the engine **reseeds to the current second**, so the value of the *next* draw is locked by the second at which you clicked the *previous* draw. Click a draw on a second `W` where `f(W)==42`, then draw again → `42` → the server hands back your team's flag.

## Analysis

No .NET decompiler was available (no SDK/`ilspycmd`, installs blocked). The assembly was unpacked with `7z` (NSIS) and disassembled with a hand-written ECMA-335 CIL dumper (`solver/ildump.py`). Relevant method bodies (IL, tokens resolved):

### `DrawEngine` — the PRNG

```
CurrentSeed():      (int) _timeProvider.GetUtcNow().ToUnixTimeSeconds()
.ctor / Reseed():   _random = new Random(CurrentSeed())
Draw(cb):           n = ToNumber(_random.Next()); cb(n); Reseed(); return n
ToNumber(x):        (x % 1000) + 1          // => n in [1, 1000]
```

So `_random.Next()` is `.NET`'s `InternalSample()` (first output of the legacy generator), and the draw is `(InternalSample(seed) % 1000) + 1`. **The seed is the Unix second**; `conv.i4` truncation is a no-op until 2038.

### `TeamRound.Draw` — the win predicate

```
n = _engine.Draw(cb)
isWinner = (n == 42)          // ldc.i4.s 42 ; ceq
Status.RegisterAttempt(isWinner)
return DrawOutcome(n, isWinner, AttemptsRemaining, isWinner ? Status.Team.Flag : null)
```

**Winning number = 42.** The flag is the team's own `Team.Flag`, loaded server-side from a teams CSV (`IdpSorteios.Infrastructure.TeamCsv`) — not present in the client — and returned only on a win.

### `Competition.Start` / `TeamStatus` — the rules

```
Start(team):  checks team ∈ competition; checks cooldown (IsAvailableAt);
              BeginTurn() -> AttemptsUsed=0, HasWon=false;
              _engine.Reseed();                 // seed = turn-start second S0
              return TeamRound(Deadline = now + TurnDuration)
Constants:    TurnDuration = 5 min,  Cooldown = 10 min
Attempts:     AttemptsRemaining = 3 - AttemptsUsed   // 3 draws per turn
IsFinished:   HasWon || AttemptsRemaining <= 0
```

### The seed timeline (the crux)

Because `Reseed()` runs at the **end** of each `Draw`, the engine seed evolves as:

```
Start(S0)    seed = S0                 (turn-start second)
Draw#1 @D1   returns f(S0);  seed = D1  (D1 = second you clicked draw #1)
Draw#2 @D2   returns f(D1);  seed = D2
Draw#3 @D3   returns f(D2)
   where  f(s) = (Random(s).Next() % 1000) + 1 ,  win iff any == 42
```

`D1` and `D2` are **your clicks** → attacker-controlled to ~1 s. Pick a known winning second `W` (precomputed), click **Draw #1 exactly at `W`** (sacrifice — sets `seed = W`), then **Draw #2** returns `f(W) = 42` → win, with the 3rd attempt spare.

### Reproducing `System.Random` and finding winning seconds

`solver/solve.py` ports the legacy generator and self-tests against the canonical anchor `new Random(0).Next() == 1559595546`. Scanning any time range lists the Unix seconds with `f(s)==42`. They are quasi-periodic (~every **863 s ≈ 14.4 min**, because the first sample is near-linear in the seed), so a 5-minute test window can always be **scheduled around a known winning second**.

```
[selftest] .NET Random(0).Next()=1559595546 OK
[result] winning seconds (draw==42): ~1/1000 density
  unix=1794668426  BRT=2026-11-14 12:00:26  UTC=15:00:26
  unix=1794669982  BRT=2026-11-14 12:26:22  UTC=15:26:22
  ...
```

## Field procedure (in-person window, 2 of 3 attempts)

1. Book a window (scheduling link) that contains a precomputed winning second `W` with ≥2 min of slack around it. Regenerate the table for the exact booked slot: `python3 solver/solve.py "<start_local>" "<end_local>"`.
2. Sync to the **test machine's** clock (the seed uses *its* `UtcNow`). Assume NTP unless it visibly disagrees; the 2-min tolerance absorbs small skew.
3. Start the turn, then do a throwaway **Draw #1 precisely at second `W`** (watch the ticking seconds).
4. Do **Draw #2** one or two seconds later → it returns **42** → flag. (Draw #3 is a spare.)

> Clock-skew hardening: clicking the setup draws on consecutive seconds `W-1, W, W+1` and reading the results on the following draws covers ±1 s of unknown offset within the 3-attempt budget.

## What didn't work / dead ends

| Hypothesis | Result | Why |
|---|---|---|
| Electron app (asar/JS) | ✗ | It's **.NET WPF**, not Electron (PresentationFramework + System.* DLLs). |
| Flag embedded in the binary | ✗ | Flag is per-team, loaded server-side from a CSV; only returned on a win. |
| `dotnet tool install ilspycmd` | ✗ | Only the .NET **runtime** is present (no SDK); installs were blocked — disassembled by hand instead. |

## Conclusion

Server-trusted client-side randomness: the "draw" is a `System.Random` seeded by the current second, and the win is a hard-coded `== 42`. Both the PRNG and the seed are fully predictable offline, so the winning second is known in advance and the in-person window is won deterministically in 2 clicks. Classic weak/predictable-PRNG (timestamp-seeded) break.

---

## Appendix — tools

- `solver/ildump.py` — `python3 -I solver/ildump.py <dll> [TypeName...]`: minimal ECMA-335 metadata + CIL disassembler (no deps), resolves call/field/string tokens.
- `solver/solve.py` — `python3 -I solver/solve.py [start_local end_local]`: reproduces `.NET Random(int).Next()`, self-tests against the canonical anchor, and lists Unix seconds where the draw equals 42 (BRT + UTC).
- Unpack: `7z x <installer>.exe -o app 'IdpSorteios*'` (NSIS → .NET assemblies + PDBs).
- Installer SHA256: `b77434619a33d43fe3964af4321e87346337e4ea0067c426f22f917ceb53e9fb`.
- Author path leaked in PDBs: `/home/j3r3mias/idp-ctf-03-sorteio/`.
