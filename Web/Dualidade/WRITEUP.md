<!--
  Writeup in English. Solved by a teammate; this is our recon/analysis up to where we stopped.
-->
<div align="center">

<a href="https://git.io/typing-svg"><img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=28&duration=700&pause=1000&color=E8423F&center=true&vCenter=true&repeat=false&width=500&height=35&lines=DUALIDADE" alt="Typing SVG" /></a>

</div>

# Dualidade — WEB · 🔴 HARD

- **Status:** ✅ SOLVED by the team — a teammate found the cookie and submitted the flag (14/11 12:25). The answer is **`Cookie: roll`**: the server hands you `rick`, and the "more iconic duo" is **Rick + Roll = Rickroll** (*Never Gonna Give You Up*). What follows is our own analysis before that: the server logic was fully reverse-engineered, and the challenge reduced to that one hard-coded cookie string, which no technical vector could leak.
- **Points:** 259 (final dynamic value)
- **Flag:** `IDP{...}` (submitted by a teammate, not recorded here)
- **Attachment / Target:** `dualidade.png` (served asset, flavor) / `<HOST>:<PORT>` (ephemeral container, ~15 min TTL)
- **Prompt:** *"Name a more iconic duo, I'll wait."*

---

## TL;DR

1. Single static **nginx/1.27.5** server. `/` returns an `index.html` whose only `<img>` is swapped by an `nginx` `map $http_cookie` rule. Theme is Rick & Morty / duality (light vs dark castle, two paths).
2. Two observed states: **`/dualidade.png`** (Rick & Morty splash, default) and **`/no.png`** (the Bugs Bunny *"no"* meme = wrong-answer troll). The server also sets a valueless cookie **`rick`** and declares `Vary: Cookie`.
3. The map has a **third branch** keyed on one exact cookie token ("a more iconic duo") that serves the flag. We fully reconstructed the matching rule but never guessed the token; a teammate did: **`roll`**, completing the server's `rick` into **Rickroll**.

## Analysis

### Served surface
```
GET / HTTP/1.1
→ 200, Content-Length: 524
  Server: nginx/1.27.5
  Set-Cookie: rick; Path=/
  Vary: Cookie
  Cache-Control: no-store
  ETag: "6aeeced4-20c"   (0x20c = 524)
  <body> <img src="/dualidade.png"> </body>
```
With a "wrong" cookie the same endpoint returns a **different static file** (`ETag "6aeeced4-205"`, 517 bytes) pointing at `<img src="/no.png">`. Same `Last-Modified` for both → two real sibling `index.html` files chosen by nginx, not dynamic code.

### The `map $http_cookie` rule (reconstructed from ~80 probes)
`$page = no.png` **iff** the `Cookie` header is a **single token with no `=` and no `;`, and not exactly `rick`**. Everything else (empty / contains `=` / contains `;` / equals `rick`) → `dualidade.png`.

```nginx
map $http_cookie $page {
    default      dualidade;   # empty, or has '=' , or has ';'
    rick         dualidade;   # exact key, higher priority than the regex
    ~^[^=;]+$    no;           # one bare token != rick  → the "no" troll
}
```

Evidence grid:

| Cookie sent | `img src` | Rule hit |
|---|---|---|
| *(none)* / `rick` / `rick; morty` / `morty; rick` | `/dualidade.png` | default / exact `rick` / has `;` |
| `morty=1` / `x=1` / `rick=1; morty=1` | `/dualidade.png` | has `=` → default |
| `morty` / `summer` / `beth` / `jerry` / `pickle` / `meeseeks` | `/no.png` | bare token ≠ rick |
| `rickmorty` / `rickandmorty` / `rick sanchez` / `C-137` | `/no.png` | bare token ≠ rick |

**Key takeaway:** there is an *exact* key `rick`. The winning answer is expected to be **another exact bare-token key** in the same shape (no `=`, no `;`) — i.e. the literal string of "a more iconic duo" — which would route to a third `index.html` carrying the flag.

## Session 2 — model fully confirmed on a fresh container

Re-ran the probes on a new instance (`nginx/1.27.5`, same build). The reconstructed `map` holds **exactly**:

| Cookie header sent | result | len / ETag |
|---|---|---|
| *(none)* / `rick` | `/dualidade.png` | 524 / `6aeeced4-20c` |
| any other bare token (`morty`, `x`, `RICK`, `Rick`, `12345`, `good&evil`, `mario&luigi`…) | `/no.png` | 517 / `6aeeced4-205` |
| contains `=` or `;`, or empty value | `/dualidade.png` (default) | 524 |

