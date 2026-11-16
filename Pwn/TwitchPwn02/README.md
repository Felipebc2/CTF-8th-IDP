# Twitch Pwn 02 — PWN · 🔴 HARD · 259 pts · 🩸 first blood

- **Status:** ✅ SOLVED
- **Flag:** `IDP{tw1tch_PWN_1m4g3m_kayb95abpj}`
- **Target:** submit an x86-64 ELF to `<HOST>`; it runs as `ctf` on a GUI desktop livestreamed on Twitch. Only output channel = the screen.

Sequel to Twitch Pwn 01. The flag dir `/twitch/desafio-02/` exists only when the root-owned `/opt/twitch-active-challenges` lists it (organizers activate it). Our flag is `/twitch/desafio-02/flag-nop.png` — a **QR code** image. Render it on screen (upscaled, centered, with a white quiet zone) and decode it off the live.

See [`WRITEUP.md`](./WRITEUP.md). Source: `recon*.c`, `exploit*.c` (compiled binaries are gitignored).
