# IDProc

- **Category:** KOTH (assembly programming, TIS-100-like)
- **Points:** 1640 (sum of rounds) · **2nd place** in the KotH ranking
- **Access:** `https://idproc.desafio.<DOMAIN>` (team login from the team card)
- **Attachment:** `manual-idproc.pdf` (sha256 `3dfc5a0a8eb0cf43b345e0967c363f8f1fde02bf9d2e16875df9d513635995ad`)
- **Description:** *"King of the Hill de programação em assembly para o processador IDProc. A cada rodada (tick) de uma hora, um problema novo aparece em https://idproc.desafio.<DOMAIN>. Escreva o programa no simulador, exporte o arquivo .idp e envie pela página do time. Vale o último envio válido até os 50 minutos da rodada (ex.: 18:50); aos 52 minutos, todos são avaliados. Cada rodada vale até 200 pontos: até 100 por usar menos ciclos e até 100 por usar menos instruções. Os pontos deste desafio são a soma das rodadas e se atualizam sozinhos. Entre com o login e a senha do cartão do time. O manual em anexo descreve a máquina e as instruções. Rodadas: hoje às 18h e 19h; amanhã de hora em hora, a partir das 8h."*
- **Status:** 🏁 finished — 4 round wins (12, 4, 6, 11); per-round results in `WRITEUP.md`

## Files

- `manual-idproc.pdf` / `manual-idproc.txt`: ISA manual (and its `pdftotext`)
- `idproc_sim.py`: local simulator (`python3 idproc_sim.py` = self-test)
- `rodadas/<HH>h/`: one folder per round: `enunciado.md`, `maquina.json`, `solucao.idp`
