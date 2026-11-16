# Party in BSB

- **Categoria:** Web
- **Pontos:** 500 (pontuação dinâmica)
- **Status:** ✅ Resolvido
- **Descrição:** "Encontre o próximo rolê em Brasília."
- **Host:** `http://<HOST>:<PORT>` (container efêmero, expira em 15 min)
- **Flag:** `IDP{sqli_t4r_syml1nk_nB4dXfaCV3}`

## Resumo
App Flask de eventos. Cadeia de 3 bugs: **SQLi** no login (`admin' -- -`) → painel admin de arquivos → **TarSlip** no import (`extractall` sem sanitizar) planta um **symlink `x -> /`** dentro de `/app` → `download?path=x/flag.txt` segue o symlink e lê `/flag.txt` fora do confinamento.

Ver `WRITEUP.md`. Artefatos: `solve.py`, `exploit.tar.gz`, `app.py` (fonte baixado via admin).
