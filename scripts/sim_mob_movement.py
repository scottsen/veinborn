#!/usr/bin/env python3
"""Headless simulation: do mobs move through real generated maps as their AI style says?

Runs the real AISystem on real dungeon maps (no UI, no mocks) with an
invulnerable player, and checks each AI style against what it is supposed to do.

Scenarios (all seeded, all deterministic):
  chase    player stands still; monster starts 4-9 path-tiles away
  far      monster starts 20+ path-tiles away (must not home in on the player)
  leash    guard monsters only: player stands just outside the guard radius
  wounded  monster at 15% HP, player 3 tiles away (flee thresholds)
  floors   real floor spawns (floors 1..N), player walks a route; invariants only

Usage:
  python3 scripts/sim_mob_movement.py [--seeds 8] [--ticks 40] [--floors 1,4,8,12] [--verbose]

Exit status is 1 if any scenario check fails, so it can gate a change.
"""

import argparse
import logging
import random
import zlib
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.core.game import Game  # noqa: E402
from src.core.base.entity import EntityType  # noqa: E402
from src.core.entity_loader import EntityLoader  # noqa: E402
from src.core.actions.move_action import MoveAction  # noqa: E402
from src.core.pathfinding import find_path, get_direction  # noqa: E402
from src.core.config.config_loader import ConfigLoader  # noqa: E402

BIG = 10 ** 6


def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def new_game(seed):
    game = Game()
    game.start_new_game(seed=seed, player_name="Sim")
    player = game.context.get_player()
    player.hp = player.max_hp = BIG
    player.defense = BIG
    return game, player


def clear_monsters(ctx):
    for m in list(ctx.get_entities_by_type(EntityType.MONSTER)):
        ctx.remove_entity(m.entity_id)


def clear_obstacles(ctx):
    """Remove ore veins/forges so isolated scenarios test pure movement."""
    for t in (EntityType.ORE_VEIN, EntityType.FORGE):
        for e in list(ctx.get_entities_by_type(t)):
            ctx.remove_entity(e.entity_id)


def walkable_tiles(game_map):
    return [(x, y) for x in range(game_map.width) for y in range(game_map.height)
            if game_map.is_walkable(x, y)]


def pick_tile(game_map, player_pos, rng, lo, hi, hi_is_min=False):
    """A walkable tile whose A* path length to the player is in [lo, hi]."""
    tiles = walkable_tiles(game_map)
    rng.shuffle(tiles)
    for t in tiles:
        if t == player_pos or manhattan(t, player_pos) > hi + 6:
            if not hi_is_min:
                continue
        path = find_path(game_map, t, player_pos)
        if path and lo <= len(path) - 1 <= hi:
            return t
    return None


class Trace:
    """Per-tick positions of one monster, plus the player's."""

    def __init__(self, monster, player):
        self.m = [(monster.x, monster.y)]
        self.p = [(player.x, player.y)]
        self.hp = [monster.hp]

    def add(self, monster, player):
        self.m.append((monster.x, monster.y))
        self.p.append((player.x, player.y))
        self.hp.append(monster.hp)

    def dist(self, i):
        return manhattan(self.m[i], self.p[i])

    def adjacent(self, i):
        m, p = self.m[i], self.p[i]
        return max(abs(m[0] - p[0]), abs(m[1] - p[1])) <= 1

    def contact_tick(self):
        for i, (m, p) in enumerate(zip(self.m, self.p)):
            if max(abs(m[0] - p[0]), abs(m[1] - p[1])) <= 1:
                return i
        return None

    def oscillations(self):
        """Count A,B,A,B,A flip-flops with nobody adjacent (a stuck chaser)."""
        n = 0
        for i in range(4, len(self.m)):
            a, b, c, d, e = self.m[i - 4:i + 1]
            if a == c == e and b == d and a != b and not self.adjacent(i):
                n += 1
        return n

    def max_stall(self):
        """Longest run of ticks with no movement while not adjacent to the player."""
        best = cur = 0
        for i in range(1, len(self.m)):
            if self.m[i] == self.m[i - 1] and not self.adjacent(i):
                cur += 1
                best = max(best, cur)
            else:
                cur = 0
        return best

    def moved_ticks(self):
        return sum(1 for i in range(1, len(self.m)) if self.m[i] != self.m[i - 1])


