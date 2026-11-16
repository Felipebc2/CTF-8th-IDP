# TwitchPwn04

Categoria: Pwn · **✅ SOLVED** · 500 pts

## Resumo
O SDK do desafio entrega o binário real `/usr/local/bin/timestamp` (PIE, not stripped),
**setuid `relogio`** (uid 996). Reversão (objdump, `main` = 12 instruções):
```c
int main(void){
    uid_t e = geteuid();
    setreuid(e, e);                         // ruid = euid → privilégio mantido na shell
    puts(<banner>);
    system("date '+%d/%m/%Y %H:%M:%S'");    // comando RELATIVO, sem path absoluto
    return 0;
}
```
`system()` procura `date` via `$PATH`; como `ruid==euid` depois do `setreuid`, a shell
roda como `relogio`. Plantamos um `date` nosso em `/tmp/ph04`, anteposto ao `$PATH`, e
rodamos `timestamp` → nosso `date` executa como `relogio` (GTFOBins: setuid + comando sem
path absoluto = PATH hijack). A flag `/twitch/desafio-04/flag-nop.png` é `-r-- relogio` e é
um **QR code** (igual à 02): o `date` falso copia o PNG pra `/tmp` e renderizamos o QR
centralizado com borda branca pra escanear na live.

## Flag
`IDP{tw1tch_PWN_p4th_h1j4ck_gvk5cbvb3g}`

## Artefatos
- `sdk/timestamp` — binário real do zip do SDK (fonte da análise).
- `exploit.c` / `exploit` — PATH hijack; provou `id=relogio` mas chutou `.txt` (não existe).
- `exploit2.c` / `exploit2` — `date` falso lista o diretório → flags são PNG por time; corrige escaping de `&&`.
- `exploit3.c` / `exploit3` — 2 fases: copia `flag-nop.png` como `relogio` + renderiza o QR (pipeline do `TwitchPwn02/exploit5.c`) → flag escaneada.

## Payload vencedor
`date` malicioso em `/tmp/ph04` anteposto ao `$PATH`, chamando `/usr/local/bin/timestamp`;
cópia privilegiada do PNG + render do QR centralizado com quiet-zone branca.

## Como roda
No `<HOST>`, como `<USER>`, submeter o ELF estático. Confirmar `uid=996(relogio)` no xterm,
depois escanear o QR (deixar os controles do player sumirem).
