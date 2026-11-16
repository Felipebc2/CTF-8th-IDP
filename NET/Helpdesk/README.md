# Helpdesk — NET

> *"Central de Chamados da Tecnologia"* · 500 pts · 🟡 MEDIUM · ✅ SOLVED

**Flag:** `IDP{ch4m4d0_r3cup3r4d0_c0m_suC3ss0}`

A pcap of a fake IT help-desk: an HTTP portal plus a **VoIP call** (RTP / G.711 µ-law on UDP 5004,
no SIP/SDP). Decode the RTP → **DTMF** beeps that dictate the password of a ZipCrypto
`backup_atendimento.zip`; the four off-grid middle beeps are brute-forced with `john`
(`482951?a?a?a?a4` → `48295133984`). The `.docx` inside holds the flag.

See [`WRITEUP.md`](WRITEUP.md). Artifacts: `captura.pcap`, `dtmf.py`, `solve.sh`.
