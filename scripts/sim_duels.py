#!/usr/bin/env python3
"""Monte Carlo duels: each class vs each monster through the real AttackAction.

Runs real combat rolls (to-hit + damage from data/balance/formulas.yaml) on a
real GameContext, so it measures whatever the config says today. Player swings
first, then they alternate until one dies. No movement, no regen, full HP.

Usage:
    python3 scripts/sim_duels.py                    # all classes, early monsters, level 1
    python3 scripts/sim_duels.py --level 4 --fights 2000
    python3 scripts/sim_duels.py --monsters goblin,orc,troll

Each cell: win% / average HP lost when the player wins (as a % of max HP).
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core.actions.attack_action import AttackAction  # noqa: E402
from core.base.game_context import GameContext  # noqa: E402
from core.character_class import CharacterClass, create_player_from_class  # noqa: E402
from core.config.config_loader import ConfigLoader  # noqa: E402
from core.entity_loader import EntityLoader  # noqa: E402
from core.game_state import GameState  # noqa: E402
from core.rng import GameRNG  # noqa: E402

EARLY = "bat,goblin,spider,wolf,skeleton,imp,orc,mimic,ogre,troll"


def make_player(cls, level):
    p = create_player_from_class(cls, 0, 0, name=cls.value)
    if level > 1:
        p.gain_xp(ConfigLoader.get_config().get_xp_for_level(level))
        p.hp = p.max_hp
    return p


def duel(cls, level, monster_id, loader, max_rounds=500):
    player = make_player(cls, level)
    monster = loader.create_monster(monster_id, 1, 0)
    state = GameState(player=player)
    state.entities[monster.entity_id] = monster
    ctx = GameContext(state)
    for _ in range(max_rounds):
        AttackAction(player.entity_id, monster.entity_id).execute(ctx)
        if not monster.is_alive:
            return True, 1 - player.hp / player.max_hp
        AttackAction(monster.entity_id, player.entity_id).execute(ctx)
        if not player.is_alive:
            return False, 1.0
    return False, 1 - player.hp / player.max_hp


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fights", type=int, default=1000)
    ap.add_argument("--level", type=int, default=1)
    ap.add_argument("--monsters", default=EARLY)
    ap.add_argument("--seed", type=int, default=1)
    args = ap.parse_args()

    import logging
    logging.disable(logging.CRITICAL)
    GameRNG.initialize(args.seed)
    loader = EntityLoader()
    monsters = args.monsters.split(",")

    print(f"level {args.level}, {args.fights} fights per cell; cell = win% / avg HP lost on a win")
    print(f"{'class':8} {'hp/atk/def':>10} " + " ".join(f"{m:>11}" for m in monsters))
    for cls in CharacterClass:
        p = make_player(cls, args.level)
        cells = []
        for m in monsters:
            wins, lost = 0, 0.0
            for _ in range(args.fights):
                won, frac = duel(cls, args.level, m, loader)
                if won:
                    wins += 1
                    lost += frac
            avg = (lost / wins * 100) if wins else 0
            cells.append(f"{wins * 100 // args.fights:3d}%/{avg:3.0f}%")
        print(f"{cls.value:8} {f'{p.max_hp}/{p.attack}/{p.defense}':>10} " + " ".join(f"{c:>11}" for c in cells))


if __name__ == "__main__":
    main()
