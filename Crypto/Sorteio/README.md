<div align="center">

<a href="https://git.io/typing-svg"><img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=28&duration=700&pause=1000&color=E8423F&center=true&vCenter=true&repeat=false&width=500&height=35&lines=SORTEIO" alt="Typing SVG" /></a>

</div>

# Sorteio — CRYPTO · 🟡 MEDIUM · ✅

- **Points:** 323 (final dynamic value)
- **Target:** `.NET 10 / WPF` desktop app (NSIS installer) · `https://sorteio-crypto.desafio.<DOMAIN>`
- **Flag:** `IDP{s0rt3_n40_3x1st3_VTF7GD46DA4K}`

## Summary

The "draw" is `number = (new Random(seed).Next() % 1000) + 1` with `seed = (int) DateTimeOffset.UtcNow.ToUnixTimeSeconds()` — a `System.Random` seeded by the wall-clock **second**. You win when the draw returns `42`. .NET's *seeded* `Random(int)` is the deterministic legacy PRNG, so the result of every second is known offline in advance. Schedule the 5-min test window around a precomputed winning second, click the draw so the engine reseeds to that second, draw again → `42` → flag.

See [`WRITEUP.md`](./WRITEUP.md) for the full analysis, the hand-written ECMA-335/CIL disassembler (`solver/ildump.py`), and the PRNG reproduction (`solver/solve.py`).
