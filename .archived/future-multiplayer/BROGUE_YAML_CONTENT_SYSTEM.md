# Brogue YAML Content System

**Date:** 2025-10-21
**Session:** icy-temple-1021
**Concept:** "Player house off brogue town that support MUD concepts via YAML config"

---

## 🎯 The Vision: YAML-Driven Player Content

**The Genius:**
- Players customize content via YAML config files
- No code execution (safe!)
- Human-readable (easy to edit)
- Shareable (copy/paste, Git)
- Validated server-side (prevent exploits)
- Editable in-game OR in text editor

**Like:**
- Minecraft resource packs
- Factorio blueprints
- Home Assistant configs
- Docker Compose files

**But for MUD content creation!**

---

## 🏠 Player House System

### Basic House YAML

```yaml
# ~/.brogue/houses/warrior_hideout.yaml

house:
  id: warrior_hideout_alice
  owner: alice
  name: "Alice's Training Hall"
  created: 2025-10-21

  description: |
    A spacious training hall with weapon racks lining the walls.
    Practice dummies stand ready for combat drills. The smell of
    oil and leather fills the air.

  rooms:
    - id: entrance
      name: "Training Hall Entrance"
      description: |
        The main entrance opens into a wide training space.
        Sunlight streams through high windows.

      exits:
        north: armory
        east: forge
        south: brogue_town  # Links back to hub

      objects:
        - type: practice_dummy
          name: "a battered practice dummy"
          interactable: true
          on_use: "You strike the dummy. Your form improves slightly."

        - type: weapon_rack
          name: "an oak weapon rack"
          description: "A sturdy rack holding various practice weapons."
          display_items:
            - wooden_sword
            - practice_spear

    - id: armory
      name: "Personal Armory"
      description: |
        Your collection of hard-won equipment. Trophies from
        countless dungeon runs adorn the walls.

      exits:
        south: entrance

      objects:
        - type: trophy_case
          name: "a glass trophy case"
          display_items:
            - starforged_blade  # From Legacy Vault
            - goblin_king_crown
            - perfect_iron_ore  # Best ore ever found

        - type: chest
          name: "an iron-banded chest"
          container: true
          capacity: 50
          contents:
            - health_potion: 10
            - iron_ore: 5

    - id: forge
      name: "Personal Forge"
      description: |
        A fully-equipped forge. The coals glow with steady heat.
        This is where you craft your legendary gear.

      exits:
        west: entrance

      objects:
        - type: forge
          name: "a master forge"
          functional: true
          allows:
            - crafting
            - smelting
            - repair

          recipes_unlocked:
            - iron_sword
            - steel_armor
            - mithril_staff

  permissions:
    visitors_allowed: true
    invited_users:
      - bob
      - carol
      - dave

    can_interact: invited_users  # Only invited can use objects
    can_edit: owner  # Only Alice can modify
```

### In-Game Commands

```
> house enter
You enter Alice's Training Hall.

> look
Training Hall Entrance
  A spacious training hall with weapon racks lining the walls...

  [North] Personal Armory
  [East] Personal Forge
  [South] Brogue Town

  You see:
    - a battered practice dummy
    - an oak weapon rack

> use dummy
You strike the dummy. Your form improves slightly.

> north
Personal Armory
  Your collection of hard-won equipment...

> examine trophy_case
A glass trophy case
  Contents:
    - Starforged Blade (Legacy Ore craft!)
    - Goblin King Crown (Boss drop - Floor 7)
    - Perfect Iron Ore (H:98, C:95, P:99)

> invite eve
Eve has been invited to your house.

> house edit
[Opens YAML editor or in-game form]
```

---

## 🎨 Visual House Builder (In-Game)

**For non-technical players, in-game forms:**

