# MUD Player Content Creation & Scripting

**Date:** 2025-10-21
**Session:** icy-temple-1021
**Question:** "What do MUDs typically offer? Is there player created content and scripts? How does all that magic work?"

---

## 🎮 What MUDs Typically Offer

### Core MUD Features (Standard Across Most MUDs)

**1. Combat & Progression**
- Classes/races with unique abilities
- Leveling system (XP-based or skill-based)
- Equipment with stats
- Spell/ability systems
- Combat mechanics (turn-based or real-time)

**2. Social Systems**
- Chat channels (global, guild, whisper)
- Guilds/clans with ranks
- Player groups/parties
- Emotes and roleplay commands
- Mail systems (send messages to offline players)

**3. Economy**
- Currency (gold, credits, etc.)
- Player shops
- Auction systems
- Crafting (varies widely)
- Trading between players

**4. World**
- Rooms/areas connected by exits
- NPCs (monsters, shopkeepers, quest givers)
- Quests and storylines
- Exploration and secrets

**5. Character Customization**
- Description (appearance)
- Equipment (visible to others)
- Skills/abilities (class-based)
- Stats (strength, intelligence, etc.)

---

## 🛠️ Player-Created Content (THE COOL PART!)

### Level 1: Basic Player Housing

**Most MUDs have this:**

```
Player buys/earns a house
Can:
  - Set room descriptions
  - Place furniture (from templates)
  - Store items
  - Invite friends
  - Customize basic appearance

Example (Achaea):
  > buy house
  > enter house
  > describe room "A cozy study filled with ancient tomes"
  > place armchair
  > place bookshelf
```

**Limited but fun:** Not full content creation, more like customization

---

### Level 2: Builder Systems (Restricted Access)

**Some MUDs give trusted players "Builder" access:**

**Aardwolf, Achaea, etc.:**
- Builders are vetted volunteers
- Get access to building commands
- Can create new areas (zones)
- Design quests
- Create NPCs with behaviors
- Set up loot tables

**Building commands:**
```
> dig north "Forest Path"
  Creates new room to the north

> create mob goblin
  name: "a snarling goblin"
  description: "A small, vicious creature"
  level: 5
  HP: 30
  attacks: ["slash", "bite"]

> create object sword
  name: "iron longsword"
  damage: 10
  weight: 5
  value: 100

> link quest "Goblin Hunt"
  trigger: kill 10 goblins
  reward: 500 XP, iron sword
```

**Review process:**
- Builders submit areas to admins
- Admins review for balance/quality
- Approved areas go live

**This is how MUDs get 10,000+ rooms without paid staff!**

---

### Level 3: In-Game Scripting (THE MAGIC!)

**Some MUDs let players PROGRAM content in-game!**

### LPMud: LPC Language

**LPMud codebase uses LPC (Lars Pensjö C):**

Players with wizard access can:
- Write code directly in-game
- Create objects, rooms, NPCs
- Define behaviors and interactions
- No compilation needed (interpreted)

**Example LPC code (in-game):**

```lpc
// Create a magic sword object
void create() {
    set_name("sword");
    set_id(({"sword", "magic sword", "excalibur"}));
    set_short("Excalibur, the legendary sword");
    set_long("A shimmering blade of immense power.");

    set_type("sword");
    set_wc(15);  // Weapon class (damage)
    set_ac(2);   // Armor class (defense bonus)

    set_hit_func((:hit_func:));  // Custom hit function
}

int hit_func(object target) {
    if(random(100) < 10) {  // 10% chance
        tell_room(environment(),
            "Excalibur glows brightly!");
        target->do_damage(50);  // Bonus damage
        return 1;
    }
    return 0;
}
```

**Yes, that's code players write IN THE GAME!**

### MOO: Object-Oriented MUD

**MOO (MUD Object-Oriented) - Even more powerful:**

**Players can:**
- Create objects that inherit from templates
- Write verbs (commands) on objects
- Define properties and behaviors
- Full programming language (MOO code)

**Example MOO code:**

```moo
// Create a talking parrot object
@create $thing named Parrot

@verb Parrot:talk this none none
@program Parrot:talk
  player:tell("The parrot squawks: '",
              this.phrases[random(length(this.phrases))],
              "'");
.

@property Parrot.phrases {}
;;Parrot.phrases = {"Hello!", "Pieces of eight!", "Squawk!"}

// Now "talk parrot" triggers the verb!
```

