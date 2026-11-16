# Pysemjail — JAIL · 184 pts · ✅ SOLVED

- **Target:** `nc <HOST> <PORT>` (ephemeral container, 15 min TTL)
- **Prompt:** *"Não eram nem pra estar nessa categoria, mas não tem outra."*
- **Flag:** `IDP{3x3cut4_qu4lqu3R_c01s4__48Pg2qj8QH}`

Fake pyjail: the service prints its own source, pre-opens `flag.txt` into global `f`, and runs `exec(eval(ascii(input())))` — which round-trips to plain `exec(input())`. No filter.

Solve: type `print(f.read())` at the `>>>` prompt. See `WRITEUP.md` and `solve.txt`.
