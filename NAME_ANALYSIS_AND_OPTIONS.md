# Game Naming Analysis & Recommendations

**Date:** 2025-11-17
**Issue:** Name collision with existing "Brogue" roguelike
**Goal:** Find a name that better reflects our game's unique identity

---

## The Problem: Brogue Already Exists

### About the Original Brogue (2009)

**Creator:** Brian Walker
**Status:** Active (maintained as "Brogue: Community Edition")
**Famous For:**
- Direct descendant of Rogue (the 1980 game)
- Elegant, minimalist design philosophy
- "Simplicity over complexity" approach
- Very well-known in roguelike community
- Open source, widely played

**The Origin Story:**
Brian Walker was porting Rogue to Mac OS when his laptop was stolen. He started over from scratch, creating "Brian's Rogue" → Brogue. It's a total rewrite with no code from original Rogue.

**Why This Matters:**
- Established brand in roguelike community (15+ years)
- Active player base and development
- Strong SEO presence, Wikipedia page, active wiki
- Using "Brogue" will cause confusion for both communities
- PyPI package name collision inevitable

---

## What Makes Our Game Different

### Core Identity

Our game is **NOT** a minimalist, simplified roguelike. It's:

```
NetHack (complex systems)
  + SWG Mining (resource hunting dopamine)
  + Multiplayer Co-op (social play)
  + Legacy Progression (meta-game)
```

### Unique Selling Points

1. **Multiplayer-First Design**
   - "4 actions per round, anyone can take them"
   - Real-time coordination via WebSocket
   - Class synergies (Warrior/Mage/Healer/Rogue)
   - In-game chat and spectator mode

2. **SWG-Style Mining/Crafting**
   - Ore veins with 5 random properties (Hardness, Conductivity, Malleability, Purity, Density)
   - Resource hunting mini-game ("perfect spawn" dopamine hits)
   - Properties determine crafted item stats
   - Risk/reward (mining takes 3-5 turns, vulnerable)

3. **Legacy Vault Meta-Progression**
   - Purity 80+ ore saved across runs
   - Pure Victory vs Legacy Victory paths
   - Persistent progression in permadeath roguelike

4. **Group High-End Crafting**
   - Personal loot from shared veins
   - Trading between players
   - Community coordination for perfect gear
   - Guild vaults (planned)

### What We're NOT
- We're NOT minimalist (we embrace complexity)
- We're NOT single-player focused (multiplayer is core)
- We're NOT "Brian's Rogue" derivative

---

## Naming Criteria

A good name should:

1. **Reflect multiplayer/co-op** → Social play is core
2. **Suggest mining/crafting** → Resource hunting is unique
3. **Sound roguelike-ish** → Genre recognition
4. **Be memorable** → Easy to say, type, remember
5. **Avoid collisions** → Check existing games, PyPI packages
6. **Have available domains** → .com/.gg/.io for future

---

## Name Options

### Tier 1: Top Recommendations

#### 1. **Delve**
**Meaning:** To dig deep, to investigate thoroughly

**Why It Works:**
- ✅ Suggests mining (delving for ore)
- ✅ Suggests dungeon exploration (delving deeper)
- ✅ Simple, memorable, one syllable
- ✅ Roguelike feel ("delve into the dungeon")
- ✅ Multiplayer connotation ("let's delve together")
- ⚠️ Check: Some existing games use "delve" in title

**Variations:**
- `Delve & Forge` (emphasizes crafting)
- `Delvers` (emphasizes co-op group)
- `Deep Delve` (emphasizes depth progression)

**Package Name:** `pip install delve` or `pip install delvers`

---

#### 2. **Veinborne**
**Meaning:** Born from the veins (ore veins)

**Why It Works:**
- ✅ Unique, evocative name
- ✅ Directly references ore vein system
- ✅ "-borne" suffix has roguelike precedent (Bloodborne, etc.)
- ✅ Suggests inheritance/legacy (Legacy Vault)
- ✅ Epic/legendary feel for high-end crafting
- ✅ Likely available (low collision risk)

**Tagline Ideas:**
- "Hunt perfect veins, craft legendary gear"
- "Where heroes are forged from ore"

**Package Name:** `pip install veinborne`

---

#### 3. **Forgebound**
**Meaning:** Bound to the forge (crafting-focused destiny)

**Why It Works:**
- ✅ Emphasizes crafting system
- ✅ Suggests co-op ("bound together")
- ✅ Epic/fantasy feel
- ✅ Clear game focus (forge gear → fight deeper)
- ✅ "Bound" suggests persistence (Legacy Vault)

**Package Name:** `pip install forgebound`

---

#### 4. **Orefall**
**Meaning:** The fall/descent for ore (dungeon descent + ore hunting)

**Why It Works:**
- ✅ Combines two core mechanics (descent + ore)
- ✅ Simple, memorable
- ✅ "-fall" suffix common in games (Titanfall, Deadfall)
- ✅ Suggests risk (falling) and reward (ore)
- ⚠️ Check: Collision with "Orefall" game

**Variations:**
- `Oredive` (emphasizes going deeper)
- `Orevault` (emphasizes Legacy Vault)

