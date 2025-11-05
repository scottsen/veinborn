# Brogue Multiplayer Turn System

**Date:** 2025-10-21
**Session:** icy-temple-1021
**Core Question:** How do turns work with 4 players?

---

## ❌ What WON'T Work: Round-Robin

**The nightmare scenario:**
```
Turn 1: Warrior moves
   (Mage waits... Rogue waits... Healer waits...)
Turn 2: Mage moves
   (Rogue waits... Healer waits... Warrior waits...)
Turn 3: Rogue moves
   (Healer waits... Warrior waits... Mage waits...)
Turn 4: Healer moves
   (Everyone waits...)
Turn 5: MONSTERS move
   (Everyone waits...)

Repeat forever → BORING! 💀
```

**Why it sucks:**
- 75% of the time you're waiting
- Kills the flow
- Feels like multiplayer chess (slow)
- People get impatient, make bad moves just to not hold up party

**Verdict:** HELL NO! ❌

---

## ✅ Solution 1: Simultaneous Turns (MASH FAST!)

**User's insight: "a player move is a player move... the end. turns is turns bitches. mash fast."**

### How It Works

**Everyone acts ASAP, turns resolve in order received:**

```
Tick 1: Warrior presses 'h' → Move action queued
        Mage presses 'f' → Fireball queued
        Rogue presses 'k' → Move queued
        Healer waiting... thinking...

Server processes:
  1. Warrior moves (received first)
  2. Mage fireballs (received second)
  3. Rogue moves (received third)
  4. Healer hasn't acted → waits

Tick 2: Healer presses 'h' → Heal action queued
        Warrior presses 'h' again → Move queued
        Mage waiting (thinking about next spell)
        Rogue presses 's' → Stealth queued

Server processes:
  1. Healer heals
  2. Warrior moves
  3. Rogue goes invisible
  4. Mage hasn't acted → waits

After all 4 players have acted this "round":
  → Monsters take their turns
  → Repeat
```

### The Flow

**Fast players get to act more:**
```
Skilled player: Mashes keys quickly → Acts 10 times/minute
Slow player: Thinks carefully → Acts 5 times/minute

Both valid strategies!
  - Fast = aggressive, risky
  - Slow = tactical, careful
```

**Natural coordination emerges:**
```
[Red] Warrior: (sees goblin, immediately attacks)
[Yellow] Healer: "Wait I was gonna buff you!"
[Red] Warrior: "Too late! Already hit him!"
[Blue] Mage: "I'll finish him" (fireballs instantly)
```

### Monster Turns

**Option A: After Each Player Action**
```
Warrior moves → Monsters move
Mage attacks → Monsters move
Rogue moves → Monsters move
Healer heals → Monsters move

Pros: True turn-based (1 action = 1 turn)
Cons: Monsters move A LOT (4x as often as single-player)
```

**Option B: After All 4 Players Act (Recommended)**
```
Round 1:
  Warrior moves
  Mage attacks
  Rogue moves
  Healer heals
  → NOW monsters take their turns (all of them)

Round 2:
  (players act again...)
  → Monsters act

Pros: Maintains single-player turn ratio
Cons: Not "pure" turn-based (4 actions before monster response)
```

**Option C: Hybrid - Monster "Speed"**
```
Fast monsters (rats, goblins):
  → Act after every 2 player actions

Medium monsters (orcs, trolls):
  → Act after every 4 player actions (1 round)

Slow monsters (golems, bosses):
  → Act after every 6 player actions

Pros: Adds variety, feels dynamic
Cons: More complex to balance
```

### Advantages

✅ **No waiting** - Mash as fast as you want
✅ **Maintains roguelike feel** - Each keypress = meaningful action
✅ **Skill expression** - Fast players act more, slow players think more
✅ **Natural urgency** - "Act before monsters do!"
✅ **Coordination through chaos** - Organized teams do better

### Disadvantages

