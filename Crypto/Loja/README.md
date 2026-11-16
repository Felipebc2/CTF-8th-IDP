# Loja — CRYPTO · 259 pts

- **Status:** ✅ SOLVED
- **Target:** `<HOST>:<PORT>` (Flask + gunicorn)
- **Prompt:** *"Já tão vendendo os brindes do evento."*
- **Flag:** `IDP{p4g4r_p4r4_g4nh4r_3CB_s9rJHYKwkf}`

## Ideia

Loja ("Lojinha IDP") vende brindes e **a flag como produto** (`/produto/flag`, R$ 31.337,42).
O gateway **IDPay** devolve o resultado do pagamento como blob **AES-ECB** (sem IV, sem MAC) em
`/pagamento/retorno?data=<hex>`. O `blk0` cifra só o `status` e é idêntico em todo pedido aprovado.
**Cut-and-paste ECB:** cola o `blk0` "aprovado" de um item barato na frente dos `blk1-4` da flag
(produto=flag) → servidor decifra, lê `status=aprovado`+`produto=flag`, entrega a flag.

Ver `WRITEUP.md` para a análise completa.

## Arquivos

- `solve/solve.py` — forja o token (`python3 solve/solve.py <token_aprovado> <token_flag>`)
- `WRITEUP.md` — writeup
- `img/` — prints
