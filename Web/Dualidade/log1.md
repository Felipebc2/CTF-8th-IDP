# Dualidade — log de tentativas (anti-retrabalho)

> Objetivo: registrar TUDO que já foi testado e o resultado, pra nenhum agente repetir.
> Status: ❌ UNSOLVED. 3 times resolveram → é solúvel, resposta provavelmente "à vista".
> Última atualização: 2026-11-14 02:00.

## Modelo do servidor (fatos confirmados)

- **nginx/1.27.5**, estático puro. Sem backend/linguagem (sem X-Powered-By, sem SSTI, HTTP/1.1 só).
- Lógica = `map $http_cookie` escolhendo qual HTML/PNG servir. Config artesanal (`add_header` manual: `Set-Cookie: rick; Path=/`, `Accept-Ranges:  none` com espaço duplo, `Cache-Control: no-store`, `Vary: Cookie`).
- **3 rotas só**: `/`, `/dualidade.png`, `/no.png`. Resto 404. Sem autoindex. `/index.html`→404, `/robots.txt`→404.
- Oráculo do cookie (match da linha `Cookie:` INTEIRA, exato, case-sensitive, não-substring):
  - **sem cookie** → `dualidade.png` + `Set-Cookie: rick` (te dá o rick)
  - **`rick`** → `dualidade.png`
  - **qualquer outro token** → `no.png`
  - **win (dupla certa)** → ??? (HTML interno atrás do cookie, não é arquivo buscável)
- HTML dos dois estados é idêntico, muda só `<img src>`. Sem comentário/title/hint.
- `ETag "6aeeced4-20c"` = mtime(07/11/2026 07:10:12) + size(524). Zero info escondida.

## O que JÁ foi testado — NÃO repetir

### Cookie / conteúdo
| Teste | Resultado |
|---|---|
| `rick` | → dualidade.png (estado inicial, NÃO é o win) |
| sem cookie / vazio | → dualidade.png + Set-Cookie rick |
| tokens únicos (~26): jekyll, hyde, yin, yang, good, evil, tom, jerry, batman, robin, holmes, watson, bert, ernie, mario, luigi, morty, bonnie, clyde... | → `no.png` (todos) |
| duplas multi-palavra com separadores ` e `, `&`, ` & `, espaço, `_`, `-`, `+`, ` and `, `` (tom&jerry, mario&luigi, yin yang, bem e mal, etc.) | → `no.png` (⚠️ a rodada grande chegou a derrubar o container; confiabilidade parcial) |
| cookies `=` genéricos: `x=1`, `morty=1` | → default (dualidade) — mas é genérico, NÃO testou pares específicos |
| capitalização / espaço / substring (` rick`, `RICK`, `rickandmorty`) | não bate (exato minúsculo) |

### Vetores técnicos (todos mortos)
| Vetor | Resultado |
|---|---|
| HTTP desync / smuggling (CL.TE) | 400 nginx, sem duo de parsers / backend |
| HTTP/2 | não suportado (h1 only) |
| portas adjacentes | fechadas (000) |
| injeção/reflexão no cookie, CRLF, SSTI `{{7*7}}` | sem reflexão, sem redirect, sem avaliação |
| alias off-by-slash (`/assets../`, static, images, img → nginx.conf) | 404 |
| traversal encodado (`../`, `%2e%2e`, `dualidade.png/../`) | 400 |
| CVEs 2026 (42533 map/regex, 42945 rewrite, 9256 captures, 60005 slice) | pré-req ausente (sem regex-captura/rewrite/redirect/slice). Rejeitadas. |
| win-image por nome: sim/yes/flag/win/true/morty/duo/rickandmorty.png | 404 (todos) |

### Análise de imagem (inerte)
- `dualidade.png` (1254×1254): meme Rick&Morty "two paths", IA-gen (C2PA/gpt-image, Trufo). Placa central **em branco** (confirmado por zoom). Sem stego/LSB/metadata útil.
- `no.png` (739×415): meme Bugs Bunny "no". PNG limpo, IEND no fim, **0 bytes anexados**, sem chunk de texto, sem strings suspeitas.

### OSINT
- Sem repo público do hackathon IDP com os challenges. Sem writeup casando "name a more iconic duo". Desafio é original (arte gerada por IA pro evento). Org não dá dicas.

## HIPÓTESE ABERTA (não testada) — PRIORIDADE

**Formato `membro1=membro2` (cookie = dupla literal).** Racional: cookie é `nome=valor` (uma dupla); reto = "Dualidade"; `Set-Cookie: rick` (sem valor) = dupla incompleta → completar o par. O separador `=` nunca entrou em wordlist nenhuma. Branch `a=b` específica no `map` é plausível e inédita.

Ordem de teste sugerida (poucos, raciocinados — NÃO brute):
1. `rick=morty` (completa o par que o servidor te deu — melhor sonda de formato)
2. `jekyll=hyde`, `yin=yang` (duplas que SÃO a dualidade — batem com o tema)
3. `tom=jerry`, `bonnie=clyde`, `mario=luigi`, `batman=robin`, `bem=mal`

Oráculo: body que NÃO referencie `dualidade.png` (524) nem `no.png` (517), ou que contenha `IDP{`/`flag` = HIT.

## Regras do engajamento
- Claude NUNCA roda contra o alvo — o usuário roda. Claude só prepara e analisa.
- Sem scan massivo / brute (regra 4.5 + derruba o container frágil). Rodadas pequenas, raciocinadas.
