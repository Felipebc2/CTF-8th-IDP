<div align="center">

<a href="https://git.io/typing-svg"><img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=28&duration=700&pause=1000&color=E8423F&center=true&vCenter=true&repeat=false&width=500&height=35&lines=TWITCH+PWN+04" alt="Typing SVG" /></a>

</div>

# Twitch Pwn 04 — PWN · 🔴 HARD

- **Status:** ✅ SOLVED — flag QR rendered live and scanned (0 solves on the board when we got it).
- **Points:** 421 (final dynamic value)
- **Flag:** `IDP{tw1tch_PWN_p4th_h1j4ck_gvk5cbvb3g}`
- **Attachment / Target:** SDK zip (`twitch-pwn-04-sdk.zip`) + web service `<HOST>` (submit an x86-64 ELF; team login `<USER>`/`<PASSWORD>`); execution streamed on Twitch `<CHANNEL>`.
- **Prompt:** *"Quem sabe faz ao vivo!"* — `/usr/local/bin/timestamp` gives the official live time; flags in `/twitch/desafio-04/`, one per team, environment restored each run.

---

## TL;DR

1. Same family as Twitch Pwn 01–03: submit an x86-64 ELF, it runs **as `ctf`** on a GUI desktop livestreamed on Twitch — the **only output channel is the streamed screen**.
2. The SDK zip ships the *real* helper, `timestamp` (PIE, **not stripped**), so we reversed it offline. On the target it is `/usr/local/bin/timestamp`, **setuid `relogio`** (uid 996). `main` is 12 instructions:
   ```c
   int main(void){
       uid_t e = geteuid();
       setreuid(e, e);                         // ruid = euid → privilege kept in the child shell
       puts(<banner>);
       system("date '+%d/%m/%Y %H:%M:%S'");    // relative command name, no absolute path
       return 0;
   }
   ```
3. `system()` resolves `date` via `$PATH`, and `setreuid(geteuid(),geteuid())` keeps real uid = effective uid, so the spawned `/bin/sh` runs as `relogio`. We plant our own `date` earlier in `$PATH` → it runs **as `relogio`** (GTFOBins-style setuid PATH hijack).
4. The flag `/twitch/desafio-04/flag-nop.png` is `-r-------- relogio:relogio` — a **QR-code PNG** (like Pwn 02), not text. So the hijacked `date` (as `relogio`) **copies** our PNG to a world-readable path, and the `ctf`-side renderer displays it centered with a white quiet-zone border; we scan the QR off the live.

## Analysis

### The SDK is the disclosure
Unlike 01–03 (black-box, probed via a recon ELF), 04 hands you the helper binary:

```
$ file sdk/timestamp
ELF 64-bit LSB pie executable, x86-64, dynamically linked, not stripped
$ objdump -T sdk/timestamp | grep UND
geteuid  setreuid  puts  system          # nothing else
```

`objdump -d` of `main`:
```asm
call geteuid@plt ; mov ebx,eax
call geteuid@plt ; mov esi,ebx ; mov edi,eax
call setreuid@plt            ; setreuid(e, e)
lea rdi,[banner] ; call puts@plt
lea rdi,["date '+%d/%m/%Y %H:%M:%S'"] ; call system@plt
```

This is the textbook **setuid + relative-path `system()`** bug (GTFOBins `date`). `setreuid(e,e)` sets `ruid == euid` *before* the `system()`, so the forked shell keeps `relogio`'s privilege with no uid mismatch to drop.

### The hijack (confirmed live)
Our submitted ELF (as `ctf`) plants `/tmp/ph04/date` (a `#!/bin/sh` script), prepends its dir to `$PATH`, and runs `PATH=/tmp/ph04:$PATH /usr/local/bin/timestamp`. The `date` lookup inside `timestamp`'s `system()` hits ours first. Proof on screen:

```
== IDP CTF :: horário oficial da live ==
[id] uid=996(relogio) gid=1000(ctf) groups=1000(ctf)     # ran as relogio, not ctf
```

### Finding the flag file
First planted `date` guessed `flag-nop.txt` → `No such file or directory`. We never ran a desafio-04 recon, so the next `date` listed the dir (as `relogio`):

