<div align="center">

<a href="https://git.io/typing-svg"><img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=28&duration=700&pause=1000&color=E8423F&center=true&vCenter=true&repeat=false&width=500&height=35&lines=LOJA" alt="Typing SVG" /></a>

</div>

# Loja — CRYPTO · 🟡 MEDIUM

- **Status:** ✅ SOLVED — forged the IDPay callback token via AES-ECB cut-and-paste.
- **Points:** 259 (final dynamic value)
- **Flag:** `IDP{p4g4r_p4r4_g4nh4r_3CB_s9rJHYKwkf}`
- **Target:** `<HOST>:<PORT>` (Flask + gunicorn container)
- **Prompt:** *"Já tão vendendo os brindes do evento."*

---

## TL;DR

1. A fake shop ("Lojinha IDP") sells swag and **the flag itself** as a product (`/produto/flag`, R$ 31.337,42). Checkout is processed by a sandbox gateway "IDPay".
2. On POST `/checkout/<slug>` the server charges the card and redirects to `/pagamento/retorno?data=<hex>`, where `data` is the **AES-ECB encrypted** payment result `{status, order_id, product, price}` — **no IV, no MAC**.
3. ECB encrypts each 16-byte block independently. Block 0 encodes only the `status` field and is **identical for every approved order**, regardless of product/price. Paste an "approved" block 0 in front of the declined flag token's blocks 1–4 → `status=approved` + `product=flag`. The return page then prints the digital product: the flag.

## Analysis

### Recon

- `Server: gunicorn`, server-side rendered HTML, **no client JS** → all logic is backend.
- Products at `/produto/<slug>`; the target is `/produto/flag` ("Desejada Flag", **R$ 31.337,42**).
- "Buy" is a GET to `/checkout/<slug>` (price is **not** client-supplied — derived from slug), which renders a card form posting to itself. IDPay sandbox note: test card `4111 1111 1111 1111`, any future expiry, any CVV.

### The payment flow

POST `/checkout/<slug>` → `302` → `Location: /pagamento/retorno?data=<80-byte hex blob>`.

| Order | Price | Verdict at `/pagamento/retorno` |
|---|---|---|
| `sal` | R$ 0,99 | ✅ "Pagamento aprovado!" (Pedido #…) |
| `flag` | R$ 31.337,42 | ❌ "Pagamento recusado — limite insuficiente" |

The sandbox test card approves cheap items but the card issuer "declines" the R$ 31k flag. The decline is decided at charge time and **baked into the encrypted `data` blob**; `/pagamento/retorno` merely decrypts and displays it.

### Breaking the token

Collected several tokens (test card) and diffed them block-by-block (16 bytes). The blob is exactly **80 bytes = 5 blocks, no trailing MAC block**.

| blk | sal1 | sal2 | flag1 | estojo | camiseta | garrafa | meaning |
|----|----|----|----|----|----|----|----|
| 0 | `f16b…6f49` | `f16b…6f49` | `d0eb…d436` | `f16b…6f49` | `f16b…6f49` | `f16b…6f49` | **status** (same for all approved, differs only for declined flag) |
| 1 | random | random | random | random | random | random | **order_id** (changes every request) |
| 2–4 | fixed per product | — | — | — | — | — | **product + price + padding** |

Key observations:

- **Deterministic / no IV:** `sal1 == sal2` on every block except the random order_id → **ECB**, not CBC.
- **Block 0 ≠ product, ≠ price:** sal (R$0,99), estojo (R$54,90), camiseta (R$19,99), garrafa all share the **same** block 0 despite different products and prices. The only field that partitions `{cheap: identical}` vs `{flag: different}` is the **status** (approved vs declined).

So block 0 is a self-contained encryption of the status field. In ECB that block can be transplanted onto any other token.

### Forge (ECB cut-and-paste)

```
forged = ENC("approved")  ||  flag[order_id] || flag[product] || flag[price] || flag[padding]
       = sal.blk0         ||  flag.blk1      || flag.blk2      || flag.blk3   || flag.blk4
```

No key, no padding oracle needed — the last block (valid PKCS#7 padding) stays untouched, only block 0 is swapped.

```bash
FORGED=$(python3 solve/solve.py <sal_token> <flag_token>)
curl -s "$URL/pagamento/retorno?data=$FORGED"
# → "Pagamento aprovado!" · "Desejada Flag · R$ 31.337,42"
# → Seu produto digital: IDP{p4g4r_p4r4_g4nh4r_3CB_s9rJHYKwkf}
```

The flag text itself spells out the bug: **3CB** (ECB) and *"pagar para ganhar"* (pay to win).

## What didn't work / ruled out

| Hypothesis | Result | Why |
|---|---|---|
| Buy flag with the sandbox test card | ✗ | Issuer "declines" R$ 31k ("limite insuficiente") |
| Client-side price tampering | ✗ | No client JS; price derived server-side from the slug, never sent by the client |
| `flag.jpg` "dá zoom na foto" stego | — (red herring) | Decoy on the product page; real path is the crypto token |

## Conclusion

Classic ECB malleability: encrypting a structured record with ECB and no integrity check lets an attacker rearrange independent blocks. The `status` field lived in its own block, so a one-block cut-and-paste flipped a declined flag purchase into an approved one. Fix: authenticated encryption (AES-GCM) or encrypt-then-MAC, and bind status to order/product/price so blocks can't be reused.

---

## Appendix — tools

- `solve/solve.py` — `python3 solve/solve.py <approved_token_hex> <flag_token_hex>`: builds the forged `?data=` by prefixing an approved status block onto the flag token.