```
┌─ HOUSE EDITOR ─────────────────────────┐
│ Room: Training Hall Entrance           │
│                                        │
│ Name: [Training Hall Entrance_____]   │
│                                        │
│ Description:                           │
│ ┌────────────────────────────────────┐ │
│ │A spacious training hall with      │ │
│ │weapon racks lining the walls.     │ │
│ │Practice dummies stand ready for   │ │
│ │combat drills.                     │ │
│ └────────────────────────────────────┘ │
│                                        │
│ Exits:                                 │
│   [North] → [Personal Armory_____]    │
│   [East]  → [Personal Forge______]    │
│   [South] → [Brogue Town_________]    │
│                                        │
│ Objects: (2)                           │
│   [+] Add Object                       │
│   [View] practice_dummy                │
│   [View] weapon_rack                   │
│                                        │
│ [Save] [Cancel] [Export YAML]          │
└────────────────────────────────────────┘
```

**Export YAML:**
- Saves to `~/.brogue/houses/warrior_hideout.yaml`
- Can edit in text editor
- Re-import edited version
- Share with friends (copy YAML file)

---

## 🗺️ Custom Dungeon Templates

### Dungeon Template YAML

```yaml
# ~/.brogue/dungeons/ore_paradise.yaml

dungeon_template:
  id: ore_paradise
  author: alice
  name: "Ore Paradise"
  version: 1.2
  created: 2025-10-21
  description: "A mining-focused dungeon with abundant ore but tough guardians."

  tags:
    - mining
    - ore-farming
    - challenging

  difficulty: medium
  recommended_party_size: 3-4

  # Dungeon generation parameters
  generation:
    floors: 10

    map_size:
      width: 80
      height: 24

    room_count:
      min: 8
      max: 12

    # Ore spawn rates (multipliers)
    ore_spawns:
      iron:
        rate: 2.0  # 2x normal
        quality_min: 60
        quality_max: 90

      mithril:
        rate: 1.5
        quality_min: 70
        quality_max: 95

      legacy:
        rate: 1.2  # Slightly higher Legacy Ore chance

    # Monster adjustments
    monsters:
      count_multiplier: 1.5  # 50% more monsters (guardians!)
      difficulty_multiplier: 1.2  # 20% tougher

      types:
        - goblin: 30%
        - orc: 25%
        - troll: 20%
        - ore_guardian: 15%  # Special ore-protecting monster
        - dragon: 10%

    # Special rooms
    special_rooms:
      - type: ore_vein_chamber
        chance: 0.15  # 15% of rooms
        contents:
          - ore_veins: 3-5
          - guardian_monster: true

      - type: treasure_vault
        chance: 0.05  # 5% of rooms
        contents:
          - legacy_ore: guaranteed
          - boss_monster: true

  # Rules/modifiers
  rules:
    mining_time: 3  # Turns to mine (default: 4)
    monster_respawn: false
    friendly_fire: false

  # Rewards
  rewards:
    xp_multiplier: 1.0  # Normal XP
    gold_multiplier: 0.8  # Less gold (trade-off)

  # Cost to use this template
  cost:
    dungeon_tokens: 10  # Earned from victories

  # Achievements
  achievements:
    - id: ore_hoarder
      name: "Ore Hoarder"
      description: "Collect 50 ore pieces in Ore Paradise"
      reward: 100 xp
```

### Using Templates

```
> dungeon list_templates

Available Dungeon Templates:
  1. Ore Paradise (alice) - Mining-focused, 10 tokens
  2. Boss Rush (bob) - Fight all bosses, 15 tokens
  3. Speed Run (carol) - Small dungeon, no cost
  4. Hardcore Gauntlet (eve) - Pure difficulty, 20 tokens

> dungeon create from ore_paradise
Creating dungeon from template "Ore Paradise"...
Cost: 10 tokens (you have: 25)

[Confirm] [Cancel]

> confirm
Dungeon created!
  Seed: 8372619
  Floors: 10
  Ore spawn rate: 2.0x
  Monsters: 1.5x count, 1.2x difficulty

> invite bob carol dave
Invitations sent!

> start
Entering dungeon...
```

---

## 🎭 NPC Dialogue System

### NPC YAML

