# Rodada 14/11 16h

- Abre 16:00 · envios até **16:50** · avaliação 16:52
- Status: recomendada `v18.idp`

## Enunciado

"Convergência tripla" (última rodada): para cada tripla A, B e C, envie A se B e C tiverem o mesmo sinal; caso contrário, envie -A.

## Máquina

N0 (A) → N1.ESQ; N1 (B) BAIXO → N3.CIMA; N2 (C) DIR → N3.ESQ; N3 → OUTPUT. Ideia: N1 manda A·sinal(B), N3 multiplica por sinal(C). Zero tratado como positivo (mesma regra da rodada 13h).

## Exemplos

A = 3,4 · B = 10,-2 · C = 5,1 → 3,-4

## Versões

| Versão | Instruções | Ciclos (local) | Ciclos (oficial) | Enviado? |
|---|---|---|---|---|
| `v18.idp` | 18 | 12 / 1239 | 12 (CORRECT) | recomendada |
| `v36_u2.idp` (N1 e N3 desenrolados) | 36 | 10 / 1281 | | não (pior com sinais mistos) |

## Ranking final

<!-- posição, ciclos/instr do topo, nossos pontos -->
