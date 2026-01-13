# 🏆 The Veinborn Floor 100 Challenge

**Goal:** Create a bot that reaches floor 100 and escapes the dungeon!

**Current Record:** Floor ??? *(Unknown - no bot has won yet!)*

**Prize:** Immortality in game credits + Hall of Fame entry

---

## The Challenge

Veinborn's victory condition is **floor 100** - escape the infinite dungeon. No bot has achieved this yet.

Your mission: Build a bot that survives deeper than anyone else, and ultimately conquers floor 100.

---

## Quick Start (10 Minutes to Your First Bot)

### Step 1: Copy the Template

```bash
cd /home/scottsen/src/projects/veinborn

# TODO: Create this template
# cp tests/fuzz/templates/custom_bot_template.py my_strategy.py
```

### Step 2: Tune Configuration

Edit `my_strategy.py`:

```python
class MyCustomBot(VeinbornBot):
    def __init__(self, verbose: bool = False):
        # Configure behavior
        combat_config = CombatConfig(
            flee_hp_threshold=0.3,        # Flee at 30% HP (0.2-0.5 range)
            aggression_level='balanced',  # 'passive' / 'balanced' / 'aggressive'
            risk_tolerance='medium',      # 'low' / 'medium' / 'high'
        )

        mining_config = MiningConfig(
            min_purity_threshold=60,      # Only mine 60+ purity ore
            prefer_rare_ores=True,        # Target mithril/adamantite
            mine_under_threat=False,      # Don't mine if monsters nearby
        )

        super().__init__(
            verbose=verbose,
            mode='strategic',
            player_name='MyBot',
            combat_config=combat_config,
            mining_config=mining_config
        )
```

### Step 3: Run & Measure

```bash
python my_strategy.py --games 100

# Output:
# Max Floor Reached: 13
# Avg Turns/Game: 247.3
# Crashes: 0
```

### Step 4: Iterate

- Too many early deaths? → Increase `flee_hp_threshold`
- Not reaching mid-game? → Enable crafting sooner
- Stuck on floor 10? → Adjust mining vs combat priority

---

## Current Leaderboard (Unofficial)

| Rank | Bot | Max Floor | Avg Floor | Author | Strategy |
|------|-----|-----------|-----------|--------|----------|
| 1 | ??? | ??? | ??? | ??? | ??? |
| 2 | WarriorBot | ~10-15? | ~5? | Default | Aggressive tank |
| 3 | MageBot | ~8-12? | ~4? | Default | Cautious caster |
| 4 | RogueBot | ~8-12? | ~4? | Default | Balanced |
| 5 | HealerBot | ~6-10? | ~3? | Default | Survival-focused |

*Note: No systematic benchmarking done yet. These are estimates. Be the first to establish real records!*

---

## Strategy Ideas

### 🛡️ **Tank Build** (Grimbash the Unstoppable)
```python
combat_config = CombatConfig(
    flee_hp_threshold=0.2,         # Tank damage (flee at 20%)
    aggression_level='aggressive',  # Seek combat
    risk_tolerance='high',          # Take chances
)
mining_config = MiningConfig(
    prefer_rare_ores=True,          # Need good gear fast
    mine_under_threat=False,        # Don't die while mining
)
```
**Philosophy:** Kill everything. Get best gear. Floor 100 or bust.

---

### 🗡️ **Glass Cannon** (High Risk, High Reward)
```python
combat_config = CombatConfig(
    flee_hp_threshold=0.4,          # Run early (glass cannon)
    aggression_level='aggressive',  # Attack when healthy
    risk_tolerance='medium',        # Not suicidal
)
mining_config = MiningConfig(
    min_purity_threshold=80,        # ONLY best ore (jackpots)
    prefer_rare_ores=True,          # Adamantite or nothing
)
```
**Philosophy:** Best gear wins. Avoid combat until equipped. Then dominate.

---

### ⛏️ **Miner Build** (Crafting First)
```python
combat_config = CombatConfig(
    flee_hp_threshold=0.5,          # Very cautious
    aggression_level='passive',     # Avoid fights
    risk_tolerance='low',           # Safety first
)
mining_config = MiningConfig(
    min_purity_threshold=50,        # Mine everything
    prefer_rare_ores=False,         # Quantity over quality
    mine_under_threat=True,         # Take risks for ore
)
```
**Philosophy:** Clear enemies → Mine everything → Craft constantly → Become unstoppable

---