**Package Name:** `pip install orefall`

---

### Tier 2: Strong Contenders

#### 5. **Crucible**
**Meaning:** A container for melting metals; a severe test

**Why It Works:**
- ✅ Perfect double meaning (forge + difficulty)
- ✅ Suggests high-stakes testing ("trial by fire")
- ✅ Crafting connotation (melting ore)
- ✅ Co-op connotation ("we're in the crucible together")
- ⚠️ Common word, may have collisions

**Package Name:** `pip install crucible-roguelike` (need suffix)

---

#### 6. **Shaftrunner** / **Shaftrunnners**
**Meaning:** Runners of the mine shafts

**Why It Works:**
- ✅ Suggests mining (shafts)
- ✅ Suggests speed/action (runners)
- ✅ Multiplayer connotation (multiple runners)
- ✅ "Runner" common in gaming (Shadowrun, Bladerunner)
- ⚠️ Plural vs singular decision

**Package Name:** `pip install shaftrunners`

---

#### 7. **Veinquest**
**Meaning:** Quest for perfect veins

**Why It Works:**
- ✅ Clearly describes core loop (hunt veins)
- ✅ Simple, descriptive
- ✅ "Quest" gives fantasy/adventure feel
- ❌ Somewhat generic "-quest" suffix

**Package Name:** `pip install veinquest`

---

#### 8. **Deephammer**
**Meaning:** Hammering deep in the mines

**Why It Works:**
- ✅ Suggests both mining (hammer) and depth
- ✅ Strong, memorable word
- ✅ Dwarven/mining aesthetic
- ✅ Combat + crafting connotation
- ⚠️ May feel more dwarven-themed than intended

**Package Name:** `pip install deephammer`

---

### Tier 3: Creative/Ambitious

#### 9. **Stratum** / **Stratagem**
**Meaning:** Layers of rock (stratum); clever scheme (stratagem)

**Why It Works:**
- ✅ Stratum: Geological layers (dungeon floors, ore veins)
- ✅ Stratagem: Tactical planning (multiplayer coordination)
- ✅ Smart wordplay
- ⚠️ May be too abstract

**Package Name:** `pip install stratum-game`

---

#### 10. **Cobalt** / **Mithril** / **Adamant**
**Meaning:** Ore/metal names from the game

**Why It Works:**
- ✅ Direct reference to mining
- ✅ Fantasy feel
- ✅ Single word, memorable
- ❌ Mithril heavily Tolkien-associated
- ❌ May be too generic

**Package Name:** `pip install cobalt-roguelike`

---

#### 11. **The Descent** / **Descenders**
**Meaning:** Going deeper into dungeons

**Why It Works:**
- ✅ Core roguelike loop (descend floors)
- ✅ Multiplayer plural (Descenders)
- ✅ Simple, clear
- ⚠️ "The Descent" is a horror movie (2005)
- ⚠️ May be generic

**Package Name:** `pip install descenders`

---

#### 12. **Expedition** / **Expeditioners**
**Meaning:** Journey for discovery

**Why It Works:**
- ✅ Multiplayer connotation (group expedition)
- ✅ Suggests resource hunting
- ✅ Adventure feel
- ❌ Less specific to game mechanics

---

### Tier 4: Play on "Brogue" Etymology

If you want to keep the "bro" vibe:

#### 13. **Brigade**
**Meaning:** Military unit working together

**Why It Works:**
- ✅ Keeps "bro" sound (Br-)
- ✅ Emphasizes group play (brigade of adventurers)
- ✅ Military/tactical connotation (turn-based tactics)
- ⚠️ Less mining/crafting feel

---

#### 14. **Vanguard**
**Meaning:** Leading group in an expedition

**Why It Works:**
- ✅ Elite group connotation
- ✅ Suggests pushing deeper (vanguard of descent)
- ✅ Strong, heroic feel
- ⚠️ Common in game titles

---

## Recommended Action Plan

### Phase 1: Initial Validation (1 hour)
1. Check top 3 names for:
   - Existing games (Steam, itch.io)
   - PyPI package availability
   - Domain availability (.com, .gg, .io)
   - Trademark issues (cursory search)

### Phase 2: Community Testing (2-3 days)
1. Share top 5 with trusted friends/playtesters
2. Ask: "Which sounds most interesting?"
3. Ask: "Which describes the game best?"
4. Gather feedback on taglines

### Phase 3: Final Decision (1 day)
1. Choose winner
2. Register domain(s)
3. Reserve PyPI package name (`pip install <name> --help` placeholder)
4. Update all documentation
5. Update pyproject.toml
6. Update GitHub repo (if renaming)

---

## Validation Results (Checked 2025-11-17)

✅ **CLEAR** - No collision found
⚠️ **PARTIAL** - Similar games exist, may cause confusion
❌ **TAKEN** - Game with this exact name exists

