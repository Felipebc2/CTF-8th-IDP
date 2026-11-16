# Rodada 14/11 12h

- Abre 12:00 · envios até **12:50** · avaliação 12:52
- Status: resolvido localmente, aguardando escolha/envio

## Enunciado

"Quádruplo e oposto": INPUT_A e INPUT_B têm a mesma quantidade de valores. Para cada posição, envie 4 × A e depois o oposto de B.

## Máquina

Mesma máquina da rodada 5 (10h): N0 (INPUT_A) → N2.ESQ, N1 (INPUT_B) → N2.DIR, N2 lê INPUT_A e INPUT_B direto e tem OUTPUT.

## Exemplos

A = 10..15, B = 50..55 → 40, -50, 44, -51, 48, -52, ...

## Versões

| Versão | Instruções | Ciclos (local) | Ciclos (oficial) | Enviado? |
|---|---|---|---|---|
| v11_3nucleos.idp (N0 faz 4A, N1 faz -B, N2 repassa) | 11 | 27 (4n+3, piso de 4 ciclos/elemento) | | |
| v9_n0_4a.idp (N0 faz 4A, N2 lê B e faz neg) | 9 | 33 | exemplo oficial: 33 ciclos / 9 instr., CORRECT | |
| v9_n1_negb.idp (N2 faz 4A, N1 faz -B) | 9 | 36 | | |
| v7_so_n2.idp (só N2) | 7 | 42 | | |

## Ranking final

<!-- posição, ciclos/instr do topo, nossos pontos -->
