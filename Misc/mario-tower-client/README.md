# Mario Tower

Desafio de plataforma da categoria Misc: suba a torre e alcance o final da fase antes do tempo acabar. A resolução está no [write-up](WRITEUP.md).

**Enunciado:** “Já jogou mario? É só chegar no final da fase.”

## Requisitos

- Python 3.12 ou mais recente
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

Use `A`/`D` ou as setas para andar, `W`, seta para cima ou espaço para pular, `Z` ou Shift para correr e `R` para reiniciar.
A sessão dura 120 segundos de jogo.

No evento, o serviço usava a porta `23195`. Substitua `<servidor>` e `<porta>` pelos dados da instância disponível.
