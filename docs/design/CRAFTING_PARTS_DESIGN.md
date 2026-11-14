---
title: "Crafting v2: weapon and armor parts, ore attributes with jobs, named ore spawns"
type: architecture
status: proposed (D1, D2 decided 2026-11-14; D3-D5 open)
date: 2026-11-14
beth_topics:
  - veinborn
  - crafting
  - ore
  - recipes
  - star-wars-galaxies
  - balance
---

# Crafting v2: parts, attributes with jobs, named ore

**Status:** proposed. Phase 0 is Scott's decisions (D1-D5 below): D1 and D2 decided
2026-11-14 (keep the six core stats, accuracy included), D3-D5 open. Phase 1 needs only D1/D2. Tasks: VB-113 (phase 0, decision gate), VB-114..VB-120 (phases 1-7, tag
`crafting-v2`; `tt list --tag crafting-v2`).

## Why

Veinborn's hook is SWG-style crafting: ore rolls properties, gear stats come from them
(`src/core/crafting.py` docstring). The data model has the right parts (five properties,
per-vein rolls inside type ranges, jackpot veins, surveying), but the recipe model loses
what made SWG's crafting good:

- **Every attribute flows into everything.** A recipe takes N ore of one type, averages
  *all five* properties, and runs every formula on that one average
  (`RecipeManager._average_ore_properties`, `CraftingRecipe.calculate_stats`). No part of an
  item cares about a different attribute, so ore is "good" or "bad", never "good for this".
- **9 of 11 crafted stats are read by nothing** (VB-113): durability, weight, fire_damage,
  stealth, evasion, spell_power, stun_chance, piercing, fire_resistance. Combat reads one
  number per side: `get_total_attack()` feeds both the to-hit roll and the damage roll,
  `get_total_defense()` both the to-hit target and the damage subtraction
  (`data/balance/formulas.yaml` `combat`). A "Flaming Sword" is a big attack number.
- **Conductivity and density do nothing for a player.** `ores.yaml` says "Mages want high
  conductivity" and density "lower is better"; no code reads either for combat.
- **No choice inside a tier.** One weapon line and one armor line per ore type (16 recipes:
  copper/iron/mithril/adamantite x weapon/armor + 6 legendaries).

What already works and stays: quality matters a lot (copper sword attack +2 from ~20 ore vs
+10 from ~95 ore; quality beats a tier step), the forge screen previews the exact result,
ore shows its quality (VB-111), and the player chooses the ore (VB-112).

## What SWG did (and what to take)

