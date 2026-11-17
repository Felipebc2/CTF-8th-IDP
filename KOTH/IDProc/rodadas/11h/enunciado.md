# Rodada 14/11 11h

- Abre 11:00 · envios até **11:50** · avaliação 11:52
- Status: **1º lugar, 165/200** (enviado solucao_13.idp)

## Enunciado

"Filtro em paralelo": as filas INPUT_A e INPUT_B têm o mesmo número de valores. Para cada posição, envie A para OUTPUT somente quando B for estritamente positivo.

## Máquina

N0 (INPUT_A) → DIR → N2.ESQ; N1 (INPUT_B) → ESQ → N2.DIR; N2 → OUTPUT. N2 não lê as entradas direto (ver `maquina.json`).

## Exemplos

A = 4, -3, 8; B = 10, 7, -2 → OUTPUT = 4, -3

## Versões

| Versão | Instruções | Ciclos (local) | Ciclos (oficial) | Enviado? |
|---|---|---|---|---|
| solucao_10.idp (óbvia: N2 testa B, descarta A com jmp) | 10 | ex. 9; soma 72 nos 4 testes | | |
| solucao_13.idp (N2 desenrolado 2x: negativo isolado custa 3 ciclos em vez de 4) | 13 | ex. 9; soma 68 nos 4 testes | exemplo oficial: 9 ciclos / 13 instr., CORRECT; ranking: 123 ciclos | **sim** |
| desenrolado3.idp (3x) | 16 | soma 66 | | não |

## Ranking final

1º NOP 123/13 → 165 · 2º jambatron, Loucos com TDAH, Prompt and Pray, Tokenless Fairies 130/10 → 150 · 2º Névoa 130/12 → 150 · 7º Litrão 154/13 → 135 · 5 times sem envio.
