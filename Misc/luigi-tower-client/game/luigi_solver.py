"""Plan valid Luigi Tower inputs locally; optionally replay them to the CTF server."""
import argparse
import copy
import heapq
import itertools
import json
from pathlib import Path
import select
import sys
import time

ROOT = Path(r"C:\Users\Fábio\hackathon8\luigi-tower-client")
sys.path.insert(0, str(ROOT))
from game import map_path
from game.engine.simulation import Game, SCALE
from game.map_loading.tilemap import load


def steering(game, target):
    # Brake before the target, accounting for inertia at the exact game rate.
    p = game.player
    x, v = p.x / SCALE, p.vx / SCALE
    stop = v * abs(v) / (2 * (154 / SCALE))
    error = target - x - stop
    if abs(error) < 1.0 and abs(v) < 0.6:
        return []
    return ["right" if error > 0 else "left", "run"]


def jump(game, target, prepare=0):
    g = copy.copy(game)
    g.player = copy.copy(game.player)
    keys_list = []
    for _ in range(prepare):
        keys = steering(g, target)
        g.step(keys)
        keys_list.append(keys)
        if g.player.dead or not g.player.grounded:
            return None
    airborne = False
    for tick in range(100):
        keys = steering(g, target)
        if tick == 0:
            keys = keys + ["jump"]
        g.step(keys)
        keys_list.append(keys)
        airborne |= not g.player.grounded
        if g.player.won:
            return g, keys_list
        if g.player.dead or g.player.y > game.player.y + 300 * SCALE:
            return None
        if airborne and g.player.grounded:
            return g, keys_list
    return None


def signature(g):
    p = g.player
    return (p.x // (8 * SCALE), p.y // SCALE, p.vx // (SCALE), g.coin_collected)


def plan():
    world = load(map_path())
    start = Game(world)
    ids = itertools.count()
    queue = [(0, next(ids), start, None, [])]
    seen = {}
    expanded = 0
    best_y = start.player.y // SCALE
    while queue and expanded < 30000:
        _, _, g, parent, segment = heapq.heappop(queue)
        key = signature(g)
        if seen.get(key, 10**9) <= g.tick_count:
            continue
        seen[key] = g.tick_count
        node = (parent, segment)
        expanded += 1
        y = g.player.y / SCALE
        if y < best_y - 400:
            best_y = int(y)
            print(f"Search: y={best_y}, ticks={g.tick_count}, nodes={expanded}", flush=True)
        if g.player.won:
            segments = []
            while node:
                node, segment = node
                segments.append(segment)
            result = [keys for segment in reversed(segments) for keys in segment]
            check = Game(world)
            for keys in result:
                check.step(keys)
            assert check.player.won and not check.player.dead
            return result, check, expanded
        x = g.player.x / SCALE
        bottom = y + 28
        targets = set()
        for platform in world.platforms + world.solids + (world.goal,):
            platform_y = platform.y + platform.height if platform is world.goal else platform.y
            if not bottom - 185 <= platform_y <= bottom + 165:
                continue
            for target in (platform.x + 2, platform.x + platform.width / 2 - 10,
                           platform.x + platform.width - 22):
                if abs(target - x) <= 285:
                    targets.add(int(target))
        # Positions on the starting pedestal are useful for taking a running jump.
        if bottom >= world.height - 64:
            targets.update((40, 224, 288, 448, 480, 652, 704, 896))
        for target in sorted(targets):
            if target > 480:
                continue
            for prepare in ((0, 2, 4, 6, 8, 10, 12, 14, 16, 20) if y < 1000 else (0, 6, 14)):
                outcome = jump(g, target, prepare)
                if not outcome:
                    continue
                nxt, actions = outcome
                if nxt.tick_count >= 7200:
                    continue
                if seen.get(signature(nxt), 10**9) <= nxt.tick_count:
                    continue
                # Favor climbing; retain alternate routes and launch velocities.
                priority = nxt.tick_count + max(0, nxt.player.y / SCALE - 220) * 1.0
                if nxt.player.won:
                    priority = -1
                heapq.heappush(queue, (priority, next(ids), nxt, node, actions))
    raise RuntimeError(f"No route found after {expanded} states (best y={best_y}).")


def replay(actions, host, port, realtime):
    from game.network import connect, recv_packet, send_packet
    g = Game(load(map_path()))
    with connect(host, port) as sock:
        initial = recv_packet(sock)
        print("Server:", initial, flush=True)
        if initial.get("character", "luigi") != "luigi":
            raise RuntimeError("Unexpected server character")
        if len(actions) > initial.get("session_ticks", 7200):
            raise RuntimeError("Route exceeds server session limit")
        started = time.monotonic()
        for i, keys in enumerate(actions):
            if realtime:
                time.sleep(max(0, started + i / 60 - time.monotonic()))
            g.step(keys)
            send_packet(sock, {"keys": keys, "state": g.state_hash()})
            if select.select([sock], [], [], 0)[0]:
                result = recv_packet(sock)
                print("Result:", json.dumps(result, ensure_ascii=False), flush=True)
                return result
        result = recv_packet(sock)
        print("Result:", json.dumps(result, ensure_ascii=False), flush=True)
        return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--send", action="store_true")
    parser.add_argument("--fast", action="store_true")
    parser.add_argument("--host", default="luigi-misc.desafio.idp-ctf.site")
    parser.add_argument("--port", type=int, default=23196)
    args = parser.parse_args()
    route_file = Path(__file__).with_name("luigi_route.json")
    if route_file.exists():
        actions = json.loads(route_file.read_text())
    else:
        actions, final, nodes = plan()
        route_file.write_text(json.dumps(actions))
        print(f"Verified route: {len(actions)} ticks ({len(actions)/60:.1f}s), {nodes} nodes", flush=True)
    if args.send:
        replay(actions, args.host, args.port, not args.fast)
