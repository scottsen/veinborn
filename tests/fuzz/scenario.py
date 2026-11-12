"""
Deep-start scenarios for bots and sims: begin a fresh game on floor N at level L.

Bots reach about floor 10 and level 7 in 3000 turns, while the game is won on
floor 100, so anything placed deeper (VB-69) never appears in an ordinary bot
run. `advance_to` puts the player there through the game's own paths: XP goes
through `gain_xp` (so level-up HP rolls happen as in play) and every floor
through `Game.descend_floor` (map generation, spawns, floor_changed events). It
only uses the game's seeded RNG, so a seed still fixes the whole game.

The player arrives with starting gear only: no crafted weapon or armour, and no
loot from the floors skipped. Treat absolute numbers from a deep start as
pessimistic; it is built for paired before/after comparisons on the same seeds
(scripts/compare_bot_runs.py), where that bias is the same on both sides.
"""

from core.config import ConfigLoader
from core.floor_manager import get_victory_floor


def advance_to(game, floor: int = 1, level: int = 1) -> None:
    """Move a just-started game's player to `floor` at `level`, at full HP."""
    config = ConfigLoader.get_config()
    victory = get_victory_floor(config)
    if not 1 <= floor < victory:
        raise ValueError(f"start floor must be 1..{victory - 1} (floor {victory} wins), got {floor}")
    if level < 1:
        raise ValueError(f"start level must be >= 1, got {level}")

    player = game.state.player
    needed = config.get_xp_for_level(level) - player.get_stat('xp', 0)
    if needed > 0:
        player.gain_xp(needed)
    while game.state.current_floor < floor:
        game.descend_floor()
    player.hp = player.max_hp