Sources: [swgr crafting](https://swgr.org/wiki/crafting),
[swgr resources](https://swgr.org/wiki/crafting_resources/),
[swgr weaponsmith](https://swgr.org/wiki/weaponsmith/),
[Koster, Designing a Living Society in SWG](https://www.raphkoster.com/?p=25717).
Exact weights varied by server era and these sources conflict on numbers; the structure is
consistent.

| SWG | Take for Veinborn |
|---|---|
| ~10 resource attributes (OQ, CD, SR, UT, MA, ...), each with a job (CD for electronics, SR/UT for weapons and armor) | Keep our 5; give each a job in specific parts (table below) |
| Weapons built from crafted sub-components (core, barrel, stock, scope, cartridge), each from its own resources; damage parts wanted OQ/CD, most others OQ/SR | 2 parts per item plus an optional gem; each part from its own ore |
| Every spawn rolled within its master type's ranges, had a unique name, appeared once, lasted 6-21 days | Named ore variants per run with skewed profiles, found on a floor window; gone once you go deeper |
| Resource quality set the starting stats and the cap; experimentation (risky rolls) pushed toward the cap | Tempering at the forge (phase 7, optional) |
| Hard-to-read economy (Koster); "only master crafters matter" critique | No player economy here; the preview already makes results readable. Keep parts to 2-3, not 5 |

## Principles

1. **Every stat the forge shows is read by the game.** Cut a stat or wire it, never keep it
   decorative. No new stat ships without the code that reads it and a test.
2. **Each attribute has a job in some part.** An ore that is bad for heads can be ideal for
   grips.
3. **Tier comes from the ore's properties, not from the recipe.** A blade takes any metal;
   adamantite ore makes a better blade because its hardness range (80-100) is higher than
   copper's (20-50). This replaces 8 per-tier recipes with a handful of part kinds.
4. **Readable in one screen.** Two parts and a gem at most; the preview shows the result.
5. **Measured, not guessed.** Every combat-facing phase ends with a paired bot A/B
   (`scripts/compare_bot_runs.py`, seeds 3000+, 4 classes x 24 games x 20000 turns).

## The stat set (decided: D1, D2)

Only stats combat can read, each with an obvious source:

| Item stat | Read by | Comes from (part: attributes) |
|---|---|---|
| `attack_bonus` (damage) | damage roll | head: hardness, purity; density adds heft |
| `accuracy` (new) | to-hit roll only | grip: malleability, purity; density costs accuracy |
| `defense_bonus` | to-hit target and damage subtraction (as today) | plates: hardness, purity |
| `max_hp_bonus` (new) | player max HP while worn | lining: malleability, density |
| `spell_power` (wire it) | force bolt damage (mage) | gem: conductivity, purity |
| `fire_damage` (phase 6) | a `@damage_modifier` + burning status | gem: conductivity, with a fire material |

Cut: durability, weight, stealth, evasion, stun_chance, piercing, fire_resistance. Density
stops being a separate "weight" stat: it becomes the heft trade-off inside the head and grip
formulas (heavy head: more damage, less accuracy).

`accuracy` changes combat: today attack does both to-hit and damage. The to-hit formula
gains a term (`roll + attacker_attack + attacker_accuracy >= 10 + defender_defense`); with
accuracy 0 for monsters and old gear, nothing changes until crafted gear has it. VB-48
removed an earlier unused accuracy block, so this is a deliberate return, with a reader.

## Parts and assemblies (phase 2)

```yaml
# data/balance/recipes.yaml (replaces the per-tier recipes; schema_version 2)
parts:
  blade:        # head of a sword
    part: head
    ore_count: 2
    accepts: metal           # any of copper / iron / mithril / adamantite
    stats:
      attack_bonus: "hardness * 0.07 + purity * 0.03 + density * 0.01"
      accuracy:     "- density * 0.01"
  axe_head:     # more heft, less control
    part: head
    ore_count: 3
    accepts: metal
    stats:
      attack_bonus: "hardness * 0.08 + purity * 0.03 + density * 0.03"
      accuracy:     "- density * 0.03"
  hilt:
    part: grip
    ore_count: 1
    accepts: metal
    stats:
      accuracy: "malleability * 0.04 + purity * 0.02"
  plates:
    part: shell
    ore_count: 3
    accepts: metal
    stats:
      defense_bonus: "hardness * 0.06 + purity * 0.03"
  lining:
    part: lining
    ore_count: 1
    accepts: metal
    stats:
      max_hp_bonus: "malleability * 0.10 + density * 0.05"
  focus_gem:    # optional slot; mage-leaning
    part: gem
    ore_count: 1
    accepts: [mithril, adamantite]
    stats:
      spell_power: "conductivity * 0.05 + purity * 0.02"

assemblies:
  sword:      {slot: weapon, parts: {head: blade, grip: hilt}, optional: [gem]}
  battle_axe: {slot: weapon, parts: {head: axe_head, grip: hilt}}
  chestplate: {slot: armor,  parts: {shell: plates, lining: lining}}
  # legendaries: an assembly with a required material (the boss drop) as a part
  flaming_sword:
    slot: weapon
    parts: {head: blade, grip: hilt}
    material: phoenix_essence     # adds fire_damage (phase 6) and a fixed bonus
    min_floor: 15
```

The coefficients above are placeholders to show the shape; phase 4 sets them from bot runs
so the totals land near today's curve (VB-75, VB-87).

- **A part is an item** (`item_type: part`, `part: head`) carrying its computed stats and
  the ore properties it came from. Its label shows its stats (`Blade +6 attack, -1 acc`).
- **Assembly** sums the parts' stats (plus a material's fixed bonus) into a wearable item,
  named from its head's ore (`Mithril Sword`, `Adamantite-Iron Sword` when the grip differs).
- **Ore choice per part** reuses VB-112: `ore_for` ranks ore by *that part's* main stat, so
  the best hilt ore (malleability) is not the best blade ore (hardness).
- **Min floor** stays on legendaries; plain parts are gated by which ore exists on a floor.
- **Saves:** existing crafted gear keeps its `attack_bonus`/`defense_bonus` and still works;
  its dead stats are ignored.

## Named ore spawns per run (phase 5)

Each run rolls one or two named variants per ore type (`Kessen Iron`, `Pale Copper`), each
with a skew profile (e.g. hardness +15, malleability -20) applied on top of the type's
ranges, and a floor window inside the type's band. Veins of a named variant only spawn in
its window; once you go deeper it is gone for the run. The name appears in the ore label
and on crafted parts (`Kessen Iron Blade`). The Legacy Vault keeps the variant name, so a
legendary spawn can carry into a later run. Deterministic from the run seed (multiplayer and
bot pairing need it).

## Tempering (phase 7, optional)

At the forge, spend N turns on a part to roll one stat toward the cap its ore allows:
`cap = the stat with every property at the ore's own maximum`. Outcomes from a small table
(crack: the part loses 1 from that stat permanently; success: +1..3; lucky: +4). Turns cost
something because monsters keep moving. No durability system: a crack is permanent stat loss.

## Phases

| # | Phase | Depends on | Size | Done when |
|---|---|---|---|---|
| 0 | Scott decides D1-D5 (VB-113) | - | - | decisions written into this doc |
| 1 (VB-114) | Combat readers: `accuracy` in to-hit, `max_hp_bonus` while worn, `spell_power` into force bolt | 0 | ~1d | each stat read by code + unit tests; old saves and monsters unchanged (accuracy 0); bot A/B shows no change with old recipes |
| 2 (VB-115) | Parts + assemblies in RecipeManager and recipes.yaml v2 (replace per-tier recipes); cut dead stats | 1 | ~2d | parts/assemblies craft through `craft` intents; legendaries as assemblies with a material; preview == result; save round-trip |
| 3 (VB-116) | Forge UI: craft a part, assemble from carried parts (picker like the ore picker); snapshot views | 2 | ~1d | keyboard-only part craft and assembly; remote client sees the same |
| 4 (VB-117) | Bots craft parts and assemble; tune coefficients against VB-75/VB-87 curves | 2, 3 | ~1-2d | paired A/B vs the pre-v2 baseline: deaths and floor within agreed band; Phoenix Armor (or its successor) crafted by bots |
| 5 (VB-118) | Named ore spawns per run (seeded), label + vault carry the name | 2 | ~1-2d | deterministic per seed; bot pairing intact; vault test |
| 6 (VB-119) | Fire: gem/material `fire_damage` via `@damage_modifier` + burning status; fire-themed monsters may resist | 2 | ~1d | flaming sword deals fire; status effect test; A/B |
| 7 (VB-120) | Tempering at the forge | 3 | ~1d | risk table tested; turn cost under monster pressure observed in a human playtest |

Order: 0 -> 1 -> 2 -> 3 -> 4, then 5/6/7 in any order. Phases 1-4 are the core; 5-7 are depth.

## Decisions for Scott (phase 0)

- **D1 Stat set: DECIDED (Scott, 2026-11-14).** Keep the six core stats (attack, accuracy,
  defense, max HP, spell power, fire damage in phase 6); cut durability, weight, stealth,
  evasion, stun_chance, piercing, fire_resistance.
- **D2 Accuracy: DECIDED with D1.** Accuracy is one of the six: weapons get a to-hit term
  separate from damage.
- **D3 Parts per item: DECIDED (Scott, 2026-11-14).** Two parts plus an optional gem (SWG used five;
  too many for quick runs).
- **D4 Tier from properties: DECIDED (Scott, 2026-11-14).** Parts accept any metal, tier comes from
  the ore's ranges, replacing the per-tier recipes.
- **D5 Named spawns:** per run, seeded, one or two per ore type? *Recommended: yes, after the
  core (phase 5).*

## Risks

- **Balance reset.** Phase 2 changes every crafted number; VB-75/VB-87 tuning is redone in
  phase 4. Keep the pre-v2 bot baseline before starting.
- **Bot complexity.** The bot must plan two crafts and an assembly; until phase 4 lands, bot
  runs under v2 are not comparable.
- **Protocol.** New snapshot fields (part views, assembly options) bump the protocol.
- **Scope creep.** No durability, no repair, no player speed in this plan; each would be its
  own system.

## Related

- [MECHANICS_REFERENCE.md](../MECHANICS_REFERENCE.md) (Crafting Mechanics, today's model)
- [CONTENT_CREATION.md](../CONTENT_CREATION.md) (adding recipes)
- [BALANCE_REVIEW.md](../development/BALANCE_REVIEW.md)
- [EXTENDING.md](../EXTENDING.md) (damage modifiers, status effects)
- Tasks: VB-75, VB-87 (balance), VB-111, VB-112 (done), VB-113 (decision gate)