### 🏃 **Speed Runner** (Descend ASAP)
```python
combat_config = CombatConfig(
    flee_hp_threshold=0.6,          # Run from everything
    aggression_level='passive',     # Only fight if cornered
    risk_tolerance='low',           # Speed > combat
)
mining_config = MiningConfig(
    prefer_rare_ores=False,         # No mining (too slow)
    mine_under_threat=False,        # Never mine
)
# Custom: Override to prioritize finding stairs
```
**Philosophy:** Skip content. Rush to floor 100. Minimal combat. Survive on luck.

---

### 🧠 **Completionist** (Clear Every Floor)
```python
combat_config = CombatConfig(
    flee_hp_threshold=0.3,          # Balanced caution
    aggression_level='balanced',    # Fight strategically
    risk_tolerance='medium',        # Calculated risks
)
mining_config = MiningConfig(
    min_purity_threshold=60,        # Good ore only
    prefer_rare_ores=True,          # Quality matters
)
# Custom: Clear all monsters before descending
```
**Philosophy:** Max XP. Max equipment. Overleveled = easier deep floors.

---

## Advanced Techniques

### Custom Perception
Override `perception` to add custom world analysis:

```python
class MyBot(VeinbornBot):
    def find_valuable_targets(self, game):
        """Custom: Find high-value ore OR weak monsters."""
        valuable_ore = self.perception.find_jackpot_ore(game)
        if valuable_ore:
            return ('mine', valuable_ore)

        # Target weak monsters for safe XP
        monsters = self.perception.find_monsters(game)
        for m in monsters:
            threat = self.get_monster_threat_level(m)
            if threat == 'trivial':
                return ('attack', m)

        return None
```

### Custom Tactics
Override `tactical_decision_service` for complex decisions:

```python
from fuzz.services.tactical_decision_service import TacticalDecisionService

class CustomTactics(TacticalDecisionService):
    def should_fight(self, game, monster):
        """Fight only if we have good equipment."""
        player = game.state.player

        # Must have crafted weapon
        if not hasattr(player, 'equipped_weapon'):
            return False

        weapon = player.equipped_weapon
        if not weapon or weapon.get_stat('attack_bonus', 0) < 5:
            return False  # Weapon too weak

        # Default threat assessment
        return super().should_fight(game, monster)
```

### Custom Action Planning
Override `action_planner` for strategic sequences:

```python
class MyBot(VeinbornBot):
    def custom_plan(self, game):
        """Multi-turn strategy: Find forge, craft, THEN descend."""
        player = game.state.player

        # Phase 1: Get ore
        if not self.has_ore_inventory(game):
            return self.planner.plan_mining_action(game)

        # Phase 2: Find forge
        forge = self.perception.find_nearest_forge(game)
        if forge and not self.at_forge(game):
            return self.planner.move_towards(game, forge.x, forge.y)

        # Phase 3: Craft
        if forge and self.has_ore_inventory(game):
            return ('craft', {})

        # Phase 4: Descend
        return self.planner.plan_descent_action(game)
```

---

## Debugging Your Bot

### Verbose Mode (See Every Action)
```bash
python my_bot.py --games 1 -v

# Output:
# Turn 1: Player @ (12,5), HP=20/20, Floor=1
# Turn 2: Moving toward monster @ (15,7)
# Turn 3: Attacking goblin (HP: 6)
# ...
```

### Quick Smoke Test
```bash
# Test 10 games, max 50 turns each (fast iteration)
python my_bot.py --games 10 --max-turns 50
```

### Profiling Performance
```bash
# Find bottlenecks in your bot
python profile_bot.py
```

---

## Submission Guidelines (Future)

**TODO: Implement leaderboard system**

Once leaderboard is live:

```bash
# Submit your bot run to official leaderboard
python my_bot.py --games 100 --record

# View rankings
python tests/fuzz/show_leaderboard.py
```

**For now:** Share your results in project discussions!

---

## Prizes & Recognition

### 🥇 First Bot to Floor 50
- **Prize:** Hall of Fame entry in `docs/development/HALL_OF_FAME.md`
- **Recognition:** Strategy documented as reference
- **Bragging rights:** "Pioneer of the Deep"

### 🥇 First Bot to Floor 100 (Victory!)
- **Prize:** Bot immortalized in game credits
- **Recognition:** Strategy analysis published
- **Legendary status:** "Conqueror of Veinborn"
- **Name in code:** Your bot's name added to game lore

### 🥈 Most Creative Strategy
- **Prize:** Featured in `docs/development/CREATIVE_STRATEGIES.md`
- **Recognition:** Showcase your innovative approach
- **Example:** "First bot to win without combat" or "Mining-only speedrun"