**LambdaMOO (famous MOO):**
- Hosted at Xerox PARC
- Players built entire virtual world
- Thousands of player-created rooms
- Complex interactive objects
- Social experiments in virtual spaces

---

### Level 4: Softcode (MUSH/MUX)

**MUSH/MUX systems have "softcode":**

**Softcode is a scripting language for building:**

```
@create Object=My Magic Door
@lock My Magic Door=has_key
@desc My Magic Door=A sturdy oak door with runes.
@success My Magic Door=You unlock the door with your key.
@fail My Magic Door=The door is locked tight.
@ofail My Magic Door=%N tries to open the door but it's locked.

// Conditionals and functions
&cmd-open My Magic Door=$open door:
  @switch hasattr(%#,key)=
    1,{@emit The door swings open!;@tel %#=Next Room},
    {@emit You don't have the key!}
```

**Softcode features:**
- Variables and attributes
- Conditionals (@switch)
- Functions (hasattr, etc.)
- Event triggers
- Player-built without server code access

---

## 🏗️ How The Magic Works (Architecture)

### Traditional MUD Architecture

```
┌─────────────────────────────────────┐
│         MUD Server                  │
│                                     │
│  ┌──────────────────────────┐      │
│  │  Core Engine (C/C++)     │      │
│  │  - Combat system         │      │
│  │  - Movement              │      │
│  │  - Command parser        │      │
│  └──────────────────────────┘      │
│              ↑                      │
│  ┌──────────────────────────┐      │
│  │  Script Interpreter      │      │
│  │  - LPC, MOO, Softcode    │      │
│  │  - Sandboxed execution   │      │
│  └──────────────────────────┘      │
│              ↑                      │
│  ┌──────────────────────────┐      │
│  │  World Database          │      │
│  │  - Rooms (with scripts)  │      │
│  │  - Objects (with code)   │      │
│  │  - NPCs (with AI)        │      │
│  └──────────────────────────┘      │
└─────────────────────────────────────┘
```

### How Player Scripting Works

**1. Sandboxed Execution**

```c
// Server code (C)
void execute_player_script(char *script_code, player *p) {
    // Create sandbox environment
    sandbox *env = create_sandbox();

    // Limit resources
    env->max_cpu_time = 100ms;  // Prevent infinite loops
    env->max_memory = 10MB;     // Prevent memory bombs
    env->permissions = PLAYER;  // Can't access admin stuff

    // Run script in sandbox
    result = run_script(script_code, env);

    if(result.error) {
        notify_player(p, "Script error: %s", result.error);
    }

    cleanup_sandbox(env);
}
```

**2. Security Model**

**Permissions hierarchy:**
```
GOD (owner)
  ├─ ADMIN (trusted staff)
  │   ├─ WIZARD (can create content)
  │   │   ├─ BUILDER (limited creation)
  │   │   └─ PLAYER (use content)
  │   └─ PLAYER
  └─ PLAYER
```

**What each level can do:**
- **PLAYER:** Use objects, basic commands
- **BUILDER:** Create rooms, simple objects (reviewed)
- **WIZARD:** Full scripting, unrestricted creation
- **ADMIN:** Modify core settings, manage players
- **GOD:** Full server access

**3. Object-Oriented World**

**Everything is an object:**

```
Object #1234: "Magic Sword"
  Parent: Weapon Template (#100)
  Properties:
    name: "Excalibur"
    damage: 15
    special_ability: "flame_strike"

  Code:
    on_hit(target):
      if random() < 0.1:
        target.damage(50)
        room.announce("Excalibur flames!")

    on_equip(player):
      player.strength += 5

    on_unequip(player):
      player.strength -= 5
```

**When player attacks:**
```
1. Combat system calls weapon.on_hit(target)
2. Sword's script executes (sandboxed)
3. Random check for special ability
4. If triggered, extra damage
5. Room notification
6. Return control to combat system
```

**4. Event-Driven Architecture**

**Objects respond to events:**

```
Events:
  - on_create()
  - on_destroy()
  - on_enter(player)
  - on_exit(player)
  - on_look(player)
  - on_use(player)
  - on_attack(attacker, target)
  - on_hit(target)
  - on_timer()  // Periodic updates
```

