import json, itertools
V = [-128, -5, -1, 0, 1, 5, 127]
def ref(a, b, c):
    return [x if (y < 0) == (z < 0) else (-x + 128) % 256 - 128 for x, y, z in zip(a, b, c)]
ex = ([3, 4], [10, -2], [5, 1])
trip = list(itertools.product([3, -7, 0, 127, -128], V, V))
big = tuple(list(t) for t in zip(*trip))
m = {"cores": {"N0": {"A": "in", "DIR": "out"}, "N1": {"B": "in", "ESQ": "in", "BAIXO": "out"},
               "N2": {"C": "in", "DIR": "out"}, "N3": {"CIMA": "in", "ESQ": "in", "OUTPUT": "out"}},
     "links": [["N0.DIR", "N1.ESQ"], ["N1.BAIXO", "N3.CIMA"], ["N2.DIR", "N3.ESQ"]],
     "inputs": {"A": ["N0.A"], "B": ["N1.B"], "C": ["N2.C"]}, "outputs": {"OUT": ["N3.OUTPUT"]},
     "tests": [{"A": a, "B": b, "C": c, "OUT": ref(a, b, c)} for a, b, c in (ex, big)]}
assert m["tests"][0]["OUT"] == [3, -4]
json.dump(m, open("maquina.json", "w"))
