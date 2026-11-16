#!/usr/bin/env python3
"""Solver 'Uma Ideia para o IDEA' (IDP CTF).
Leva uma proposta a required_votes (250) resolvendo o PoW de 24 bits,
nonce no formato IDP-CTF-NNNNNN (6 digitos, imposto pelo servidor).
Hashing paralelo (multicore); votos enviados 1 por vez (rede como cliente normal).

Uso: python3 solve.py http://<HOST>:45804 4
"""
import sys, re, json, hashlib, os, time
from multiprocessing import Pool
import urllib.request, urllib.error, http.cookiejar

BASE = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://<HOST>:45804"
PID  = sys.argv[2] if len(sys.argv) > 2 else "4"
PRE  = "urna-aberta:v1:"
SPACE = 1_000_000
NPROC = max(1, (os.cpu_count() or 4))
FLAG = re.compile(r"IDP\{[^}]+\}")

def scan_chunk(args):
    prefix, lo, hi = args
    pre = PRE
    for d in range(lo, hi):
        n = "IDP-CTF-%06d" % d
        if hashlib.sha256((pre + n).encode()).hexdigest().startswith(prefix):
            return n
    return None

def main():
    cj = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

    def get(p):
        for _ in range(5):
            try:
                r = op.open(BASE + p, timeout=20); return r.status, r.read().decode("utf-8","replace")
            except urllib.error.HTTPError as e:
                return e.code, e.read().decode("utf-8","replace")
            except Exception:
                time.sleep(0.5)
        raise SystemExit("falha de rede em GET " + p)

    def post(p, o):
        for _ in range(5):
            try:
                req = urllib.request.Request(BASE+p, data=json.dumps(o).encode(),
                        headers={"Content-Type":"application/json"}, method="POST")
                r = op.open(req, timeout=20); return r.status, r.read().decode("utf-8","replace")
            except urllib.error.HTTPError as e:
                return e.code, e.read().decode("utf-8","replace")
            except Exception:
                time.sleep(0.5)
        raise SystemExit("falha de rede em POST " + p)

    def hunt(t, tag):
        m = FLAG.search(t)
        if m:
            print("\n" + "="*50 + "\n>>> FLAG (%s): %s\n" % (tag, m.group(0)) + "="*50)
            return True
        return False

    st, home = get("/")
    m = re.search(r'name="csrf-token" content="([^"]+)"', home)
    csrf = m.group(1)
    cm = re.search(r'data-proposal-id="%s".*?<strong>\s*([0-9]+)\s*/\s*([0-9]+)'%re.escape(PID), home, re.S)
    cur, need = (int(cm.group(1)), int(cm.group(2))) if cm else (0, 250)
    print("csrf=%s  proposta %s: %d/%d  cores=%d" % (csrf, PID, cur, need, NPROC))

    # chunks fixos do espaco de nonce
    step = SPACE // NPROC
    chunks = [(None, i*step, (SPACE if i==NPROC-1 else (i+1)*step)) for i in range(NPROC)]

    pool = Pool(NPROC)
    votes_done = 0
    fetches = 0
    t0 = time.time()
    while True:
        # pega um challenge e tenta resolver; refetch ate achar
        nonce = None; chid = None
        while nonce is None:
            _, ch = get("/api/pow/challenge"); fetches += 1
            c = json.loads(ch); chid = c["challenge"]; prefix = c["prefix"]
            jobs = [(prefix, lo, hi) for (_, lo, hi) in chunks]
            for res in pool.imap_unordered(scan_chunk, jobs):
                if res:
                    nonce = res; break
        st, v = post("/api/votes", {"csrf":csrf,"challenge":chid,"nonce":nonce,"proposal_id":PID})
        try:
            vj = json.loads(v)
        except Exception:
            vj = {}
        if st == 200 and vj.get("ok"):
            votes_done += 1
            iv = vj.get("idea_votes")
            if iv is not None: cur = iv
            if votes_done % 5 == 0 or (iv and iv >= need-3):
                dt = time.time()-t0
                print("  voto %d  idea_votes=%s  fetches=%d  %.1fs" % (votes_done, iv, fetches, dt))
            if hunt(v, "voto"): break
            if iv is not None and iv >= need:
                print("\nATINGIU %d/%d apoios." % (iv, need))
                break
        else:
            print("  [!] voto rejeitado: %s %s" % (st, v))
            if "nova prova" in v or "aceita" in v:
                continue   # so refaz a prova
            time.sleep(0.5)
    pool.terminate()

    # pos-250: procura a flag na home, na proposta e tenta endpoints de recompensa
    print("\n-- procurando flag pos-apoio --")
    _, home2 = get("/"); hunt(home2, "home")
    for ep in ["/api/votes", "/propostas/%s"%PID, "/api/propostas/%s"%PID,
               "/recompensa", "/api/recompensa", "/reward", "/api/reward", "/flag", "/api/flag"]:
        try:
            s, b = get(ep);
            if s==200:
                print("  GET %s -> 200 (%d bytes)" % (ep, len(b))); hunt(b, ep)
        except Exception:
            pass
    print("\nultima resposta de voto:\n", v)

if __name__ == "__main__":
    main()