**Example: Magical fountain**

```lpc
// Fountain object
void on_enter(object player) {
    tell_room(environment(),
        player->query_name() + " enters the fountain room.");
}

void on_use(object player) {
    if(player->query_hp() < player->query_max_hp()) {
        player->heal(10);
        tell_player(player,
            "You drink from the fountain. +10 HP!");

        // Set 1-hour cooldown
        set_property("last_use_" + player->query_name(), time());
    }
    else {
        tell_player(player, "The water has no effect.");
    }
}

// Fountain refills every 10 minutes
void on_timer() {
    // Reset cooldowns older than 1 hour
    cleanup_old_cooldowns();
    call_out("on_timer", 600);  // Schedule next call
}
```

---

## 🎯 Real Examples from Active MUDs

### Achaea's Crafting System

**Players can:**
- Design custom items (clothing, jewelry, weapons)
- Submit designs for approval
- Craft approved designs in-game

**Design submission:**
```
> craft design robe
  Appearance: "a flowing crimson robe"
  Examined: "This elegant robe is crafted from the finest
            silk, dyed a deep crimson. Intricate golden
            runes are embroidered along the hem."

  Material: silk (100 units)
  Skill required: Tailoring 5

> submit design for approval
```

**Admin reviews, approves/rejects**

**Once approved:**
```
> craft "crimson robe" with silk
  You carefully stitch together a flowing crimson robe.
  *crafting sound*
  Success! You have crafted: a flowing crimson robe
```

**Economy:** Players sell custom designs, creating unique items!

---

### Aardwolf's Quest System

**Builders create quests using OLC (Online Creation):**

```
> quest edit 123
  Quest: "The Lost Amulet"

  Trigger: kill "ancient guardian"
  Objectives:
    1. Find lost amulet in tomb
    2. Return amulet to priest

  Rewards:
    - 5000 XP
    - 1000 gold
    - +5 Reputation with Temple
    - Questpoint

  Failure conditions:
    - Amulet destroyed
    - 24 hours elapsed

> quest save
```

**Complex quest chains:**
- Quest A unlocks Quest B
- Branching outcomes
- World state changes (NPC dialogue updates)

---

### MOO Player-Built Spaces

**LambdaMOO (famous example):**

Player creates coffee shop:
```
@dig Coffee Shop
You enter the Coffee Shop.

@describe here as "A cozy coffee shop with mismatched
  furniture and the aroma of fresh espresso. Jazz plays
  softly in the background."

@create $thing named espresso machine
@verb espresso machine:make this with any
@program espresso machine:make
  if(!player:has(coffee beans))
    player:tell("You need coffee beans!");
    return;
  endif

  player:remove_item("coffee beans");
  new_coffee = $recycler:_create($thing);
  new_coffee.name = "fresh espresso";
  new_coffee:moveto(player);
  player:tell("You brew a perfect espresso!");
.

> make espresso with beans
You brew a perfect espresso!
```

**Players built entire social spaces!**

---

## 🔒 Security & Anti-Abuse

### How MUDs Prevent Exploits

**1. Resource Limits**

```c
// Prevent infinite loops
while(condition) {
    ops_executed++;
    if(ops_executed > MAX_OPS) {
        abort_script("Too many operations!");
        break;
    }
    // ... player code ...
}

// Prevent memory bombs
void* allocate_memory(size_t size) {
    if(current_memory + size > MAX_MEMORY) {
        return NULL;  // Allocation fails
    }
    // ... allocate ...
}

// Prevent stack overflow
int call_depth = 0;
void call_function() {
    call_depth++;
    if(call_depth > MAX_DEPTH) {
        abort_script("Stack too deep!");
        return;
    }
    // ... function code ...
    call_depth--;
}
```

**2. Capability-Based Security**

**Objects can only do what they're allowed:**

```lpc
// Player tries to access admin function
if(!has_permission(caller, PERMISSION_ADMIN)) {
    error("Access denied!");
    return;
}

// Can't damage other players directly (unless combat)
void damage_player(object target, int amount) {
    if(!in_combat(this_player(), target)) {
        error("You can't attack them here!");
        return;
    }
    // ... apply damage ...
}

// Can't create items from nothing (unless wizard)
object create_item(string template) {
    if(!is_wizard(this_player())) {
        error("Only wizards can create items!");
        return NULL;
    }
    // ... create item ...
}
```

