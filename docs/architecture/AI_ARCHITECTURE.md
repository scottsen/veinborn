---
title: "Veinborn AI architecture: engine, tactics, abilities"
type: architecture
beth_topics:
  - veinborn
  - ai-behavior
  - monster-ai
  - abilities
  - architecture
  - perception
  - status-effects
---

# Veinborn AI Architecture

**Status:** Accepted, in progress (ADR-019 in [DECISIONS.md](DECISIONS.md)), 2026-11-12.
Built: range metric (VB-58), parameters and validation (VB-59), perception and provocation (VB-60),
morale (VB-61).
Everything else below is the plan.
**Tasks:** umbrella `VB-47`; children `VB-58` to `VB-65`, plus `VB-66` (`tt list --children-of VB-47`).
**Read with:** [../EXTENDING.md](../EXTENDING.md) (the content contract this changes),
`data/entities/monsters.yaml`, `data/balance/ai_behaviors.yaml`.

## Summary

Monster AI is split into three layers, each owning one question:

| Layer | Owns | Lives in |
|---|---|---|
| **Engine** | *Can this monster act, what does it know, is it breaking?* Parameter resolution, speed, perception (range + line of sight + provocation), morale, the one range metric, validation | `src/core/systems/ai_system.py` (core) |
| **Tactics** | *Where should it stand?* Approach, kite, hold a post, keep away, wander | `@ai_behavior` in `src/core/content/ai/` |
| **Abilities** | *What can it do besides walk and hit?* Bolts, heals, summons, drains, with cooldowns and config | `@ability` in `src/core/content/abilities/`, shared by players and monsters |

A monster is then data: `tactics + abilities + parameters` in `monsters.yaml`. For example a
lich would be `ai: {type: defensive}` with `abilities: {death_bolt: {enabled: true}, summon_undead: {enabled: true}}`.

## Why: what is wrong today

Found while investigating VB-47 (session vevine-1112). Every point was checked in code.

1. **Knobs are declared and never read.** All 19 monsters declare `ai.aggro_range` (1 to 15) and
   `ai.move_speed` (0.6 to 1.5); `EntityLoader.create_monster` stores only `ai.type`. Chase range
   comes from the behaviour section of `ai_behaviors.yaml`, so every aggressive monster chases at 10.
   The troll ("near-sighted", 6) and the mimic ("only attacks when adjacent", 1) do not behave as
   their YAML says.
2. **Each behaviour senses and flees on its own.** `defensive`, `passive` and `sniper` each
   implement "flee below X% HP"; `guard` has `flee_threshold: 0.2` in YAML and never flees.
   No classic behaviour checks line of sight: monsters chase by distance through walls.
3. **`passive` is dead.** It reacts to `was_attacked_last_turn`, which nothing sets, it never
   fights back, and no monster uses it.
4. **`default_ai_by_type` is dead.** It names `rat` and `dragon` (not monsters), and its only
   caller is a unit test.
5. **Three distance metrics.** AI and spawning use Manhattan, `force_bolt` uses Chebyshev,
   `Entity.distance_to` is Euclidean. Movement and adjacency are 8-way, so a Manhattan 10 is
   5 to 7 tiles on the diagonal.
6. **Behaviours bake in abilities.** `sniper` contains a ranged attack and `summoner` contains
   summoning, so "a lich that bolts and summons" needs a new behaviour. Meanwhile 13 of the 19
   monsters already declare about 30 abilities in `monsters.yaml`, all `enabled: false`
   (see the inventory below). The data already models monsters as abilities; the code does not.

## Engine

The engine is core code, not content: it must work in single-player and in the multiplayer
server, which does not install content event handlers (VB-55).

### Turn shape

```
AISystem.update():                      # called once per round by TurnProcessor (SP) and session.py (MP)
  for monster in living monsters:
    params = resolve_params(monster)    # Parameters
    gain energy; while energy >= 1:     # Speed
      target = perceive(monster, params)     # Perception + Provocation
      if morale_breaks(monster, params, target): flee_from(target)   # Morale
      elif use_ready_ability(monster, params, target): pass          # Abilities for any actor
      else: tactics(ai, monster, params)     # the @ai_behavior
      energy -= 1
```

### Parameters (VB-59, built)

`params = defaults <- behaviour section (both ai_behaviors.yaml) <- monster ai: block (monsters.yaml) <- ai_params stat`
(`AISystem.params_for`).

- Resolved at runtime from `monster.content_id`, **not copied into stats**. Saves store the whole
  stats dict, so copying would freeze today's numbers into every save; a lookup lets YAML tuning
  reach existing games.