❌ **Can't plan carefully** - Someone might act before you
❌ **Healer might be too slow** - "I'm trying to heal you!"
❌ **Accidental actions** - Mash too fast, make mistakes

---

## ✅ Solution 2: Action Queue System

**Slight refinement: Let players queue actions during a "planning phase"**

### How It Works

```
PLANNING PHASE (2 seconds):
  Warrior: Queues "Move north"
  Mage: Queues "Fireball goblin"
  Rogue: Queues "Move west"
  Healer: Queues "Heal warrior"

  UI shows queued actions:
    [Red] → ↑
    [Blue] → 🔥 Goblin
    [Green] → ←
    [Yellow] → ✚ Red

EXECUTION PHASE (instant):
  All actions resolve simultaneously
  Monsters react
  Repeat

Optional: Can change action during planning phase
```

### Advantages

✅ **Coordination window** - See what allies plan to do
✅ **Less chaotic** - Can plan synergies
✅ **Still fast-paced** - 2 second rounds
✅ **Can adjust** - "Wait, I'll heal, you attack instead!"

### Disadvantages

❌ **Less roguelike** - Feels more "tactics game"
❌ **Rhythm disruption** - Waiting 2 seconds between actions

---

## ✅ Solution 3: Boss Fight Tactical Mode

**User's idea: "maybe critical battles let you do that?"**

### Normal Exploration: MASH FAST MODE

```
Exploring dungeon, fighting normal monsters:
  → Simultaneous turns (mash fast!)
  → Fast-paced, exciting
  → Mistakes happen, that's OK
```

### Boss Fights: TACTICAL MODE

```
Boss room entered → UI announces:
  "TACTICAL MODE ACTIVATED"

Now:
  → Turn-based with planning
  → Can see party's queued actions
  → Discuss strategy in chat
  → When everyone ready, actions execute
  → Boss acts
  → Repeat

Alternative: Pause is available
  → Any player can hit SPACE to pause
  → Discuss in chat
  → Resume when ready
```

### Best of Both Worlds

**Fast dungeon crawling:**
- Mash keys, kill goblins
- Fast and fun
- Mistakes punish you (roguelike!)

**Strategic boss fights:**
- Slow down, think
- Coordinate abilities
- Plan 2-3 moves ahead
- "Warrior tanks, Mage nukes adds, Rogue backstabs, Healer keeps us up"

---

## 🎮 Recommended: Hybrid System

**Combine mash-fast + tactical mode + pause option:**

### Default Mode: Mash Fast (Simultaneous Turns)

```python
class TurnSystem:
    def __init__(self):
        self.action_queue = []  # Actions this round
        self.round_count = 0

    def submit_action(self, player_id: str, action: Action):
        """Player submits action instantly"""
        self.action_queue.append((player_id, action))

        # Process immediately (first-come, first-served)
        self.process_action(player_id, action)

    def process_action(self, player_id: str, action: Action):
        """Execute player action immediately"""
        result = self.game_state.execute(player_id, action)

        # Check if all players have acted this round
        if len(self.action_queue) >= 4:
            self.monster_turn()
            self.action_queue = []
            self.round_count += 1

    def monster_turn(self):
        """All monsters take their turns"""
        for monster in self.game_state.monsters:
            monster.take_turn()
```

**Flow:**
- Player presses key → Action executes immediately
- After 4 player actions → Monsters act
- Repeat

**Feel:** Fast, chaotic, exciting!

### Boss Fight Mode: Tactical

```python
class BossFightMode:
    def __init__(self):
        self.queued_actions = {}  # {player_id: action}
        self.planning_phase = True

    def submit_action(self, player_id: str, action: Action):
        """Queue action during planning"""
        self.queued_actions[player_id] = action

        # Show in UI: "Yellow has queued: Heal Red"

        if len(self.queued_actions) == 4:
            # All players ready
            self.execute_round()

    def execute_round(self):
        """Execute all queued actions simultaneously"""
        # Resolve in priority order (buffs, then attacks, then heals)
        for action in self.sort_by_priority(self.queued_actions):
            self.game_state.execute(action)

        # Boss acts
        self.boss.take_turn()

        # Reset for next round
        self.queued_actions = {}
```