**3. Review Process**

**Content goes through approval:**
```
Player submits area/quest/item
  ↓
Queue for review
  ↓
Admin/senior builder reviews
  ↓
Approve (goes live) OR Reject (send feedback)
```

**Quality control maintains standards**

---

## 💡 What Could Brogue Adopt?

### Option 1: Simple Player Housing (Easy)

**Players customize personal spaces:**

```
> create house
Your personal dungeon hideout has been created!

> describe hideout "A warrior's training hall with
  weapon racks and practice dummies"

> place forge
You install a personal forge. (Can craft here!)

> place trophy_case
You display your best finds.

> invite Bob
Bob can now visit your hideout.
```

**Limited but fun, easy to implement**

---

### Option 2: Dungeon Templates (Medium)

**Players can customize dungeon generation:**

```
> create dungeon_template "Ore Paradise"
  Ore spawn rate: 200% (costs tokens)
  Monster difficulty: 50% (easier)
  Legacy Ore chance: 5% (slightly higher)
  Theme: Mining-focused

> start dungeon from template "Ore Paradise"
Generating dungeon...
  → Lots of ore spawns!
  → Easier monsters
  → Perfect for ore farming with friends
```

**Meta-currency system:**
- Earn "Dungeon Tokens" from runs
- Spend tokens to customize template
- Tradeoffs (easier = less XP, more ore = more monsters)

---

### Option 3: Scriptable Dungeons (Advanced)

**Python-based dungeon scripting (sandboxed):**

```python
# User-created dungeon script (sandboxed Python)
from brogue import Dungeon, OreVein, Monster, Event

@dungeon_script
def treasure_hunt():
    """A dungeon focused on finding rare ore"""

    # Custom room generation
    @on_room_generate
    def add_treasure_room(room):
        if random() < 0.1:  # 10% of rooms
            room.add_ore_vein(
                ore_type="Legacy",
                hardness=random(90, 100),
                guarded_by=Monster("Dragon", hp=200)
            )

    # Custom events
    @on_floor_3
    def ore_rain():
        announce("The ceiling cracks! Ore falls from above!")
        for player in party:
            player.inventory.add(random_ore())

    # Modify rules
    settings.ore_mining_time = 2  # Faster mining
    settings.monster_respawn = False  # No respawns
    settings.legacy_ore_tradeable = True  # Can trade
```

**Submitted to community for approval**
**Popular scripts featured in "Community Dungeons"**

---

### Option 4: Quest Builder (Medium-Advanced)

**Visual quest editor (in-game):**

```
> quest create "The Ore Shortage"

Step 1: Talk to NPC "Blacksmith Bob"
  Dialogue: "I need 10 iron ore for the king's armor!"

Step 2: Collect 10 Iron Ore (H > 70)

Step 3: Return to Blacksmith Bob
  Reward:
    - Legendary Sword Recipe
    - 1000 XP
    - +50 Reputation

> quest publish
Quest submitted for approval!
```

**Community-created quests keep content fresh**

---

## 🎯 Recommendation for Brogue

### Phase 1: Basic Customization

**Start simple, add complexity later:**

**Personal Hideout:**
- Cosmetic customization only
- Trophy display (show off gear/ore)
- Private forge (craft without going to dungeon)
- Invite friends to visit

**Implementation:** 1-2 weeks
**Risk:** Low (just persistence + templates)

---

### Phase 2: Dungeon Templates

**Let players tweak generation params:**

**Template system:**
```python
class DungeonTemplate:
    ore_spawn_rate: float = 1.0  # Multiplier
    monster_difficulty: float = 1.0
    floor_count: int = 10
    theme: str = "default"  # "mining", "combat", "exploration"

    cost: int  # Dungeon tokens to use template
```

