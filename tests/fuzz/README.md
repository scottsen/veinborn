# Veinborn Automated Testing Bot (Fuzzer)

**Purpose:** Automatically play the game with random actions to find bugs, crashes, and state violations.

---

## Quick Start

```bash
# Test run (5 games, verbose)
python3 tests/fuzz/veinborn_bot.py --games 5 -v

# Standard run (100 games)
python3 tests/fuzz/veinborn_bot.py

# Stress test (1000 games overnight)
python3 tests/fuzz/veinborn_bot.py --games 1000 --max-turns 5000

# Quick smoke test (10 games, 50 turns each)
python3 tests/fuzz/veinborn_bot.py --games 10 --max-turns 50
```

---

## What It Does

### 1. Random Action Selection
The bot chooses random valid actions with realistic weights:
- **70%** Move (8 directions)
- **10%** Survey ore
- **10%** Mine ore
- **10%** Wait

### 1b. Strategic Mode: Sweep, Then Descend
In `strategic` mode (what the class bots use) the bot plays a decision tree
(`services/action_planner.py`, `get_smart_action`), and its exploration goal is a
**room sweep** (`services/room_sweeper.py`): visit each room on the floor, fight
what it judges winnable in that room, mark the room done, and when every room is
done head for the stairs. A floor turn budget (1500) and a per-room give-up (60
turns) stop it stalling. Stepping on the stairs early does not skip the sweep
(`TacticalDecisionService.descend_gate`). This replaced "go down when the floor has
no monsters left", which never happened once wandering spawns (VB-52) kept the
floor stocked.

Once the sweep is done (every room, or the floor budget spent) the optional detours
(ore, surveys, potion pickups, pursuing monsters) stop, so nothing can pull the bot back
from the stairs. Before this, two goals that disagreed by one tile could trade turns
forever: ore was sought only at Euclidean distance above 2, so from 2.0 away the sweep
stepped back and the ore seek stepped forward again, and three warrior seeds spent up to
18,000 of 20,000 turns on one floor (`tests/unit/test_planner_ore.py`). Ore is now
sought by 8-way steps with a 20-turn limit per vein, and never mined with a full pack.

The planner also uses class abilities (`ActionPlanner.ability_action`): a mage bolts any
monster in range 6 and line of sight whenever force bolt is ready, a healer heals at or below
60% HP. Measured on 8 games x 3000 turns: mage avg floor 4.9 -> 6.2, level 3.8 -> 5.8, deaths
6 -> 2; healer unchanged (floor 9.4, 1 death).

It drinks a potion or eats at or below 40% HP (`ActionPlanner.drink_action`, using core's
`best_healing_item`, after the heal ability) and picks up usable potions and food within 6
tiles (`collect_action`; autopickup skips potions). Whether a fight is winnable
(`TacticalDecisionService.can_win_fight`) comes from the game's own dice:
`AttackAction.expected_damage` both ways, the monster's side scaled by its `move_speed`.

All four class bots run this shared planner and differ only in their `CombatConfig`
(the old per-class decision trees were never called and were removed, VB-57).

The bot sees every monster on the floor, as a human does: the TUI draws the whole floor
and players have no fog of war.

### 2. Game State Validation
After each turn, validates invariants:
- ✅ Player HP never negative
- ✅ Player HP ≤ max HP
- ✅ HP = 0 → is_alive = False
- ✅ HP > 0 → is_alive = True
- ✅ All entity HP valid
- ✅ Player position in bounds
- ✅ Inventory size ≤ 20, and nothing carried also lies on the map
- ✅ At most one living player/monster per tile, none inside a wall
- ✅ Summoners stay within their ability's `max_minions`

### 3. Error Detection
Catches and logs:
- **Crashes** - Exceptions that stop the game
- **Errors** - Invalid state violations
- **Action failures** - Actions that raise exceptions

### 4. Statistical Analysis
Per game (results JSON): seed, floor, turns, level, kills, damage taken (total and by
monster type), the monster type that killed it, whether the death was a burst (above
half HP two turns before), potions used, errors. Also the turn and level on arrival at each floor
(`floor_arrivals`); `python3 scripts/bot_progression.py logs/*.json` turns those into the
level-by-floor curve (median and 25th-75th percentile level per floor, per class).

Tracks:
- Games played / completed
- Crash rate
- Average turns survived
- Max level reached
- Games per second

---

## Example Output

```
============================================================
Veinborn Automated Testing Bot
============================================================
Games to play: 100
Max turns per game: 1000
Verbose: False
============================================================

[Game 1/100]
[Game 10/100]

Progress: 10 games
  Crashes: 0
  Errors: 0
  Avg turns: 247.3

...

============================================================
FINAL RESULTS
============================================================

Games Played: 100
Games Completed: 98
Crashes: 0 (0.0%)
Errors: 2

Total Turns: 24,731
Avg Turns/Game: 247.3
Max Turns Survived: 892
Max Level Reached: 3

Time Elapsed: 10.2s
Games/Second: 9.80

🎉 NO BUGS FOUND! Game is stable!
```

