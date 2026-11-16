#!/usr/bin/env python3
"""Local IDProc simulator, following manual-idproc.pdf (Ed. 1).

  python3 idproc_sim.py machine.json program.idp [--no-wrap] [--trace]
  python3 idproc_sim.py                     # self-test

machine.json:
  {"cores":   {"N0": {"INPUT": "in", "DIR": "out"}, "N1": {"ESQ": "in", "OUTPUT": "out"}},
   "links":   [["N0.DIR", "N1.ESQ"]],
   "inputs":  {"IN":  ["N0.INPUT"]},          # external queue -> ports that read it
   "outputs": {"OUT": ["N1.OUTPUT"]},
   "tests":   [{"IN": [1, 2, 3], "OUT": [2, 3, 4]}]}

Not specified by the manual (assumptions, confirm in the official simulator):
  - wrap: IPT returns to 0 after the last instruction (TIS-100 style). --no-wrap = core halts.
  - end of run: all expected outputs produced, or no core can complete an instruction.
  - instruction count = sum over all cores.
"""
import argparse, json, re, sys

OPS = {"MOV", "SAV", "SWP", "NEG", "ADD", "SUB", "JMP", "JEQ", "JNZ", "JGZ", "JLZ", "NOP"}
JUMPS = {"JMP", "JEQ", "JNZ", "JGZ", "JLZ"}
ARITY = {**{o: 0 for o in OPS}, "MOV": 2, "ADD": 1, "SUB": 1, **{j: 1 for j in JUMPS}}
RESERVED = OPS | {"ACC", "BAK", "IPT", "NIL"}
LIT = re.compile(r"-?(0|[1-9][0-9]*)")
IDENT = r"[A-Za-z_][A-Za-z0-9_]*"


class Err(Exception):
    pass


def wrap(x):
    return (x + 128) % 256 - 128


def split(ref):
    core, port = ref.upper().split(".")
    return core, port


class Machine:
    def __init__(self, cfg):
        self.ports = {c.upper(): {p.upper(): d.lower() for p, d in ps.items()}
                      for c, ps in cfg["cores"].items()}
        self.peer, self.inch, self.outch = {}, {}, {}
        for a, b in cfg.get("links", []):
            a, b = split(a), split(b)
            self.peer[a], self.peer[b] = b, a
        for ch, refs in cfg.get("inputs", {}).items():
            self.inch.update({split(r): ch for r in refs})
        for ch, refs in cfg.get("outputs", {}).items():
            self.outch.update({split(r): ch for r in refs})
        for c, p in [*self.peer, *self.inch, *self.outch]:
            if p not in self.ports.get(c, {}):
                raise Err(f"config: porta {c}.{p} não declarada")
        self.inputs = list(cfg.get("inputs", {}))
        self.outputs = list(cfg.get("outputs", {}))
        self.tests = cfg.get("tests", [{}])


def parse(text, m):
    """-> {core: [(op, x, y, text)]}; jump targets resolved to indexes."""
    progs, labels, cur = {}, {}, None
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        sec = re.fullmatch(r"\[\s*(" + IDENT + r")\s*\]", line)
        if sec:
            cur = sec.group(1).upper()
            if cur not in m.ports:
                raise Err(f"linha {n}: núcleo {cur} não existe na máquina")
            if cur in progs:
                raise Err(f"linha {n}: seção {cur} repetida")
            progs[cur], labels[cur] = [], {}
            continue
        if cur is None:
            raise Err(f"linha {n}: instrução fora de seção [Nx]")
        code, labs = progs[cur], labels[cur]
        lab = re.match(r"(" + IDENT + r")\s*:(.*)$", line)
        if lab:
            name = lab.group(1).upper()
            if name in RESERVED or name in labs:
                raise Err(f"linha {n}: rótulo inválido/repetido {name}")
            labs[name] = len(code)
            line = lab.group(2).strip()
            if not line:
                continue
        toks = line.replace(",", " ").split()
        op, args = toks[0].upper(), [t.upper() for t in toks[1:]]
        if op not in OPS:
            raise Err(f"linha {n}: instrução desconhecida {toks[0]}")
        if len(args) != ARITY[op]:
            raise Err(f"linha {n}: {op} espera {ARITY[op]} operando(s)")
        ports = m.ports[cur]

        def operand(t):
            if LIT.fullmatch(t) and t != "-0":
                v = int(t)
                if not -128 <= v <= 127:
                    raise Err(f"linha {n}: literal fora de faixa {t}")
                return v
            if t in ("ACC", "NIL"):
                return t
            if t == "BNK":
                raise Err(f"linha {n}: BNK desconhecido (o nome correto é BAK)")
            if t in ports:
                return "@" + t
            raise Err(f"linha {n}: operando inválido {t}")

        x = y = None
        if op == "MOV":
            x, y = operand(args[0]), operand(args[1])
            xp, yp = isinstance(x, str) and x[0] == "@", isinstance(y, str) and y[0] == "@"
            if xp and y != "ACC" or yp and x != "ACC":
                raise Err(f"linha {n}: MOV inválido (porta só ↔ ACC)")
            if xp and ports[x[1:]] not in ("in", "io") or yp and ports[y[1:]] not in ("out", "io"):
                raise Err(f"linha {n}: porta incompatível")
        elif op in ("ADD", "SUB"):
            x = operand(args[0])
            if not (isinstance(x, int) or x == "ACC"):
                raise Err(f"linha {n}: {op} {args[0]} inválido (só literal ou ACC; portas via MOV porta ACC)")
        elif op in JUMPS:
            x = args[0]
        code.append((op, x, y, f"{line}"))
    for c, code in progs.items():
        for i, (op, x, y, t) in enumerate(code):
            if op in JUMPS:
                if x not in labels[c]:
                    raise Err(f"[{c}] rótulo inexistente {x}")
                code[i] = (op, labels[c][x], y, t)
    return {c: code for c, code in progs.items() if code}