```yaml
# ~/.brogue/npcs/blacksmith_bob.yaml

npc:
  id: blacksmith_bob
  name: "Blacksmith Bob"
  location: brogue_town_forge

  appearance:
    description: |
      A burly man with soot-stained arms and a friendly grin.
      His leather apron bears the scars of countless hours at the forge.

    symbol: "B"
    color: orange

  dialogue:
    greeting:
      default: "Welcome to my forge, adventurer!"

      conditions:
        - if: player.pure_victories > 0
          say: "Ah, a pure victor! Your reputation precedes you."

        - if: player.has_item("starforged_iron")
          say: "Is that Starforged Iron? I haven't seen that in decades!"

    topics:
      - keyword: "repair"
        response: |
          I can repair your gear for a fee. The cost depends on
          the damage and the quality of the item.

        options:
          - text: "Repair my equipment"
            action: open_repair_menu

          - text: "How much does it cost?"
            response: "10 gold per durability point."

      - keyword: "craft"
        response: |
          Looking to craft? I can help with basic items, or you
          can use the forge yourself if you have the recipes.

        options:
          - text: "Show crafting menu"
            action: open_crafting_menu

          - text: "Teach me a recipe"
            condition: player.gold >= 500
            response: "For 500 gold, I'll teach you the Iron Sword recipe."
            action: learn_recipe(iron_sword)

      - keyword: "legacy_ore"
        condition: player.legacy_vault_count > 0
        response: |
          Ah, you've collected Legacy Ore! Those are precious beyond
          measure. I can craft legendary items from them... for a price.

        options:
          - text: "What can you make?"
            action: show_legacy_crafting

      - keyword: "story"
        response: |
          I've been smithing here for thirty years. Seen adventurers
          come and go. Some return victorious, others... don't return at all.

        unlocks_topic: "old_tales"

      - keyword: "old_tales"
        condition: topic_unlocked("old_tales")
        response: |
          Once, a warrior came through here wielding the Starforged Blade.
          Said he found it on the deepest floor anyone had reached - Floor 50!
          Never saw him again after that...

  shop:
    currency: gold

    items:
      - id: health_potion
        name: "Health Potion"
        price: 50
        stock: 10  # Refreshes daily

      - id: iron_ore
        name: "Iron Ore (H:60)"
        price: 100
        stock: 5

      - id: repair_kit
        name: "Repair Kit"
        price: 200
        stock: 3

  quests:
    - id: ore_shortage
      name: "The Ore Shortage"
      description: "Bring me 10 iron ore"

      objectives:
        - collect: iron_ore
          count: 10

      rewards:
        - gold: 1000
        - xp: 500
        - item: legendary_sword_recipe
        - reputation: blacksmith_guild +50

  schedule:
    monday_friday:
      - time: "08:00-18:00"
        location: brogue_town_forge
        available: true

      - time: "18:00-08:00"
        location: home
        available: false

    saturday_sunday:
      - time: "10:00-14:00"
        location: brogue_town_forge
        available: true
```

### Interacting with NPCs

```
> talk blacksmith_bob
Blacksmith Bob: "Welcome to my forge, adventurer!"

> ask about repair
Blacksmith Bob: "I can repair your gear for a fee..."
  [1] Repair my equipment
  [2] How much does it cost?

> 1
Repair Menu:
  Starforged Blade (durability: 80/100) - Cost: 200 gold
  Iron Armor (durability: 50/100) - Cost: 500 gold

> repair starforged_blade
Blacksmith Bob repairs your Starforged Blade.
  -200 gold
  Starforged Blade: 100/100 durability
```

---

## 📜 Quest System

### Quest YAML

