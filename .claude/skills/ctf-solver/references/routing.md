# Routing — sintoma do desafio → referência

Ler isto primeiro ao triar um desafio. Carregar só a(s) referência(s) que batem.

| Se o desafio tem... | Carregar |
|---|---|
| URL/porta HTTP(S), login, API, painel admin | `web.md` |
| Cookie/token JWT para analisar ou forjar | `web.md` |
| Parâmetro de URL que aceita outra URL (webhook, preview, import) | `web.md` |
| Upload de arquivo, campo de busca, formulário | `web.md` |
| Fluxo legítimo não alcança o objetivo (contador, clearance, saldo) | `web.md` (race/TOCTOU) |
| `n`, `e`, `c` (RSA) ou chave pública fornecida | `crypto.md` |
| Ciphertext + XOR / AES (ECB, CBC, CTR, OFB) | `crypto.md` |
| Script Python de geração de "aleatórios" (LCG, `random.seed`) | `crypto.md` |
| Hash para quebrar (MD5, SHA1, bcrypt, NTLM) | `crypto.md` |
| Duas assinaturas/mensagens com mesmo nonce ou mesma chave | `crypto.md` |
| Esquema de assinatura pós-quântico / multivariado (oil-vinegar, UOV) | `crypto.md` |
| Curva elíptica (ECC, ECDSA) com parâmetro estranho | `crypto.md` |
| Binário ELF/PE fornecido, com ou sem `nc host port` | `pwn-reverse.md` |
| Menção a buffer overflow, stack, canary, ROP, format string | `pwn-reverse.md` |
| "Descompile", "engenharia reversa", "encontre a lógica" | `pwn-reverse.md` |
| APK/.smali/.dex, bytecode, .wasm, verificador de provas / DSL | `pwn-reverse.md` |
| Arquivo `.pcap` / `.pcapng` | `forensics.md` |
| Dump de memória (`.mem`, `.raw`, `.vmem`, `.dmp`) | `forensics.md` |
| "Tem algo escondido nesse arquivo" / tamanho estranho | `forensics.md` |
| Imagem/áudio suspeito (LSB, espectrograma, metadados) | `forensics.md` ou `misc-stego.md` |
| QR code, encoding exótico, base-N, texto cifrado por substituição | `misc-stego.md` |
| HTML auto-contido que "transmite" algo (frames piscando) | `misc-stego.md` |
| Username, foto, email, domínio, perfil para rastrear (pública) | `osint-arg-prog.md` (OSINT) |
| Trilha de pistas cruzando plataformas/mídias (ARG) | `osint-arg-prog.md` (ARG) |
| Serviço `nc host port` com muitas rodadas de puzzle sob tempo | `osint-arg-prog.md` (programação) |
| Nada bate / categoria ambígua | ver abaixo |

## Cruzamento de categorias

Carregar a referência da **camada de entrada** primeiro; adicionar a segunda ao
identificar a virada (ex.: achou binário dentro do pcap → + `pwn-reverse.md`;
pcap com ciphertext → + `crypto.md`).

## Se não bater em nada

Perguntar ao usuário a categoria conforme o rótulo da plataforma (a maioria dos
CTFs já marca Web/Crypto/Pwn/Rev/Forensics/Misc) antes de adivinhar.