**Flow:**
- Planning phase: Queue actions, see allies' plans
- Execute: All actions resolve simultaneously
- Boss reacts
- Repeat

**Feel:** Strategic, coordinated, intense!

### Pause Anytime (Safety Valve)

```python
class PauseSystem:
    def __init__(self):
        self.paused = False

    def toggle_pause(self, player_id: str):
        """Any player can pause"""
        self.paused = not self.paused

        if self.paused:
            self.broadcast(f"{player_id} paused the game")
            # Chat still works
            # Can discuss strategy
        else:
            self.broadcast(f"{player_id} resumed the game")
```

**Use cases:**
- "Wait, I need to check my inventory!"
- "Hold on, phone ringing"
- "Let me read the ore stats"
- "Strategy discussion before pulling boss"

---

## 🎯 Strategic Turn Allocation (The Hidden Depth!)

**User's insight: "the team can let the healer take all 4 turns, or ... they can have fun trying to race over and stab easy mobs!"**

### The Core Mechanic

**4 actions per round, ANY player can take ANY number of them:**

```
Round can be:
  - 1 player takes all 4 actions
  - 4 players take 1 action each
  - 2 players take 2 actions each
  - Any combination!

No rules about who acts when.
First-come, first-served.
```

**This simple rule creates MASSIVE strategic depth!**

---

### Scenario 1: Healer Emergency (Cooperative)

**Party at critical HP after boss AOE:**

```
[Red] Warrior: 3/20 HP (critical!)
[Blue] Mage: 2/8 HP (one hit from death)
[Green] Rogue: 5/12 HP (low)
[Yellow] Healer: 12/12 HP (full, but low mana)

Team coordination:
  [Red] "Everyone HOLD!"
  [Blue] "Not pressing anything"
  [Green] "Healer, go!"

Healer takes all 4 actions:
  Action 1: Heal Warrior (+8 HP → 11/20)
  Action 2: Heal Mage (+8 HP → 10/8... capped at 8)
  Action 3: Heal Rogue (+8 HP → 13/12... capped at 12)
  Action 4: Move to safer position

Monsters act → But party is healthy now!

Next round: Counter-attack with confidence
```

**Strategic elements:**
- Team explicitly defers to healer
- Everyone shows discipline (not pressing keys)
- Healer can multi-heal without interruption
- Coordinated decision-making

---

### Scenario 2: Race for the Kill (Competitive)

**One goblin left, 2 HP remaining:**

```
[Red] Warrior: "MINE!" *MASHES 'h'*
[Blue] Mage: "I GOT IT!" *MASHES 'f'*
[Green] Rogue: "NO, ME!" *MASHES 'k'*
[Yellow] Healer: *watches, amused*

Server receives:
  1. Warrior move (arrived 0.001s)
  2. Rogue move (arrived 0.003s)
  3. Mage fireball (arrived 0.005s)

Warrior gets there first → Kills goblin!
Rogue arrives at empty tile → "Dammit!"
Mage fireball hits nothing → "Wasted mana!"

[Red] "Haha! I got it!"
[Green] "You always do this!"
[Blue] "My finger slipped..."
```

**Strategic elements:**
- Friendly competition
- Speed/reflexes matter
- Risk of wasting actions
- Fun trash talk
- Builds camaraderie

---

### Scenario 3: Mining Operation (Turn Sacrifice)

**Warrior found high-quality ore vein:**

```
[Red] Warrior: "I'm mining this, 4 turns needed"
[Blue] Mage: "We'll cover you"
[Green] Rogue: "I'll watch for monsters"
[Yellow] Healer: "Ready to heal if needed"

Round 1 (Mining Round):
  Warrior action 1: Start mining (1/4)
  Warrior action 2: Mining... (2/4)
  Warrior action 3: Mining... (3/4)
  Warrior action 4: Mining complete! → Ore collected

Monsters act → Attack warrior (can't dodge while mining!)

Round 2 (Cleanup):
  Mage: Kill monster attacking warrior
  Rogue: Move to next area
  Healer: Heal warrior
  Warrior: Check ore stats ("Hardness 95! YES!")
```

