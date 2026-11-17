# Rodada 14/11 13h

- Abre 13:00 · envios até **13:50** · avaliação 13:52
- Status: enviado d3_bit_u2.idp (zero tratado como positivo, sem confirmação da organização)

## Enunciado

"Concordância de sinal": leia A e B em pares. Envie A para OUTPUT somente quando A e B tiverem o mesmo sinal.

Ambíguo: o enunciado não diz como o zero conta. Três leituras: d1 = A·B > 0 (zero nunca sai), d2 = sinal de 3 valores (0 com 0 sai), d3 = bit de sinal (zero conta como positivo).

## Máquina

N0 (porta A) → N2.ESQ; N1 (porta B) → N2.DIR; N2 só tem OUTPUT (layout da rodada 6).

## Exemplos

A = 1, -3, 7; B = 2, 4, -1 → OUTPUT = 1 (o exemplo não distingue o zero). Oficial deu 11 ciclos onde o simulador local dava 6: a execução só termina depois de **todas as entradas lidas**. `idproc_sim.py` corrigido, e continua batendo com as rodadas 4–7.

## Versões

| Versão | Instruções | Ciclos (local) | Ciclos (oficial) | Enviado? |
|---|---|---|---|---|
| d1_estrito.idp (zero nunca sai) | 16 | ex. 11; 52 pares: 283 | | |
| d2_sinal3.idp (0 com 0 sai) | 17 | ex. 11; 52 pares: 290 | | |
| d3_bit.idp (zero = positivo) | 12 | ex. 11; 52 pares: 260 | exemplo oficial: 11 ciclos / 12 instr., CORRECT | |
| d3_bit_u2.idp (d3 desenrolado 2x) | 17 | ex. 10; 52 pares: 242 | exemplo oficial: 10 ciclos / 17 instr., CORRECT | **escolhida pelo time ~13:10** |

## Ranking final

<!-- posição, ciclos/instr do topo, nossos pontos -->