```yaml
# ~/.brogue/quests/ore_shortage.yaml

quest:
  id: ore_shortage
  name: "The Ore Shortage"
  author: alice
  version: 1.0

  description: |
    The king's blacksmith needs ore for a special commission.
    Help gather high-quality iron ore for the royal armory.

  quest_giver: blacksmith_bob
  location: brogue_town_forge

  requirements:
    min_level: 5
    min_pure_victories: 0  # Available to all

  objectives:
    - id: gather_iron
      type: collect
      target: iron_ore
      count: 10
      conditions:
        - hardness >= 70  # Must be quality ore!

      progress_messages:
        - at: 0.25
          message: "You've found some good iron ore. Keep going!"
        - at: 0.50
          message: "Halfway there! Bob will be pleased."
        - at: 0.75
          message: "Almost enough ore! Just a bit more."

    - id: return_to_bob
      type: talk
      target: blacksmith_bob
      condition: gather_iron.complete

  rewards:
    xp: 1000
    gold: 500

    items:
      - id: legendary_sword_recipe
        name: "Recipe: Legendary Sword"

      - id: blacksmith_token
        name: "Blacksmith's Token"
        description: "10% discount at forges"

    reputation:
      - faction: blacksmith_guild
        amount: 50

    unlocks:
      - quest: royal_commission  # Unlocks next quest
      - npc_dialogue: blacksmith_bob.advanced_crafting

  failure_conditions:
    - ore_destroyed: true
      message: "The ore was destroyed! Quest failed."

    - timeout: 7_days
      message: "The commission deadline has passed."

  stages:
    - id: introduction
      dialogue:
        npc: blacksmith_bob
        text: |
          The king needs armor, and I'm short on quality ore.
          Can you help me gather 10 pieces of iron ore with
          hardness 70 or better?

      options:
        - text: "I'll help you."
          action: accept_quest

        - text: "Not right now."
          action: decline_quest

    - id: in_progress
      condition: quest_accepted

      on_objective_complete:
        - gather_iron:
            dialogue:
              npc: blacksmith_bob
              text: "Excellent ore! This will make fine armor."

    - id: completion
      condition: all_objectives_complete

      dialogue:
        npc: blacksmith_bob
        text: |
          Outstanding work! The king will be pleased. Here's
          your reward - and a special recipe I've been holding onto.

      rewards_given: true
      quest_complete: true
```

---

## 🎲 Item Templates

### Custom Item YAML

```yaml
# ~/.brogue/items/custom_sword.yaml

item:
  id: dragonslayer_sword
  author: alice

  name: "Dragonslayer"
  type: weapon
  subtype: sword

  appearance:
    short_desc: "Dragonslayer"
    long_desc: |
      A massive greatsword forged from dragon bone and adamantite.
      Runes glow faintly along the blade, pulsing with ancient power.

    symbol: ")"
    color: "#FF4500"  # Orange-red

  stats:
    damage: 25
    attack_speed: slow
    weight: 15
    durability: 150
    value: 5000

  requirements:
    class: warrior
    level: 10
    strength: 15

  effects:
    on_equip:
      - stat_bonus:
          strength: +5
          fire_resistance: +20

    on_attack:
      - chance: 0.15  # 15% chance
        effect: fire_burst
        description: "The blade erupts in flames!"
        damage: 30
        damage_type: fire
        aoe: 1  # Hits adjacent enemies

    on_hit:
      - chance: 0.05  # 5% chance
        effect: dragon_roar
        description: "The sword roars like a dragon!"
        debuff:
          target: all_enemies_in_room
          effect: fear
          duration: 3_turns

  crafting:
    recipe:
      materials:
        - dragonbone_ore: 1
        - adamantite_ore: 1
        - phoenix_feather: 1

      skill_required: blacksmithing_10
      crafting_time: 10_turns
      success_rate: 0.8  # 80% success

    destroys_materials_on_fail: true

  lore: |
    Forged from the bones of the ancient Dragon King, this sword
    has slain countless dragons. Its wielder is said to gain the
    strength and fury of dragonkind.

  unique: true  # Only one can exist
  tradeable: true
  droppable: true
  soulbound: false  # Can be traded/sold
```

---

## 🛡️ Validation & Security

### Server-Side Validation

