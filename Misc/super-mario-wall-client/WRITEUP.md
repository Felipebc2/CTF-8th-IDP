<div align="center">

<a href="https://git.io/typing-svg"><img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=28&duration=700&pause=1000&color=E8423F&center=true&vCenter=true&repeat=false&width=500&height=35&lines=SUPER+MARIO+WALL" alt="Super Mario Wall" /></a>

</div>

# Super Mario Wall — MISC

- **Status:** ✅ SOLVED — locally reproduced and confirmed by the server.
- **Points:** 323 in the supplied event screenshot; the score at solve time is unconfirmed.
- **Flag:** `IDP{m4l4b4r1sm0_d3_0bj3t0s_834dd2a1}`
- **Attachment / target:** Super Mario Wall client / `<HOST>:23197`
- **Original prompt:** *“Hora de derrubar a parede na força bruta.”*

---

## TL;DR

1. Pick up the fire flower and use the Koopa as a boost to reach the roof.
2. Fire repeatedly to fill the fixed sprite table and evict old wall blocks.
3. Drop through the opening onto the goal coin.

## Analysis

Manual exploration showed that bouncing on the enemy could get Mario onto the box, but the goal was enclosed. The code revealed that blocks and temporary entities share the same [sprite table](game/engine/sprites.py), limited to 35 slots in [constants](game/engine/constants.py). When a spawn finds no free slot, `SpriteTable.spawn` evicts the sprite with the oldest sequence number. Blocks are spawned when the level resets, before the flower and Koopa, and active blocks are included in the solid collision list.

After obtaining fire power, rapidly spawning fireballs fills the available slots. Further spawns can evict the older blocks, which removes them from collision and opens the box. Firing requires a fresh press and has a two-tick cooldown, so the solver alternates the run/fire input while jumping at the left edge of the roof.

The [solver](game/auto_solver.py) first collects the flower, uses the Koopa to reach the roof, fires repeatedly and walks over the opening. Run it from the client directory:

```sh
PYTHONPATH=. .venv/bin/python -m game.auto_solver
PYTHONPATH=. .venv/bin/python -m game.auto_solver <HOST> 23197
```

The local run reached the coin on frame 471. A subsequent replay against the challenge server returned the flag shown above. Network packets contain the input keys and the locally calculated state hash, allowing the server to validate the simulated run.

## Conclusion

The shared fixed-size entity table made permanent level geometry vulnerable to eviction by temporary projectiles. Filling it opened a path to the coin.
