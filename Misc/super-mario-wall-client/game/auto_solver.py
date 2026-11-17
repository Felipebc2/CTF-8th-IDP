"""Replay a locally tested sequence using the game's normal network protocol."""

import argparse
import select
import time
from pathlib import Path

from game.engine.simulation import Game
from game.map_loading.tilemap import load
from game.network import connect, recv_packet, send_packet


def moves():
    # Pick up the flower, bounce off the koopa, and stop on the roof.
    for keys, count in (
        (["left"], 30),
        (["right", "run"], 93),
        (["right", "run", "jump"], 79),
        (["left"], 40),
        ([], 70),
    ):
        for _ in range(count):
            yield keys

    # Fire on alternate ticks while jumping at the left edge of the roof.
    for tick in range(100):
        yield (["jump"] if tick == 0 else []) + (["run"] if tick % 2 == 0 else [])

    # Walk over the opening and let Mario fall onto the goal.
    for _ in range(35):
        yield ["right"]
    for _ in range(100):
        yield []


def main():
    parser = argparse.ArgumentParser(description="Replay the Super Mario Wall solution.")
    parser.add_argument("host", nargs="?", help="CTF server hostname; omit for a local simulation")
    parser.add_argument("port", type=int, nargs="?", default=23197)
    args = parser.parse_args()

    map_path = Path(__file__).parent / "resources" / "maps" / "level.tmx"
    game = Game(load(map_path))
    sock = connect(args.host, args.port) if args.host else None
    try:
        if sock:
            print("Servidor:", recv_packet(sock), flush=True)
        for tick, keys in enumerate(moves(), 1):
            game.step(keys)
            if sock:
                send_packet(sock, {"keys": keys, "state": game.state_hash()})
                if game.player.won or select.select([sock], [], [], 0)[0]:
                    print("Resposta do servidor:", recv_packet(sock), flush=True)
                    return
                time.sleep(1 / 60)
            elif game.player.won:
                print(f"Simulação local concluída: moeda alcançada no frame {tick}.")
                return
        print("A sequência terminou sem alcançar a moeda.")
    finally:
        if sock:
            sock.close()


if __name__ == "__main__":
    main()