**Strategic elements:**
- Team sacrifices round for long-term gain
- Warrior vulnerable while mining
- Team protects mining teammate
- High-risk, high-reward decision

---

### Scenario 4: Rogue Scouting (Specialist Work)

**Entering dangerous unknown area:**

```
[Green] Rogue: "I'll scout ahead, stay back"
[Red] Warrior: "Be careful"
[Yellow] Healer: "Don't get surrounded"

Round 1 (Scout Round):
  Rogue action 1: Activate stealth (invisible)
  Rogue action 2: Move north (into unknown)
  Rogue action 3: Move north (deeper)
  Rogue action 4: Move north (see boss room!)

Monsters act → Can't see invisible rogue (safe)

Round 2 (Report):
  [Green] Rogue: "Boss room ahead! Troll Chieftain + 4 goblin adds"
  [Green] Rogue: "Legacy Ore vein on east wall!"

  Team can now plan strategy before engaging
```

**Strategic elements:**
- Specialist takes whole round
- Class ability enables solo operation
- Information gathering
- Reduced risk through stealth

---

### Scenario 5: Mage Nuke Setup (Positioning)

**Monsters clustered in tight corridor:**

```
[Blue] Mage: "Perfect fireball opportunity, let me set up"
[Red] Warrior: "Take your time"

Round 1 (Setup Round):
  Mage action 1: Move to optimal angle
  Mage action 2: Charge fireball spell
  Mage action 3: FIREBALL! → Hits 5 monsters for 12 damage each!
  Mage action 4: Move back to safety

Monsters act → 3 died from fireball, 2 badly wounded

Round 2 (Cleanup):
  Warrior finishes wounded monster 1
  Rogue finishes wounded monster 2
  Mage: "60 damage in one spell, thank you"
  Healer: "Nice!"
```

**Strategic elements:**
- AOE maximization
- Positioning matters
- One player can take multiple sequential actions
- Payoff for setup time

---

### Scenario 6: Healer Buff Bomb (Combo Stacking)

**Preparing for boss fight:**

```
Party at boss door, full HP, full mana

[Yellow] Healer: "Buff round before we go in?"
[Red] Warrior: "Do it"

Round 1 (Buff Bomb):
  Healer action 1: Blessing on Warrior (+2 defense, 10 turns)
  Healer action 2: Blessing on Mage (+2 defense, 10 turns)
  Healer action 3: Blessing on Rogue (+2 defense, 10 turns)
  Healer action 4: Strength on Warrior (+3 attack, 10 turns)

Monsters act (still outside boss room, safe)

Round 2 (Boss Pull):
  [Red] Warrior: *enters boss room*
  → Has +2 def AND +3 attack!
  → Boss fight with full buffs
```

**Strategic elements:**
- Pre-fight preparation
- Buff stacking
- Duration timers (10 turns = 2-3 boss rounds)
- Resource management (mana spent strategically)

---

### Scenario 7: Speed Looting (Division of Labor)

**After big fight, lots of loot scattered:**

```
[Green] Rogue (fastest player): "I'll loot, you guys heal up"
[Yellow] Healer: "Works for me"

Round 1 (Loot Round):
  Rogue action 1: Move to loot pile 1
  Rogue action 2: Pickup iron ore (H:78)
  Rogue action 3: Move to loot pile 2
  Rogue action 4: Pickup health potion

Round 2 (Recovery Round):
  Healer action 1: Heal Warrior
  Healer action 2: Heal Mage
  Warrior action 3: Drink health potion
  Rogue action 4: Move to loot pile 3 (still looting!)

Efficient division of labor!
```

