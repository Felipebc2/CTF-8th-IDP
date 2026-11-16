# 8º Hackathon IDP — III Capture The Flag 2026.2

Responda em português. Writeups em inglês.

- Regulamento completo: `docs/regulamento.md` (fonte de verdade; casos omissos = organização)
- Presencial, térreo do IDP Norte. Formato jeopardy, pontuação dinâmica, placar pode congelar no final
- Competição contínua de 24h (Brasília): **13/11 18h → 14/11 18h**, sem pausa noturna (3.6/3.7 alterados pela organização em 13/11). Reto, envio de flag e writeup permitidos a noite toda. Após 14/11 18h, Claude não trabalha em reto
- Flag: `IDP{...}` (ex. `IDP{s0u_A_resposta}`), uma por desafio. Só sugerir flag confirmada, nunca chutada
- Flag do regulamento (9.3): `IDP{L1_e_c0rc0rd0_3_v0u_s3Gu1R_0_c0mB1N4d0}`, usar conforme orientação da organização
- Desempate: quem atingiu a pontuação final primeiro. Enviar flag assim que confirmada
- Proibido compartilhar flags entre equipes ou receber ajuda de fora do time (4.4)

## Resultado (evento encerrado)

Time **NOP: 2º lugar, 13813 pts**, 53/54 retos (só My Little Plone ficou aberto, 0 solves geral), 12 first bloods, KotH IDProc 2º (1640). Pontos nos writeups = valor dinâmico final.

## Credenciais

Em `CLAUDE.local.md` (gitignored). Nunca colocar credenciais em arquivo rastreado.

## Estrutura

`<Categoria>/<NomeDoChallenge>/` com `README.md` (card) + `WRITEUP.md` (segue `WRITEUP_TEMPLATE.md`) + artefatos/solve. Categorias (as da plataforma): `Crypto`, `JAIL`, `KOTH` (king of the hill), `Misc` (atividades práticas e o resto), `NET` (redes), `OSINT`, `PPC` (programação), `Pwn`, `Rev`, `Web`. Prints em `img/`. Ao mudar status de um reto, atualizar a tabela do `README.md` raiz. Artefatos >100 MB vão para o `.gitignore` (sha256 no writeup).

## Regras invioláveis

1. NUNCA executar nada contra servidor/instância do reto, plataforma ou rede do evento (curl, nc, nmap, ssh, requests, browser...). Quem roda é o usuário.
2. Proibido: brute force no envio de flags, DoS, scan massivo, atacar plataforma ou outros times (4.5).
3. Nunca enviar flags nem publicar writeups/push durante a competição.

## Dispatch

Plugin `ctf-dispatch` habilitado neste projeto. O formato `IDP{...}` é gravado a cada sessão pelo hook `SessionStart` em `.claude/settings.local.json` (conferir com `/ctf-dispatch:setflag`).

## Writeups

`WRITEUP.md` por reto (seguindo `WRITEUP_TEMPLATE.md`, em inglês) pode ser escrito localmente assim que o reto for resolvido; evento encerrado, publicar/push liberado (só a pedido do usuário). Atualizar a tabela do `README.md` junto. Anonimizar credenciais reais e hosts de infra (`<HOST>`, `<USER>`, `<TOKEN>`); flags e valores derivados do reto ficam.
