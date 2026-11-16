#!/usr/bin/env python3
# Cofre (Rev, iOS) — solver. VOCE roda; ele faz o HTTP.
# Recuperado estaticamente do binario Mach-O arm64 (Cofre.app/Cofre):
#   combinacao = [4, 8, 15, 16, 23, 42]              (CofreCore.ChallengeCombination.values)
#   key HMAC   = 32 bytes = obfuscatedHMACKey XOR 0xA7
#   mac        = HMAC_SHA256(key, "sid|nonce|step|value|dir")  hex minusculo
#   step e 1-based.  body JSON: {"sid","i"=step,"value","dir","mac"}  (chave do step e "i")
#   POST /api/session -> {sid,nonce} ; POST /api/step ; rate-limit 10s/passo.
import hmac, hashlib, json, time, sys, urllib.request, urllib.error

BASE  = "https://cofre-rev.desafio.<DOMAIN>"
KEY   = bytes.fromhex("b630355ac23fc05af613d32a4fd5117b5e8a1af283a8fc90f460173c26170a4b")
COMBO = [4, 8, 15, 16, 23, 42]
WAIT  = 11          # rate-limit do servidor = 10s; margem de 1s
UA    = "Cofre/1.0"

def mac(sid, nonce, step, value, d):
    return hmac.new(KEY, f"{sid}|{nonce}|{step}|{value}|{d}".encode(), hashlib.sha256).hexdigest()

def post(path, body):
    req = urllib.request.Request(BASE + path, data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json", "User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        try:    return e.code, json.loads(e.read() or b"{}")
        except Exception: return e.code, {}

def attempt(dirs):
    _, s = post("/api/session", {})
    sid, nonce = s["sid"], s["nonce"]
    print(f"session {sid}  dirs={dirs}")
    for i, value in enumerate(COMBO):
        step = i + 1                       # 1-based
        d = dirs[i]
        body = {"sid": sid, "i": step, "value": value, "dir": d,
                "mac": mac(sid, nonce, step, value, d)}
        while True:
            st, rep = post("/api/step", body)
            if st == 429:                  # rate-limit -> espera e repete o MESMO passo
                print(f"  [429] step {step} aguardando {WAIT}s..."); time.sleep(WAIT); continue
            break
        print(f"  step {step} value {value:>2} dir {d:>3} -> {st} {rep}")
        if isinstance(rep, dict):
            if rep.get("flag"):
                print("\n>>> FLAG:", rep["flag"]); return rep["flag"], None
            if rep.get("open"): print(">>> cofre aberto!")
        if st != 200 or (isinstance(rep, dict) and rep.get("error")):
            return None, i                 # passo i falhou -> direcao desse passo e a oposta
        if step < len(COMBO):
            time.sleep(WAIT)               # respeita o rate-limit antes do proximo
    return None, None

if __name__ == "__main__":
    assert mac("S","N",1,4,"cw") == hmac.new(KEY,b"S|N|1|4|cw",hashlib.sha256).hexdigest()
    dirs = ["cw", "ccw", "cw", "ccw", "cw", "ccw"]   # step1=cw confirmado; alterna
    for _ in range(12):
        flag, failed = attempt(dirs)
        if flag: sys.exit(0)
        if failed is None:
            print("Sequencia terminou sem flag — veja as respostas acima."); break
        dirs[failed] = "ccw" if dirs[failed] == "cw" else "cw"   # aprende direcao do passo e refaz
        print(f"  -> passo {failed+1} era '{'cw' if dirs[failed]=='ccw' else 'ccw'}', troco p/ '{dirs[failed]}' e reinicio\n")
        time.sleep(WAIT)