**Strategic elements:**
- Parallel task execution
- Fast player handles time-sensitive tasks
- Healer can focus on healing
- Optimized action economy

---

### Scenario 8: Panic Mode (Everyone Acts Fast!)

**Ambush! Monsters everywhere!**

```
[Red] Warrior: *MASH MASH MASH* → Attacks nearest
[Blue] Mage: *MASH MASH* → Fireball cluster
[Green] Rogue: *MASH* → Backstab vulnerable target
[Yellow] Healer: *MASH* → Emergency heal on Warrior

Round happens in 2 seconds (chaos!)

Everyone: "WHAT JUST HAPPENED?!"
[Blue] "Did we win?"
[Red] "I think so?"
[Yellow] "Everyone alive?"

Check results: All monsters dead, party at 60% HP
  → Survived through sheer chaos and fast reflexes!
```

**Strategic elements:**
- High-pressure situations
- Reflexes > strategy
- Adrenaline rush
- Natural combat flow

---

### Scenario 9: The Bait Strategy (Coordinated Trap)

**Planning to ambush monster patrol:**

```
[Red] Warrior: "I'll bait them into corridor"
[Blue] Mage: "I'll fireball when grouped"
[Green] Rogue: "I'll backstab from behind"
[Yellow] Healer: "I'll keep Warrior up"

Round 1 (Bait):
  Warrior action 1: Move to monster vision
  Warrior action 2: Move back (monsters follow)
  Warrior action 3: Move to corridor
  Warrior action 4: Ready defensive stance

Monsters act → All move toward Warrior (in corridor now!)

Round 2 (Spring Trap):
  Mage action 1: FIREBALL corridor → Hits all monsters!
  Rogue action 2: Backstab wounded monster
  Healer action 3: Heal Warrior (took damage)
  Warrior action 4: Finish last monster

Perfect execution!
```

**Strategic elements:**
- Multi-round planning
- Coordination across rounds
- Positioning and tactics
- Team synergy

---

### Scenario 10: The Sacrifice Play (Heroic Moment)

**Party fleeing, boss chasing, Warrior at low HP:**

```
[Red] Warrior: "You guys run, I'll hold him off"
[Blue] Mage: "No! We can—"
[Red] Warrior: "GO! I'll respawn!"

Round 1 (Sacrifice):
  Warrior action 1: Taunt boss (forces boss to attack Warrior)
  Warrior action 2: Defensive stance
  Warrior action 3: Block doorway
  Warrior action 4: "Tell my story!"

Other players: Running away (not taking actions)

Monsters act → Boss kills Warrior

Round 2 (Escape):
  [Yellow] Healer: "We have resurrect, we'll get you back!"
  Party continues to safe room
  [Yellow] Uses resurrection ability
  [Red] Warrior: "That was epic!"
```

**Strategic elements:**
- Heroic plays
- Permadeath mitigation (resurrection)
- Emergent storytelling
- Memorable moments

---

## 🎮 Emergent Meta-Strategies

### The Healer Carry

**Strategy:** Let healer take 2-3 actions per round

```
Sustainable dungeon crawling:
  Round 1:
    - 2 DPS actions (kill monsters)
    - 2 Healer actions (heal + buff)

  Round 2:
    - 3 DPS actions (push forward)
    - 1 Healer action (top-off healing)

Result: Slower but safer progression
Good for: Learning, hardcore mode, deep floor attempts
```

### The Speedrun Allocation

**Strategy:** Fastest player dominates actions

```
Optimized for speed:
  Round 1:
    - Warrior (fastest): 3 actions (move move attack)
    - Rogue: 1 action (loot on the way)

  Round 2:
    - Warrior: 2 actions (move attack)
    - Mage: 1 action (kill from range)
    - Rogue: 1 action (loot)

Result: Maximum speed, risky
Good for: Experienced teams, time trials
```

### The Balanced Rotation

**Strategy:** Everyone takes 1 action per round

