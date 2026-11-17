# Super Mario Wall

Desafio de plataforma da categoria Misc: alcance a moeda dentro da caixa. A análise da mecânica explorada está no [write-up](WRITEUP.md).

**Enunciado:** “Hora de derrubar a parede na força bruta.”

## Requisitos

- Python 3.12
- Uma janela gráfica

## Instalação

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Como jogar

```sh
PYTHONPATH=. .venv/bin/python -m game.client <servidor> <porta>
```

Sem servidor e porta, o jogo roda só localmente.

Use `A`/`D` ou as setas para andar, `W`, seta para cima, espaço ou 4 do teclado numérico para pular, `Z`, `X`, Shift ou 5 do teclado numérico para correr e atirar, `S` ou seta para baixo para abaixar e `R` para reiniciar.
A sessão dura 100 segundos de jogo.

No evento, o serviço usava a porta `23197`.

## Solução automatizada

Na raiz do cliente, `PYTHONPATH=. .venv/bin/python -m game.auto_solver` verifica a sequência em uma simulação local. Para reproduzi-la no serviço, use `PYTHONPATH=. .venv/bin/python -m game.auto_solver <servidor> <porta>`.
