# 8º Hackathon IDP — III Capture The Flag 2026.2

Responda em português. Writeups em inglês.

- Regulamento completo: `docs/regulamento.md` (fonte de verdade; casos omissos = organização)
- Presencial, térreo do IDP Norte. Formato jeopardy, pontuação dinâmica, placar pode congelar no final
- Janelas de competição (Brasília): **13/11 18h–20h** e **14/11 08h–17h**. Pausa obrigatória 20h–08h: nada de reto nem envio, nem remoto (3.6). Fora das janelas, Claude não trabalha em reto
- Flag: `IDP{...}` (ex. `IDP{s0u_A_resposta}`), uma por desafio. Só sugerir flag confirmada, nunca chutada
- Flag do regulamento (9.3): `IDP{L1_e_c0rc0rd0_3_v0u_s3Gu1R_0_c0mB1N4d0}`, usar conforme orientação da organização
- Desempate: quem atingiu a pontuação final primeiro. Enviar flag assim que confirmada
- Proibido compartilhar flags entre equipes ou receber ajuda de fora do time (4.4)

## Estrutura

`<Categoria>/<NomeDoChallenge>/` com `README.md` (card) + `WRITEUP.md` (segue `WRITEUP_TEMPLATE.md`) + artefatos/solve. Categorias: `Web`, `Crypto`, `Forensics`, `Pwn`, `Rev`, `PPC` (programação), `OSINT`, `ARG`, `Misc` (atividades práticas e o resto). Prints em `img/`. Ao mudar status de um reto, atualizar a tabela do `README.md` raiz. Artefatos >100 MB vão para o `.gitignore` (sha256 no writeup).

## Regras invioláveis

1. NUNCA executar nada contra servidor/instância do reto, plataforma ou rede do evento (curl, nc, nmap, ssh, requests, browser...). Quem roda é o usuário.
2. Proibido: brute force no envio de flags, DoS, scan massivo, atacar plataforma ou outros times (4.5).
3. Nunca enviar flags nem publicar writeups/push durante a competição.

## Dispatch

Plugin `ctf-dispatch` habilitado neste projeto. O formato `IDP{...}` é gravado a cada sessão pelo hook `SessionStart` em `.claude/settings.local.json` (conferir com `/ctf-dispatch:setflag`).

- **Durante a competição:** só `/dispatch <CATEGORIA> "<conceito/palavras-chave que o usuário já identificou>"`, como consulta ao Arsenal (documentação). Nunca passar enunciado completo nem artefatos. Parar no checkpoint humano e **nunca** aprovar `solver-*` (4.3.4).
- **Após 14/11 17h:** uso livre (solvers incluídos) para revisar e documentar.

## Writeups

Só depois do encerramento (14/11 17h) e com tudo concluído: `WRITEUP.md` por reto seguindo `WRITEUP_TEMPLATE.md`, em inglês, e tabela do `README.md` atualizada. Anonimizar credenciais reais e hosts de infra (`<HOST>`, `<USER>`, `<TOKEN>`); flags e valores derivados do reto ficam.