Decisive findings this session:

- **`curl -b` footgun.** `curl -b "morty"` (no `=`) treats the arg as a **cookie-jar filename**, not a cookie — it sends **no Cookie header**, so everything falsely looked like `dualidade`. The oracle only works with `-H "Cookie: <value>"`. Documented so nobody loses an hour to it again.
- **Cookie is the ONLY `map` input.** `Referer`, `User-Agent`, `Accept-Language`, `X-Forwarded-For`, `?arg`, `?k=v` → all `/dualidade.png`. No alternate vector.
- **Case-sensitive, exact.** `RICK`/`Rick` → `no`. Only the literal `rick` hits the dualidade branch.
- **No cookie-shape bypass.** Duplicate `Cookie` headers (joined `rick; rick` → has `;` → default), leading/trailing space/tab, `=rick`, `rick;zzz`, `rick=zzz`, empty value — all behave per the model; no crafted shape reaches a hidden branch.
- **No config/error leak.** 404/405/416 are nginx **stock** pages (Content-Length 153/157/197), no custom `error_page`, no `Allow` beyond GET/HEAD, no TRACE reflection. `robots.txt`/`favicon.ico`/`sitemap.xml`/`.well-known/security.txt` → stock 404.
- **Images definitively inert.** `dualidade.png` holds only one metadata chunk (`caBX` = C2PA), **fully CBOR-decoded**: standard ChatGPT/`gpt-image` credential signed by Trufo — actions `c2pa.created`/`converted`/`watermarked`, `dc:title=image.png`, `instanceID` GUID, created `2026-11-07T03:43:21Z`, **no prompt / description / hint** (OpenAI does not embed the prompt). No trailing bytes, no `tEXt`/`iTXt`. `no.png` has **zero** metadata. Visual enhancement (gamma/equalize) + LSB bit-planes reveal no hidden text. Pure flavor.

**Oracle property (useful):** a *wrong* bare token → `/no.png` (517); `rick` → `/dualidade.png` (524); the *correct* duo is expected to be a **third** response (img ≠ either / len ≠ 517,524 / `IDP{…}`). So a candidate can be validated locally without ever touching flag submission.

**Why guessing is unavoidable here:** the meme *"name a more iconic duo, I'll wait"* (origin: Kendall & Kylie Jenner, 2016) has **no canonical answer** — the author hard-coded one specific string, and no leak path exists to read it.

### Challenge card (platform) — the full prompt is the only hint
The `<DOMAIN>` card for **Dualidade** carries nothing beyond:
> **Name a more iconic duo, I'll wait.**

No extra description, no hint button, no downloadable attachment (both PNGs are served by the container). `WEB`, `500`, **1 solve**. So the one-line meme phrase *is* the whole clue — the answer is a pop-culture / wordplay judgment call, not something derivable from the artifacts.

### Targeted (non-brute) guess rounds tried this session — all `→ /no.png`
Each round was reasoned from a specific angle, kept small, rate-limited, stop-on-hit. None hit:

| Angle | Candidates (joiner/case variants each) | Result |
|---|---|---|
| User hunch | `mario & luigi` (`&`, ` e `, ` and `, concat, reversed, Title) | ✗ no |
| Meme origin | `kendall & kylie`, `kylie & kendall`, `jenner` | ✗ no |
| "Dualidade" = binary | `0 & 1`, `0 e 1`, `0&1`, `zero e um`, `zero and one`, `1 and 0`, `0 1`, `bit and byte` | ✗ no |
| "I'll wait" punchline (there is none) | `none`, `nobody`, `ninguem` | ✗ no |

### Third-page / third-image discovery — no file to find
The two known index files hardcode `/dualidade.png` and `/no.png`; a win page would plausibly carry a third `$page`-named image. Probed `yes/sim/win/flag/correct/certo/iconic/duo/true/good/victory/secret/congrats/nice/morty/rick(.png)` → **all 404**. The win page (if any) likely just prints the flag as text; it cannot be discovered by filename, only by the correct cookie.

## What didn't work