```
-r-------- 1 relogio relogio 587 flag-hackatromba.png
-r-------- 1 relogio relogio 587 flag-hackher.png
-r-------- 1 relogio relogio 587 flag-jambatron.png
...                                   flag-nop.png        # ours (team NOP)
```

Per-team **PNG** flags, `relogio`-owned. `cat` just dumps binary — it's a **QR code** (same trick as Pwn 02).

### Getting the QR off the stream
Two stages in one submitted ELF:
- **Stage 1 (as `relogio`):** the planted `date` copies **only** `/twitch/desafio-04/*nop*` → `/tmp/flag04.png`, `chmod 0644` (we only ever touch our own flag).
- **Stage 2 (as `ctf`):** render `/tmp/flag04.png` the way Pwn 02's `exploit5.c` did — upscale nearest-neighbor (`-filter point`), **moderate size, centered, wide white quiet-zone border** (`-bordercolor white -border 160`), opened with `feh` (fallbacks `eog`/`ristretto`/`display`), held ~115 s. Centered + quiet-zone keeps the QR clear of the Twitch player's bottom control bar (the clipping that bit us on Pwn 02's first try). Scanned:

```
IDP{tw1tch_PWN_p4th_h1j4ck_gvk5cbvb3g}
```

The flag text (`p4th_h1j4ck`) confirms the intended trick.

## What didn't work

| Hypothesis | Result | Why |
|---|---|---|
| Read the flag directly as `ctf` | ✗ | Flag is `relogio:relogio -r--------` |
| `cat` our flag in the hijacked `date` | ✗ (binary) | The flag is a **QR PNG**, not text |
| Guess filename `flag-nop.txt` | ✗ | Real file is `flag-nop.png` (enumerated the dir as `relogio`) |
| Naive fullscreen QR render | ✗ (clip risk) | Twitch player bottom bar clips the QR — use centered + white quiet zone |
| Bad `&&` escaping in planted script | ✗ (fixed) | `\&\&` reached `/bin/sh` → syntax error; replaced with `if/then/fi` |

## Next time (série TwitchPwn)

Flags nesta série alternam entre **texto** (01, 03) e **QR PNG** (02, 04). Lição pra próxima:
assim que tivermos leitura da flag (como o dono, via o helper), **testar as duas formas no
mesmo run** — `cat` (caso seja texto) **e** abrir como imagem / renderizar o QR centralizado
com quiet-zone branca (caso seja PNG). Não assumir texto: aqui o `cat` do `.png` só cuspiu
binário e custou uma iteração. Fazer `file`/`ls` + `cat` + render de imagem de uma vez.

## Conclusion

GTFOBins-style **setuid PATH hijack**: a setuid-`relogio` binary runs `date` by bare name after `setreuid(geteuid(),geteuid())`, so controlling `$PATH` substitutes our executable and inherits `relogio`'s privilege — no memory corruption. The flag being a `relogio`-owned **QR PNG** adds the Pwn-02 exfil twist: copy it out as the privileged user, then render it readably (centered, quiet-zone border) on the one-way video channel.

---

## Appendix — tools

All submitted binaries are static x86-64 ELFs (`gcc -O2 -static`) reusing the `TwitchPwn03/recon.c` auto-paging xterm harness; the QR renderer is the `TwitchPwn02/exploit5.c` pipeline. We only ever read/copy **our own** `flag-nop.png`.

- `sdk/timestamp` — the real helper from the SDK zip; reversed with `objdump` (12-instruction `main`, no Ghidra needed).
- `exploit.c` / `exploit` — PATH hijack; proved `id=relogio` but guessed `.txt` (file not found).
- `exploit2.c` / `exploit2` — planted `date` enumerates `/twitch/desafio-04` → flags are per-team **PNGs**, ours `flag-nop.png` (also fixed an `&&`-escaping bug → `if/then/fi`).
- `exploit3.c` / `exploit3` — two-stage: copy `flag-nop.png` out as `relogio`, then render the QR centered with a white quiet-zone border → **scanned the flag**.

Build: `gcc -O2 -static -o <name> <name>.c` · verify `file <name>` → *ELF 64-bit x86-64, statically linked*.
