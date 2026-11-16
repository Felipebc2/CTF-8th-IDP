#!/usr/bin/env python3
"""
Loja (WEB/CRYPTO) — ECB cut-and-paste forge of the IDPay payment callback.

The shop encrypts the payment result {status, order_id, product, price} with
AES-ECB (no IV, no MAC) and ships it as /pagamento/retorno?data=<hex>.
Block layout (16-byte blocks):
    blk0 = status      (identical for every APPROVED order, differs only for the declined flag)
    blk1 = order_id    (random per request)
    blk2..4 = product + price + padding

ECB encrypts each block independently, so we paste an "approved" blk0 (from any
cheap item) in front of the flag token's blk1..4 (product=flag). Server decrypts,
reads status=approved + product=flag, and hands over the digital product (the flag).

Usage:
    python3 solve.py <approved_token_hex> <flag_token_hex>
    # prints the forged ?data= value to request at /pagamento/retorno

Get the two tokens from the Location header of a POST /checkout/<slug> using the
IDPay sandbox test card 4111 1111 1111 1111 (any future expiry, any CVV):
    sal  (R$0,99)      -> approved
    flag (R$31.337,42) -> declined ("limite insuficiente")
"""
import sys

BS = 16

def blocks(hexstr):
    b = bytes.fromhex(hexstr)
    assert len(b) % BS == 0, f"token not block-aligned: {len(b)} bytes"
    return [b[i:i+BS] for i in range(0, len(b), BS)]

def forge(approved_hex, flag_hex):
    appr = blocks(approved_hex)
    flag = blocks(flag_hex)
    # keep approved status block (blk0) + flag's order_id/product/price blocks
    forged = [appr[0]] + flag[1:]
    return b"".join(forged).hex()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    print(forge(sys.argv[1], sys.argv[2]))
