# WAForte — WEB · 🔴 HARD

- **Status:** ✅ SOLVED
- **Points:** 259 (final dynamic value)
- **Flag:** `IDP{p0p3n_3_rcE_3_cr0n_n3h_yHQd7ikF9y}`
- **Target:** `<HOST>:<PORT>` (Apache 2.4 + PHP 8.3, container efêmero 15 min)
- **Prompt:** *"Dessa vez você não vai conseguir ler a flag."*

`index.php` (visível com `?source=1`) faz `eval($_GET['code'])` depois de remover,
em loop, os chars `f l a g t x` (case-insensitive) e `` ` ``. Com **escapes octais
`\nnn`** (só `\` + dígitos) monta-se qualquer string → RCE irrestrito como
`www-data`. Mas `/flag.txt` é `0400 root:root` — "não dá pra ler". Privesc: o
`cron` roda `/usr/local/bin/run-scripts` como **root a cada minuto**, executando
`/bin/sh` em cada `*.sh` de `/opt/scripts` — diretório **world-writable**. Dropar
um `.sh` que copia a flag pra `/tmp` legível → flag.

See [`WRITEUP.md`](WRITEUP.md) · payload gen: [`solve.py`](solve.py).
