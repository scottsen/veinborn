# Veinborn Bot Creation Guide

**Status:** 🚧 **OUTLINE** - Full guide TODO (2-3 hours to complete)
**Purpose:** Teach bot creation from beginner to advanced
**Audience:** Anyone who can copy/paste Python code

---

## Quick Links

- **[Bot Challenge](BOT_CHALLENGE.md)** - The Floor 100 challenge
- **[Bot System Analysis](BOT_SYSTEM_ANALYSIS.md)** - Technical deep dive
- **[Fuzz Testing README](../../tests/fuzz/README.md)** - Bot infrastructure overview

---

## Table of Contents (Planned)

### Part 1: Getting Started (30 minutes)
1. **Your First Bot** - Copy template, run it, see results
2. **Understanding the Output** - What the metrics mean
3. **Quick Tuning** - Change 2 numbers, see 2x improvement
4. **Challenge: Reach Floor 10**

### Part 2: Configuration (1 hour)
5. **CombatConfig Deep Dive** - flee_hp_threshold, aggression, risk
6. **MiningConfig Deep Dive** - purity thresholds, ore preferences
7. **Character Classes** - Warrior, Mage, Rogue, Healer differences
8. **Challenge: Beat WarriorBot**

### Part 3: Architecture (2 hours)
9. **Service Layer Overview** - Perception, Tactics, Planning
10. **Perception Service** - Finding monsters, ore, forges
11. **Tactical Service** - Combat decisions, mining strategy
12. **Action Planner** - Strategic action sequences
13. **Challenge: Custom perception method**

### Part 4: Advanced Customization (3 hours)
14. **Override Perception** - Custom world analysis
15. **Override Tactics** - Complex decision trees
16. **Override Planning** - Multi-turn strategies
17. **State Machine Bots** - Phase-based gameplay (explore → equip → conquer)
18. **Challenge: Implement "Miner Build" strategy**

### Part 5: Optimization (2 hours)
19. **Profiling Your Bot** - Find performance bottlenecks
20. **Data Analysis** - Using bot_results_*.json
21. **A/B Testing Configs** - Statistical comparison
22. **Challenge: Improve avg floor by 20%**

### Part 6: Advanced Topics (4+ hours)
23. **Machine Learning Bots** - RL integration basics
24. **Genetic Algorithms** - Evolving configurations
25. **Bot Tournaments** - Bracket play
26. **Challenge: First bot to floor 50**

---

## Part 1: Getting Started (DRAFT)

### Your First Bot (10 minutes)

**TODO: Create template first**

```bash
# 1. Copy the template
cd /home/scottsen/src/projects/veinborn
cp tests/fuzz/templates/custom_bot_template.py my_first_bot.py

# 2. Run it (no changes needed yet)
python my_first_bot.py --games 10

# Output:
# Max Floor Reached: 5
# Avg Turns/Game: 123.4
# Crashes: 0
```

**Congratulations!** You just ran your first bot.

---

### Understanding the Output

```
Games Played: 10
Games Completed: 8
Crashes: 0 (0.0%)
Errors: 0

Total Turns: 1234
Avg Turns/Game: 123.4     ← How long you survive
Max Turns Survived: 247   ← Best single run
Max Level Reached: 2      ← Highest player level
Max Floor Reached: 5      ← MOST IMPORTANT (goal: 100)
```

**Key Metrics:**
- **Max Floor Reached**: Your bot's best performance
- **Avg Turns/Game**: How consistent your bot is
- **Crashes/Errors**: Game bugs (report these!)

**Goal:** Increase Max Floor Reached

---

### Quick Tuning: The Magic Number

Open `my_first_bot.py` and find this line:

```python
flee_hp_threshold=0.3,  # Flee at 30% HP
```

**Experiment:**

| Value | Behavior | Result |
|-------|----------|--------|
| `0.2` | Brave (flee at 20%) | More XP, riskier, dies in combat |
| `0.3` | Balanced (flee at 30%) | Good default |
| `0.4` | Cautious (flee at 40%) | Safer, survives longer |
| `0.5` | Very cautious (flee at 50%) | Runs from everything, slow progress |

**Try it:**
```bash
# Change to 0.4, save file, run again
python my_first_bot.py --games 10

# Did Max Floor improve?
```

**Challenge:** Find the optimal flee_hp_threshold for floors 1-10.

---

## Part 2: Configuration (TODO)

### CombatConfig Parameters (TODO)