def run_ticks(game, ai, monster, player, ticks):
    tr = Trace(monster, player)
    for _ in range(ticks):
        ai.update()
        tr.add(monster, player)
    return tr


def setup_one(seed, monster_id, lo, hi):
    """Fresh real map, player fixed, one monster placed lo..hi path-tiles away."""
    game, player = new_game(seed)
    ctx = game.context
    clear_monsters(ctx)
    clear_obstacles(ctx)
    rng = random.Random(seed * 7919 + zlib.crc32(monster_id.encode()) % 1000)
    t = pick_tile(ctx.get_map(), (player.x, player.y), rng, lo, hi)
    if t is None:
        return None
    monster = EntityLoader().create_monster(monster_id, *t)
    ctx.add_entity(monster)
    return game, ctx.get_system('ai'), monster, player


class Report:
    def __init__(self, verbose):
        self.verbose = verbose
        self.rows = defaultdict(lambda: defaultdict(list))   # style -> metric -> [values]
        self.fails = []

    def note(self, style, metric, value):
        self.rows[style][metric].append(value)

    def check(self, ok, where, msg):
        if not ok:
            self.fails.append(f"{where}: {msg}")


def scenario_chase(rep, types, seeds, ticks):
    for mid, style in types.items():
        for seed in seeds:
            s = setup_one(seed, mid, 4, 9)
            if not s:
                continue
            game, ai, mon, pl = s
            tr = run_ticks(game, ai, mon, pl, ticks)
            where = f"chase/{style}/{mid}/seed{seed}"
            contact = tr.contact_tick()
            rep.note(style, "chase: reached player", contact is not None)
            rep.note(style, "chase: ticks to contact", contact if contact is not None else None)
            rep.note(style, "chase: osc", tr.oscillations())
            rep.note(style, "chase: max stall", tr.max_stall())
            rep.note(style, "chase: end dist", tr.dist(-1))
            in_range = manhattan(tr.m[0], tr.p[0]) <= ConfigLoader.get_config().get_ai_behavior_config(style).get("chase_range", 10)
            rep.note(style, "chase: start in chase_range", in_range)
            if style in ("aggressive", "defensive") and in_range:
                path_len = len(find_path(game.context.get_map(), tr.m[0], tr.p[0]) or []) - 1
                rep.check(contact is not None and contact <= path_len + 6, where,
                          f"{style} monster {path_len} tiles away not adjacent within {path_len + 6} ticks (contact={contact})")
                rep.check(tr.oscillations() == 0, where, f"{style} monster flip-flops between two tiles")
            if style == "coward":
                rep.check(tr.dist(-1) >= tr.dist(0) - 1, where,
                          f"coward ended closer to the player ({tr.dist(0)} -> {tr.dist(-1)})")
                rep.check(contact is None, where, "coward walked up to the player")


def scenario_far(rep, types, seeds, ticks):
    for mid, style in types.items():
        for seed in seeds:
            s = setup_one(seed, mid, 22, 80)
            if not s:
                continue
            game, ai, mon, pl = s
            tr = run_ticks(game, ai, mon, pl, ticks)
            where = f"far/{style}/{mid}/seed{seed}"
            closed = tr.dist(0) - tr.dist(-1)
            rep.note(style, "far: tiles closed in", closed)
            rep.note(style, "far: moved ticks", tr.moved_ticks())
            rep.check(tr.contact_tick() is None, where, "monster far outside chase range reached the player")