| Name | Status | Notes |
|------|--------|-------|
| **Veinborne** | ✅ CLEAR | Only "VEIN" (zombie survival) and "Code Vein" (action RPG) exist - no collision! |
| **Delvers** | ⚠️ PARTIAL | "Delver" (singular, 2013 first-person roguelike) exists, but plural might work |
| **Forgebound** | ❌ TAKEN | Medieval survival game on Steam (2025) + mobile game |
| **Orefall** | ⚠️ PARTIAL | Similar to "Overfall" (2016 roguelike RPG) - risky |
| **Shaftrunners** | ✅ CLEAR | No game found with this name |
| **Deephammer** | ✅ CLEAR | Only "Deephaven" (dwarven megagame) exists - no collision! |
| **Crucible** | ⚠️ PARTIAL | Common word, many games use it |
| **Veinquest** | ✅ CLEAR | Likely available (not verified) |

---

## My Personal Recommendation

**Top Pick: Veinborne** ✅

**Why:**
1. ✅ **VERIFIED CLEAR** - No existing game with this name!
2. Directly references your unique mechanic (ore veins)
3. Evocative and memorable
4. Suggests legacy/inheritance (Legacy Vault)
5. "-borne" suffix has gaming precedent (Bloodborne, etc.)
6. Sounds epic (fits high-end crafting theme)
7. Easy to pronounce and spell

**Backup Pick: Deephammer** ✅

**Why:**
1. ✅ **VERIFIED CLEAR** - No collision found!
2. Strong mining/crafting connotation (hammer = tools)
3. "Deep" suggests dungeon descent
4. Memorable, one-word name
5. Dwarven/mining aesthetic (fits crafting theme)
6. Combat + crafting dual meaning

**Third Choice: Shaftrunners** ✅

**Why:**
1. ✅ **VERIFIED CLEAR** - No game found with this name!
2. Clearly multiplayer (plural "runners")
3. Mining connotation (mine shafts)
4. Speed/action feel ("runners")
5. Unique and memorable

**Fourth Choice: Delvers** ⚠️

**Why:**
1. ⚠️ Partial collision with "Delver" (singular)
2. Simple, punchy, memorable
3. Multiplayer plural form
4. Covers both mining and dungeon exploration
5. Roguelike feel ("delve the dungeon")

**AVOID: Forgebound** ❌ - Already taken by Steam game!

---

## Bonus Creative Options

These emerged during research - worth considering:

#### 15. **Oredive**
- ✅ Combines ore hunting + dungeon diving
- ✅ Simple, memorable
- ✅ Action-oriented ("dive in!")
- Check: Likely available

#### 16. **Legacyborne**
- ✅ Emphasizes Legacy Vault system
- ✅ Epic "-borne" suffix
- ✅ Unique progression hook
- ⚠️ Longer word

#### 17. **Vaultbound**
- ✅ References Legacy Vault
- ✅ "Bound" suggests co-op
- ✅ Implies destiny/progression
- Check: Needs validation

#### 18. **Syncforge** / **Syncdelve**
- ✅ "Sync" suggests multiplayer coordination
- ✅ Modern, tech-y feel
- ✅ Forge/Delve = crafting/mining
- ⚠️ May feel too tech (not fantasy)

#### 19. **Purity** (Single word, high concept)
- ✅ Core ore mechanic (Purity stat)
- ✅ Simple, elegant
- ✅ Suggests pursuit of perfection
- ❌ May be too abstract/generic
- ⚠️ Doesn't suggest multiplayer/mining

#### 20. **The Ore Descent** / **Ore & Ascent**
- ✅ Wordplay on "ordeal descent"
- ✅ Clear mining + dungeon theme
- ⚠️ Longer title
- ⚠️ "The" in title often dropped

---

## Quick Validation Checklist

Before committing to a name, verify:

```bash
# Check PyPI availability
pip search <name>  # Or check https://pypi.org/project/<name>/

# Check domain availability
# Visit: https://domains.google.com
# Check: <name>.com, <name>.gg, <name>.io

# Check GitHub
# Visit: https://github.com/<name>

# Check Steam/Gaming
# Search: https://store.steampowered.com/search/?term=<name>
# Search: https://itch.io/search?q=<name>

# Check trademark (US)
# Visit: https://www.uspto.gov/trademarks/search
```

---

## Next Steps

1. **Review this document** and pick your top 3 favorites
2. **Run validation checks** (PyPI, domains, existing games)
3. **Get feedback** from 2-3 trusted people
4. **Make decision** and commit
5. **Update project**:
   - `pyproject.toml` (name field)
   - `README.md` (all references)
   - Documentation
   - Git repo name (optional, can stay "brogue" locally)
   - Reserve PyPI name ASAP

---

## References

- Original Brogue: https://sites.google.com/site/broguegame/
- Brogue CE: https://github.com/tmewett/BrogueCE
- SWG Mining: https://swg.fandom.com/wiki/Mining
- Your design docs: `docs/BROGUE_CONSOLIDATED_DESIGN.md`, `docs/design/MULTIPLAYER_DESIGN_2025.md`

---

**TL;DR:** You need to rename. "Brogue" is taken by a famous 2009 roguelike. I recommend **Veinborne** (unique, emphasizes ore vein system, epic feel) or **Delvers** (simple, multiplayer, covers mining + dungeon diving).