def run(progs, m, test, wrap_ipt=True, max_cycles=100_000, trace=False):
    queues = {ch: list(test.get(ch, [])) for ch in m.inputs}
    outs = {ch: [] for ch in m.outputs}
    expected = {ch: test[ch] for ch in m.outputs if ch in test}
    st = {c: [0, 0, 0] for c in progs}  # ACC, BAK, IPT
    cycle, status = 0, "parou"
    while True:
        if expected and all(len(outs[ch]) >= len(v) for ch, v in expected.items()) and not any(queues.values()):
            status = "fim"
            break
        if cycle >= max_cycles:
            status = "timeout"
            break
        cur = {c: progs[c][s[2]] for c, s in st.items() if s[2] < len(progs[c])}

        def ready(c, ins):
            op, x, y, _ = ins
            if op != "MOV":
                return True
            for end, other in ((x, 2), (y, 1)):  # receiving needs partner's dst, sending partner's src
                if isinstance(end, str) and end[0] == "@":
                    key = (c, end[1:])
                    if key in m.inch:
                        return bool(queues[m.inch[key]])
                    if key in m.outch:
                        return True
                    if key in m.peer:
                        pc, pp = m.peer[key]
                        return pc in cur and cur[pc][0] == "MOV" and cur[pc][other] == "@" + pp
                    return False  # unconnected port waits forever
            return True

        go = {c: ins for c, ins in cur.items() if ready(c, ins)}
        if not go:
            status = "parou" if not cur else "travado"
            break
        cycle += 1
        readers = {}
        for c, (op, x, _, _) in go.items():
            if op == "MOV" and isinstance(x, str) and (c, x[1:]) in m.inch:
                readers.setdefault(m.inch[(c, x[1:])], []).append(c)
        for ch, cs in readers.items():
            if len(cs) > 1:
                raise Err(f"ciclo {cycle}: disputa de entrada em {ch} ({', '.join(cs)})")
        new, pops, emitted = {}, [], []
        for c, (op, x, y, _) in go.items():
            acc, bak, ipt = st[c]
            nxt = ipt + 1
            if op == "MOV":
                if x == "ACC":
                    v = acc
                elif x == "NIL":
                    v = 0
                elif isinstance(x, int):
                    v = x
                elif (c, x[1:]) in m.inch:
                    ch = m.inch[(c, x[1:])]
                    v = queues[ch][0]
                    pops.append(ch)
                else:
                    v = st[m.peer[(c, x[1:])][0]][0]
                if y == "ACC":
                    acc = v
                elif isinstance(y, str) and (c, y[1:]) in m.outch:
                    emitted.append((m.outch[(c, y[1:])], v))
            elif op == "SAV":
                bak = acc
            elif op == "SWP":
                acc, bak = bak, acc
            elif op == "NEG":
                acc = wrap(-acc)
            elif op in ("ADD", "SUB"):
                v = acc if x == "ACC" else x
                acc = wrap(acc + v if op == "ADD" else acc - v)
            elif (op == "JMP" or op == "JEQ" and acc == 0 or op == "JNZ" and acc != 0
                  or op == "JGZ" and acc > 0 or op == "JLZ" and acc < 0):
                nxt = x
            if nxt >= len(progs[c]):
                nxt = 0 if wrap_ipt else len(progs[c])
            new[c] = [acc, bak, nxt]
        if trace:
            line = "  ".join(f"{c}:{'ok ' if c in go else '.. '}{cur[c][3]:<16} ACC={st[c][0]}"
                             for c in cur)
            print(f"{cycle:>5} | {line}")
        st.update(new)
        for ch in pops:
            queues[ch].pop(0)
        for ch, v in emitted:
            outs[ch].append(v)
    ok = bool(expected) and all(outs[ch] == v for ch, v in expected.items())
    return {"ciclos": cycle, "status": status, "correto": ok, "saida": outs}


