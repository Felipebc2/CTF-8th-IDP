<div align="center">

<a href="https://git.io/typing-svg"><img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=28&duration=700&pause=1000&color=E8423F&center=true&vCenter=true&repeat=false&width=500&height=35&lines=TWITCH+PWN+02" alt="Typing SVG" /></a>

</div>

# Twitch Pwn 02 — PWN · 🔴 HARD

- **Status:** ✅ SOLVED — flag QR rendered on the live stream and decoded.
- **Points:** 259 (final dynamic value) · 🩸 first blood
- **Flag:** `IDP{tw1tch_PWN_1m4g3m_kayb95abpj}`
- **Attachment / Target:** web service `<HOST>` (submit an x86-64 ELF; team login `<USER>`/`<PASSWORD>`); execution streamed on Twitch `<CHANNEL>`.
- **Prompt:** *"Quem sabe faz ao vivo! Acompanhe em Twitch TV."* — files in `/twitch/desafio-02/`, one flag per team, environment restored each run.

---

## TL;DR

1. Same machine as **Twitch Pwn 01**: you submit an x86-64 ELF, it runs **as `ctf`** on a GUI desktop **livestreamed on Twitch**. The **only output channel is the streamed screen** — no stdout comes back.
2. `/twitch/desafio-02/` **did not exist** at first. A root-owned file **`/opt/twitch-active-challenges`** lists the *active* challenge(s); only the listed ones are materialized under `/twitch`. It said only `desafio-01`. The dir appeared **only after the organizers appended `desafio-02`** to that file (we can't write it — `root:root 0644`).
3. Once active, our flag is **`/twitch/desafio-02/flag-nop.png`** — a tiny PNG (not text) that encodes the flag as a **QR code**. Render it on screen, read/scan the QR off the live. Final twist: the QR's bottom rows get clipped by the Twitch player control bar, so the clean capture (quiet zone + full grid) matters; a clipped one is still recoverable via Reed–Solomon.

## Analysis

### The mechanism (confirmed by recon)
Submitted binaries ran as `uid=1000(ctf)`. The only exfil is the screen, so every recon binary **dumps its findings to a file and opens it in a window** that stays up ~115 s (the box resets at 120 s). Because the files are long and **Mousepad can't scroll on a one-way video channel**, we used an **auto-paging xterm**: `mapfile` the file, print 38–42-line pages, `sleep` ~12 s each, loop — the stream captures every page over time.

### Where is `desafio-02`?
First recon:

```
$ ls -la /twitch
drwxr-xr-x 3 root root ... desafio-01          # desafio-02 absent
$ id
uid=1000(ctf) gid=1000(ctf) groups=1000(ctf)
```

`/twitch`, `/opt` are `root:root`; no sudo (password required); only stock setuid (`passwd`, `su`, `mount`, `pkexec`-less). Another team's binary (seen on stream) revealed the key file:

```
/opt/twitch-active-challenges   root:root 0644   content = "desafio-01"
```

So a root process stages `/twitch/<name>` for each `<name>` listed in `active-challenges`. We **cannot write it** (`0644`, owned by root) — confirmed `WRITE_DENIED`. There is no local privesc intended here: the directory simply **isn't active yet**.

### Activation
A later run showed the file had grown to 22 bytes:

```
content = "desafio-01\ndesafio-02"
```

and `/twitch/desafio-02/` now existed — the organizers had switched the challenge on. (This is why the board showed 0 solves for a long time: the target didn't exist to attack.)

### The flag is an image
```
$ ls -la /twitch/desafio-02
-r--r--r-- 1 ctf ctf 586 ... flag-nop.png      # ours (team NOP)
-r--r--r-- 1 ctf ctf 599 ... flag-<team>.png   # one per team
...
```

Files are world-readable PNGs owned by `ctf` — but `cat` just prints binary (`\x89PNG...`), and `strings` finds no `IDP{` (no tEXt chunk). The flag is **drawn in the image**: a QR code. We only ever touch our own `flag-nop.png`.

### Getting the QR off the stream
`cp` our PNG to `/tmp`, **upscale nearest-neighbor** (ImageMagick, `-filter point`) so it survives stream compression, and open **fullscreen** with `feh -F -Z` (fallbacks: `eog`/`ristretto`/`gpicview`/`display`). The QR showed — but its **bottom rows were covered by the Twitch player's control-bar gradient** (viewer-side UI), so a direct `zbarimg` decode failed.

Fix: render the QR at **moderate size, centered, with a wide white quiet-zone border** (`-bordercolor white -border 160`), so the whole code sits mid-screen, clear of the player UI. With the player controls hidden (no mouse movement for a few seconds), the capture is clean. The clipped first capture was also recoverable: 29×29 grid, mask 2 / EC level L, standard `EC 11` pad bytes restored, and the ~14 unknown bytes rebuilt with **Reed–Solomon** → ZXing confirmed:

```
IDP{tw1tch_PWN_1m4g3m_kayb95abpj}
```

The flag text (`1m4g3m`) confirms the intended trick: the secret lives in an image.

## What didn't work

| Hypothesis | Result | Why |
|---|---|---|
| Pwn01 trick: `chmod u+r` + `cat` our flag | ✗ | File is readable already, but it's a **PNG**, not text — `cat` prints binary |
| Write `desafio-02` into `/opt/twitch-active-challenges` | ✗ `WRITE_DENIED` | `root:root 0644` — `ctf` can't write; no setuid/sudo to privesc |
| Attack before activation | ✗ | `/twitch/desafio-02` didn't exist until the organizers appended it |
| `strings` the PNG for a text chunk | ✗ | Pure QR image, no `IDP{` in bytes |
| Phone-scan the QR off the live | ✗ | Too small / clipped by the player control bar on the stream |
| `zbarimg` on the first fullscreen capture | ✗ | Bottom QR rows covered by the Twitch player UI gradient |
| Centered QR + white quiet zone, controls hidden | ✓ | Full grid captured → decodes (and clipped grid recoverable via Reed–Solomon) |

## Conclusion

Not a memory-corruption pwn and not a privesc: arbitrary code execution as `ctf` is handed to you. The real puzzle is **(1)** recognizing that the target materializes only when `/opt/twitch-active-challenges` (root-owned) lists it — you wait for activation, you don't force it — and **(2)** exfiltrating a **QR-encoded flag image** over a **one-way video channel**, including making the QR readable despite the Twitch player clipping its bottom (upscale + quiet zone, or Reed–Solomon recovery).

---

## Appendix — tools

All binaries are static x86-64 ELFs (`gcc -O2 -static`) submitted to the service; each renders to the screen and holds ~115 s for the stream. We only ever listed the directory and read **our own** `flag-nop.png`.

- `recon.c` / `recon2.c` / `recon3.c` — environment enumeration (`id`, `/twitch`, FS-wide flag search, setuid/caps); `recon3` adds the **auto-paging xterm** so long dumps are fully captured on the one-way channel.
- `exploit2.c` — found the orchestration: `/opt/twitch-active-challenges` is `root:root 0644`; write denied; located the per-team flag dir.
- `exploit3.c` — listed `/twitch/desafio-02` once active; found the flags are **PNGs** owned by `ctf`; ours is `flag-nop.png`.
- `exploit4.c` — upscales and shows the QR **fullscreen** (`feh`); first working render (bottom clipped by player UI).
- `exploit5.c` — QR at moderate size, **centered with a white quiet-zone border**, clear of the player controls → clean capture → `zbarimg` / ZXing decodes the flag.

Build: `gcc -O2 -static -o <name> <name>.c` · verify `file <name>` → *ELF 64-bit x86-64, statically linked*.
