# TwitchPwn03

Categoria: Pwn · **✅ SOLVED** · 500 pts

## Resumo
Flag `/twitch/desafio-03/flag-nop.txt` é `-r--------` dono `chat:chat` → só `chat` lê
(somos `ctf`; o truque de `chmod` da 01 não serve, não somos donos). O helper
`/usr/local/bin/recado` é `-rws--x--x chat:chat` = **setuid `chat`**, world-exec, não
legível. Ele imprime o argumento "sem filtro" via `printf(<texto>)` sem format
specifier → **format string**. Rodando como `chat`, ele carrega a flag num buffer da
stack; `%12$s` vaza a flag direto na live. Sem shell, sem `%n`.

## Flag
`IDP{tw1tch_PWN_f0rm4t4_c0rd4s_c6h8qc8wqe}`

## Artefatos
- `recon.c` / `recon` — enumeração (id, ls, modo/setuid do `recado`, probe de leitura).
- `exploit.c` / `exploit` — tentativa 1: injeção de comando (mostrou que `recado` ecoa literal, sem shell).
- `exploit2.c` / `exploit2` — quebra de aspas + sonda `%p` → confirmou o bug de format string.
- `exploit3.c` / `exploit3` — dump de format string (`%1$p..%40$p` + `%6$s..%20$s`) → slot 12 = flag.

## Payload vencedor
Argumento único do `recado`: `%12$s`

## Como roda
No `<HOST>`, como `<USER>`, submeter o ELF estático (`gcc -O2 -static`); ele abre um
xterm visível com a saída paginada (~14s/página). A flag aparece na linha `%12$s`.
