# Referência: Web Security

## Quando usar
Desafio expõe URL HTTP(S) — login, API, upload, painel admin.

## Recon (comandos para o usuário rodar contra o alvo)
```bash
curl -i http://TARGET/            # headers, cookies, tech stack
curl -i http://TARGET/robots.txt
whatweb http://TARGET/
ffuf -u http://TARGET/FUZZ -w /usr/share/wordlists/dirb/common.txt -mc all
```
Checar: `Server`, `X-Powered-By`, cookies (`HttpOnly`, `SameSite`), CSP. Se o
HTML/JS do cliente expõe o fluxo (rotas, headers de auth, estados), mapear tudo
antes de atacar — muitas vezes a lógica inteira está no front.

## Classes de vulnerabilidade (por prioridade)

### Autenticação / JWT
- `alg: none` — reassinar sem assinatura.
- HS256 com secret fraca — brute (`hashcat -m 16500`, `jwt_tool -C -d wl.txt`).
- Confusão RS256→HS256 — usar a chave pública como secret HMAC.
- `jwt_tool <token> -T` (interativo).

### Injeção
- **SQLi:** `'`, `" OR 1=1--`, time-based (`SLEEP()`), UNION. `sqlmap` só depois
  de confirmar o ponto manualmente.
- **SSTI:** `{{7*7}}` / `${7*7}` / `#{7*7}` conforme engine; se confirmar,
  escalar para RCE (`{{ self.__init__.__globals__... }}` em Jinja2).
- **Path traversal:** `../../../etc/passwd`, encoding (`%2e%2e%2f`), bypass de
  filtro "../".

### Lógica / controle de acesso
- **IDOR:** variar IDs em endpoints autenticados; comparar respostas.
- **SSRF:** parâmetros que aceitam URL (webhook, import, preview) →
  `http://127.0.0.1`, `http://169.254.169.254/latest/meta-data/`, `file://`, `gopher://`.
- **Race condition / TOCTOU**: quando o fluxo
  legítimo não alcança o objetivo (ex.: voucher de uso único que sobe clearance
  só 1x, mas a flag exige 10). Se check→update→mark não forem atômicos, disparar
  N requests simultâneos com o mesmo token passa todos pela checagem antes da
  gravação. PoC: barreira de threads liberando ~32 POSTs de uma vez; confirmar
  por múltiplos `200` no mesmo recurso e estado final acima do limite.

### XSS
- `<script>alert(1)</script>` baseline; evadir filtro (encoding, `onerror=`).
- **Pegadinha:** payload em JS via URL quebra com `%3D`/`%2B` mal decodificados;
  `encodeURIComponent` aninhado gera double-encoding — **imprimir a URL final
  antes de mandar.**

### Server-side moderno
- RSC/SSR (Next.js): RCE via deserialização de Server Actions, endpoints internos
  (`/_next/...`, payloads `.rsc`).

## Template de script
```python
import requests
TARGET = "http://IP:PORT"          # hardcoded no topo
s = requests.Session()
r = s.get(f"{TARGET}/", timeout=5)
print(r.status_code, dict(r.headers))
# ajustar payload conforme a vuln identificada
r = s.post(f"{TARGET}/endpoint", json={"...": "..."}, timeout=5)
print(r.status_code, r.text[:2000])
```
Para race: `threading.Barrier(N)` + N threads, cada uma segurando no barrier e
disparando o POST junto. Evitar paralelismo exagerado contra o alvo fora disso.

## Referências externas
- PortSwigger Academy: https://portswigger.net/web-security
- OWASP WSTG: https://owasp.org/www-project-web-security-testing-guide/
- jwt_tool: https://github.com/ticarpi/jwt_tool
- HackTricks web: https://book.hacktricks.xyz/pentesting-web
