# Uma Ideia para o IDEA — WEB · 🔴 HARD

- **Status:** ✅ SOLVED (teammate submitted the flag; our solver reproduces the full path)
- **Points:** 259 (final dynamic value)
- **Flag:** `IDP{...}`
- **Target:** `<HOST>:<PORT>` (Flask + gunicorn, ephemeral)
- **Prompt:** *"Uma ideia pode abrir caminhos. Escolha uma proposta do Idea Lab e faça acontecer."*

"Idea Lab" voting app: each proposal needs `250 apoios` to be rewarded, and every vote
requires a **proof-of-work**. The slow PoW (24-bit prefix) is throttled **only client-side**
(`app.js` caps the search to 1,000,000 nonces and the format to `IDP-CTF-NNNNNN`), so manual
voting almost never succeeds. The server only validates the hash prefix, the 6-digit nonce
format and that each challenge is single-use — no reuse, no per-session dedup. Script and
parallelize the PoW, vote ~244× to drive a proposal to `250/250`, and the reward unlocks.

See [`WRITEUP.md`](WRITEUP.md) · solver: [`solve.py`](solve.py) · recon: `probe.py`, `probe2.py`, `probe3.py`.