```python
# Server validates all YAML configs

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict
import yaml

class HouseRoom(BaseModel):
    id: str
    name: str
    description: str
    exits: Dict[str, str]
    objects: List[dict] = []

    @validator('description')
    def description_length(cls, v):
        if len(v) > 1000:
            raise ValueError('Description too long (max 1000 chars)')
        return v

    @validator('exits')
    def valid_exits(cls, v):
        allowed_directions = ['north', 'south', 'east', 'west',
                             'up', 'down', 'brogue_town']
        for direction in v.keys():
            if direction not in allowed_directions:
                raise ValueError(f'Invalid direction: {direction}')
        return v

class House(BaseModel):
    id: str
    owner: str
    name: str
    description: str
    rooms: List[HouseRoom]
    permissions: dict

    @validator('rooms')
    def max_rooms(cls, v):
        if len(v) > 10:
            raise ValueError('Max 10 rooms per house')
        return v

def validate_house_yaml(yaml_file: str, player_id: str):
    """Validate player house YAML"""
    try:
        with open(yaml_file) as f:
            data = yaml.safe_load(f)

        # Pydantic validation
        house = House(**data['house'])

        # Ownership check
        if house.owner != player_id:
            raise ValueError('You can only edit your own house!')

        # Resource limits
        if len(house.rooms) > 10:
            raise ValueError('Maximum 10 rooms')

        # Content filtering
        for room in house.rooms:
            if contains_profanity(room.description):
                raise ValueError('Inappropriate content detected')

        return house

    except Exception as e:
        return {"error": str(e)}
```

### Sandbox Limits

```yaml
# Server-enforced limits

limits:
  house:
    max_rooms: 10
    max_objects_per_room: 20
    max_description_length: 1000
    max_name_length: 50

  dungeon_template:
    max_floors: 20
    ore_spawn_rate_max: 3.0  # Can't exceed 3x
    monster_count_max: 2.0  # Can't exceed 2x
    xp_multiplier_max: 1.5  # Prevent XP farming

  quest:
    max_objectives: 10
    max_reward_gold: 10000
    max_reward_xp: 5000

  item:
    max_damage: 50
    max_stats: 100
    max_effects: 5
```

---

## 📤 Sharing & Community

### YAML Export/Import

```
> house export
Exported to: ~/.brogue/houses/warrior_hideout.yaml

You can share this file with friends!

> house import alice_hideout.yaml
Importing house from file...
  Owner: alice
  Rooms: 3
  Objects: 12

[Accept] [Cancel]

> accept
House imported successfully!
Visit with: house visit alice_hideout
```

### Community Workshop

```
┌─ COMMUNITY WORKSHOP ───────────────────┐
│ Browse player-created content          │
│                                        │
│ Houses:                                │
│  ⭐⭐⭐⭐⭐ Warrior's Armory (alice)    │
│  ⭐⭐⭐⭐ Mage Tower (bob)              │
│  ⭐⭐⭐ Mining HQ (carol)               │
│                                        │
│ Dungeon Templates:                     │
│  ⭐⭐⭐⭐⭐ Ore Paradise (alice)        │
│  ⭐⭐⭐⭐ Boss Rush (eve)               │
│  ⭐⭐⭐ Speed Run (frank)               │
│                                        │
│ Quests:                                │
│  ⭐⭐⭐⭐ The Ore Shortage (alice)      │
│  ⭐⭐⭐ Dragon Hunt (bob)               │
│                                        │
│ [Download] [Rate] [Report]             │
└────────────────────────────────────────┘
```

**Workshop features:**
- Upload YAML configs
- Download popular configs
- Rate and review
- Report inappropriate content
- Curated "Featured" section

---

## 🔄 Git Integration (Advanced)

### Version Control Your Content

```bash
# Player's local setup
~/.brogue/
  houses/
    warrior_hideout.yaml
  dungeons/
    ore_paradise.yaml
  quests/
    ore_shortage.yaml

# Initialize Git
cd ~/.brogue
git init
git add .
git commit -m "Initial Brogue content"

# Share on GitHub
git remote add origin git@github.com:alice/brogue-content.git
git push

# Others can clone
git clone git@github.com:alice/brogue-content.git
```

**Benefits:**
- Version history (rollback changes)
- Collaboration (pull requests!)
- Sharing (clone repo)
- Backups (GitHub)

---

## 🎯 Implementation Roadmap

### Phase 1: Player Houses (Week 1-2)

