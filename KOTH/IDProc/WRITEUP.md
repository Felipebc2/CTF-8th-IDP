<div align="center">

<a href="https://git.io/typing-svg"><img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=28&duration=700&pause=1000&color=E8423F&center=true&vCenter=true&repeat=false&width=500&height=35&lines=IDPROC" alt="Typing SVG" /></a>

</div>

# IDProc — KOTH

- **Status:** 🏁 FINISHED — **2nd place** in the KotH ranking (1640 pts), 4 round wins (rounds 12, 4, 6 and 11).
- **Points:** 1640 (sum of all rounds; final KotH ranking: Prompt and Pray 1840 · **NOP 1640** · Litrão por 9,90 1560)
- **Flag:** none (King of the Hill, points come straight from the round rankings)
- **Attachment / Target:** `manual-idproc.pdf` (ISA manual) / `https://<HOST>` (problem page, simulator, team submission)
- **Prompt:** *"King of the Hill de programação em assembly para o processador IDProc. A cada rodada (tick) de uma hora, um problema novo aparece em https://<HOST>. Escreva o programa no simulador, exporte o arquivo .idp e envie pela página do time. Vale o último envio válido até os 50 minutos da rodada (ex.: 18:50); aos 52 minutos, todos são avaliados. Cada rodada vale até 200 pontos: até 100 por usar menos ciclos e até 100 por usar menos instruções. Os pontos deste desafio são a soma das rodadas e se atualizam sozinhos. Entre com o login e a senha do cartão do time. O manual em anexo descreve a máquina e as instruções. Rodadas: hoje às 18h e 19h; amanhã de hora em hora, a partir das 8h."*

---

## TL;DR

1. Every hour a new problem is posted for the IDProc, a TIS-100-style multi-core 8-bit assembly machine.
2. You write the program in the web simulator, export a `.idp` file and submit it by HH:50. Everything is evaluated at HH:52. Each round gives up to 100 points for fewest cycles and up to 100 for fewest instructions.
3. Approach: a local simulator (`idproc_sim.py`) lets the program be optimized offline. The team validates the final version in the official simulator and submits it.

## Timeline

| Round | Opens | Submit by | Rank | Notes |
|---|---|---|---|---|
| 1 | 13/11 18:00 | 18:50 | — | voided by the organizers |
| 2 | 13/11 19:00 | 19:50 | 4th | no submission (0 pts) |
| 12 "Eco controlado" | 13/11 21:00 | 21:50 | **1st** | 2 instructions, 2 cycles/value (`rodadas/tick12/`) |
| 3 "Filtro de Sinal" | 14/11 08:00 | 08:50 | 2nd | 170/200, 4 instructions, 3 cycles/value (`rodadas/08h/`) |
| 4 "Pipeline aritmético" | 14/11 09:00 | 09:50 | **1st** | unique variant `solucao_v2.idp`, 6 instructions (3+3), 11 cycles (official = local) (`rodadas/09h/`) |
| 5 "Alternador de desvios" | 14/11 10:00 | 10:50 | 3rd | 140/200, 3-core layout, 10 instructions (3+4+3), 148 official cycles; tied with 4 other teams at 148/10 (`rodadas/10h/`) |
| 6 "Filtro em paralelo" | 14/11 11:00 | 11:50 | **1st** | 165/200, N2 unrolled 2x, 13 instructions, 123 official cycles (`rodadas/11h/solucao_13.idp`) |
| 7 | 14/11 12:00 | 12:50 | 5th | `rodadas/12h/` |
| 8 | 14/11 13:00 | 13:50 | 2nd | `d3_bit_u2.idp` (`rodadas/13h/`) |
| 9 | 14/11 14:00 | 14:50 | 4th | solution not archived (`rodadas/14h/` holds only the statement template) |
| 10 "Mistura até esgotar" | 14/11 15:00 | 15:50 | 4th | `v24_u2.idp` recommended (`rodadas/15h/`) |
| 11 "Convergência tripla" | 14/11 16:00 | 16:50 | **1st** | `v18.idp`, 18 instructions, 12 cycles on the example (`rodadas/16h/`) |

Round 2 top of the board: two teams with `correct` at 96 cycles / 3 instructions (180 pts each), one team at 126 cycles / 4 instructions (180 pts). Every other team, including ours, had no submission.

## Analysis

### The machine (manual, Ed. 1)

- **Cores:** each core has its own program, `ACC`, `BAK`, `IPT` and ports. There is no shared memory.
- **Ports:** each port is `in`, `out` or `io`. A link between cores has **no buffer**: a transfer happens only when the sender (`MOV ACC P`) and the receiver (`MOV Q ACC`) are both ready in the same cycle. The received value is usable from the next cycle on.
- **External channels:** an input channel is a FIFO, and reading it while empty blocks. Two reads of the same input in the same cycle are a runtime error. Output is always ready.
- **Data:** signed 8-bit integers with wraparound (`127+1 = -128`, `NEG -128 = -128`).
- **Registers:**
  - `ACC` is the accumulator.
  - `BAK` is only reachable through `SAV` (`BAK=ACC`) and `SWP`.
  - `NIL` reads as 0 and discards writes.
