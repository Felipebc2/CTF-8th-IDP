---
name: ctf-challenge-flow
description: >-
  Processo padrão de cada desafio do 8º IDP CTF — organização e documentação (não
  é como resolver; para técnicas use ctf-solver). Use ao COMEÇAR um reto ("começar",
  "novo desafio", "abrir reto", "organiza a pasta") para criar a estrutura padrão
  da pasta e a branch; e ao TERMINAR/documentar ("writeup", "fechar reto", "abrir PR")
  para escrever o WRITEUP.md pelo WRITEUP_TEMPLATE.md, atualizar a tabela do README
  e abrir o PR no GitHub. Respeita as regras do evento: nunca rodar contra o alvo,
  nada de push/envio de flag/writeup durante a competição.
---

# CTF Challenge Flow — 8º IDP CTF

Padroniza o ciclo de vida de cada reto neste projeto. O `CLAUDE.md` deste repo é
a **fonte de verdade** das regras — em conflito, ele vence. Técnicas de solução
ficam na skill `ctf-solver`; esta skill é só o processo (pasta, writeup, PR).

## Janela de tempo (checar ANTES de qualquer git/envio)

Competição (Brasília): **13/11 18h–20h** e **14/11 08h–17h**. Pausa 20h–08h.
Durante a competição (regra 3 do CLAUDE.md): **nunca** `push`, enviar flag, nem
publicar writeup — nem remoto. Writeups e PR **só após 14/11 17h**. Fora das
janelas, não trabalhar em reto. Organizar pasta/branch localmente é permitido;
publicar não.

## Ao COMEÇAR um reto

1. **Categoria + nome.** Categorias (pastas já existem): `Web`, `Crypto`,
   `Forensics`, `Pwn`, `Rev`, `PPC` (programação), `OSINT`, `ARG`, `Misc`.
2. **Branch do reto** (a partir de `main`):
   `git checkout main && git checkout -b solve/<cat-minuscula>-<slug>`
   (ex.: `solve/web-login-bypass`).
3. **Pasta + card.** Criar `<Categoria>/<NomeDoChallenge>/` com:
   - `README.md` — card/working doc (template abaixo); recon e hipóteses vão aqui
     durante a prova.
   - artefatos fornecidos + `solve.py` (TARGET/HOST hardcoded no topo — ver `ctf-solver`).
   - `img/` para prints, se houver.
4. Carregar a skill `ctf-solver` para a técnica da categoria.

Template do card (`<Categoria>/<Nome>/README.md`):
```markdown
# <Nome> — <Categoria>

- **Status:** ❌ UNSOLVED
- **Points:** —
- **Target/Attachment:** `<arquivo>` ou `<HOST>:<PORT>`
- **Prompt:** "<enunciado>"

## Recon / hipóteses
- ...
```

## DURANTE (regras invioláveis)

- **Claude nunca executa** contra o alvo/plataforma/rede (curl, nc, nmap, requests,
  browser...). Escreve o script pronto; o usuário roda e cola o output.
- Arsenal durante a prova: `/dispatch <CATEGORIA> "<conceito já identificado>"` —
  nunca passar enunciado completo nem artefatos; parar no checkpoint humano;
  nunca aprovar `solver-*`.
- Só sugerir flag **confirmada**, nunca chutada. Não enviar durante a prova sem
  orientação; enviar assim que confirmada é decisão do time na plataforma.
- Ao mudar o status de um reto, atualizar a tabela do `README.md` raiz (fazer isso
  no commit do writeup, após a prova — não publicar durante).

## Ao TERMINAR (somente após 14/11 17h)

1. **Writeup.** Copiar `WRITEUP_TEMPLATE.md` → `<Categoria>/<Nome>/WRITEUP.md`,
   preencher **em inglês**. Anonimizar credenciais reais e hosts de infra
   (`<HOST>`, `<USER>`, `<TOKEN>`); flags e valores derivados do reto ficam.
   Artefato >100 MB vai pro `.gitignore` com sha256 no writeup.
2. **README raiz.** Atualizar a tabela de desafios (nome, categoria, dificuldade,
   pontos, status ✅/❌).
3. **Commit** na branch do reto:
   `git add <Categoria>/<Nome> README.md && git commit -m "writeup(<cat>): <Nome>"`
4. **Labels de categoria (uma vez por repo).** Para buscar writeups depois por
   `label:<Categoria>`, garantir que as labels existam no repo — criar as que
   faltarem (idempotente):
   ```sh
   for c in Web Crypto Forensics Pwn Rev PPC OSINT ARG Misc; do
     gh label create "$c" -f --color BFD4F2 >/dev/null 2>&1 || true
   done
   ```
   (opcional: dificuldade — `easy` 🟢, `medium` 🟡, `hard` 🔴, `insane` 🟣.)
5. **Push + PR** (remote `origin` = `github.com/Felipebc2/CTF-8th-IDP`; conta local
   `rafacandido7`) — **sempre** com título padronizado e `--label "<Categoria>"`:
   - **Título:** `[<Categoria>] <Nome>` (ex.: `[Crypto] Weak RSA`). Prefixo da
     categoria ajuda a busca por texto além da label; se cruza categorias, usar a
     de entrada (`[Web→Pwn] <Nome>`).
   - **Body:** aponta pro writeup, ex.: `--body "Writeup: <Categoria>/<Nome>/WRITEUP.md"`.
   - Colaborador: `git push -u origin solve/<cat>-<slug>` e
     `gh pr create --base main --title "[<Categoria>] <Nome>" --label "<Categoria>"
     --body "Writeup: <Categoria>/<Nome>/WRITEUP.md"`.
   - Sem acesso: fork (`gh repo fork Felipebc2/CTF-8th-IDP --remote`), push no fork,
     e `gh pr create --repo Felipebc2/CTF-8th-IDP --base main
     --head rafacandido7:solve/<cat>-<slug> --title "[<Categoria>] <Nome>"
     --label "<Categoria>" --body "Writeup: <Categoria>/<Nome>/WRITEUP.md"`.
   - Cruza categorias → mais de uma label (`--label A --label B`).
   - **Confirmar com o usuário antes do push/PR** (ação externa; e só após 14/11 17h).

Buscar o writeup depois: `gh pr list --repo Felipebc2/CTF-8th-IDP --label "<Categoria>"`,
ou no GitHub pela busca `label:<Categoria>`.

## Relação com outras skills

- `ctf-solver` — como resolver (referências por categoria + captação de técnicas).
- Esta skill — o processo em volta (pasta, branch, writeup, PR), colada às regras
  do evento.
