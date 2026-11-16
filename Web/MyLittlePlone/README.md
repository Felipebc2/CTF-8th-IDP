# My Little Plone

- **Categoria:** Web
- **Pontos:** 500 (pontuação dinâmica)
- **Status:** ❌ UNSOLVED (primitivo anônimo confirmado; sandbox escape não concluído — ver `WRITEUP.md`)
- **Alvo:** `http://<HOST>:46600` (container, expira ~20 min)
- **Flag:** `IDP{...}`

## Descrição

> n-day sem público, o melhor que tem pra sofrer aprender.

Portal de notícias temático "equestria agora" (My Little Pony). O nome é trocadilho
com **Plone** (CMS Python/Zope).

## Pistas

- `/author/admin` → perfil de autor Plone (enumera usuário `admin`).
- Formulário de login via `POST /login` (dica: "login sem criptografia" / `came_from`).

## Hipótese (vetor) — resolvida

Bug pretendido = **Plone Security Hotfix 20261110** (11/11/2026, sem PoC público = o
"n-day sem público"): cadeia **anônima** de RCE. Não era o portlet CVE — esse foi
distrator de recon. Detalhes e refs no `WRITEUP.md`.

- **Front (confirmado):** `Products.CMFEditions` — `ConditionalTalesModifier.edit`
  sem declaração de segurança → anônimo grava condição TALES e lê o valor avaliado
  de volta por `isApplicable`. Write via **XML-RPC** (`REQUEST=None`); exige prefixo
  `python:`. Confirmado `python:42` → `42`.
- **Back (parede):** 4 pacotes core com `allow_module` amplo (CMFPlone.utils /
  browser.navtree / OFS.ObjectManager, MimetypesRegistry.common, plone.batching,
  plone.restapi→json) expõem o grafo de import. Dá pra alcançar o **objeto** `os`,
  mas `os.popen` cai no `guarded_getattr` (302). Falta: um callable importado direto
  (`from os import …`) num namespace público — enumerar na fonte 6.1.x, offline.
- **Fallback autenticado:** CVE-2026-57149 (portlet Classic, `Template`/`Macro` TALES)
  — RCE limpa mas exige sessão (`Manage portlets` = `Manager` por padrão); nenhuma
  credencial obtida.

## Progresso

- [x] Fingerprint (Plone 6 Classic / Waitress; versão exata não vazou)
- [x] Vetor anônimo identificado e primitivo confirmado (`portal_modifier` TALES)
- [ ] Sandbox escape → RCE (bloqueado no `guarded_getattr`)
- [ ] Ler flag