- The `ai_params` per-instance override exists for elites, summoned minions and tests.
- Universal keys are the keys of the `defaults` block (`aggro_range`, `memory_turns`,
  `move_speed`, `flee_threshold`), plus `type` and `description`. Any other key in a monster's
  `ai:` block must be a key of its behaviour's section.

### Perception (VB-60, built)

`ai.perceive(monster, params) -> player | None` is what the monster *knows*:

- **Sight:** a living player within `aggro_range` (8-way steps) with line of sight. If several
  are visible, the current target wins, then the nearest.
- **Memory:** the player it last saw or was attacked by stays its target for `memory_turns`
  after losing sight (stats `target_id`, `target_seen_turn`), so it paths around walls after you.
- `ai.provoked_by(monster, params)` is the attacker within `memory_turns` (stats `provoked_by`,
  `provoked_turn`), for behaviours that treat being attacked specially.

What the monster *does* about it is the behaviour's engagement policy, using its own ranges:
aggressive and berserker engage anything perceived (aggressive no longer has a `chase_range`;
the berserker's enrage raises its `aggro_range` to `enraged_aggro_range`), defensive engages
within `chase_range` unless provoked, guard within `chase_range` without leaving `guard_radius`,
coward flees within `flee_range`, neutral engages only its attacker.

It is a toolkit call, not something the engine forces on tactics. What keeps every behaviour
honest is a **contract test** (`tests/unit/systems/test_ai_perception.py`) parametrized over
every registered `@ai_behavior`: with a player out of sight range, the monster neither attacks,
approaches nor flees from them; with an adjacent attacker it reacts (positive control).

Found while building it: `wander` could step onto the player's tile, which is a bump attack, so
"peaceful" wanderers hit adjacent players. It now only steps onto free tiles.

### Provocation (VB-60, built)

`AISystem` subscribes to `ATTACK_RESOLVED` on the game's event bus and, when the defender is a
monster, records the attacker as above. Player melee and `force_bolt` both emit this event
(published by `process_action_outcome` in both single-player and the server), so one
subscription covers every damage source that follows the event convention. `Game` passes its bus
(and detaches the previous `AISystem` on a new or loaded game); the server's `session.py`
passes its own.

This is what makes a real `aggro_range` safe: a mage bolting a mimic (`aggro_range` 1) from six
tiles is now its target. It also made `passive` a useful **neutral** type: it wanders, and
fights back when attacked.

### Morale (VB-61, built)

Before a monster's behaviour runs (`AISystem._morale_breaks`): if it perceives a player and
`hp / max_hp < flee_threshold`, it flees instead and the behaviour is skipped that turn.
`flee_threshold` is a universal parameter (default 0 = never), set per behaviour (defensive 0.3,
neutral 0.5, sniper 0.3) or per monster. This replaced the copies in defensive, passive/neutral
and the sniper; guards and aggressive monsters hold (0); the coward's fleeing is its tactic
(`flee_range`), not morale. Morale is the one step the engine forces, because every behaviour
wants it and forgetting it was the bug: a test registers a new behaviour that never flees and
shows the engine makes it flee anyway.

### Speed (VB-62)

Each update a monster gains `move_speed` energy and acts while it has at least 1. A bat (1.5) acts
3 times per 2 rounds; a golem (0.6) acts 3 times per 5. Both drivers call `ai_system.update()`
once per round, so this needs no new turn loop. Player speed (haste, slow) is out of scope; when
it comes it should use the same rule in a shared scheduler.

### Distance (VB-58, built)

One range metric, `geometry.chebyshev(a, b) = max(|dx|, |dy|)`, for AI ranges, ability ranges,
the guard leash and the spawn distance. It matches 8-way movement and what the player sees.
Euclidean `dist2` stays only where it picks the best escape tile in `flee_from`.

### Validation (VB-59, built)

At load, raise `ContentValidationError` (as `create_monster` already does for unknown ids) for an
unknown `ai.type`, an unknown key in a monster's `ai:` block, or an `enabled: true` ability with
no registered `@ability`. Today a typo in `ai.type` silently becomes `aggressive` with a runtime
warning. `enabled: false` stays the honest marker for planned abilities.

## Tactics

After the engine work a behaviour is only movement and positioning:
`(ai, monster, params)`, using `ai.perceive`, `ai.move_towards`, `ai.flee_from`, `ai.wander`,
`ai.attack` (melee) and `ai.distance`. The classic five stay (with `passive` becoming neutral);
`sniper` becomes kiting (hold `ideal_range_min..max`) and `summoner` keep-away, with their attacks
moved into abilities. `berserker` keeps enrage as a tactics concern (it changes ranges), or
becomes a passive ability if more monsters need it.

## Abilities for any actor (VB-63)

Player abilities are already nearly actor-agnostic: `AbilityAction` reads the actor's
`abilities` and `cooldowns` stats. The player-only part is targeting (`force_bolt` picks "the
nearest monster"). The change:

- `context.hostiles_of(actor)`: players are hostile to monsters and the reverse. This also turns
  the special case in `move_action._handle_collision` (monsters don't bump-attack monsters) into
  a rule, and leaves room for charmed or allied monsters later.
- `@ability` gains target selection over `hostiles_of`, and a `should_use(context, actor, target)`
  hint. The fuzz bot's `ActionPlanner.ability_action` already follows the same shape for players.
- Engine step: a perceiving monster uses a ready, enabled ability before its tactics.
- Monster ability config comes from its `abilities:` block in `monsters.yaml`.

This ships with every monster ability still disabled, so it changes no gameplay by itself.

## Monster ability inventory

Declared in `monsters.yaml` today, all `enabled: false`. **Wave 1** abilities need no status
effects and are the suggested first ones to enable (VB-64, a design and balance call for Scott).

| Monster | Declared abilities | Wave 1 candidates |
|---|---|---|
| troll | regeneration | regeneration |
| spider | poison | — (needs status effects) |
| imp | teleport, fire_bolt | fire_bolt |
| wyvern | poison_sting, aerial_dive | aerial_dive |
| wraith | phase_shift, life_drain | life_drain |
| mimic | disguise, adhesive | — |
| vampire | life_drain, bat_swarm | life_drain, bat_swarm |
| lich | death_bolt, summon_undead, phylactery | death_bolt, summon_undead |
| demon | hellfire, teleport, fire_aura | fire_aura |
| basilisk | petrifying_gaze, poison_bite | — (needs status effects) |
| phoenix | rebirth, flame_aura, dive_bomb | flame_aura, dive_bomb |
| ancient_horror | reality_warp, summon_horrors, regeneration, phase_two | summon_horrors, regeneration, phase_two |

Goblin, orc, bat, skeleton, ogre, wolf and golem declare none. Wolf "pack tactics" and wraith
"phases through walls" appear only in flavour text; they would be a tactic and a movement rule
respectively, and are not planned.

## Later: status effects (VB-65)

Poison, stun, root (mimic adhesive) and petrify need timed effects on a target, and no such
primitive exists. Shape: a per-entity list of effects `(name, turns_left, magnitude)` kept in
stats (so saves carry it), ticked by the turn loop in both single-player and multiplayer, an
`@status_effect` registry, and action-gating effects (stun, root) checked in the action pipeline.
Player abilities (VB-53) can use the same system.

## Phasing

| Order | Task | Gameplay change | Ends with |
|---|---|---|---|
| 1 | VB-58 range metric | Yes (diagonal ranges) | Bot before/after |
| 2 | VB-59 parameters + validation | No (resolution only) | Tests |
| 3 | VB-60 perception + provocation | Yes (line of sight, real aggro ranges) | Bot before/after |
| 4 | VB-61 morale | Small (guards stop fleeing, sniper/defensive unchanged) | Bot before/after |
| 5 | VB-62 speed | Yes | Bot before/after |
| 6 | VB-63 abilities for any actor | No | Tests |
| 7 | VB-64 enable monster abilities | Yes, per ability | Bots + play-test |
| later | VB-65 status effects | Enables the rest | — |

Bot runs: `tests/fuzz/<class>_bot.py --games 8 --max-turns 3000` from a tree copy in tmux, all
four classes; see [../../tests/fuzz/README.md](../../tests/fuzz/README.md).

## Rejected alternatives

- **Patch each knob where it is read.** Fast, but leaves sensing and fleeing duplicated in every
  behaviour, which is how the knobs drifted in the first place.
- **A fixed pipeline that hands tactics a pre-chosen target.** Too rigid for enrage, leashes and
  per-behaviour reaction ranges. Perception is a toolkit call guarded by a contract test instead.
  Morale is the one forced step.
- **Provocation as a content event handler.** It would silently do nothing in multiplayer, which
  installs no content handlers (VB-55).
- **Copying YAML parameters into monster stats at spawn.** Freezes values into saves; runtime
  lookup by `content_id` with an optional override is both tunable and flexible.
- **A full energy scheduler for all actors now.** Correct eventually (haste, slow), but monsters
  alone fit inside `AISystem.update` today in both game modes.
- **Deleting `passive`.** With provocation tracked, a neutral type costs almost nothing.

## Side findings

- `AISystem.attack` discards the monster attack's `outcome.events`, so monster attacks never
  reach the event bus (VB-66).
- `AISystem.wander` moves in 4 directions only.
