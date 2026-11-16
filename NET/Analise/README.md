# Análise

- **Category:** NET
- **Points:** 100 (final dynamic value)
- **Description:** "É necessário analisar se todos os dados estão de acordo."
- **Attachment:** `2c24735704c58d0be506679bd730320e.zip` (sha256 `d500e9e4c4eee0b2f0dae8fe16d4dab9197dca9924cb2ffae0b22a8de020e2da`) → `captura.pcap`
- **Status:** ✅ solved
- **Flag:** `IDP{c0ntr4t4-s3_pr0Gr4mad0r_VBA}`

## Solve path

1. `tshark -z conv,tcp` → HTTP noise + one FTP session (`RETR entrega-higor-evento.xls`)
2. `tshark --export-objects ftp-data,out/ftp` → Excel workbook with a VBA macro
3. `olevba --decode` → `CodigoDeValidacao()` = chain of `Chr()` → flag

Details in [WRITEUP.md](WRITEUP.md).
