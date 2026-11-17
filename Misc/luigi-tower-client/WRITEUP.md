<div align="center">

<a href="https://git.io/typing-svg"><img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=28&duration=700&pause=1000&color=E8423F&center=true&vCenter=true&repeat=false&width=500&height=35&lines=LUIGI+TOWER" alt="Luigi Tower" /></a>

</div>

# Luigi Tower — MISC

- **Status:** ✅ SOLVED — locally reproduced and confirmed by the server.
- **Points:** 184 in the supplied event screenshot; the score at solve time is unconfirmed.
- **Flag:** `IDP{d4_pr4_sub1R_d3_OLH0s_f3ch4d0s_58b8c8ff}`
- **Attachment / target:** Luigi Tower client / `<HOST>:23196`
- **Original prompt:** *“Agora é uma subida de precisão.”*

---

## TL;DR

1. Inspect the level and display all platforms to make the ascent visible.
2. Use the local game simulation to search for a sequence of precise jumps.
3. Replay the inputs with their corresponding state hashes to the server.

## Analysis

The initial approach was to play the level manually and understand its layout. A visualization script revealed the blocks and platforms; the current [client](game/client.py) draws every platform in its map. The server handshake supplies `rendered_platforms`, a selection of platform indices, while the map and simulation retain the full layout.

One jump appeared impossible during manual play, so a solver was developed to explore the game's actual movement rules. The [planner](game/luigi_solver.py) simulates jumps toward candidate positions on nearby platforms, accounts for horizontal velocity and braking, and searches alternate states. It checks the resulting sequence by replaying it in a fresh local simulation.

Run it from the client directory:

```sh
PYTHONPATH=. .venv/bin/python -m game.luigi_solver
PYTHONPATH=. .venv/bin/python -m game.luigi_solver --send --host <HOST> --port 23196
```

The first command saves `game/luigi_route.json`; the second replays the route at 60 ticks per second, sending keys and the locally computed state hash. In a later local verification, the planner found a winning route of 3,156 ticks (52.6 seconds at 60 Hz), within the 7,200-tick session limit.

## Remote verification

The challenge was solved during the event, but its flag was not saved at the time. In a later attempt, accelerated replay ended with a socket timeout and no flag. Replaying the same route at the normal game rate succeeded, and the server returned the flag shown above.

## Conclusion

Revealing the level and searching against the same simulation used by the client turned a difficult manual ascent into a reproducible route, confirmed by the server.