```python
# Server implementation

class HouseManager:
    def load_house(self, player_id: str):
        """Load player's house from YAML"""
        path = f"~/.brogue/houses/{player_id}.yaml"
        with open(path) as f:
            data = yaml.safe_load(f)
        return House(**data['house'])

    def enter_house(self, player_id: str):
        """Player enters their house"""
        house = self.load_house(player_id)
        player.location = house.rooms[0]  # Entrance
        return house.rooms[0].description

    def interact_object(self, object_id: str):
        """Player interacts with object"""
        obj = current_room.get_object(object_id)
        if obj.interactable:
            return obj.on_use
```

### Phase 2: Dungeon Templates (Week 3-4)

```python
class DungeonGenerator:
    def generate_from_template(self, template_file: str):
        """Generate dungeon from YAML template"""
        with open(template_file) as f:
            template = yaml.safe_load(f)

        # Apply generation parameters
        params = template['generation']

        dungeon = Dungeon(
            floors=params['floors'],
            ore_rate=params['ore_spawns'],
            monster_mult=params['monsters']['count_multiplier']
        )

        return dungeon.generate()
```

### Phase 3: NPCs & Quests (Week 5-6)

```python
class NPCManager:
    def load_npc(self, npc_id: str):
        """Load NPC from YAML"""
        path = f"~/.brogue/npcs/{npc_id}.yaml"
        with open(path) as f:
            data = yaml.safe_load(f)
        return NPC(**data['npc'])

    def talk(self, npc_id: str, topic: str):
        """Handle NPC dialogue"""
        npc = self.load_npc(npc_id)
        for dialogue_topic in npc.dialogue['topics']:
            if dialogue_topic['keyword'] == topic:
                return dialogue_topic['response']
```

---

## 💡 Why YAML > Scripting

**Advantages:**

✅ **Safe** - No code execution, just data
✅ **Simple** - Easy to learn (human-readable)
✅ **Validated** - Server can verify all values
✅ **Shareable** - Copy/paste, Git, workshop
✅ **Accessible** - Text editors or in-game forms
✅ **Version-friendly** - Git diffs work great
✅ **Fast to implement** - Just parse + validate

**vs. Scripting:**

❌ Code execution = security risk
❌ Sandboxing = complex
❌ Review process = slow
❌ Learning curve = high
❌ Debugging = hard for players

**YAML is 80% of the power with 20% of the risk!**

---

## 🎮 Player Experience

### Beginner (In-Game Forms)

```
> house create
House Creation Wizard
  Step 1: Name your house
  [Warrior's Training Hall___________]

  Step 2: Choose entrance description
  [Template] [Write Custom]

  > template
  Choose template:
    [1] Training Hall
    [2] Cozy Cottage
    [3] Dark Cave
    [4] Wizard Tower

  > 1
  Description set!

  Step 3: Add rooms (optional)
  [Skip] [Add Room]

  > add room
  Room Name: [Personal Armory____________]
  Connect to: [North of entrance________]

  [Save House]
```

### Intermediate (Export/Edit YAML)

```
> house export
Exported to: ~/.brogue/houses/alice_house.yaml

Player edits file in VS Code:
  - Add custom descriptions
  - Tweak object placement
  - Add complex exits

> house import alice_house.yaml
Validating... ✓
Imported successfully!
```

### Advanced (Git + Community)

```bash
# Fork popular template
git clone brogue-community/ore-paradise-template.git

# Customize
vim ore_paradise.yaml
  - Increase difficulty
  - Add special rooms
  - Custom ore types

# Share back
git commit -m "Hard mode variant"
git push

# Others can use
> dungeon install alice/ore-paradise-hard
Template installed!
```

---

## ✅ Summary

**YAML-Based Content System:**
- Player houses (customize hideout)
- Dungeon templates (tweak generation)
- NPC dialogues (custom NPCs)
- Quests (community content)
- Items (custom designs)

**How It Works:**
- YAML config files
- Server-side validation (Pydantic)
- In-game editor OR text file
- Workshop for sharing
- Git-friendly

**Why It's Brilliant:**
- Safe (no code execution)
- Simple (human-readable)
- Powerful (deep customization)
- Shareable (community content)
- Fast (easy to implement)

**MUD concepts via YAML = Best of both worlds!**

---

**This could be a killer feature!** Players creating content without security risks. Want to prototype a simple house system first?
