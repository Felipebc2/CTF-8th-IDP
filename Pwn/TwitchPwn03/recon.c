/* Twitch Pwn 03 - recon v1. Same paging-xterm harness as TwitchPwn02 (screen
 * is the only output channel on this box). Purely informational: id, ls -la
 * on /twitch and /twitch/desafio-03, ls/file/strings on the setuid helper
 * /usr/local/bin/recado, and a plain read probe of flag-nop.* to report
 * success/errno. No exploit, no writes outside /tmp. */
#include <stdlib.h>
int main(void) {
    system(
        "export DISPLAY=\"${DISPLAY:-:0}\"; "
        "export XAUTHORITY=\"${XAUTHORITY:-$HOME/.Xauthority}\"; "
        "O=/tmp/RECON_TP03.txt; "
        "{ "
        "  echo '===== RECON TWITCH PWN 03 ====='; "
        "  echo '--- id / whoami ---'; id; whoami; "
        "  echo '--- ls -la /twitch ---'; ls -la /twitch 2>&1; "
        "  echo '--- ls -la /twitch/desafio-03 ---'; ls -la /twitch/desafio-03 2>&1; "
        "  echo '--- recado: ls -l ---'; ls -l /usr/local/bin/recado 2>&1; "
        "  echo '--- recado: file ---'; file /usr/local/bin/recado 2>&1; "
        "  echo '--- recado: strings -n 6 ---'; strings -n 6 /usr/local/bin/recado 2>&1 | head -n 80; "
        "  echo '--- flag read probe ---'; "
        "  for f in /twitch/desafio-03/flag-nop.*; do "
        "    echo \"[probe] $f\"; "
        "    if head -c1 \"$f\" >/dev/null 2>/tmp/err_$$; then "
        "      echo '  read: OK'; "
        "    else "
        "      echo \"  read: FAIL ($(cat /tmp/err_$$))\"; "
        "    fi; rm -f /tmp/err_$$; "
        "  done; "
        "  echo '===== END ====='; "
        "} > \"$O\" 2>&1; "
        /* auto-paging xterm: ~38-line pages, 14s each, loop */
        "( xterm -fa Monospace -fs 15 -geometry 130x42+10+10 -e bash -c '"
            "mapfile -t L < \"$0\"; n=${#L[@]}; per=38; "
            "while true; do "
              "for ((i=0;i<n;i+=per)); do "
                "printf \"\\033c\"; "
                "for ((j=i;j<i+per && j<n;j++)); do echo \"${L[j]}\"; done; "
                "echo; echo \"---- page $((i/per+1))/$(( (n+per-1)/per )) ----\"; "
                "sleep 14; "
              "done; "
            "done' \"$O\" "
        "  || mousepad \"$O\" "
        ") >/dev/null 2>&1 & "
        "sleep 118"
    );
    return 0;
}
