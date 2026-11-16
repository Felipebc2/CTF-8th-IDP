# Rodada 14/11 15h

- Abre 15:00 · envios até **15:50** · avaliação 15:52
- Status: recomendada `v24_u2.idp`

## Enunciado

"Mistura até esgotar": Alterne A e B. Quando uma fila terminar em 0, consuma o sentinela e escoe a outra fila sem enviar seu sentinela.

## Máquina

N0 (A_IN) → N2.ESQ, N1 (B_IN) → N2.DIR, N2 → OUTPUT. `maquina.json` (exemplo + 26 casos gerados por `gen.py`).

## Exemplos

A = 1,2,0 · B = 10,20,30,0 → 1,10,2,20,30

## Versões

| Versão | Instruções | Ciclos (local) | Ciclos (oficial) | Enviado? |
|---|---|---|---|---|
| `v19_jmp.idp` (ingênua) | 19 | 20 / 801 | | não |
| `v18.idp` (jnz pula pro fim, sem jmp no laço) | 18 | 18 / 742 | | |
| `v24_u2.idp` (v18 + escoamento desenrolado 2x) | 24 | 18 / 711 | | recomendada |
| `v_u3.idp` (escoamento 3x) | 30 | 18 / 702 | | |

## Ranking final

<!-- posição, ciclos/instr do topo, nossos pontos -->