def evaluate(machine_cfg, program_text, **kw):
    m = Machine(machine_cfg)
    progs = parse(program_text, m)
    per_core = {c: len(code) for c, code in progs.items()}
    results = [run(progs, m, t, **kw) for t in m.tests]
    return per_core, results


def selftest():
    two = {"cores": {"N0": {"INPUT": "in", "SEND": "out"}, "N1": {"RECV": "in", "OUTPUT": "out"}},
           "links": [["N0.SEND", "N1.RECV"]], "inputs": {"IN": ["N0.INPUT"]},
           "outputs": {"OUT": ["N1.OUTPUT"]}, "tests": [{"IN": [1, 2, 127], "OUT": [2, 3, -128]}]}
    manual = "[N0]\nMOV INPUT ACC\nADD 1\nMOV ACC SEND\n\n[N1]\nMOV RECV ACC\nMOV ACC OUTPUT\n"
    cores, [r] = evaluate(two, manual)
    assert r["correto"] and r["ciclos"] == 10 and sum(cores.values()) == 5, r

    one = {"cores": {"N0": {"INPUT": "in", "OUTPUT": "out"}}, "inputs": {"IN": ["N0.INPUT"]},
           "outputs": {"OUT": ["N0.OUTPUT"]},
           "tests": [{"IN": list(range(32)), "OUT": [i + 5 for i in range(32)]}]}
    _, [r] = evaluate(one, "[N0]\nmov input, acc  # comment\nADD 5\nMOV ACC OUTPUT\n")
    assert r["correto"] and r["ciclos"] == 96, r  # round 2 shape: 3 instr / 96 cycles
    _, [r] = evaluate(one, "[N0]\nL: MOV INPUT ACC\nADD 5\nMOV ACC OUTPUT\nJMP L\n")
    assert r["correto"] and r["ciclos"] == 127, r
    _, [r] = evaluate(one, "[N0]\nMOV INPUT ACC\nADD 5\nMOV ACC OUTPUT\n", wrap_ipt=False)
    assert not r["correto"] and r["status"] == "parou", r

    abs_ = "[N0]\nMOV INPUT ACC\nJGZ P\nNEG\nP: MOV ACC OUTPUT\n"
    m = {**one, "tests": [{"IN": [-3, 4, 0, -128], "OUT": [3, 4, 0, -128]}]}
    assert evaluate(m, abs_)[1][0]["correto"]

    for bad, msg in [("ADD INPUT", "inválido"), ("SWP BNK", "operando"), ("MOV BNK ACC", "BNK"),
                     ("ADD 128", "fora de faixa"), ("JMP X", "rótulo inexistente"),
                     ("MOV INPUT OUTPUT", "porta só"), ("MOV 1 OUTPUT", "porta só"),
                     ("MOV ACC INPUT", "incompatível")]:
        try:
            evaluate(one, f"[N0]\n{bad}\n")
            raise AssertionError(f"aceitou: {bad}")
        except Err as e:
            assert msg in str(e), (bad, e)

    race = {"cores": {"N0": {"A": "in"}, "N1": {"B": "in"}}, "inputs": {"IN": ["N0.A", "N1.B"]},
            "tests": [{"IN": [1, 2]}]}
    try:
        evaluate(race, "[N0]\nMOV A ACC\n[N1]\nMOV B ACC\n")
        raise AssertionError("sem disputa")
    except Err as e:
        assert "disputa" in str(e)
    print("selftest ok")


def main():
    if len(sys.argv) == 1:
        return selftest()
    ap = argparse.ArgumentParser()
    ap.add_argument("machine")
    ap.add_argument("program")
    ap.add_argument("--no-wrap", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--max-cycles", type=int, default=100_000)
    a = ap.parse_args()
    with open(a.machine) as f:
        cfg = json.load(f)
    with open(a.program, encoding="utf-8") as f:
        text = f.read()
    try:
        cores, results = evaluate(cfg, text, wrap_ipt=not a.no_wrap,
                                  max_cycles=a.max_cycles, trace=a.trace)
    except Err as e:
        sys.exit(f"ERRO: {e}")
    print(f"instruções: {sum(cores.values())}  {cores}")
    for i, r in enumerate(results):
        print(f"teste {i}: {'correct' if r['correto'] else 'WRONG'}  ciclos={r['ciclos']}  "
              f"({r['status']})  saida={r['saida']}")
    print(f"ciclos: max={max(r['ciclos'] for r in results)}  soma={sum(r['ciclos'] for r in results)}")


if __name__ == "__main__":
    main()