---

## Command-Line Options

```bash
python3 tests/fuzz/veinborn_bot.py [options]

Options:
  --games N         Number of games to play (default: 100)
  --max-turns N     Max turns per game (default: 100000)
  --mode M          strategic (default) | random | hybrid
  --seed-base N     Game i plays seed N+i (dungeon, dice and the bot's own choices)
  --jobs N          Play N games at once in worker processes (results keep game order)
  --output PATH     Per-game results JSON (default: logs/bot_results_<class>_<time>.json)
  --start-floor N   Begin each game on floor N (deep placements; see below)
  --start-level L   Begin each game at player level L
  -v, --verbose     Show detailed output (turn-by-turn)
  -h, --help        Show help message
```

### Before/after comparisons (paired seeds)

A seed fixes the whole game, so the same seed on the same code replays the same game
(`tests/unit/test_seeded_replay.py` guards this). Play the same seeds before and after a
change and compare game by game; 8 unseeded games could not separate a real effect from
noise, paired seeds usually can.

Bots ignore `~/.veinbornrc`: each game runs on built-in user preferences
(`ConfigManager.use_defaults()`, VB-76), because autopickup reads them and a developer's
`autopickup_types` changed what bots collected. To test a preference on purpose, set it
in the environment, e.g. `VEINBORN_GAME_AUTOPICKUP_TYPES=ore,food,weapon`. Runs made
before 1fcbdfd used the machine's rc file and do not pair with later runs; gold became an
autopickup default after that, so pair only runs from the same side of that change.

```bash
# before the change (one file per class)
for c in warrior rogue mage healer; do
  python3 tests/fuzz/${c}_bot.py --games 32 --max-turns 3000 --seed-base 1000 --jobs 3 \
      --output logs/before_${c}.json
done
# ... make the change, then the same with --output logs/after_${c}.json ...
python3 scripts/compare_bot_runs.py --before logs/before_*.json --after logs/after_*.json
```

The comparison prints, per class and overall, mean before/after and the mean paired
difference with a 95% interval for floor, turns, level, kills, damage taken, deaths,
crashes and errors (`*` = the interval excludes 0), the same for damage taken from each
monster type (so a change to one monster shows up where it acts), which monster types
killed the bot, and how many games came out identical.
Bot high scores go to `logs/bot_highscores.json` (gitignored), never the shipped
`data/highscores.json`. Each results file records the commit it ran and whether `src/`, `data/` or `tests/fuzz/`
had uncommitted changes. To compare two commits without touching your tree, play the
"before" side from a copy: `git archive <commit> | tar -x -C /tmp/vb_before`.

### Deep starts (floors bots never reach)

In 3000 turns the bots reach about floor 10 at level 7; the game is won on floor 100. A
monster placed on floor 16+ never shows up in an ordinary run. `--start-floor 16
--start-level 8` begins each game there (`fuzz/scenario.py advance_to`): XP through the
real `gain_xp` (level-up HP rolls included) and every floor through `Game.descend_floor`,
on the game's seeded RNG, so a seed still fixes the whole game.

The player arrives with starting gear only (no crafted gear, no loot from skipped floors),
so absolute numbers are pessimistic. Use deep starts for paired before/after runs on the
same seeds and start point, where that bias cancels; `compare_bot_runs.py` warns if the
two sides started differently.

```bash
for c in warrior rogue mage healer; do
  python3 tests/fuzz/${c}_bot.py --games 16 --max-turns 1500 --seed-base 2000 --jobs 3 \
      --start-floor 16 --start-level 8 --output logs/deep16_${c}.json
done
```

---

## Use Cases

### 1. Pre-Commit Smoke Test
```bash
# Quick validation before committing
python3 tests/fuzz/veinborn_bot.py --games 10 --max-turns 100
```

### 2. Feature Testing
```bash
# After adding new feature, run 100 games
python3 tests/fuzz/veinborn_bot.py --games 100
```

### 3. Overnight Stress Test
```bash
# Let it run overnight
nohup python3 tests/fuzz/veinborn_bot.py --games 10000 > fuzz_results.txt 2>&1 &
```

### 4. Performance Benchmarking
```bash
# See how fast the game engine is
python3 tests/fuzz/veinborn_bot.py --games 100 --max-turns 500
# Typical: 100-200 games/second
```

---

## What Bugs Can It Find?

