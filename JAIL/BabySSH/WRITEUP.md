<div align="center">

<a href="https://git.io/typing-svg"><img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=28&duration=700&pause=1000&color=E8423F&center=true&vCenter=true&repeat=false&width=500&height=35&lines=BABY+SSH" alt="Typing SVG" /></a>

</div>

# Baby SSH — JAIL · 🟢 EASY

- **Status:** ✅ SOLVED — read the flag with a pure Bash builtin on a system with no coreutils.
- **Points:** 184 (final dynamic value)
- **Flag:** `IDP{s3cuRE_th3_fl4g_AND_s3cur3_TH3_SH3LL_XdjtF8t6rs}`
- **Target:** `ssh -p <PORT> idp@<HOST>` (ephemeral Ubuntu 24.04 container)
- **Prompt:** *"First time?"* — `usuario: idp` / `pass: hackathon2026`

---

## TL;DR

1. SSH in with the given creds — you land in a normal (non-restricted) Bash shell inside a *minimized* container.
2. `flag.txt` is right there in `$HOME`, but `cat` (and the rest of coreutils) has been removed: `cat: command not found`.
3. Read the file without any external binary using Bash's command-substitution file read: `echo "$(<flag.txt)"`.

## Analysis

### Landing shell
SSH with `idp:hackathon2026` succeeds and drops to an interactive Bash prompt:

```
idp@537563c04cab:~$ ls
flag.txt
idp@537563c04cab:~$ cat flag.txt
-bash: cat: command not found
```

This is **not** `rbash`: there is no "restricted" error, `cd`/`pwd`/`whoami` work, and `/` in paths is
allowed. The "jail" is a **minimized image** — Ubuntu strips non-essential packages, so `/bin/cat`,
`less`, `head`, etc. simply aren't installed. The banner even says so:

```
This system has been minimized by removing packages and content that are
not required on a system that users do not log into.
```

### Reading without coreutils
Bash can open and read a file on its own, no external process needed. Command substitution with the
`<` redirection operator — `$(<file)` — makes Bash slurp the file's contents:

```
idp@537563c04cab:~$ echo "$(<flag.txt)"
IDP{s3cuRE_th3_fl4g_AND_s3cur3_TH3_SH3LL_XdjtF8t6rs}
```

The flag name is self-describing: *secure the flag AND secure the shell* — the lesson is that removing
`cat` is not a security boundary when the shell itself can read files.

### Other working reads (all builtin / shell-only)
```bash
while read -r l; do echo "$l"; done < flag.txt   # pure bash loop
mapfile -t x < flag.txt; printf '%s\n' "${x[@]}" # bash 4+ mapfile
read -r f < flag.txt; echo "$f"                  # single-line file
```

## What didn't work

| Hypothesis | Result | Why |
|---|---|---|
| `cat flag.txt` | ✗ | coreutils removed from the minimized image (`command not found`) |
| GTFOBins rbash escape (`vi`, `less`, `find -exec`) | ✗ (unneeded) | not a restricted shell, and those binaries are absent anyway |

## Conclusion

Closed with a one-liner. The challenge isn't a real sandbox escape — it's "can you read a file when the
obvious tool is gone?". Bash's `$(<file)` does it with zero external binaries.

---

## Appendix — commands

```bash
ssh -p <PORT> idp@<HOST>      # pass: hackathon2026
echo "$(<flag.txt)"           # read the flag, no coreutils needed
```