```
Democratic approach:
  Every round:
    - Warrior: 1 action
    - Mage: 1 action
    - Rogue: 1 action
    - Healer: 1 action

Result: Fair, predictable, coordinated
Good for: Casual play, new teams, learning synergies
```

### The Specialist Rounds

**Strategy:** Rotate who takes majority of actions

```
Role-focused rotation:
  Round 1: Healer round (3 heals + 1 DPS action)
  Round 2: DPS round (3 attacks + 1 support action)
  Round 3: Scout round (Rogue takes 3 moves + 1 DPS action)
  Round 4: Setup round (buffs/positioning)

Result: Each role gets spotlight
Good for: Utilizing all class abilities, complex fights
```

---

## 📊 Strategic Depth Analysis

### What This System Creates

**From one simple rule ("4 actions per round, anyone can take them"):**

✅ **Cooperative Strategy**
- Deferring to specialists
- Turn sacrifice for team benefit
- Coordinated multi-round plans

✅ **Competitive Fun**
- Racing for kills
- Speed contests
- Bragging rights

✅ **Role Specialization**
- Healers can take healing rounds
- Scouts can take scouting rounds
- Tanks can hold all defensive actions

✅ **Skill Expression**
- Fast players can dominate
- Slow players can be deliberate
- Both are viable

✅ **Emergent Gameplay**
- Teams discover optimal patterns
- Meta-strategies develop
- Unique playstyles emerge

✅ **Memorable Moments**
- Heroic sacrifices
- Perfect combos
- Clutch saves
- Epic fails

---

## 🎯 UI Features to Support Strategy

### Turn Allocation Display

```
┌─ ROUND STATUS ─────────────────┐
│ Actions: 2/4                   │
│                                │
│ ✓ [Red] Warrior (acted)        │
│ ✓ [Blue] Mage (acted)          │
│ ○ [Green] Rogue (waiting)      │
│ ○ [Yellow] Healer (waiting)    │
│                                │
│ Next: Monsters act after 2     │
└────────────────────────────────┘
```

### Quick Communication

```
Quick action callouts:
  Ctrl+1: "Taking turn!"
  Ctrl+2: "Passing, you go"
  Ctrl+3: "Need healing!"
  Ctrl+4: "I'll take next round"
  Ctrl+5: "Everyone hold!"
```

### Action History (Last Round)

```
┌─ LAST ROUND ───────────────────┐
│ Round 41:                      │
│   [Red] Move north             │
│   [Red] Attack goblin          │
│   [Blue] Fireball (3 targets)  │
│   [Yellow] Heal Red            │
│ → Monsters acted (2 died)      │
└────────────────────────────────┘
```

### Turn Allocation Stats

```
┌─ ROUND PARTICIPATION ──────────┐
│ Last 10 rounds:                │
│ [Red] ████████ 32 actions      │
│ [Green] ██████ 22 actions      │
│ [Blue] ████ 15 actions         │
│ [Yellow] ██ 11 actions         │
│                                │
│ Warrior dominating (40% share) │
└────────────────────────────────┘
```

---

## 💡 Game Design Insights

### Why This Works

**1. Simple Rule, Complex Outcomes**
- "4 actions per round" is trivial to understand
- But creates infinite strategic possibilities
- Like Go: simple rules, deep game

**2. Supports All Playstyles**
- Competitive players: Race for actions
- Cooperative players: Defer to teammates
- Strategic players: Plan multi-round combos
- Casual players: Just take 1 action per round

**3. Natural Skill Ceiling**
- Beginners: Take 1 action, don't rush
- Intermediate: Learn when to take 2-3 actions
- Advanced: Coordinate complex turn allocations
- Expert: Frame-perfect action sequences

**4. Emergent Teamwork**
- Not enforced by game
- Develops naturally from player coordination
- Creates unique team dynamics
- Different teams play differently

**5. Story Generation**
- "Remember when Warrior mined that ore while we held off the boss?"
- "That time Healer used all 4 turns to save us from a wipe"
- "When we all raced for the last goblin and missed"
- Creates shared memorable moments