def scenario_wounded(rep, types, seeds, ticks):
    for mid, style in types.items():
        for seed in seeds:
            s = setup_one(seed, mid, 3, 4)
            if not s:
                continue
            game, ai, mon, pl = s
            mon.hp = max(1, int(mon.max_hp * 0.15))
            tr = run_ticks(game, ai, mon, pl, min(ticks, 15))
            where = f"wounded/{style}/{mid}/seed{seed}"
            rep.note(style, "wounded: dist change", tr.dist(-1) - tr.dist(0))
            if style in ("defensive", "coward", "guard"):
                thr = ConfigLoader.get_config().get_ai_behavior_config(style).get("flee_threshold", 0)
                if thr >= 0.15 and style != "guard":
                    rep.check(tr.dist(-1) >= tr.dist(0), where,
                              f"wounded {style} moved toward the player ({tr.dist(0)} -> {tr.dist(-1)})")


def scenario_leash(rep, types, seeds, ticks):
    cfg = ConfigLoader.get_config().get_ai_behavior_config("guard")
    radius = cfg.get("guard_radius", 4)
    for mid, style in types.items():
        if style != "guard":
            continue
        for seed in seeds:
            # Player is 6 tiles away: inside chase_range(6), outside guard_radius(4).
            s = setup_one(seed, mid, 6, 6)
            if not s:
                continue
            game, ai, mon, pl = s
            spawn = (mon.x, mon.y)
            tr = run_ticks(game, ai, mon, pl, ticks)
            where = f"leash/guard/{mid}/seed{seed}"
            far = max(manhattan(p, spawn) for p in tr.m)
            rep.note(style, "leash: max dist from spawn", far)
            rep.note(style, "leash: reached player", tr.contact_tick() is not None)
            rep.note(style, "leash: osc", tr.oscillations())
            rep.check(far <= radius + 1, where,
                      f"guard strayed {far} tiles from spawn (radius {radius}) -- leash not enforced")


def detour_exists(gmap, ctx, start, goal, blocked):
    """BFS (8-dir) over walkable tiles treating `blocked` tiles as walls."""
    from collections import deque
    seen, q = {start}, deque([start])
    while q:
        x, y = q.popleft()
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                n = (x + dx, y + dy)
                if n in seen or not gmap.in_bounds(*n) or not gmap.is_walkable(*n):
                    continue
                if n == goal:
                    return True
                if n in blocked:
                    continue
                seen.add(n)
                q.append(n)
    return False


