# Rodada 4 (14/11 09:00–09:50) - Pipeline aritmético

## Enunciado
Para cada valor de INPUT, produza 2 × valor + 1. N0 dobra o valor; N1 soma 1 e escreve.

## Máquina
N0 (INPUT) → N1 (OUTPUT). Portas do link assumidas `DIR` (N0) / `ESQ` (N1).

## Exemplos
2, -3, 4 → 5, -5, 9

## Versões
| Arquivo | Instr. | Ciclos (local, exemplo) | Status |
|---|---|---|---|
| solucao.idp (3+3, balanceado) | 6 | 11 (oficial: 11 ciclos / 6 instr.) | enviado 09:03 |
| split 2+4 | 6 | 13 | descartado (gargalo 4 ciclos/valor) |
| solucao_v2.idp (SUB -1, [N1] antes, minúsculas, vírgulas, rótulos, comentário) | 6 | 11 | enviado 09:31 (oficial 11 ciclos / 6 instr.), VÁLIDO |
