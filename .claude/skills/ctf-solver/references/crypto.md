# Referência: Criptografia

## Quando usar
Ciphertext, chave pública, script de geração, serviço TCP que cifra/assina, ou
esquema matemático a inverter.

## Triagem rápida

| Sintoma | Suspeita |
|---|---|
| `n`, `e` pequenos (e=3, e=7) ou `n` fatorável | RSA fraco — Fermat, Wiener, factordb |
| `m^e < n` (mensagem curta, e pequeno) | **Small exponent — raiz e-ésima inteira, sem mod** |
| Vários `n` compartilhando fator | Common factor (`gcd` entre pares de `n`) |
| Mesmo `c` sob vários `n` com mesmo `e` | Håstad broadcast (CRT + raiz e-ésima) |
| Assinatura RSA sem padding / `e` pequeno | Bleichenbacher / forjar assinatura |
| Mesmo nonce/IV em AES-CTR/OFB ou XOR | Keystream reuse — XOR entre ciphertexts |
| AES-ECB (blocos de 16 repetidos) | ECB byte-at-a-time / block shuffling |
| AES-CBC com oráculo de padding | Padding oracle |
| "Aleatórios" previsíveis / `random.seed(x)` | LCG ou MT19937 — recuperar estado |
| ECDSA com nonce `k` repetido | Recuperar chave privada por 2 assinaturas |
| Esquema multivariado sem termos oil–oil | **UOV — fixar vinegar, resolver linear mod p** |
| Hash MD5/SHA1 colidindo | fastcoll / md5textcoll (ver `../../../shattered-*.pdf`) |
| `n` < 1024 bits e tempo disponível | Coppersmith / `small_roots()` (SageMath) |

## RSA — checklist
```python
from Crypto.Util.number import long_to_bytes, inverse
import gmpy2, math

n, e, c = ..., ..., ...

# 1. Fatoração fácil: factordb.com primeiro; depois RsaCtfTool (-n N -e E --uncipher C)
# 2. p,q próximos -> Fermat
def fermat(n):
    a = gmpy2.isqrt(n) + 1
    b2 = a*a - n
    while not gmpy2.is_square(b2):
        a += 1; b2 = a*a - n
    b = gmpy2.isqrt(b2)
    return a-b, a+b
# 3. GCD entre vários n -> fator comum: math.gcd(n1, n2) != 1
# 4. e pequeno + m curta -> raiz e-ésima direta (SEM mod):
m, exact = gmpy2.iroot(c, e)   # exact==True confirma raiz exata
print(long_to_bytes(int(m)))
```

### Small exponent "sem mod"
Quando `m` é curta e `e` pequeno (ex.: 7), `m^e < n`, então o `mod n` não faz
nada: `c == m^e` como inteiro. Recuperar `m` é só a raiz e-ésima inteira
(`gmpy2.iroot(c, e)`, checar `exact`). Vale tanto para a mensagem quanto para
seeds/valores curtos cifrados assim.

## XOR / keystream reuse
```python
# Com plaintext parcial conhecido (header de arquivo, prefixo de flag),
# recupera o keystream e aplica no resto.
known = b"\x89PNG\r\n\x1a\n"            # ex. PNG; validar estrutura além do magic
ks = bytes(a ^ b for a, b in zip(ct[:len(known)], known))
# Pegadinha comum: a "chave" pode VARIAR por bloco/pacote
# (ex.: XOR 1-byte subindo +7 a cada pacote: 0x2a,0x31,0x38,0x3f...). Checar
# se a "chave" é constante ou progressão antes de assumir.
```

## PRNG previsível
- **LCG:** com >= 3 saídas consecutivas, recuperar `a`,`c`,`m` via GCD de
  diferenças; depois prever/retroceder.
- **MT19937 (`random` do Python):** 624 saídas de 32 bits reconstroem o estado
  (`randcrack`). `random.seed(x)` com `x` pequeno/conhecido → reproduzir direto.
  Comum quando a seed vem de um valor cifrado recuperável
  (recuperar seed → `random.seed(seed*(i+1))` → inverter N shuffles na ordem).

## UOV / oil-vinegar (assinatura multivariada)
Se o gerador de polinômios inclui termos vinegar–vinegar e vinegar–oil mas
**nenhum termo oil–oil**, o sistema vira linear ao fixar as variáveis vinegar:
chutar os `V` vinegar → cada polinômio vira `Σ a_i·o_i = b (mod p)` → sistema
linear em `O` incógnitas oil, resolvido por eliminação de Gauss mod p
(`pow(a, -1, p)` para inverter). Buscar o chute de vinegar que dá sistema
consistente → recupera a assinatura.

## Coppersmith / small_roots (SageMath via sagecell.sagemath.org)
Quando parte da chave/mensagem é conhecida (partial key exposure, padding):
```python
n, e, c = ..., ..., ...
PR.<x> = PolynomialRing(Zmod(n))
f = (x + known_prefix)^e - c    # ajustar ao problema
f = f.monic()
print(f.small_roots(X=2^unknown_bits, beta=1.0))
```

## Hash cracking
```bash
hashcat -m <modo> -a 0 hash.txt ../../../rockyou.txt
john --wordlist=../../../rockyou.txt hash.txt
```
`hashlib` libera o GIL → threads em Python servem para brute de hash
(ao contrário de CPU-bound puro). Colisões MD5/SHA1: `shattered-*.pdf` na raiz
do repo são o exemplo clássico de colisão SHA1.

## Referências externas
- RsaCtfTool: https://github.com/Ganapati/RsaCtfTool
- CryptoHack (metodologia por técnica): https://cryptohack.org/
- SageCell: https://sagecell.sagemath.org/ · factordb: https://factordb.com/
