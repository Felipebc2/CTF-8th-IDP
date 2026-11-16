#!/usr/bin/env python3
"""Probe3: testa REUSO de prova e multi-voto por sessao.
A) resolve 1 challenge valido (6 dig), vota (idea_votes=N).
B) reenvia o MESMO corpo valido 3x -> o challenge/nonce e reutilizavel?
C) na MESMA sessao, resolve um NOVO challenge e vota -> sessao pode votar de novo?
Uso: python3 probe3.py http://<HOST>:45804 4
"""
import sys, re, hashlib, json
import urllib.request, urllib.error, http.cookiejar

BASE = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://<HOST>:45804"
PID  = sys.argv[2] if len(sys.argv) > 2 else "4"
PRE  = "urna-aberta:v1:"

cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
def get(p):
    r = op.open(BASE+p, timeout=15); return r.status, r.read().decode("utf-8","replace")
def post(p, o):
    req = urllib.request.Request(BASE+p, data=json.dumps(o).encode(),
                                 headers={"Content-Type":"application/json"}, method="POST")
    try:
        r = op.open(req, timeout=15); return r.status, r.read().decode("utf-8","replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8","replace")
def csrf_of(h):
    m = re.search(r'name="csrf-token" content="([^"]+)"', h); return m.group(1) if m else None
def solve6(prefix):
    for d in range(1_000_000):
        n = "IDP-CTF-%06d" % d
        if hashlib.sha256((PRE+n).encode()).hexdigest().startswith(prefix): return n
    return None

st, home = get("/"); csrf = csrf_of(home)
print("csrf=%s" % csrf)

def solved_challenge():
    while True:
        _, ch = get("/api/pow/challenge"); c = json.loads(ch)
        n = solve6(c["prefix"])
        if n: return c["challenge"], c["prefix"], n

print("\n[A] resolvendo 1 prova valida...")
chid, prefix, nonce = solved_challenge()
body = {"csrf":csrf,"challenge":chid,"nonce":nonce,"proposal_id":PID}
st, v = post("/api/votes", body); print("  voto inicial -> %s %s" % (st, v))

print("\n[B] replay do MESMO corpo 3x (teste de reuso):")
for i in range(3):
    st, v = post("/api/votes", body); print("  replay %d -> %s %s" % (i+1, st, v))

print("\n[C] mesma sessao, NOVO challenge, vota de novo:")
chid2, _, nonce2 = solved_challenge()
st, v = post("/api/votes", {"csrf":csrf,"challenge":chid2,"nonce":nonce2,"proposal_id":PID})
print("  voto 2 (nova prova) -> %s %s" % (st, v))