---

## 📊 Turn Speed Comparison

### Single-Player Brogue (Traditional)

```
Player action → Monster action → Repeat

Actions per minute: ~30 (deliberate, tactical)
Turn ratio: 1:1 (fair)
```

### Multiplayer Option A: Pure Sequential

```
P1 → M → P2 → M → P3 → M → P4 → M → Repeat

Actions per minute (per player): ~7.5
Turn ratio: 1:4 (monsters act 4x as often!)
Feel: SLOW, monsters overwhelming
```

### Multiplayer Option B: Simultaneous (Recommended)

```
P1, P2, P3, P4 → All monsters → Repeat

Actions per minute (per player): ~30 (same as single-player!)
Turn ratio: 4:N (4 players vs N monsters, scales naturally)
Feel: FAST, exciting, tactical
```

---

## 🎯 Final Recommendation

### Core System: Simultaneous Turns (Mash Fast)

**Rules:**
1. Press key → Action executes immediately
2. After 4 player actions → Monsters act (all of them)
3. Repeat

**Variants:**
- Fast players can act multiple times before slow players
- But monsters act after every 4 total actions (fair ratio)

**Example:**
```
Round 1 (4 actions):
  Warrior moves (action 1)
  Mage attacks (action 2)
  Warrior moves again! (action 3, fast player)
  Healer heals (action 4)
  → Monsters act

Round 2 (4 actions):
  Rogue moves (action 1)
  Warrior moves AGAIN! (action 2, very fast player)
  Mage attacks (action 3)
  Healer moves (action 4)
  → Monsters act
```

**Fast warrior acted 3 times, others acted 1-2 times. Fair? YES!**
- Fast player takes more risks
- More opportunities to make mistakes
- Skill expression

### Boss Fights: Optional Tactical Mode

**Trigger:** Boss room entered, or any player presses 'T'

**Rules:**
1. Planning phase (5 seconds or until all ready)
2. See queued actions: "[Red]→↑ [Blue]→🔥Boss [Green]→Stealth [Yellow]→Heal Red"
3. Can change action during planning
4. All execute simultaneously when ready
5. Boss reacts
6. Repeat

**Feel:** Coordinated, strategic, "let's plan this out"

### Pause: Always Available

**Rules:**
- Any player presses SPACE → Game pauses
- Chat still works (coordinate)
- Resume when ready
- Can't spam (cooldown: 5 seconds)

---

## 💡 Strategic Implications

### Fast Players Have Advantage

**Good at games, fast reflexes:**
- Act 2-3x per round
- More aggressive plays
- Higher risk, higher reward
- "I'm the carry!"

**Slower, methodical players:**
- Act 1x per round
- Think carefully
- Fewer mistakes
- "I'll support you"

**Both styles valid!** Like fighting games: execution vs reads.

### Natural Roles Emerge

**Warrior (Fast):**
- Mash movement keys
- Always at front
- Quick reactions
- "Go go go!"

**Mage (Medium):**
- Aim carefully
- Choose targets
- Moderate pace
- "Let me line up this shot"

**Rogue (Fast):**
- Quick flanking
- Opportunistic
- React to openings
- "I'll circle around!"

**Healer (Slow):**
- Watch health bars
- Deliberate decisions
- Calm under pressure
- "I've got you all in range"

### Coordination Through Chaos

**Early game (learning):**
```
[Red] "Everyone's moving too fast!"
[Blue] "Wait for me!"
[Yellow] "I can't keep up with healing!"
```

**Mid game (coordinating):**
```
[Red] "I'm pulling, get ready"
[Blue] "Fireball charged"
[Yellow] "In position to heal"
[Green] "Flanking now"
```

**Late game (flow state):**
```
(No chat needed, everyone just KNOWS)
Warrior pulls → Mage nukes → Rogue backstabs → Healer tops off
Perfect execution, no words needed
```

---

## 🧪 Testing the System

### Prototype Test

