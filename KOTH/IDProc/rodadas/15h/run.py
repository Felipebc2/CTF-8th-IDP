import sys, json
sys.path.insert(0, "../..")
import idproc_sim as S
cfg = json.load(open("maquina.json"))
for f in sys.argv[1:]:
    m = S.Machine(cfg); progs = S.parse(open(f).read(), m)
    n = sum(len(p) for p in progs.values()) if isinstance(progs, dict) else None
    rs = [S.run(progs, m, t) for t in cfg["tests"]]
    print(f, "instr", n, "ex", rs[0]["ciclos"], "total", sum(r["ciclos"] for r in rs), "ok" if all(r["correto"] for r in rs) else "FAIL " + str([i for i, r in enumerate(rs) if not r["correto"]]))