**Balancing:**
- Higher rewards = higher cost
- Tradeoffs required (can't max everything)
- Earn tokens from Pure Victories

**Implementation:** 2-3 weeks
**Risk:** Medium (balancing tricky)

---

### Phase 3: Mod Support (Long-term)

**Python plugin system:**

```python
# mods/treasure_hunter.py
from brogue.api import DungeonMod

class TreasureHunterMod(DungeonMod):
    def on_room_generate(self, room):
        if random() < 0.05:
            room.add_treasure_chest()

    def on_monster_death(self, monster):
        if random() < 0.1:
            return LegacyOre("Blessed Iron")
```

**Load mods:**
```
> mod load treasure_hunter
Mod loaded: Treasure Hunter v1.2

> create dungeon with mods
  [x] Treasure Hunter
  [ ] Ore Madness
  [ ] Boss Rush
```

**Community workshop:**
- Players upload mods
- Ratings/reviews
- Curated featured mods

**Implementation:** 4-6 weeks
**Risk:** High (security, sandboxing, review process)

---

## 🔐 Security Lessons from MUDs

**If we add scripting, MUST have:**

1. **Sandboxing** - Isolated execution (no file system access)
2. **Resource limits** - CPU time, memory caps
3. **Review process** - Approve scripts before public use
4. **Permissions** - What players can/can't do
5. **Rollback** - If script breaks something, undo it

**Python sandboxing:**
```python
from RestrictedPython import compile_restricted

def execute_player_script(code_string):
    # Compile with restrictions
    bytecode = compile_restricted(code_string, '<player_script>', 'exec')

    # Limited globals (no os, sys, etc.)
    safe_globals = {
        'random': random.random,
        'Monster': Monster,
        'OreVein': OreVein,
        # ... safe API only
    }

    # Execute with timeout
    with timeout(seconds=1):
        exec(bytecode, safe_globals)
```

---

## 📊 Comparison: Content Creation Approaches

| Approach | Implementation | Power | Risk | Timeline |
|----------|---------------|-------|------|----------|
| **Housing** | Easy | Low | Low | 1-2 weeks |
| **Templates** | Medium | Medium | Medium | 2-3 weeks |
| **Quest Builder** | Medium | Medium | Medium | 3-4 weeks |
| **Python Mods** | Hard | High | High | 4-6 weeks |
| **Full Scripting** | Very Hard | Very High | Very High | 8-12 weeks |

---

## 💡 Key Insights

**What MUDs teach us:**

1. **Player content = longevity**
   - MUDs from 1990s still growing (player-built content)
   - Community becomes invested (their creations)

2. **Start simple, add complexity**
   - Begin with templates/customization
   - Add scripting later if demand exists

3. **Trust but verify**
   - Review process maintains quality
   - Prevents exploits and abuse

4. **Sandboxing is CRITICAL**
   - If players can code, must be sandboxed
   - Resource limits prevent crashes

5. **Community moderation works**
   - Senior players become builders
   - Reduces admin burden
   - Creates ladder of progression

---

## 🚀 Recommended Path for Brogue

### MVP: No Player Content

**Focus on core game first:**
- Get 4-player co-op working
- Nail the mining/crafting loop
- Prove the game is fun

**Then add:**

### Phase 1: Personal Hideout (Simple)

```
Week 1-2:
  - Player can customize descriptions
  - Trophy display
  - Invite friends to visit
  - Private forge

Value: Social, identity expression
Risk: Low
```

### Phase 2: Dungeon Templates (Medium)

```
Week 3-4:
  - Tweak generation parameters
  - Earn tokens from victories
  - Tradeoff system (balance)
  - Share templates with friends

Value: Replayability, variety
Risk: Medium (balance)
```

### Phase 3: Mod System (Advanced)

```
Week 8-12:
  - Python API for mods
  - Sandboxed execution
  - Community workshop
  - Featured mods

Value: Infinite content
Risk: High (security)
```

**Don't rush to Phase 3!** MUDs took YEARS to get there.

---

## ✅ Summary

**MUDs typically offer:**
- ✅ Player housing (cosmetic customization)
- ✅ Builder systems (trusted players create content)
- ✅ Scripting languages (LPC, MOO, softcode)
- ✅ Quest creation tools
- ✅ Object-oriented worlds (everything is programmable)

**How it works:**
- Sandboxed execution (security)
- Event-driven architecture (objects respond to events)
- Permission systems (player < builder < wizard < admin)
- Review processes (quality control)

**For Brogue:**
- Start simple (housing, templates)
- Add complexity if needed (mods, scripting)
- Learn from 30+ years of MUD experience
- Prioritize security if adding player code

**The magic:** Players become co-creators, communities thrive for decades!

---

**Related:** Check out Evennia (Python MUD framework) - shows how all this works in modern Python!