```python
# Simple test with 2 players
def test_simultaneous_turns():
    game = MultiplayerGame()

    # Player 1 acts fast
    game.submit_action("warrior", MoveAction("north"))
    assert game.action_count == 1

    # Player 2 acts
    game.submit_action("mage", AttackAction("goblin"))
    assert game.action_count == 2

    # Player 1 acts AGAIN (fast player)
    game.submit_action("warrior", AttackAction("orc"))
    assert game.action_count == 3

    # Player 2 acts again
    game.submit_action("mage", MoveAction("south"))
    assert game.action_count == 4

    # NOW monsters should act
    assert game.monsters_have_acted == True
    assert game.action_count == 0  # Reset for next round
```

### Balance Testing

**Questions to answer:**
1. Do fast players dominate too much?
2. Do slow players feel left behind?
3. Is healer role viable (reactive, needs time)?
4. Do monsters feel overwhelming or fair?
5. Is tactical mode actually used for bosses?

---

## 🎮 UI Considerations

### Turn Indicator

**Show current "round" and action count:**

```
┌─ TURN INFO ────────────────────┐
│ Round: 42                      │
│ Actions this round: 2/4        │
│                                │
│ Next monster turn after 2 acts │
└────────────────────────────────┘
```

### Action Queue Visualization (Boss Mode)

```
┌─ QUEUED ACTIONS ───────────────┐
│ [Red] Warrior: ↑ (Move north)  │
│ [Blue] Mage: 🔥 Boss           │
│ [Green] Rogue: ⚔️ Boss         │
│ [Yellow] Healer: ? (thinking)  │
│                                │
│ Waiting for Yellow...          │
└────────────────────────────────┘
```

### Speed Feedback

**Show who's acting most/least:**

```
┌─ PARTY ACTIVITY ───────────────┐
│ [Red] Warrior: ████████ 40 APM │
│ [Green] Rogue: ██████ 30 APM   │
│ [Blue] Mage: ████ 20 APM       │
│ [Yellow] Healer: ██ 10 APM     │
└────────────────────────────────┘

APM = Actions Per Minute
```

---

## 🎯 Implementation Notes

### Server-Side

```python
class TurnManager:
    def __init__(self):
        self.actions_this_round = 0
        self.actions_per_round = 4  # For 4 players

    def submit_action(self, player_id: str, action: Action):
        # Validate action
        if not self.is_valid_action(player_id, action):
            return Error("Invalid action")

        # Execute immediately
        result = self.game_state.execute(player_id, action)
        self.actions_this_round += 1

        # Broadcast to all clients
        self.broadcast_state_update()

        # Check for monster turn
        if self.actions_this_round >= self.actions_per_round:
            self.monster_turn()
            self.actions_this_round = 0

        return result

    def monster_turn(self):
        for monster in self.game_state.monsters:
            monster.ai_take_turn()
        self.broadcast_state_update()
```

### Client-Side

```python
class BrogueClient:
    def handle_keypress(self, key: str):
        # Convert key to action
        action = self.parse_key(key)

        # Send to server immediately (no queuing)
        await self.ws.send(json.dumps(action))

        # Optional: Show "action pending" indicator
        self.ui.show_pending_action(action)

    async def receive_state_update(self, state: GameState):
        # Render new state
        self.ui.render(state)

        # Clear pending indicator
        self.ui.clear_pending_action()
```

---

## ✅ Decision: Simultaneous Turns + Boss Tactical Mode

**Default:** Mash fast, actions execute immediately
**Boss fights:** Optional tactical mode with planning phase
**Safety valve:** Pause available anytime

**Why this works:**
- ✅ Keeps roguelike feel (action = turn)
- ✅ No waiting around (boring)
- ✅ Fast-paced and exciting
- ✅ Skill expression (fast vs deliberate)
- ✅ Coordination emerges naturally
- ✅ Bosses can be strategic
- ✅ Flexible (pause if needed)

**User was right:** "turns is turns bitches. mash fast." 🎮

Let's build THIS system!