- **ISA:**
  - `MOV`: allowed forms are `lit|ACC|NIL → ACC|NIL`, `port → ACC` and `ACC → port`.
  - `SAV`, `SWP`, `NEG`.
  - `ADD`/`SUB`, with a literal or `ACC` as operand only.
  - Jumps `JMP`, `JEQ`, `JNZ`, `JGZ`, `JLZ`, which test `ACC` against 0.
  - `NOP`.
  - There is no `JRO`.
- **Timing:** every completed instruction takes 1 global cycle. Cores run in parallel, so two cores completing in the same cycle still cost one cycle.
- **Program format:** UTF-8 text with `[N0]` sections, `#` comments and core-local `label:` labels. Case is ignored, and a comma between `MOV` operands is accepted.

### Inferences from round 2

The winning 3 instructions / 96 cycles fits `MOV INPUT ACC / ADD k / MOV ACC OUTPUT` over 32 inputs with **no `JMP`**. That implies the program wraps back to its first instruction after the last one, like TIS-100. The manual does not state this. **Confirmed in tick 12:** the 2-line echo (`MOV INPUT ACC / MOV ACC OUTPUT`, no `JMP`) processed every input in the official simulator.

### Optimization levers (to apply per round)

- **Fewer instructions:** rely on the implicit wrap instead of `JMP`, reuse `BAK` instead of extra cores, and use `ADD ACC` for doubling.
- **Uniqueness:** per the organizers, identical submissions from different teams lose value for all of them. Varying only the text (`SUB -1` vs `ADD 1`, case, labels) does **not** count as different; see the round 5 note below. Do **not** reorder sections: the official simulator assigns them by position (first section = N0).
- **Fewer cycles:** unroll loops, and split work across cores working in parallel. Interleave reads of a shared input so that two reads never land in the same cycle.
- **Duplicates are judged by score, not by code (round 5):** five teams with different text but the same 148 cycles / 10 instructions all got 140, while the two teams with unique pairs (216/6 and 180/8) got 170. Text variation does not help; the (cycles, instructions) pair has to differ from the other teams. Prefer a Pareto point nobody else is likely to hit, or beat the obvious layout.
- **Round 6 confirmed it:** we spent 3 extra instructions to unroll the N2 loop (a negative B costs 3 cycles instead of 4) and got the only 123-cycle result. That was 1st with 165, while the four teams on the obvious 130/10 got 150 each. Raw data for fitting the formula (cycles/instructions → points): R2 96/3 ×2 → 180, 126/4 → 180; R5 216/6 → 170, 180/8 → 170, 148/10 ×5 → 140; R6 123/13 → 165, 130/10 ×4 → 150, 130/12 → 150, 154/13 → 135. Cycles seem to weigh more than instructions (130/12 scored the same as 130/10).
- **Official cycles ≠ example cycles:** round 5 local example gave 26 cycles, the ranking showed 148 (the official run uses more/longer test inputs). The cycle ordering between layouts still holds.
- These two goals usually conflict, so build both versions and keep the one with the higher combined score.

## What didn't work

| Hypothesis | Result | Why |
|---|---|---|
| Run the Dispatch `brainstormer` subagent for triage | ✗ | Auto mode could not review the call because a context-mode hook rewrites the Agent input. Triage was done manually from the manual instead. |

## Conclusion

Finished **2nd of 12 teams** in the KotH with 1640 pts (200 behind Prompt and Pray), with 4 round wins out of 11 scored rounds. Missing round 2 (no submission) cost the most; from round 12 on we placed in every round.

What made the difference:
- The local simulator (`idproc_sim.py`) let us iterate offline and only use the official simulator for the final check. It reproduced round 2's 96-cycle / 3-instruction result, tick 12 confirmed the implicit wrap, and round 4 confirmed that instructions are summed over all cores and that local cycles match the official count.
- Reading the scoring right: duplicates are judged by the (cycles, instructions) pair, so aiming for a Pareto point nobody else hits (rounds 6 and 11) beat the "obvious" layout that four or five teams tied on.

---

## Appendix — tools

- `idproc_sim.py`: run `python3 idproc_sim.py maquina.json solucao.idp [--trace] [--no-wrap]`. It parses and validates a `.idp` against a machine config and runs every test case. It reports instructions (per core and total), cycles, and `correct`/`WRONG` per test. Run it with no arguments for the self-test.
- `rodadas/<HH>h/`: one folder per round, holding the statement, the machine config and the solution.
