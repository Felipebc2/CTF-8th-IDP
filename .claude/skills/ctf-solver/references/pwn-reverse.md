# Referência: Reverse Engineering & Binary Exploitation (pwn)

## Quando usar
Binário fornecido (ELF/PE), bytecode (APK/.smali/.dex, .wasm, .class), com ou sem
serviço TCP (`nc host port`), ou pedido de "reverter a lógica".

## Recon (local sobre o binário — permitido)
```bash
file ./chall
checksec --file=./chall     # NX, PIE, canary, RELRO, Fortify
strings ./chall | less      # "flag", "/bin/sh", format strings
objdump -d ./chall | less    # disasm sem GUI
nm ./chall | grep -i -E 'win|flag|system|secret'
```

## Análise estática — Ghidra
```bash
$GHIDRA_HOME/support/analyzeHeadless /tmp/proj ctf -import ./chall -postScript decompile.py
```
Focar em: `main`, funções que leem input (`gets`, `read`, `scanf`), comparações
de flag, funções não referenciadas (possível "win function": `system("/bin/sh")`,
`print_flag`). Alternativa leve: **Cutter** (radare2 GUI).

## Debug dinâmico — gdb + pwndbg/GEF
```bash
gdb ./chall
break main ; run ; info functions ; disassemble main ; x/20i $pc
```
Usar para confirmar offset de overflow, layout de stack, valores de registrador
no crash.

## Buffer overflow — template pwntools
```python
from pwn import *
context.arch = 'amd64'          # ajustar conforme `file`
HOST, PORT = "IP", 0            # hardcode do alvo

# io = process("./chall")       # testar LOCAL primeiro
io = remote(HOST, PORT)         # só depois de validar local
# offset = cyclic_find(0x6161616161616161)  # valor lido no RIP após crash
payload  = b"A" * OFFSET
payload += p64(RET_ADDR)
io.sendline(payload); io.interactive()
```

## Pipelines de operação / verificadores (categoria recorrente)
- **Inversão de pipeline:** mapear a sequência de operações aplicadas ao input
  (soma, xor, rotação, shuffle) e inverter a ordem + a operação inversa de cada
  passo. Se o shuffle usa PRNG semeado, recuperar a seed primeiro (ver `crypto.md`).
- **Proof assistant / DSL:** ler as regras de inferência aceitas pelo verificador
  e procurar regra mal validada (prova incompleta aceita, confusão de tipo) —
  tratar como mini-parser a fuzzear manualmente primeiro.
- **Determinismo oculto:** init que parece aleatório mas deriva de seed fixa
  conhecida (ex.: SHAKE-256(seed || contador) com seed default `"00"*32`) →
  calcular o valor direto sem simular o protocolo inteiro.

## Reverse de mobile / VM
- APK: `apktool d app.apk` → ler `smali/` ou decompilar com jadx. Procurar
  checagem de flag/licença em `onClick`/`check`.
- `.wasm`: converter com `wasm2wat`; para forjar módulo mínimo, escrever WAT
  que só produz o output exigido e compilar com `wat2wasm`.

## Erros recorrentes a evitar
- Prompt do servidor com bytes não-ASCII (`Op\xc3\xa7\xc3\xa3o:`) — comparar
  bytes exatos no `recvuntil`, não a string decodificada visualmente.
- Typos no output do server ("Difculdade") — copiar literal, não "corrigir".
- `recvuntil` multi-etapa — validar cada etapa isolada antes de encadear.
- Flag que só existe do lado da organização (lida de `.env`/serviço remoto):
  o exploit pode estar 100% certo localmente e só sair placeholder — nesse caso
  o bloqueio é de submissão, não de lógica (confirmar fluxo com a staff).

## Referências externas
- Ghidra: https://ghidra-sre.org/ · pwntools: https://docs.pwntools.com/
- pwndbg: https://github.com/pwndbg/pwndbg · ROP Emporium: https://ropemporium.com/
- HackTricks binexp: https://book.hacktricks.xyz/binary-exploitation
