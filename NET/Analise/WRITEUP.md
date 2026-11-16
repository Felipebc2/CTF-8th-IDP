<div align="center">

<a href="https://git.io/typing-svg"><img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=28&duration=700&pause=1000&color=E8423F&center=true&vCenter=true&repeat=false&width=500&height=35&lines=An%C3%A1lise" alt="Typing SVG" /></a>

</div>

# Análise — NET · 🟡 MEDIUM

- **Status:** ✅ SOLVED — flag recovered from a VBA macro inside a file carried over FTP
- **Points:** 100 (final dynamic value)
- **Flag:** `IDP{c0ntr4t4-s3_pr0Gr4mad0r_VBA}`
- **Attachment:** `2c24735704c58d0be506679bd730320e.zip` → `captura.pcap` (pcap, Raw IPv4, 2058 packets, 48.5 s)
- **Prompt:** *"É necessário analisar se todos os dados estão de acordo."* ("You need to check whether all the data adds up.")

---

## TL;DR

1. The capture is cleartext HTTP (a small "facilities" API + noise) and one FTP session.
2. FTP downloads `entrega-higor-evento.xls`, an Excel workbook with a VBA macro for a financial reconciliation.
3. The macro's `CodigoDeValidacao()` builds the flag with `Chr()` calls. Decoding them gives the flag.

## Analysis

### Traffic overview

```bash
P=extracted/captura.pcap
tshark -r $P -q -z io,phs        # tcp → http (json) + ftp + ftp-data
tshark -r $P -q -z conv,tcp      # 1 FTP control, 1 FTP data, 405 short HTTP conversations
```

The HTTP conversations split into blocks by size:

| Client ports | Count | Endpoint | Content |
|---|---|---|---|
| 51000–51004 | 5 | `/recebimentos/pendentes`, `/projetos/pre-save/execucao`, `/pedidos/N`, `/api/entregas/N`, CSS | small JSON with the story |
| 51005–51224 | 220 | `/assets/icones/material-N.svg` | `<svg/>`, noise |
| 51225–51404 | 180 | `/api/recebimentos/atualizacoes?pagina=N` | `{"itens":[]}`, all empty (the size step comes from the page number's digit count) |

The non-empty JSON tells the story: `{"pendentes":3}`, `{"responsavel":"Higor","equipe":"Projetos"}`, `{"fornecedor":"Atlas Suprimentos"}` and `{"arquivo":"entrega-higor-evento.xls","situacao":"aguardando conferencia"}`. The file waiting for reconciliation is the one sent over FTP.

### FTP

```bash
tshark -r $P -Y ftp -T fields -e ftp.request.command -e ftp.request.arg -e ftp.response.code -e ftp.response.arg
```

```
220 <HOST>
USER facilities / PASS outubro2026 → 230 Login successful
257 "/recebimentos/2026/outubro"
TYPE I, PORT 10,32,8,24,195,80 (active mode, port 50000)
RETR entrega-higor-evento.xls
```

```bash
tshark -r $P -q --export-objects ftp-data,out/ftp
file out/ftp/entrega-higor-evento.xls   # Composite Document File V2 (Excel), author "Jeremias Moreira Gomes"
```

### The workbook and its macro

Sheet `Conferência financeira`: 16 supplier rows with columns *previsto* (expected) / *realizado* (actual) / *situação* (status). The text asks you to run the `AtualizarConferenciaFinanceira` routine before closing the books. Static extraction, with no macro execution:

```bash
olevba --decode out/ftp/entrega-higor-evento.xls > out/vba.txt
```

`AtualizarConferenciaFinanceira` recomputes `realizado - previsao` per row and marks it `Conciliado` if `|diff| ≤ 5`. It always ends with:

```vb
MsgBox "Conferência financeira atualizada." & vbCrLf & _
       "Pendências encontradas: " & pendencias & vbCrLf & _
       "Protocolo de validação: " & CodigoDeValidacao(), ...
```

And the obfuscated function:

```vb
Public Function CodigoDeValidacao() As String
    CodigoDeValidacao = Chr(73) & Chr(68) & Chr(80) & Chr(123) & Chr(99) & Chr(48) & ...
End Function
```

```bash
python3 -I -c "import re;s=open('out/vba.txt').read();b=s[s.find('CodigoDeValidacao'):];b=b[:b.find('End Function')];print(''.join(chr(int(n)) for n in re.findall(r'Chr\((\d+)\)',b)))"
# IDP{c0ntr4t4-s3_pr0Gr4mad0r_VBA}
```

### The "data doesn't add up" part

The prompt's inconsistency is real, but it only points you to the macro:

- The API reports `pendentes: 3`. Applying the macro's rule to the sheet gives **4** pending rows: Metrópole Transportes and Café do Campus (`Aguardando…`), plus Atlas Suprimentos (−33.30) and Conecta TI (−36.50). Those last two are marked `Conciliado` even though the difference is over the R$ 5 tolerance.
- The protocol (flag) is printed unconditionally, so no specific reconciliation result is needed.

## What didn't work

| Hypothesis | Result | Why |
|---|---|---|
| Flag in cleartext / base64 / hex in the pcap | ✗ | `strings` only hits the FTP `PASS` |
| Paginated API carries data | ✗ | All 180 pages are `{"itens":[]}` |
| SVG icon requests as covert channel | ✗ | All 220 are identical `<svg/>` with the same sizes |
| Flag from reconciliation mismatches | ✗ | Mismatches exist (3 vs 4 pending) but encode nothing |

## Conclusion

The network part is "follow the file": spot the FTP download among the HTTP noise, carve it, and treat the `.xls` as a maldoc. Use `olevba` to read the macro statically, never open it in Excel. The `Chr()` chain decodes straight to the flag.

---

## Appendix — tools

- `tshark` (`-z conv,tcp`, `--export-objects ftp-data`), `olevba` (oletools), `xlrd` to dump the cells without running macros.