### 🥉 Best Average Floor (100 games)
- **Prize:** "Most Consistent" award
- **Recognition:** Reliable strategy documentation
- **Metric:** Avg floor reached over 100 games

---

## Resources

### Existing Bots (Study These)
- `tests/fuzz/veinborn_bot.py` - Base bot (896 lines, well-commented)
- `tests/fuzz/warrior_bot.py` - Aggressive melee example
- `tests/fuzz/mage_bot.py` - Cautious caster example
- `tests/fuzz/rogue_bot.py` - Balanced example
- `tests/fuzz/healer_bot.py` - Survival example

### Services (Extend These)
- `tests/fuzz/services/perception_service.py` - World analysis
- `tests/fuzz/services/tactical_decision_service.py` - Combat/mining decisions
- `tests/fuzz/services/action_planner.py` - Action sequencing

### Documentation
- `tests/fuzz/README.md` - Bot system overview
- `docs/development/BOT_SYSTEM_ANALYSIS.md` - Technical deep dive
- `docs/development/BOT_CREATION_GUIDE.md` - *(TODO: Create this)*

### Game Balance
- `data/balance/game_constants.yaml` - Core game rules
- `data/balance/monster_spawns.yaml` - Enemy difficulty curves
- `data/balance/formulas.yaml` - Combat/crafting formulas
- `docs/development/BALANCE_REVIEW.md` - Pre-validated balance concerns

---

## Tips for Success

### 1. Start with a Copy
Don't modify existing bots. Copy and customize.

### 2. Iterate Quickly
Run 10-50 games frequently. Don't wait for 100-game runs to tune.

### 3. Focus on One Thing
Master combat OR mining OR speed. Don't try to optimize everything at once.

### 4. Study the Numbers
- Floor 1-5: Easy (goblins)
- Floor 6-10: Hard (trolls appear, need equipment)
- Floor 11-15: Very hard (elite monsters, better gear required)
- Floor 16+: Unknown territory (nobody has data yet!)

### 5. Test Edge Cases
What happens if:
- No ore veins on floor 1-3? (very rare but possible)
- Troll on floor 6 with no equipment? (fatal without flee strategy)
- Mining interrupted 5 times in a row? (stuck detection triggers)

### 6. Watch for Patterns
If your bot dies the same way repeatedly (e.g., "Troll on floor 7"), that's the bottleneck to fix.

### 7. Balance Safety vs Speed
- Too cautious? → Waste turns healing, slow progression
- Too aggressive? → Early death, never reach deep floors

### 8. Crafting Wins Games
From `BALANCE_REVIEW.md`: Trolls are unbeatable at level 1 without gear. Prioritize crafting!

---

## FAQ

### Q: How many games should I run?
**A:** 10 for quick tests, 100 for benchmarking, 1000+ for leaderboard submission.

### Q: What's a good max floor for a first attempt?
**A:** Floor 10+ is solid. Floor 20+ is excellent. Floor 50+ is legendary.

### Q: Can I use machine learning?
**A:** Yes! RL-trained bots are encouraged (advanced project). See Phase 3 in BOT_SYSTEM_ANALYSIS.md.

### Q: How fast do bots run?
**A:** 100-300 games/second. 100 games = ~0.5-1 second.

### Q: Can bots cheat (see all monsters, ore purity, etc.)?
**A:** Bots currently have "perfect information" (know monster stats, ore purity before surveying). This is intentional for testing. Future: Add "fog of war" mode for fair competition.

### Q: Can I share my bot code?
**A:** Yes! Open source. Share strategies, learn from each other.

### Q: What if I find a bug in the game?
**A:** Report it! Bots are QA tools too. File an issue on GitHub.

---

## The Challenge Awaits

**Floor 100 has never been reached.**

**Will your bot be the first?**

```bash
# Start now:
# cp tests/fuzz/templates/custom_bot_template.py my_conquest.py
# python my_conquest.py --games 100

# Good luck, challenger! 🏆
```

---

## Updates & Announcements

**2026-01-08:** Challenge announced! No official records yet.

**TODO:** Implement leaderboard system (4-6 hours)

**TODO:** Create bot template (2 hours)

**TODO:** First victory celebration plan

---

**May your bots reach the depths no human has seen. 🎮**

**Questions?** Open an issue or discussion on GitHub.

**Ready?** Copy a bot, tune it, run it, conquer it.