| Hypothesis | Result | Why |
|---|---|---|
| Stego / appended data in `dualidade.png` | ✗ | `binwalk` clean, `zsteg` only noise, no trailing bytes. Image is AI-generated (C2PA/ChatGPT manifest), pure flavor. |
| Stego / hint in `no.png` | ✗ | Clean PNG, no `tEXt`/trailing/metadata. Plain Bugs Bunny meme. |
| Generation prompt leaked in C2PA (`caBX`) | ✗ | Manifest only holds the OpenAI logo SVG + Trufo signing cert. No prompt/answer. |
| Hidden vhost via `Host:` header | ✗ | ~19 hosts (dark, evil, morty, admin, flag, internal, localhost…) all → default 524. |
| Path traversal / alias off-by-slash | ✗ | `/%2e%2e/`, `/..%2f..%2f` (400), `/x/../` all normalize to default; no leak. |
| Static config/backup leak | ✗ | `nginx.conf`, `default.conf`, `Dockerfile`, `.git/config`, `*.bak`, `flag.txt`, `/pages/`, `/no/`, `/dualidade/` all 404. |
| Alternate HTTP methods | ✗ | `OPTIONS/POST/PUT/DELETE/TRACE/PATCH` → 405 (static). |
| Image bytes change per cookie | ✗ | `md5(/dualidade.png)` and `md5(/no.png)` constant across all cookies. |
| Guessing the duo token (EN/global): jekyll&hyde, yin&yang, tom&jerry, batman&robin, good&evil, rick&morty, … (3 spellings each: bare / `&` / `and`) | ✗ | All → `dualidade.png` or `/no.png`. ~60 strings tried. |
| Targeted guesses this session (mario&luigi, kendall&kylie/jenner, binary 0&1, troll `none`/`ninguem`) | ✗ | All → `/no.png`. See "Targeted guess rounds" above. |

## Session 3 — four non-guess technical vectors, all dead

Explicitly probed the remaining "it might not be the duo" theories, deterministically (not wordlists):

| Vector | Probe | Result |
|---|---|---|
| **HTTP desync / request smuggling** (front-end+back-end "duo") | `CL.TE` and duplicate `Content-Length` raw requests via `nc` | both → stock `400 Bad Request`, `nginx/1.27.5`. **No backend; single parser.** |
| **HTTP/1.1 vs HTTP/2 duality** | `curl --http2-prior-knowledge` vs `--http1.1` | h2 returns nothing — server speaks **HTTP/1.1 only**. |
| **Second service / port** (dual instance) | `curl` on `PORT±1`, 80, 443, 8080, 5000, 3000 | all `000` (connection refused). **One instance, one port.** |
| **Cookie match semantics** | `rick`, `xrickx`, `rickx`, `xrick`, `rick morty` | only exact `rick` → `/dualidade.png`; every other → `/no.png`. **Exact, case-sensitive, non-regex, non-substring** (leading/trailing space is just curl trimming the header value). |

So the `map` really is an **exact-string** lookup with no second parser, no second port, no protocol fork, and no substring behavior to abuse. The flag branch (if it exists) is an exact unknown token — there is **no technical handle** on it, confirming the Session 1–2 conclusion from four new angles.

### Cookie injection — no sink
Tested whether the cookie value reaches any sink (reflection or filename construction):

- **No reflection.** A marker cookie (`Cookie: INJx7Q9z`) appears **nowhere** in the body or in any response header. `Cookie: {{7*7}}` → `/no.png` (no SSTI, no template eval).
- **Filename is config-fixed, not cookie-derived.** `Cookie: no`, `dualidade`, `flag`, `index`, `no.png`, `../no`, `../../etc/passwd`, `no%00` → **all** `src="/no.png"`; only exact `rick` → `src="/dualidade.png"`. The served filename never echoes the cookie, so there is no path-traversal / filename-injection surface.

**Conclusion:** the cookie only toggles between two static files; it is not interpolated into output or into a path. Nothing to inject.

### Route map — only three routes exist
Enumerated likely static files/dirs (small, reasoned, rate-limited — not a wordlist):

| Path | Code |
|---|---|
| `/` | **200** (524 b, cookie-selected) |
| `/index.html` | **404** — note: `/` is a special `location`, **not** a disk `index.html` |
| `/dualidade.html`, `/no.html`, `/rick.html`, `/win.html`, `/flag.html`, `/sim.html`, `/duo.html`, `/iconic.html` | 404 |
| `/pages/`, `/html/`, `/static/`, `/assets/` | 404 (no autoindex anywhere) |
| `/dualidade.png`, `/no.png` | 200 (known assets) |

Only **three** reachable routes exist: `/`, `/dualidade.png`, `/no.png`. The win page (if any) is **not** a directly-fetchable file — it can only be reached through the correct cookie. No directory listing, no third HTML/image discoverable by name. Mapping further would be blind filename brute, which is the anti-pattern logged in the Rule above.

### Alias / path-traversal probe — negative (line closed)
One pointed probe (`curl --path-as-is`, 7 requests) to test the two canonical nginx file-read misconfigs, then drop the line:

