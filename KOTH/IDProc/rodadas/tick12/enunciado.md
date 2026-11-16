# Tick 12 — Eco controlado (13/11 ~21h, "exemplo público")

## Enunciado

Copie cada valor de INPUT para OUTPUT.

## Máquina

- 1 núcleo `N0`; porta `INPUT` (in, topo) ← canal INPUT; porta `OUTPUT` (out, base) → canal OUTPUT
- Exemplo público: INPUT `8, -3` → gabarito `8, -3`

## Versões

| Versão | Instruções | Ciclos (local, exemplo) | Ciclos (oficial) | Enviado? |
|---|---|---|---|---|
| `solucao.idp` (wrap implícito) | 2 | 4 | ok | ✅ |
| `solucao_jmp.idp` (fallback) | 3 | 5 | — | não (wrap confirmado) |

Mínimo teórico: 2 instruções (não existe MOV porta→porta), 2 ciclos por valor.

## Ranking final

