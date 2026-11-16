<!--
  Writeup in English. Flag not captured by us (a teammate submitted it); left as IDP{...}.
  Infra host anonymized as <HOST>:<PORT>.
-->
<div align="center">

<a href="https://git.io/typing-svg"><img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=28&duration=700&pause=1000&color=E8423F&center=true&vCenter=true&repeat=false&width=500&height=35&lines=Uma+Ideia+para+o+IDEA" alt="Typing SVG" /></a>

</div>

# Uma Ideia para o IDEA — WEB · 🔴 HARD

- **Status:** ✅ SOLVED (by a teammate; our analysis + solver reproduced the full path)
- **Points:** 259 (final dynamic value)
- **Flag:** `IDP{...}` (submitted by a teammate — not recorded here)
- **Target:** `<HOST>:<PORT>` (Flask + gunicorn, ephemeral container)
- **Prompt:** *"Uma ideia pode abrir caminhos. Escolha uma proposta do Idea Lab e faça acontecer."*

---

## TL;DR

1. "Idea Lab" voting app: each proposal shows `X / 250 apoios`; reaching **250** supports
   rewards the idea. Supporting an idea requires solving a **proof-of-work** per vote.
2. The PoW is throttled **only in the client**: `app.js` caps the search to `NONCE_SPACE_SIZE = 1_000_000`
   and the nonce format to `IDP-CTF-NNNNNN` (6 digits), while the target is a **24-bit** hash
   prefix. A human basically can never vote — hence the proposals stuck at 3–7/250.
3. The server validates **only** the hash prefix + 6-digit nonce format + one-time challenge.
   Script the PoW, parallelize the hashing, and vote **244×** to drive a proposal to 250/250
   → the reward (flag) unlocks. No reuse, no dedup, no format bypass.

## Analysis

### The app
- `GET /` → static HTML listing proposals as `<article data-proposal-id="N">` with a
  `N / 250 apoios` counter. A hidden form `POST /propostas` creates ideas (`title, author,
  district, summary` + `csrf`). Session is a **Flask signed cookie** (`{"csrf":...}`,
  then `{"challenge":{"id","prefix"},"csrf":...}` after a challenge is fetched).
- `app.js` wires the **"Apoiar ideia"** button → `registerSupport()`.

### The proof-of-work (client)
```js
const NONCE_SPACE_SIZE = 1_000_000;                 // client self-throttle
async function sha256(v){ /* hex of SHA-256("urna-aberta:v1:"+v) */ }
function nextNonce(){ return `IDP-CTF-${String(cursor).padStart(6,"0")}`; } // 6 digits only
async function solveProofOfWork(prefix){ /* find nonce whose hash startsWith(prefix) */ }
```
Voting flow: `GET /api/pow/challenge` → `{algorithm, challenge, nonce_format:"IDP-CTF-XXXXXX",
prefix}` (binds `challenge`+`prefix` into the session cookie) → solve → `POST /api/votes`
`{csrf, challenge, nonce, proposal_id}`.

**The key numbers:** `prefix` is always **6 hex chars = 24 bits** (≈16.7M expected tries),
but the client only searches **1,000,000** nonces → a legit client succeeds on only
~`1-(1-2^-24)^1e6 ≈ 5.8%` of challenges. That artificial throttle is the whole difficulty.

### What the server actually enforces (probed)
| Test | Input | Result |
|---|---|---|
| Hash correct, wrong format | nonce `680433` (bare number), hash starts with prefix | `400` "prova não foi aceita" → **format is enforced** |
| Correct 6-digit nonce | `IDP-CTF-206330` | `200` `idea_votes+1` → happy path works |
| 7-digit nonce (space-cap bypass) | `IDP-CTF-18135987`, hash correct | `400` → **server enforces exactly 6 digits** |
| Replay same valid `(challenge,nonce)` | identical body ×3 | `400` "Solicite uma nova prova" → **one-time** |
| Same session, new challenge | second solved PoW | `200` `idea_votes+1` → **no per-session/IP dedup** |

So: the only lever is raw throughput. ~6% of challenges are solvable in the 6-digit space →
~17 `GET /api/pow/challenge` + up to 17M SHA-256 per vote. Parallelizing the hashing across
all cores makes ~244 votes finish in minutes; votes are sent **one at a time** (normal client
traffic, not a flood).

## What didn't work

| Hypothesis | Result | Why |
|---|---|---|
| Client-side cap bypass (nonce > 6 digits / arbitrary) | ✗ | server regex is `^IDP-CTF-\d{6}$` |
| Hash-only forgery (ignore nonce format) | ✗ | server re-validates the nonce format |
| Replay a solved proof to skip re-hashing | ✗ | challenge is single-use ("Solicite uma nova prova") |
| Mass-assignment of a vote count on `POST /propostas` | ✗ | create form ignores extra fields (not needed) |

## Conclusion

A "web" challenge whose vulnerability is **trust placed in client-side difficulty**: the
expensive, deliberately-slow PoW loop lives in `app.js`, but the server only checks the
cheap invariants (prefix, 6-digit format, single-use). Automate + parallelize the PoW, drive
any proposal from its current count to `250/250`, and the reward unlocks. Low solve count (2)
is purely because manual voting is near-impossible by design.

---

## Appendix — tools

- `probe.py` — recon: wiring + arbitrary-nonce rejection (proves format is enforced).
- `probe2.py` — distinguishes 6-digit-cap vs unlimited-digit server validation.
- `probe3.py` — tests proof reuse (one-time) and per-session multi-vote (allowed).
- `solve.py` — `python3 solve.py <HOST:PORT> <proposal_id>`: multicore PoW + sequential
  votes until `idea_votes >= required_votes` (250), then hunts `IDP{...}` in the vote
  response, the home page, and candidate reward endpoints.
