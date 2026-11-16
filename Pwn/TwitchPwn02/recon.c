/* Twitch Pwn 02 - recon only. Runs as `ctf`, dumps the environment to a window
 * so we can read it off the Twitch live. Touches ONLY our own team dir listing,
 * never reads another team's flag contents. */
#include <stdlib.h>
int main(void) {
    system(
        "export DISPLAY=\"${DISPLAY:-:0}\"; "
        "export XAUTHORITY=\"${XAUTHORITY:-$HOME/.Xauthority}\"; "
        "D=/twitch/desafio-02; "
        "O=/tmp/RECON.txt; "
        "{ "
        "  echo '===== RECON TWITCH PWN 02 ====='; "
        "  echo '--- id ---';            id; "
        "  echo '--- uname ---';         uname -a; "
        "  echo '--- ls -la dir ---';    ls -la \"$D\" 2>&1; "
        "  echo '--- our flag stat ---'; ls -l \"$D\"/flag-nop.txt 2>&1; stat \"$D\"/flag-nop.txt 2>&1; "
        "  echo '--- getfacl ours ---';  getfacl \"$D\"/flag-nop.txt 2>&1; "
        "  echo '--- try read ours ---'; cat \"$D\"/flag-nop.txt 2>&1 | head -c 80; echo; "
        "  echo '--- caps on dir ---';   getcap -r \"$D\" 2>/dev/null; "
        "  echo '--- sudo -l ---';       sudo -n -l 2>&1; "
        "  echo '--- setuid bins ---';   find / -perm -4000 -type f 2>/dev/null | head -n 40; "
        "  echo '--- caps bins ---';     getcap -r /usr /bin /sbin 2>/dev/null | head -n 40; "
        "  echo '--- groups file users ---'; cat /etc/passwd 2>&1 | grep -vE 'nologin|false' | head -n 30; "
        "  echo '===== END ====='; "
        "} > \"$O\" 2>&1; "
        /* render on screen, keep it up ~115s through the stream delay.
         * mousepad is known-present on this box; xterm cat / xmessage are fallbacks. */
        "( mousepad \"$O\" "
        "  || xterm -fa Monospace -fs 14 -geometry 160x48+20+20 -e cat \"$O\" "
        "  || gedit \"$O\" || xmessage -center -file \"$O\" "
        ") >/dev/null 2>&1 & "
        "sleep 115"
    );
    return 0;
}
