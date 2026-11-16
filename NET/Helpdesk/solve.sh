#!/usr/bin/env bash
# Helpdesk (NET) — pcap RTP/G.711 → DTMF → crack ZipCrypto → flag in docx.
# Usage: ./solve.sh captura.pcap
set -euo pipefail
PCAP="${1:-captura.pcap}"
OUT="extracted"; mkdir -p "$OUT"

# 1. RTP (forced dissector, no SDP) → raw mu-law → PCM wav
tshark -r "$PCAP" -d udp.port==5004,rtp -Y rtp -T fields -e rtp.payload \
  | tr -d ':\n' \
  | python3 -c 'import sys,binascii;sys.stdout.buffer.write(binascii.unhexlify(sys.stdin.read().strip()))' > call.ul
sox -t ul -r 8000 -c 1 call.ul -e signed -b 16 call_pcm.wav

# 2. DTMF: 6 clear digits + 4 off-grid middle beeps (see dtmf.py for the table)
python3 dtmf.py call_pcm.wav || true   # yields 482951 <????> 4

# 3. Export the password-protected zip from HTTP, crack the 4-digit gap
tshark -r "$PCAP" --export-objects "http,$OUT/" >/dev/null 2>&1
zip2john "$OUT/backup_atendimento.zip" > hash.txt 2>/dev/null
john --mask='482951?a?a?a?a4' hash.txt >/dev/null 2>&1 || true
PW=$(john --show hash.txt | grep -oE '48295[0-9]+' | head -1)   # 48295133984
echo "[+] password: $PW"

# 4. Open the docx, print the flag
7z x -p"$PW" -o"$OUT/zipout" -y "$OUT/backup_atendimento.zip" >/dev/null
unzip -o "$OUT/zipout/relatorio_recuperacao.docx" -d "$OUT/docx" >/dev/null
grep -rao 'IDP{[^}]*}' "$OUT/docx/"
