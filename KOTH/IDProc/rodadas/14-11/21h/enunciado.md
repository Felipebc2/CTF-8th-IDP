# Rodada 13/11 21h — Tick 12: Eco controlado

Esta pasta registra a mesma rodada também documentada em [`tick12/`](../tick12/).

## Enunciado

Copie cada valor de INPUT para OUTPUT.

## Máquina

- 1 núcleo `N0`; porta `INPUT` (in, topo) ← canal INPUT; porta `OUTPUT` (out, base) → canal OUTPUT
- Exemplo público: INPUT `8, -3` → gabarito `8, -3`
- A captura do console identifica a máquina como **Eco controlado**, exemplo público do **tick 12**, e mostra o núcleo `N0` com `INPUT` e `OUTPUT`.
- O segundo caso em [`maquina.json`](maquina.json), com `-128, 127, 0, 1, -1`, é um teste local adicional; não aparece na captura.

## Versões

| Versão | Instruções | Ciclos (local, exemplo) | Ciclos (oficial) | Enviado? |
|---|---|---|---|---|
| `solucao.idp` (wrap implícito) | 2 | 4 | ok | ✅ |
| [`solucao_jmp.idp`](../tick12/solucao_jmp.idp) (fallback) | 3 | 5 | — | não (wrap confirmado) |

Mínimo teórico: 2 instruções (não existe MOV porta→porta), 2 ciclos por valor.

## Ranking final

