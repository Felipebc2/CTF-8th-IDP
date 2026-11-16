# Referência: Forense

## Quando usar
PCAP, dump de memória, imagem de disco, ou arquivo "estranho" (imagem/áudio com
dados escondidos). Para stego mais "misc" (QR, encoding, espectrograma), ver
também `misc-stego.md`.

## PCAP — triagem (tshark / Wireshark)
```bash
tshark -r cap.pcap -q -z io,phs                      # hierarquia de protocolos
tshark -r cap.pcap -Y "http.request"                 # requests HTTP
tshark -r cap.pcap --export-objects http,/tmp/out    # extrair arquivos por HTTP
tshark -r cap.pcap -Y "ftp || ftp-data"              # credenciais/arquivos FTP
tshark -r cap.pcap -Y "icmp"                         # exfil via ICMP (payload no ping)
tshark -r cap.pcap -Y "dns"                          # exfil via subdomínio DNS
tshark -r cap.pcap -x                                # bytes crus (ver além da interpretação)
```
GUI: `Follow > TCP Stream` reconstrói a conversa (flag costuma estar no meio de
um stream). **Parsing importa nos detalhes:** campos de NTP/ICMP podem carregar
dados fora do uso normal do protocolo; olhar os bytes crus, não só a
interpretação do Wireshark. Payload de poucos pacotes PSH pode estar cifrado
(ex.: XOR com chave variável — ver `crypto.md`).

## Arquivo escondido dentro de arquivo (carving)
```bash
file suspeito.jpg
binwalk suspeito.jpg          # assinaturas de formatos embutidos
binwalk -e suspeito.jpg       # extrai o que achar
exiftool suspeito.jpg         # metadados (autor, GPS, comentários)
strings -n 6 suspeito.jpg | grep -i flag
xxd suspeito.jpg | head -20   # magic bytes reais vs extensão
```
### Carving manual
Magic/EOI antecipado seguido de outro arquivo: JPEG com `FFD9` (EOI) cedo e um
ZIP (`PK\x03\x04`) embutido depois. Recortar os bytes do arquivo embutido por
offset (`dd`/Python slice) e extrair. ZIP pode ter "general purpose flag = 0"
(não criptografado de verdade apesar de parecer) → `unzip -p` extrai direto.
Marcadores úteis: `FFD8…FFD9` (JPEG), `PK\x03\x04`/`PK\x05\x06` (ZIP),
`%PDF`/`%%EOF` (PDF), `\x89PNG…IEND` (PNG).

## Esteganografia (imagem/áudio)
```bash
steghide extract -sf img.jpg      # senha simples/vazia
zsteg img.png                      # LSB em PNG/BMP
stegsolve                          # análise visual por bit-plane (GUI)
```
Áudio: abrir espectrograma (Sonic Visualiser / Audacity) — flag pode estar
desenhada no espectro; ou dados em LSB de WAV. Sempre conferir espectrograma e LSB
antes de assumir que o áudio é só áudio.

## Memory forensics (Volatility3)
```bash
vol -f dump.mem windows.info        # SO/profile
vol -f dump.mem windows.pslist      # processos
vol -f dump.mem windows.cmdline     # linha de comando dos processos
vol -f dump.mem windows.filescan    # arquivos referenciados
vol -f dump.mem windows.dumpfiles --virtaddr <addr>
```

## Validar SEMPRE antes de concluir
```bash
file extraido; wc -c extraido; xxd extraido | head
```
Regra do harness: nunca assumir extração "limpa" sem validar magic bytes e
tamanho — arquivo truncado ou com header errado é causa recorrente de retrabalho.

## Referências externas
- Wireshark Guide: https://www.wireshark.org/docs/wsug_html_chunked/
- binwalk: https://github.com/ReFirmLabs/binwalk
- Volatility3: https://volatility3.readthedocs.io/
- HackTricks Forensics: https://book.hacktricks.xyz/forensics
