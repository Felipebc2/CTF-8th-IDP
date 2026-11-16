import json, random
def ref(a, b):
    out, i, j = [], 0, 0
    while True:
        if a[i] == 0: out += b[j:-1]; return out
        out.append(a[i]); i += 1
        if b[j] == 0: out += a[i:-1]; return out
        out.append(b[j]); j += 1
random.seed(1)
tests = [([1,2,0],[10,20,30,0])]
tests += [([0],[0]), ([0],[5,6,0]), ([5,6,0],[0]), ([1,0],[2,0]), ([1,2,3,0],[4,0]), ([-128,127,0],[-1,1,-5,0])]
for _ in range(20):
    nz = [v for v in range(-128,128) if v]
    tests.append(([random.choice(nz) for _ in range(random.randint(0,8))]+[0], [random.choice(nz) for _ in range(random.randint(0,8))]+[0]))
m = {"cores": {"N0": {"A_IN": "in", "DIR": "out"}, "N2": {"ESQ": "in", "DIR": "in", "OUTPUT": "out"}, "N1": {"B_IN": "in", "ESQ": "out"}},
     "links": [["N0.DIR", "N2.ESQ"], ["N1.ESQ", "N2.DIR"]], "inputs": {"A": ["N0.A_IN"], "B": ["N1.B_IN"]}, "outputs": {"OUT": ["N2.OUTPUT"]},
     "tests": [{"A": a, "B": b, "OUT": ref(a, b)} for a, b in tests]}
assert m["tests"][0]["OUT"] == [1,10,2,20,30]
json.dump(m, open("maquina.json", "w"))
