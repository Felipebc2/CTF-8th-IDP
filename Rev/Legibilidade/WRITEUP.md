<div align="center">

<a href="https://git.io/typing-svg"><img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=28&duration=700&pause=1000&color=E8423F&center=true&vCenter=true&repeat=false&width=500&height=35&lines=Legibilidade" alt="Typing SVG" /></a>

</div>

# Legibilidade — REV · 🟢 EASY

- **Status:** ✅ SOLVED — flag recovered statically from the binary, without running it
- **Points:** 100 (final dynamic value) · 🩸 first blood
- **Flag:** `IDP{stR1nGs_3_r0t_Eh_s3mpr3_UtiL_48b839d27}`
- **Attachment:** `16349b0703c14087700d3b0e0203056b.zip` → `programa` (ELF 64-bit PIE, x86-64, dynamically linked, not stripped, 16176 bytes, sha256 `6a9971eda16d4438a3c765a70cd01a43a5fe3a9ba929851ab2bf6651675448f3`)
- **Prompt:** *"As vezes só não dá pra ler a strings mesmo."* ("Sometimes you just can't read the strings.")

---

## TL;DR

1. `programa` is a small flag checker. It asks for the flag, then compares the input with `strcmp`.
2. The expected flag is stored in `.rodata` as the symbol `flag`, but it is ROT13-encoded. `strings` shows it, it just isn't readable as `IDP{...}`.
3. Applying ROT13 to `VQC{fgE1aTf_3_e0g_Ru_f3zce3_HgvY_48o839q27}` gives the flag.

## Analysis

### Triage

The binary is not stripped, so `nm` lists the interesting symbols directly:

```
00000000000011c9 T main
0000000000002020 R flag
```

`flag` is a read-only object in `.rodata` (`0x2000`, size `0x80`). The file offset equals the vaddr, so the string starts at file offset `0x2020`. `strings` also shows it, next to the prompt and the success message:

```
VQC{fgE1aTf_3_e0g_Ru_f3zce3_HgvY_48o839q27}
Digite a flag: 
Parabens!
```

`VQC{` stands in for `IDP{`. Each letter is shifted by 13 (`I→V`, `D→Q`, `P→C`), while the braces, digits and underscores are unchanged. This is ROT13.

### `main`

The disassembly of `main` (`0x11c9`) confirms it. The loop walks `flag` byte by byte into a stack buffer at `rbp-0xe0`:

- If the byte is a letter (`0x41..0x5a` or `0x61..0x7a`), it picks the base `'A'` (`0x41`) or `'a'` (`0x61`) and computes `(c - base + 13) % 26 + base`. The `% 26` is compiled as a multiply by the magic constant `0x4ec4ec4f`, followed by `sar 3` and `imul 0x1a`.
- Any other byte is copied as is.

```asm
12b5:  movsx  edx,al                 ; c
12b8:  movsx  eax,BYTE PTR [rbp-0xe9] ; base ('A' or 'a')
12bf:  sub    edx,eax
12c1:  lea    eax,[rdx+0xd]          ; c - base + 13
12c7:  imul   rdx,rdx,0x4ec4ec4f     ; ... % 26
12dc:  imul   ecx,edx,0x1a
12df:  sub    eax,ecx
12ea:  add    eax,edx                ; + base
```

After decoding, it prints `Digite a flag: `, reads the input with `scanf("%100s")` into `rbp-0x70`, and compares it with the decoded buffer using `strcmp`. On a match it prints `Parabens!`, otherwise `Nao foi dessa vez..`.

ROT13 is its own inverse, so decoding the stored string gives the expected input:

```
VQC{fgE1aTf_3_e0g_Ru_f3zce3_HgvY_48o839q27} -> IDP{stR1nGs_3_r0t_Eh_s3mpr3_UtiL_48b839d27}
```

The flag text ("strings e rot é sempre útil", i.e. "strings and rot are always useful") fits the method.

## What didn't work

| Hypothesis | Result | Why |
|---|---|---|
| Packed binary / self-decrypting code (`mprotect` + XOR) | ✗ | No `mprotect` import, no unusual sections, and `main` disassembles cleanly |
| Stack strings or `.init_array` constructors hiding the flag | ✗ | `.init_array` only holds `frame_dummy`. The flag is a plain `.rodata` symbol |
| Multi-byte XOR key | ✗ | Not needed. The shift is a fixed 13 applied to letters only |

## Conclusion

The "unreadable" strings were just ROT13. Reading `.rodata` and recognising `VQC{` as a shifted `IDP{` solves the challenge. The disassembly of `main` confirms the transform, so the binary never had to be run.

---

## Appendix — tools

- `solve.py` — `python3 -I solve.py extracted/programa`: reads the NUL-terminated string at file offset `0x2020`, applies ROT13, and asserts that the result matches `IDP{...}`.
