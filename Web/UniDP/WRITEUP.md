<div align="center">

<a href="https://git.io/typing-svg"><img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=28&duration=700&pause=1000&color=E8423F&center=true&vCenter=true&repeat=false&width=500&height=35&lines=UniDP" alt="Typing SVG" /></a>

</div>

# UniDP — WEB · 🔴 HARD

- **Status:** ✅ SOLVED — Flask session forgery (weak `SECRET_KEY`) + role-check IDOR on `uid`.
- **Points:** 259 (final dynamic value)
- **Flag:** `IDP{r3s3t_m4il_t4mp3r_K3zvMzAUhg}`
- **Attachment / Target:** `<HOST>:<PORT>` (Flask + gunicorn container, ephemeral)
- **Prompt:** *"Gerencie sua vida acadêmica, ou procure quem pode fazer isso junto com você."*

---

## TL;DR

1. "Portal do Aluno" (Flask/gunicorn). Self-registration; login is by **matrícula** (8-digit id). The Flask signed cookie stores identity as `{"csrf":…, "is_coordinator": false, "uid": N}`.
2. The signing key is trivial: **`SECRET_KEY = 'dev'`**, recovered offline with `flask-unsign`. So we can forge any session.
3. Forging `is_coordinator:true` only makes the **"/coordination"** nav link appear (a template check). The route itself re-validates the role **in the DB, by `uid`** → 403 for a normal user. Enumerating `uid` shows **uid=1 is the coordinator** (Profa. Linik Mayara Meireles).
4. Forge `{is_coordinator:true, uid:1}` and open **`/profile`** → the coordinator's "Informação reservada" field leaks the flag.

## Analysis

### Stack & surface
`Server: gunicorn`, `Set-Cookie: session=<b64>.<ts>.<sig>` → Flask's `itsdangerous` signed cookie. Base64 of the first segment decodes to plain JSON:

```json
{"csrf":"…","is_coordinator":false,"uid":91}
```

Routes discovered: `/` (login), `/register`, `/forgot-password`, `/dashboard`, `/profile`, `/subjects/<CODE>`, `/professors/<id>`, `/coordination`, `/logout`. Registration collects `name`, `registration` (matrícula, `[0-9]{8}`), `email`, `course`, `password` — **no role field** (no mass-assignment on signup). Login username = the matrícula.

### Weak SECRET_KEY → session forgery
The cookie is signed, not encrypted, and the identity (`uid`) and role (`is_coordinator`) live inside it. Recover the key offline (never touches the server):

```
flask-unsign --unsign --cookie "<session value>"
# [+] Found secret key … 'dev'
```

With `SECRET_KEY='dev'` we can mint any session.

### The role check is deeper than the cookie
Forging `is_coordinator:true` for our own `uid` makes the dashboard render a new nav link **`/coordination`** — but hitting it returns **403**. So the link is gated by the cookie flag (template: `{% if session.is_coordinator %}`) while the route re-loads the user **from the DB by `uid`** and checks the *stored* role. Our student `uid` is not a coordinator → 403. `uid=184` (a professor) → dashboard redirect (professors are a separate table from the session `uid` space).

### Find the coordinator uid (small, targeted enumeration)
Our registration got `uid=91`, so ~90 users are seeded (uids 1..90). Forge `is_coordinator:true` while sweeping a small `uid` range and watch `/coordination`:

```
uid=1  -> HTTP 200   # coordinator
```

`uid=1` passes. The `/coordination` panel is a full admin (create/edit users with a `Papel` field, subjects, enrollments).

### The flag
The flag is not on the panel. The coordinator's own **`/profile`** (uid=1 = *Profa. Linik Mayara Meireles*, matrícula 731, `linik@docente.unidp.edu.br`) has an extra **"Informação reservada"** block:

```
IDP{r3s3t_m4il_t4mp3r_K3zvMzAUhg}
```

### Intended vs. used path
The flag name — `r3s3t_m4il_t4mp3r` (reset-mail tamper) — points at the **intended** vector: abuse the `/forgot-password` flow to tamper the recovery e-mail and take over the coordinator. The weak `SECRET_KEY='dev'` let us skip straight to forging the coordinator session; both land on the same `/profile` secret.

## What didn't work

| Hypothesis | Result | Why |
|---|---|---|
| Mass assignment on `/register` (`role`/`is_coordinator`) | ✗ | Form only takes name/matrícula/email/course/password; no role field honored |
| Forge `is_coordinator:true` with our own `uid` | ✗ (403) | `/coordination` re-checks the role in the DB by `uid`, not the cookie flag |
| Forge `uid` of a professor (184) | ✗ | Professors are a separate table from the session `uid` space; dashboard redirects |
| Flag literally on `/coordination` | ✗ | Panel only exposes admin forms + user/subject tables; flag lives on the coordinator's `/profile` |

## Conclusion

Two independent server-side flaws compounded: a guessable Flask `SECRET_KEY` (forge any `uid`/role cookie) **and** an authorization model split between a forgeable template flag and a DB role keyed on `uid` (so the IDOR on `uid` finds the one real coordinator). Forged `{is_coordinator:true, uid:1}` → `/profile` → flag.

---

## Appendix — tools

- `solve.py` — `python3 solve.py http://HOST:PORT`: registers a throwaway student, reads `SECRET_KEY='dev'`-signed claims, sweeps `uid` for the coordinator against `/coordination`, then reads `/profile` and prints the flag. Requires `requests` and `flask-unsign[wordlist]`.
- `flask-unsign` — offline `SECRET_KEY` recovery and cookie (re)signing.
