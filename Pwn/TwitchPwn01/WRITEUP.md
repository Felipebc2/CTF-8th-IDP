<div align="center">

<a href="https://git.io/typing-svg"><img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=28&duration=700&pause=1000&color=E8423F&center=true&vCenter=true&repeat=false&width=500&height=35&lines=TWITCH+PWN+01" alt="Typing SVG" /></a>

</div>

# Twitch Pwn 01 — PWN · 🟡 MEDIUM

- **Status:** ✅ SOLVED — flag read live off the Twitch stream.
- **Points:** 184 (final dynamic value) · 🩸 first blood
- **Flag:** `IDP{tw1tch_PWN_p3rm1SSo3s_mf5hc523dg}`
- **Attachment / Target:** web service `<HOST>` (login `<USER>` / `<PASSWORD>`), binary submission; execution streamed on `https://www.twitch.tv/<CHANNEL>`
- **Prompt:** *"Quem sabe faz ao vivo! Acompanhe em Twitch TV."* — flags in `/twitch/desafio-01/`, one per team; environment restored each run.

---

## TL;DR

1. The service accepts an arbitrary **x86-64 ELF** (≤42 MB, ≤120 s) and runs it on a Linux desktop whose screen is **livestreamed on Twitch**. There is no stdout channel back — the **only output channel is the streamed screen**.
2. Our flag is `/twitch/desafio-01/flag-nop.txt`, owned by `ctf:ctf` but with mode `----------` (no read bit for anyone). The submitted binary runs **as `ctf`** — i.e. the **owner** of the file.
3. An owner may `chmod` its own file regardless of the current permission bits. So: `chmod` the flag readable → read it → **render it on screen** → read the flag off the live.

## Analysis

### The mechanism
After logging in with the team credential (`<USER>` / `<PASSWORD>`), the service exposes a single action: upload one x86-64 binary to a queue. Constraints shown:

- x86-64 only, ≤42 MB, ≤120 s runtime, one submission per team at a time, environment wiped after each run.
- *"Siga as regras da Twitch para o chat e no que é exibido na tela"* — the hint that **what is drawn on screen** is the exfiltration channel. Execution happens on a GUI desktop (xterm/mousepad available) captured by the stream.

So code execution is *given*; the challenge is exfiltrating a file over a **one-way video channel**.

### The permission twist
First submission just listed the directory and `cat`'d everything:

```
drwxr-xr-x 2 root root 4096 ... .
---------- 1 ctf  ctf    38 ... flag-nop.txt
---------- 1 ctf  ctf    38 ... flag-<other-team>.txt
...
```

The directory is world `r-x` (listing/traversal OK), but every flag file is `----------`. A plain `open()`/`cat` returns *permission denied* — **even for the owner**, because the read bit is cleared. (We saw another team's binary loop over all files printing *"não consegui abrir"* for exactly this reason.)

Key fact: `[id]` from inside the binary was `uid=1000(ctf)` — **we run as the file owner**. `chmod(2)` is gated by *ownership*, not by the file's mode bits, so the owner can always relax permissions:

```
chmod u+r /twitch/desafio-01/flag-nop.txt   # succeeds: we own it
cat       /twitch/desafio-01/flag-nop.txt   # now readable
```

`[stat]` after the chmod confirmed `-rw-r--r-- ctf ctf`.

### Getting it on screen
No stdout reaches us, so the binary writes the flag to `/tmp/FLAG.txt` and opens it in a large window (`xterm -fa Monospace`, falling back to `mousepad`/`zenity`/`xmessage`/`notify-send`), then `sleep`s ~115 s so the window stays up long enough to show through the stream's delay before the box is wiped. We only touch our own `flag-nop.txt` (fair play — never other teams').

Result on the live:

```
===== FLAG NOP =====
IDP{tw1tch_PWN_p3rm1SSo3s_mf5hc523dg}

[id]   uid=1000(ctf) gid=1000(ctf) groups=1000(ctf)
[stat] -rw-r--r-- 1 ctf ctf 38 ... /twitch/desafio-01/flag-nop.txt
```

## What didn't work

| Hypothesis | Result | Why |
|---|---|---|
| `cat` the flag directly (v1) | ✗ | Mode `----------` → read denied even for owner |
| Read as if we needed root/privesc | ✗ (unnecessary) | We already run as the owner `ctf`; `chmod` suffices |
| Looping/opening every flag without chmod (other team) | ✗ | Same read-bit denial on all files |

## Conclusion

Not a memory-corruption pwn: arbitrary code execution is handed to you, and the real puzzle is a **Unix-permissions insight** (owner can `chmod` a `----------` file) combined with an **unusual exfil channel** (the Twitch livestream is the only output). The flag's own text (`p3rm1SSo3s`) confirms the intended trick.

---

## Appendix — tools

- `solve.c` / `solve` — static x86-64 ELF submitted to the service. Chmods `flag-nop.txt`, reads it, and renders it in an on-screen window for the stream.

```c
#include <stdlib.h>
int main(void) {
    system(
        "export DISPLAY=\"${DISPLAY:-:0}\"; "
        "export XAUTHORITY=\"${XAUTHORITY:-$HOME/.Xauthority}\"; "
        "T=/twitch/desafio-01/flag-nop.txt; "
        "chmod u+r \"$T\" 2>/dev/null; chmod 0644 \"$T\" 2>/dev/null; "
        "{ echo '===== FLAG NOP ====='; cat \"$T\" 2>&1; "
        "  echo; echo \"[id] $(id)\"; echo \"[stat] $(ls -l \"$T\" 2>&1)\"; } > /tmp/FLAG.txt 2>&1; "
        "F=$(cat /tmp/FLAG.txt); "
        "( xterm -fa Monospace -fs 22 -geometry 100x16+40+40 -e \"cat /tmp/FLAG.txt; sleep 115\" "
        "  || mousepad /tmp/FLAG.txt || gedit /tmp/FLAG.txt "
        "  || zenity --info --no-wrap --title='FLAG' --text=\"$F\" "
        "  || xmessage -center \"$F\" || notify-send 'FLAG' \"$F\" ) >/dev/null 2>&1 & "
        "sleep 115"
    );
    return 0;
}
```

Build: `gcc -O2 -static -o solve solve.c` · verify `file solve` → *ELF 64-bit x86-64, statically linked*.
