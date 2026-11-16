<div align="center">

<a href="https://git.io/typing-svg"><img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=28&duration=700&pause=1000&color=E8423F&center=true&vCenter=true&repeat=false&width=500&height=35&lines=TWITCH+PWN+03" alt="Typing SVG" /></a>

</div>

# Twitch Pwn 03 — PWN · 🔴 HARD

- **Status:** ✅ SOLVED — flag leaked live via a format-string `%12$s` (exploit and flag mine; a teammate submitted it on the platform).
- **Points:** 377 (final dynamic value)
- **Flag:** `IDP{tw1tch_PWN_f0rm4t4_c0rd4s_c6h8qc8wqe}`
- **Attachment / Target:** web service `<HOST>` (submit an x86-64 ELF; team login `<USER>`/`<PASSWORD>`); execution streamed on Twitch `<CHANNEL>`.
- **Prompt:** *"Quem sabe faz ao vivo! Acompanhe em Twitch TV."* — "mande o seu recado para a live utilizando `/usr/local/bin/recado <recado>`: ele será mostrado para os nossos milhões de viewers... vai aparecer **tudo, sem filtro**." Flags in `/twitch/desafio-03/`, environment restored each run.

---

## TL;DR

1. Same machine as **Twitch Pwn 01/02**: you submit an x86-64 ELF, it runs **as `ctf`** on a GUI desktop **livestreamed on Twitch**. The **only output channel is the streamed screen**.
2. This time the flag `/twitch/desafio-03/flag-nop.txt` is `-r--------` owned **`chat:chat`** — `ctf` **cannot** read it (the Pwn01 `chmod` trick fails: we're not the owner). The helper `/usr/local/bin/recado` is `-rws--x--x chat:chat` = **setuid `chat`**, world-executable, not readable.
3. `recado` prints your message **"sem filtro"** — it does `printf(<your text>)` with **no format specifier** → a **format-string vulnerability**. It runs as `chat`, and it holds a copy of the flag on its stack. Passing `%12$s` makes `printf` dereference the stack slot pointing at that buffer and **print the flag** on the live. No shell, no `%n` write needed.

## Analysis

### Recon
A static recon ELF (reusing the Pwn02 auto-paging xterm, since the screen is the only output) showed:

```
id → uid=1000(ctf) gid=1000(ctf)
/twitch/desafio-03/flag-nop.txt   -r--------  chat chat   42
/usr/local/bin/recado             -rws--x--x  chat chat   14576
flag read probe → FAIL (Permission denied)   # ctf can't read a chat-only file
```

So: the flag is readable **only by `chat`**, and the one thing we have that runs as `chat` is the setuid `recado`. The challenge's "sem filtro" is the hint about `recado`'s bug.

### Wrong turn: command injection
First guess was that `recado` shells out with our argument unescaped. We tried `$(...)`, `;`, backticks, both quote styles — all were **echoed literally**:

```
Recado para o chat: $(cat /twitch/desafio-03/flag-nop.txt)
Recado para o chat: '; id; cat /twitch/desafio-03/flag-nop.txt; echo '
```

No shell is involved. But a format-string probe did fire:

```
arg: %p.%p.%p.%p.%p.%p...
Recado para o chat: 0x7ffcf79f94d0.(nil).(nil).0x14.0x7.0x7ffcf79f9858.0x200300000...
```

The `%p`s were **consumed** → `recado` calls `printf(buf)` where `buf` already contains our argument. Classic format string.

### The leak
A format string only reads **memory**, not files — so this works **only because `recado` loads the flag into its own memory** (it runs as `chat`, opens the `chat`-owned flag, keeps it in a stack buffer). We dumped `%6$s`..`%20$s`, each in a separate `fork()+execl()` child so a bad-pointer segfault in one slot doesn't kill the others. Slot **12** held the flag:

```
--- [9] string dump slot 12 (%12$s) ---
arg: %12$s
Recado para o chat: IDP{tw1tch_PWN_f0rm4t4_c0rd4s_c6h8qc8wqe}
[status: 0]
```

The flag text (`f0rm4t4_c0rd4s` ≈ "format string / strings") confirms the intended trick.

## What didn't work

| Hypothesis | Result | Why |
|---|---|---|
| Pwn01 `chmod u+r` + `cat` our flag | ✗ | Flag is owned by `chat`, not `ctf` — we can't `chmod` what we don't own |
| Shell command injection via `recado` arg (`$()`, `;`, backticks, quote breakout) | ✗ | `recado` never spawns a shell — it prints the argument literally |
| Format-string `%n` write → code-exec as `chat` | ✗ (unnecessary) | The flag is already in `recado`'s memory; a plain `%N$s` read suffices |
| `%p` map / `%s` on wrong slots | partial | Non-string slots just print `(nil)` or segfault that child; slot 12 held the flag |

## Next time (série TwitchPwn)

Flags nesta série alternam entre **texto** (01, 03) e **QR PNG** (02, 04). Lição pra próxima:
assim que tivermos leitura da flag, **testar as duas formas no mesmo run** — `cat` (caso seja
texto) **e** abrir como imagem / renderizar o QR centralizado com quiet-zone branca (caso seja
PNG) — além de um `file`/`ls` no arquivo antes. Não assumir texto nem imagem: fazer os dois de
uma vez economiza uma iteração (cada run no alvo custa ~120s).

## Conclusion

Not command injection and not a `%n` corruption chain: `recado` is **setuid `chat`**, reads the `chat`-owned flag into a stack buffer, and prints user input through a **format-string bug** (`printf(buf)`). Submitting `%12$s` leaks the flag straight onto the livestream. The owner split (flag `chat:chat`, we run as `ctf`) is what forces you through the setuid helper instead of reading the file directly.

---

## Appendix — tools

All binaries are static x86-64 ELFs (`gcc -O2 -static`) submitted to the service; each renders to the screen via the auto-paging xterm (DISPLAY/XAUTHORITY export, write to a `/tmp` file, hold ~115 s) and calls `recado` via `fork()+execl()` so each payload is passed as one literal `argv[1]` (our own code never runs a shell over it). We only ever read **our own** `flag-nop.txt`.

- `recon.c` / `recon` — enumerates `id`, `/twitch/desafio-03`, `recado`'s mode/setuid bit, and a direct flag-read probe.
- `exploit.c` / `exploit` — first attempt: three shell-injection shapes (showed `recado` echoes literally → no shell).
- `exploit2.c` / `exploit2` — quote-breakout + a `%p` format-string probe → **confirmed the format-string bug**.
- `exploit3.c` / `exploit3` — format-string dump: `%1$p`..`%40$p` stack map + `%6$s`..`%20$s` string leaks → **slot 12 = flag**.

Winning payload (single `recado` argument):

```
%12$s
```

Build: `gcc -O2 -static -o <name> <name>.c` · verify `file <name>` → *ELF 64-bit x86-64, statically linked*.
