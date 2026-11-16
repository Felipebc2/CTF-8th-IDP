# Central de Chamados — WEB (496)

> Esse ano, o TI agora só abre chamados via sistema. O que acha?

- **Categoria:** Web · **Pontos:** 377 · **Status:** ✅ SOLVED
- **Flag:** `IDP{at3nd1m3nt0_ign0r4d0_c0m_SuC3SS0_dqaDr93Xev}`
- **Alvo:** `http://<HOST>:<PORT>` (container, TTL 15 min, porta muda a cada relançamento)

## Resumo

App **custom em Python/Flask** (`Server: gunicorn`) fantasiado de **GLPI**. As CVEs de GLPI são isca.

Cadeia: **self-register** → **stored XSS** no `conteudo` do feedback (`/Form/Render/95`). A visão do solicitante **escapa** o HTML, mas a do **admin renderiza cru** (`conteudo-rico`). Um **bot admin (HeadlessChrome)** abre cada feedback → o `<img onerror>` dispara no browser dele → exfiltra o **cookie de sessão** do admin (**não-HttpOnly**) pra um listener externo. Reusando o cookie, o chamado interno **#23846 "Senha do cofre de senhas"** contém a flag.

Detalhes em [`WRITEUP.md`](WRITEUP.md).
