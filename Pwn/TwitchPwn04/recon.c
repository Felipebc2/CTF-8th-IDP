/* Twitch Pwn 04 - recon v1. Same paging-xterm harness as TwitchPwn03 (screen
 * is the only output channel on this box). Purely informational: id, ls -la
 * on /twitch/desafio-04 and /usr/local/bin, ls/file/strings -n6 on any setuid
 * helper found there, a plain read probe of flag-nop.*, and ls -la /opt in
 * case there is an orchestration file. No exploit, no writes outside /tmp. */
#include <stdlib.h>
int main(void) {
    system(
        "export DISPLAY=\"${DISPLAY:-:0}\"; "
        "export XAUTHORITY=\"${XAUTHORITY:-$HOME/.Xauthority}\"; "
        "O=/tmp/RECON_TP04.txt; "
        "{ "
        "  echo '===== RECON TWITCH PWN 04 ====='; "
        "  echo '--- id / whoami ---'; id; whoami; "
        "  echo '--- ls -la /twitch/desafio-04 ---'; ls -la /twitch/desafio-04 2>&1; "
        "  echo '--- ls -la /usr/local/bin ---'; ls -la /usr/local/bin 2>&1; "
        "  for b in /usr/local/bin/*; do "
        "    if [ -u \"$b\" ]; then "
        "      echo \"--- setuid helper: $b ---\"; "
        "      ls -l \"$b\" 2>&1; "
        "      file \"$b\" 2>&1; "
        "      if [ -r \"$b\" ]; then strings -n 6 \"$b\" 2>&1 | head -n 80; "
        "      else echo '  (not readable, skipping strings)'; fi; "
        "    fi; "
        "  done; "
        "  echo '--- flag read probe ---'; "
        "  for f in /twitch/desafio-04/flag-nop.*; do "
        "    echo \"[probe] $f\"; "
        "    stat -c '  owner=%U:%G mode=%A' \"$f\" 2>&1; "
        "    if head -c1 \"$f\" >/dev/null 2>/tmp/err_$$; then "
        "      echo '  read: OK'; "
        "    else "
        "      echo \"  read: FAIL ($(cat /tmp/err_$$))\"; "
        "    fi; rm -f /tmp/err_$$; "
        "  done; "
        "  echo '--- ls -la /opt ---'; ls -la /opt 2>&1; "
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
