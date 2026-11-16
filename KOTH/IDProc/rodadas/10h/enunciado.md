# Rodada 5 (14/11 10:00–10:50) - Alternador de desvios

## Enunciado
As filas INPUT_A e INPUT_B têm a mesma quantidade de valores. Para cada posição, envie A + 1 e depois B - 1.

## Máquina
N0 (INPUT_A) → N2 ← N1 (INPUT_B). N2 tem OUTPUT e o cabeçalho mostra INPUT_A e INPUT_B. Portas do link assumidas: N0.DIR→N2.ESQ, N1.ESQ→N2.DIR.

## Exemplo
A = 10..15, B = 50..55 → 11, 49, 12, 50, ..., 16, 54

## Versões (local)
| Arquivo | Instr. | Ciclos (exemplo) | Status |
|---|---|---|---|
| so_n2.idp (só N2 lê A e B direto) | 6 | 36 | base |
| hibrido.idp (N2 lê A, N1 manda B-1) | 8 | 30 | descartado |
| tres_nucleos.idp (N0/N1 calculam, N2 repassa) | 10 | 26 | base |
| solucao.idp (variante única do só-N2) | 6 | 36 (oficial 36 ciclos / 6 instr.) | não enviado |
| solucao_3nucleos.idp (variante única 3 núcleos) | 10 | 26 (oficial 26 ciclos / 10 instr.) | enviado ~10:04; ranking: 148 ciclos / 10 instr., 140 pts (empate com 4 times) |