def scenario_floors(rep, floors, seeds, ticks):
    """Real floor spawns with a walking player: movement invariants only."""
    for seed in seeds:
        for floor in floors:
            game, player = new_game(seed)
            ctx, gmap = game.context, game.context.get_map()
            clear_monsters(ctx)
            ents = game.bootstrapper.spawn_entities(game.spawner, floor, gmap)
            for m in ents['monsters']:
                ctx.add_entity(m)
            ai = ctx.get_system('ai')
            mons = list(ctx.get_entities_by_type(EntityType.MONSTER))
            tiles = walkable_tiles(gmap)
            rng = random.Random(seed * 31 + floor)
            goal = rng.choice(tiles)
            prev = {m.entity_id: (m.x, m.y) for m in mons}
            where = f"floors/seed{seed}/floor{floor}"
            blocked_run = defaultdict(int)
            for t in range(ticks):
                # player walks toward a waypoint, picks a new one on arrival
                if (player.x, player.y) == goal:
                    goal = rng.choice(tiles)
                d = get_direction(gmap, (player.x, player.y), goal)
                if d:
                    a = MoveAction(player.entity_id, *d)
                    if a.validate(ctx):
                        a.execute(ctx)
                before = {m.entity_id: (m.x, m.y) for m in mons if m.is_alive}
                ai.update()
                obstacle_tiles = {(e.x, e.y) for et in (EntityType.ORE_VEIN, EntityType.FORGE)
                                  for e in ctx.get_entities_by_type(et)}
                for m in mons:
                    if not m.is_alive or (m.x, m.y) != before.get(m.entity_id):
                        blocked_run[m.entity_id] = 0
                        continue
                    ppos = (player.x, player.y)
                    if max(abs(m.x - player.x), abs(m.y - player.y)) <= 1:
                        continue
                    style = m.get_stat('ai_type')
                    if style not in ("aggressive", "defensive", "guard"):
                        continue
                    if manhattan((m.x, m.y), ppos) > ConfigLoader.get_config().get_ai_behavior_config(style).get("chase_range", 10):
                        blocked_run[m.entity_id] = 0
                        continue
                    d = get_direction(gmap, (m.x, m.y), ppos, allow_diagonals=True)
                    if d and (m.x + d[0], m.y + d[1]) in obstacle_tiles:
                        blocked_run[m.entity_id] += 1
                        rep.note("(all)", "floors: ticks blocked by ore/forge", 1)
                        if blocked_run[m.entity_id] == 10:
                            alt = detour_exists(gmap, ctx, (m.x, m.y), ppos, obstacle_tiles)
                            rep.note("(all)", "floors: stuck>=10 ticks behind ore/forge", 1)
                            rep.note("(all)", "floors: ...and a detour existed", 1 if alt else 0)
                            rep.check(not alt, where,
                                      f"{m.name} at {(m.x, m.y)} stuck 10+ ticks behind an ore/forge although a detour to the player exists")
                    else:
                        blocked_run[m.entity_id] = 0
                seen = {}
                for e in ctx.get_entities_by_type(EntityType.MONSTER) + ctx.get_alive_players():
                    if not e.is_alive:
                        continue
                    pos = (e.x, e.y)
                    rep.check(gmap.is_walkable(*pos), where, f"t{t}: {e.name} on non-walkable tile {pos}")
                    if pos in seen:
                        rep.check(False, where, f"t{t}: {e.name} and {seen[pos]} share tile {pos}")
                    seen[pos] = e.name
                    if e.entity_id in prev:
                        step = max(abs(pos[0] - prev[e.entity_id][0]), abs(pos[1] - prev[e.entity_id][1]))
                        rep.check(step <= 1, where, f"t{t}: {e.name} jumped {step} tiles")
                        prev[e.entity_id] = pos
            rep.note("(all)", "floors: monsters simulated", len(mons))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=8)
    ap.add_argument("--ticks", type=int, default=40)
    ap.add_argument("--floors", default="1,4,8,12")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()
    logging.disable(logging.CRITICAL)

    loader = EntityLoader()
    types = {mid: loader.get_monster_definition(mid)["ai"]["type"] for mid in loader.get_monster_ids()}
    seeds = list(range(1, args.seeds + 1))
    floors = [int(f) for f in args.floors.split(",")]

    rep = Report(args.verbose)
    scenario_chase(rep, types, seeds, args.ticks)
    scenario_far(rep, types, seeds, args.ticks)
    scenario_wounded(rep, types, seeds, args.ticks)
    scenario_leash(rep, types, seeds, args.ticks)
    scenario_floors(rep, floors, seeds[:max(2, len(seeds) // 3)], args.ticks * 5)

    print("AI styles in use:", {s: sorted(m for m, t in types.items() if t == s) for s in sorted(set(types.values()))})
    print()
    for style in sorted(rep.rows):
        print(f"[{style}]")
        for metric, vals in rep.rows[style].items():
            nums = [v for v in vals if v is not None]
            if not nums:
                print(f"  {metric:28s} n=0")
            elif isinstance(nums[0], bool):
                print(f"  {metric:28s} {sum(nums)}/{len(nums)}")
            else:
                print(f"  {metric:28s} mean={sum(nums) / len(nums):.1f} min={min(nums)} max={max(nums)} n={len(nums)}")
    print()
    by_where = defaultdict(int)
    for f in rep.fails:
        by_where[f.split(":")[0].rsplit("/seed", 1)[0] + " :" + f.split(":", 1)[1].split(":")[-1][:70]] += 1
    if rep.fails:
        print(f"FAILED CHECKS: {len(rep.fails)}")
        for k, n in sorted(by_where.items(), key=lambda kv: -kv[1])[:25]:
            print(f"  {n:4d}  {k}")
        if args.verbose:
            for f in rep.fails[:200]:
                print("   ", f)
    else:
        print("ALL CHECKS PASSED")
    return 1 if rep.fails else 0


if __name__ == "__main__":
    sys.exit(main())