| Probe | Result |
|---|---|
| alias off-by-slash `/{assets,static,images,img}../etc/nginx/nginx.conf` | 4× **404** (153 b stock page) — no `location` uses `alias` |
| encoded traversal `/../../../../etc/passwd`, `/%2e%2e/...`, `/dualidade.png/../../../etc/nginx/nginx.conf` | 3× **400** (157 b Bad Request) — nginx rejects `..`, does not normalize or escape webroot |

No file read, no config leak. Confirms plain static serving with no traversal surface. **CVE angles (map/regex overflow, rewrite-capture, slice) rejected on precondition:** the config has no regex-capture, no `rewrite`, no redirect, no `slice` — `Accept-Ranges: bytes` is default static behavior, not evidence of the slice module. Not reopened.

## Conclusion

**Answer: `Cookie: roll`.** The server sets a cookie named `rick`; the "more iconic duo" is not Rick & Morty but **Rick & Roll**, the Rickroll meme (*Never Gonna Give You Up*). A teammate found it and submitted the flag. The Bugs Bunny "no" image for every wrong answer fits the troll theme in hindsight.

In hindsight, the missing step was reading the cookie the server gives you as **one half of the duo** and asking what completes it as a meme, instead of which duo beats Rick & Morty. Every guess round we ran (Mario & Luigi, Kendall & Kylie, 0 & 1…) sent a whole duo as the token, never a single word that pairs with `rick`.

Our notes from before the solve, kept for the record:

The challenge reduces cleanly to **one unknown: the exact cookie token that is "a more iconic duo than Rick & Morty."** Server logic, asset analysis and infra are fully mapped and dead-ended everywhere except that single `map` key.

We were stuck because the winning value is an **exact string match** with unknown wording/spelling, and the only oracle is `dualidade.png` / `no.png` — blind brute is impractical **and** against the rules (4.5 — no mass scan). No technical vector was identified across every test performed:
- **No leak** of the nginx config / page directory — stock error pages, Cookie is the only `map` input, no cookie-shape bypass, no custom error_page. Ruled out.
- **No stego / metadata** — both PNGs inert (C2PA fully decoded, LSB + visual enhancement clean).
- **No third-file to discover** by name — all candidate `$page` images 404.

What's left is purely the **author's intended answer** to "name a more iconic duo" — a human judgment call with no technical handle. Reasoned, theme-grounded rounds (user hunch, meme origin, binary duality, punchline) all missed. The platform shows **1 solve**, so a correct string exists; the realistic ways forward are non-technical:
- a specific pop-culture / wordplay duo the author had in mind (possibly a Brazilian duo, an IDP in-joke, or an exact spelling/case we haven't matched);
- intel from outside the artifacts (organizer hints, the solving team's writeup after the event).

**Decision at the time:** stop guessing and park it. A teammate then solved it with `roll`.

> ### 🔒 Rule — no blind wordlist on a guess-the-magic-string challenge
> When a challenge reduces to **one unknown exact string matched by the server** (here: an `nginx` `map $http_cookie` key), **do not fire wordlists at it.** Reasons, in order:
> 1. **Against the rules** — blind/mass fuzzing is prohibited (regulamento 4.5), and the ephemeral container **falls over under burst load** (confirmed: `ffuf` at rate 40 killed it), wasting the TTL on restarts.
> 2. **It's a human-judgment answer, not a technical handle** — the full server model, both images and the infra are already mapped and dead. No amount of wordlist changes that; only the author's intended word solves it.
> 3. **The only ethical/effective moves are deterministic or out-of-band:** a config/source leak (none exists here), an organizer hint, or the exact pop-culture/pt-BR/IDP-in-joke duo reasoned from the prompt — tried in small, rate-limited, stop-on-hit rounds, **not** mass lists.
>
> **Operating rule going forward:** on any "magic value" challenge, exhaust deterministic leaks first; if none, limit to tiny reasoned guess rounds (≤ ~20, with `sleep`), and if those miss, **park it** pending a concrete lead. Never brute.

## Appendix — recon commands

```bash
U=http://<HOST>:<PORT>
curl -sik $U/                              # headers + index (note Set-Cookie: rick, Vary: Cookie)
curl -sik $U/ -H "Cookie: morty"           # → /no.png  (the troll)
curl -sik $U/ -H "Cookie: rick; morty"     # → /dualidade.png
# map-boundary probing: single bare token != rick → no.png ; anything with '=' or ';' → dualidade.png
```

No `solve.py` — challenge unsolved.
