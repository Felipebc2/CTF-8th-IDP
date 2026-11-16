<div align="center">

<a href="https://git.io/typing-svg"><img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=28&duration=700&pause=1000&color=E8423F&center=true&vCenter=true&repeat=false&width=500&height=35&lines=HELPDESK" alt="Typing SVG" /></a>

</div>

# Helpdesk — NET · 🟡 MEDIUM

- **Status:** ✅ SOLVED
- **Points:** 323 (final dynamic value)
- **Flag:** `IDP{ch4m4d0_r3cup3r4d0_c0m_suC3ss0}`
- **Attachment:** `captura.pcap` (pcap, Raw IPv4, 484 packets, 6.78 s)
- **Prompt:** *"Central de Chamados da Tecnologia"*

---

## TL;DR

1. The pcap mixes a fake IT help-desk HTTP portal (JSON/XML tickets, 16 SVG icons, a **password-protected** `backup_atendimento.zip`) with a **VoIP call** on UDP 5004 — an **RTP / G.711 µ-law** stream, no SIP/SDP signaling.
2. Decode the RTP to audio: it is a sequence of **DTMF** beeps that dictate the zip password. Six digits read cleanly (`482951 … 4`); the four middle beeps are ambiguous on a naive FFT.
3. Anchor the clear digits and **brute the ambiguous middle** (`john`, mask `482951?a?a?a?a4`) → password **`48295133984`** → open the `.docx` inside the zip → flag in the report body.

## Analysis

### 1. Triage — two channels in one capture

```
udp 288  ├─ dns 2            portal.empresa.local → 10.44.7.9
         └─ data 286         <-- 57 KB undissected UDP
tcp 196  └─ http 64          JSON/XML help-desk API + 1 zipfile
```

The HTTP side is flavor: a portal `portal.empresa.local` (`10.44.7.18 → 10.44.7.9:80`) with a
ticket about recovering a backup, paginated notifications, 16 Office-style SVG icons, and
`GET /arquivos/backup_atendimento.zip`. Nothing contains the flag in clear text.

The real payload is the **286 UDP packets 5004↔5004** (`10.44.7.31 → 10.44.7.18`):

```
80 00 0b b8 00 00 fa 00 52 b1 a0 5e ...
^^ ^^                   ^^^^^^^^^^^ SSRC
RTP v2, PT=0 (G.711 µ-law/PCMU), seq 0x0bb8++, timestamp +160/pkt (20 ms @ 8 kHz)
```

There is no SIP/SDP, so Wireshark shows it as `data`. Force the dissector:

```bash
tshark -r captura.pcap -d udp.port==5004,rtp -q -z rtp,streams
# SSRC 0x52B1A05E  g711U  286 pkts  Lost 0 (0.0%)   -> clean 5.7 s call
```

### 2. RTP → audio → DTMF

Extract the RTP payload in sequence order and decode µ-law to PCM:

```bash
tshark -r captura.pcap -d udp.port==5004,rtp -Y rtp -T fields -e rtp.payload \
  | tr -d ':\n' | python3 -c 'import sys,binascii;sys.stdout.buffer.write(binascii.unhexlify(sys.stdin.read().strip()))' > call.ul
sox -t ul -r 8000 -c 1 call.ul -e signed -b 16 call_pcm.wav
```

A spectrogram (`sox call_pcm.wav -n spectrogram`) shows **11 tone bursts** at 0.52 s spacing,
each a pair of pure tones — classic **DTMF**. Measuring each burst by FFT:

| burst | tones (Hz) | digit |
|---|---|---|
| 0 | 770 + 1209 | **4** |
| 1 | 852 + 1336 | **8** |
| 2 | 697 + 1336 | **2** |
| 3 | 852 + 1477 | **9** |
| 4 | 770 + 1336 | **5** |
| 5 | 697 + 1209 | **1** |
| 6–9 | ~430 + ~1010 | **?** (off-grid) |
| 10 | 770 + 1209 | **4** |

So the password is `482951` + **4 unknown digits** + `4`. The four middle bursts measured as
~430/1010 Hz — not on the DTMF grid — so a naive decoder can't resolve them. (They are the four
missing password digits; a robust decoder / brute resolves them, see below.)

### 3. Crack the four middle digits, open the backup

The zip is **traditional ZipCrypto** (`extract using 2.0`, flag `09 00`), so `john` cracks it fast.
Anchor the known digits and brute only the middle — ~10⁴ (or 95⁴ printable) candidates, seconds:

```bash
zip2john extracted/backup_atendimento.zip > hash.txt
john --mask='482951?a?a?a?a4' hash.txt
# relatorio_recuperacao.docx : 48295133984
```

Password = **`48295133984`** (the middle beeps were `3 3 9 8`). Extract and read the `.docx`:

```bash
7z x -p48295133984 extracted/backup_atendimento.zip
unzip relatorio_recuperacao.docx -d docx && \
  grep -rao 'IDP{[^}]*}' docx/
# docx/word/document.xml: IDP{ch4m4d0_r3cup3r4d0_c0m_suC3ss0}
```

The flag is the *"Código de validação do procedimento"* at the end of the recovery report.

## What didn't work

| Hypothesis | Result | Why |
|---|---|---|
| Flag in HTTP JSON / docx in clear | ✗ | `grep IDP{` on all exported HTTP objects empty; zip is encrypted |
| 16 SVG icons hide a glyph/char each | ✗ | plain Office-theme UI icons (`<path>` rects/circles), no text |
| Middle = one printable char repeated ×k | ✗ | exhausted `482951 + c*k + 4` for all printable c, k≤6 (CRC check) |
| Password is purely the 7 clear digits | ✗ | `482951`, `4829514` rejected |
| Pure-numeric brute, length ≤ 9 | ✗ | `john --mask='?d…'` finished with no hit → middle not ≤3 digits |

## Conclusion

A two-layer NET challenge: an RTP/G.711 VoIP call (no signaling, forced dissector) carries DTMF that
dictates the ZipCrypto password of a `.docx` served over HTTP. The four off-grid middle beeps are the
only snag — anchoring the clean DTMF digits and brute-forcing the 4-digit gap with `john` closes it
without perfectly decoding those tones.

---

## Appendix — tools

- `dtmf.py` — `python3 dtmf.py call_pcm.wav`: energy-split the WAV into bursts, FFT each, snap to the DTMF grid, print the string.
- `solve.sh` — end-to-end: pcap → `call_pcm.wav` → DTMF table → `zip2john`/`john` crack → docx → flag.
