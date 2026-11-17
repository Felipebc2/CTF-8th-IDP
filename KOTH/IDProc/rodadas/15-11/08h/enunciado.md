# Rodada 3 — 14/11 08h — Filtro de Sinal

- Abre 08:00 · envios até **08:50** · avaliação 08:52
- Status: enviado 08:05, VÁLIDO; placar do time: 200 pts (tick 12 = 1º)

## Enunciado

Copie para OUTPUT somente os valores estritamente positivos de INPUT.

## Máquina

- 1 núcleo `N0`; porta `INPUT` (in) ← canal INPUT; porta `OUTPUT` (out) → canal OUTPUT
- Exemplo público: INPUT `-4, 3, -1, 5` → gabarito `3, 5`

## Versões

Não existe salto "≤ 0" em uma instrução só: `NEG`/`SUB 1` quebram em `-128` (wrap), então o mínimo é 4 instruções.

| Versão | Instr | Ciclos local (exemplo / 38 valores) | Oficial | Enviado? |
|---|---|---|---|---|
| `solucao.idp` (JGZ + JMP) | 4 | 12 / 108 | output ok | ✅ VÁLIDO 08:05 |
| `solucao_unroll.idp` (2× desenrolado) | 6 | 10 / 97 | | |
| `solucao_2saltos.idp` (JLZ + JEQ) | 4 | 12 / 109 | | |

## Ranking final