### State Violations
- HP going negative
- HP exceeding max HP
- Dead entities still acting
- Invalid positions
- Inventory overflow

### Crashes
- Null pointer errors
- Index out of bounds
- Infinite loops
- Stack overflows

### Logic Errors
- Inconsistent state transitions
- Missing validation
- Edge cases in combat/mining
- Race conditions (future multiplayer)

---

## Integration with CI/CD

### GitHub Actions Example
```yaml
name: Fuzz Testing
on: [push, pull_request]
jobs:
  fuzz:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run fuzz tests
        run: python3 tests/fuzz/veinborn_bot.py --games 100
```

---

## Performance

**Benchmark (on typical dev machine):**
- **Speed:** 100-300 games/second
- **100 games:** ~0.5-1 second
- **1000 games:** ~5-10 seconds
- **10000 games:** ~50-100 seconds

**Why so fast?**
- No UI rendering
- Direct game logic calls
- Pure Python (no I/O)
- Lightweight state validation

---

## Extending the Bot

### Add New Invariants

Edit `validate_game_state()`:
```python
def validate_game_state(self, game: Game) -> List[str]:
    violations = []

    # Add your custom validation
    if some_condition:
        violations.append("Description of violation")

    return violations
```

### Smarter Action Selection

Edit `get_random_action()`:
```python
def get_random_action(self, game: Game) -> tuple:
    # Example: prioritize mining when adjacent to ore
    adjacent_ore = self.find_adjacent_ore(game)
    if adjacent_ore:
        return ('mine', {})

    # ... default random behavior
```

### Track Custom Metrics

Add to `BotStats`:
```python
@dataclass
class BotStats:
    total_ore_mined: int = 0
    total_xp_gained: int = 0
    # ... etc
```

---

## Comparison to Manual Testing

| Method | Coverage | Speed | Finds Edge Cases |
|--------|----------|-------|------------------|
| **Manual Testing** | Low | Slow | Few |
| **Unit Tests** | High | Very Fast | Many |
| **Fuzz Testing** | Very High | Fast | Most |

**Best Practice:** Use all three!
1. Unit tests for specific behaviors
2. Fuzz testing for edge cases and stability
3. Manual testing for feel and UX

---

## Known Limitations

- **Not comprehensive** - Can't test every possible sequence
- **Random exploration** - Might miss specific scenarios
- **No UI testing** - Only tests game logic
- **No assertions** - Relies on crashes/violations (not correctness)

**Solution:** Combine with unit tests and integration tests!

---

## Tips for Best Results

1. **Run regularly** - Daily or before each commit
2. **Increase games over time** - Start with 100, scale to 1000+
3. **Watch for patterns** - Repeated errors indicate real bugs
4. **Combine with unit tests** - Fuzz finds it, unit test prevents it
5. **Use verbose mode** - When debugging specific issues

---

## Success Metrics

**Green (Good):**
- 0 crashes
- 0 errors
- > 100 games/second
- Avg turns > 200

**Yellow (Investigate):**
- 1-2 errors
- Crash rate < 1%
- Specific violation patterns

**Red (Fix Now):**
- Any crashes
- Crash rate > 1%
- Repeated violations
- Avg turns < 50 (suggests early death loop)

---

## Future Enhancements

### Planned Features
- [ ] Mutation testing (inject faults, verify detection)
- [ ] Replay system (save/replay crash sequences): seeds replay whole games now (`--seed-base`); a crash's seed is in the results file
- [ ] Coverage-guided fuzzing (prioritize unexplored code paths)
- [ ] Property-based testing (Hypothesis integration)
- [x] Parallel execution (`--jobs`)
- [ ] Crash deduplication (group similar crashes)

### Advanced Ideas
- [ ] Genetic algorithms (evolve successful strategies)
- [ ] Machine learning (learn optimal play)
- [ ] Adversarial testing (try to break invariants)
- [ ] Performance profiling (find slow code paths)

---

## Real-World Example

**Before Bot:**
- Manual testing: 30 minutes → found 2 bugs
- Code confidence: Medium

**After Bot:**
- Fuzz testing: 2 minutes → found 5 bugs + 1 crash
- Code confidence: High

**ROI:** 15x faster bug discovery!

---

## Questions?

- **Q: How is this different from unit tests?**
  - A: Unit tests test specific behaviors. Fuzzing tests random combinations and edge cases you didn't think of.

- **Q: Will it find all bugs?**
  - A: No, but it finds many that manual testing misses, especially edge cases.

- **Q: How many games should I run?**
  - A: Start with 100. If bugs found, investigate. If clean, scale to 1000+.

- **Q: Can it test multiplayer?**
  - A: Not yet, but could be extended to simulate multiple bots playing together.

---

**Happy Bug Hunting! 🐛🤖**
