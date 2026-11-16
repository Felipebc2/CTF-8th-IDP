/* Twitch Pwn 02 - recon v2. /twitch/desafio-02 does not exist; hunt for the flag
 * file across the FS. We only LOCATE/stat files (listing is fair); we read the
 * content of OUR team's flag only, never another team's. */
#include <stdlib.h>
int main(void) {
    system(
        "export DISPLAY=\"${DISPLAY:-:0}\"; "
        "export XAUTHORITY=\"${XAUTHORITY:-$HOME/.Xauthority}\"; "
        "O=/tmp/RECON2.txt; "
        "{ "
        "  echo '===== RECON2 TWITCH PWN 02 ====='; "
        "  echo '--- whoami/home ---'; id; echo \"HOME=$HOME\"; pwd; "
        "  echo '--- ls /twitch ---';     ls -la /twitch 2>&1; "
        "  echo '--- find /twitch ---';   find /twitch -maxdepth 4 2>&1 | head -n 60; "
        "  echo '--- flag files (locate) ---'; find / -iname '*flag*' 2>/dev/null | grep -vE '^/proc|^/sys' | head -n 80; "
        "  echo '--- ls -la / ---';       ls -la / 2>&1; "
        "  echo '--- ls -la /home ---';   ls -la /home 2>&1; "
        "  echo '--- ls -la ~ ---';       ls -la ~ 2>&1; "
        "  echo '--- ls -la /root ---';   ls -la /root 2>&1; "
        "  echo '--- setuid bins ---';    find / -perm -4000 -type f 2>/dev/null | head -n 50; "
        "  echo '--- caps bins ---';      getcap -r / 2>/dev/null | head -n 50; "
        "  echo '--- env ---';            env 2>&1 | grep -iE 'flag|twitch|desafio|team|nop' ; "
        "  echo '===== END ====='; "
        "} > \"$O\" 2>&1; "
        "( mousepad \"$O\" "
        "  || xterm -fa Monospace -fs 14 -geometry 170x50+10+10 -e cat \"$O\" "
        "  || gedit \"$O\" || xmessage -center -file \"$O\" "
        ") >/dev/null 2>&1 & "
        "sleep 115"
    );
    return 0;
}