```python
CombatConfig(
    flee_hp_threshold=0.3,        # When to run (0.2-0.5)
    aggression_level='balanced',  # How to fight ('passive'/'balanced'/'aggressive')
    risk_tolerance='medium',      # Risk appetite ('low'/'medium'/'high')
)
```

**TODO:** Explain each parameter with examples

---

### MiningConfig Parameters (TODO)

```python
MiningConfig(
    min_purity_threshold=60,      # Only mine 60+ purity (0-100)
    prefer_rare_ores=True,        # Prioritize mithril/adamantite
    mine_under_threat=False,      # Mine even if monsters nearby
)
```

**TODO:** Explain mining strategy trade-offs

---

## Part 3: Architecture (TODO)

### The Three Services (TODO)

**1. PerceptionService** - "What do I see?"
- Find monsters, ore, forges, stairs
- Calculate distances, threats
- Cache results for performance

**2. TacticalDecisionService** - "What should I do?"
- Fight or flee?
- Mine or craft?
- Descend or explore?

**3. ActionPlanner** - "How do I do it?"
- Move toward target
- Execute action sequence
- Handle stuck states

**TODO:** Code examples, override patterns

---

## Part 4: Advanced Customization (TODO)

### Custom Perception Example (TODO)

```python
class MyBot(VeinbornBot):
    def find_best_target(self, game):
        """Custom: Prioritize weak monsters OR jackpot ore."""
        # TODO: Explain implementation
        pass
```

---

### Custom Tactics Example (TODO)

```python
class CustomTactics(TacticalDecisionService):
    def should_fight(self, game, monster):
        """Only fight if we have weapon."""
        # TODO: Explain implementation
        pass
```

---

## Part 5: Optimization (TODO)

### Using Profiler (TODO)

```bash
python profile_bot.py
# Shows performance hotspots
```

---

### Analyzing Results (TODO)

```bash
# TODO: Create this tool first
python tests/fuzz/analyze_bot_results.py logs/bot_results_*.json
```

---

## Part 6: Advanced Topics (TODO)

### Machine Learning Integration (TODO)

**Placeholder:** Reinforcement learning (DQN/PPO) basics

---

### Genetic Algorithms (TODO)

**Placeholder:** Evolving bot configurations

---

## Quick Reference

### Running Bots

```bash
# Quick test (10 games)
python my_bot.py --games 10

# Benchmark (100 games)
python my_bot.py --games 100

# Stress test (1000 games)
python my_bot.py --games 1000

# Verbose mode (see actions)
python my_bot.py --games 1 -v

# Debug mode (full trace)
python my_bot.py --games 1 --debug
```

### Config Templates

```python
# TANK BUILD
CombatConfig(flee_hp_threshold=0.2, aggression_level='aggressive', risk_tolerance='high')

# GLASS CANNON
CombatConfig(flee_hp_threshold=0.4, aggression_level='aggressive', risk_tolerance='medium')

# SURVIVOR
CombatConfig(flee_hp_threshold=0.5, aggression_level='passive', risk_tolerance='low')
```

---

## Examples to Study

**Existing Bots (Good Starting Points):**
- `tests/fuzz/warrior_bot.py` - Aggressive tank
- `tests/fuzz/mage_bot.py` - Cautious caster
- `tests/fuzz/rogue_bot.py` - Balanced
- `tests/fuzz/healer_bot.py` - Survival-focused

**Copy one of these, rename it, tune it, and make it yours!**

---

## TODO: Complete This Guide

**Sections to write:**
- [ ] Part 2: Configuration deep dives
- [ ] Part 3: Architecture explanations with code examples
- [ ] Part 4: Advanced customization patterns
- [ ] Part 5: Optimization techniques
- [ ] Part 6: ML/GA integration guides
- [ ] Screenshots/ASCII output examples
- [ ] Common pitfalls section
- [ ] Troubleshooting guide

**Estimated time:** 2-3 hours to complete all sections

**Dependencies:**
- Bot template must exist first (2 hours to create)
- Leaderboard for submission examples (4-6 hours)
- Analytics tool for optimization section (3-4 hours)

---

## Contributing

Found this guide helpful? Want to contribute examples?

- Add your successful strategy to BOT_CHALLENGE.md
- Share interesting bot behaviors
- Report bugs in existing bots
- Suggest improvements to this guide

---

**Status:** This is an outline. Full guide coming after bot template creation.

**For now:** Study `tests/fuzz/veinborn_bot.py` (896 lines, well-commented) and copy an existing bot to start.
