# Luigi Tower

Desafio de plataforma da categoria Misc com uma subida de precisão. A análise e a solução estão no [write-up](WRITEUP.md).

**Enunciado:** “Agora é uma subida de precisão.”

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

No evento, o serviço usava a porta `23196`. O cliente desta cópia desenha todas as plataformas; o servidor informa uma seleção delas na conexão.

## Planejador de rota

Na raiz do cliente, execute `PYTHONPATH=. .venv/bin/python -m game.luigi_solver` para calcular e verificar uma rota localmente. O script salva os comandos em `game/luigi_route.json`. Acrescente `--send --host <servidor> --port <porta>` para tentar reproduzi-la no servidor; `--fast` envia os quadros sem aguardar o ritmo de jogo. O resultado remoto depende da disponibilidade e validação do serviço.
