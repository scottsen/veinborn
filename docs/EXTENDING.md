---
title: "Extending Veinborn: adding content in Python"
type: guide
beth_topics:
  - veinborn
  - extensibility
  - modding
  - ai-behavior
  - abilities
  - event-handlers
  - content
---

# Extending Veinborn

Veinborn is extended in plain Python. Game content lives in modules under
`src/core/content/` and registers itself with a decorator; the engine looks it up
by name. **Adding content means adding one file. No core file changes.**

(Veinborn used to have a Lua scripting layer. It was removed on 2026-11-11: it had
never run end to end, and a second language cost more than it gave a one-author
game. See `docs/architecture/DECISIONS.md`, ADR-018.)

## What goes where

| You want to add | How | Where |
|---|---|---|
| A monster, item, ore, recipe, loot table | Data (YAML) | `data/entities/`, `data/balance/`; see [CONTENT_CREATION.md](CONTENT_CREATION.md) |
| A monster AI behaviour | `@ai_behavior("name")` | `src/core/content/ai/` |
| An ability (a player presses z for it; monsters use it too) | `@ability("name", should_use=...)` | `src/core/content/abilities/` |
| A passive combat effect (like backstab) | `@damage_modifier("name")` | `src/core/content/abilities/` |
| Something that reacts to game events (achievements, quests, ...) | `@event_handler` class with `@on(...)` methods | `src/core/content/events/` |

Everything in `src/core/content/` is imported automatically on the first lookup
(`core.content.load_content()`), and the decorators in `core.extensions` do the
registering. A content module that fails to import is logged and skipped, and one
that raises while running is logged and skipped for that turn or event; neither
stops the game. Registering a name twice is an error (pass `replace=True` to
override on purpose).

## Add an AI behaviour

A behaviour is a function `(ai, monster, config)`. `ai` is the `AISystem`; its
public methods are the toolkit:

- `perceive(monster, config)`: the player this monster knows about, or `None`: one it
  can see (within `aggro_range`, line of sight), or one it saw or was attacked by in
  the last `memory_turns` turns. **Start every behaviour here**; the contract test in
  `tests/unit/systems/test_ai_perception.py` runs every registered behaviour and fails
  one that attacks or approaches a player it cannot perceive.
- `provoked_by(monster, config)`: whoever attacked it within `memory_turns`, or `None`.
- `distance` (8-way steps, Chebyshev), `in_sight`, `attack(monster, target, ranged=False)`,
  `move_towards(monster, target, leash=None)`, `flee_from`, `wander`,
  `summon(monster, monster_id)`, `abilities_for(monster)`.
- `nearest_player` ignores perception; behaviours should not use it.

Ranges in a behaviour's own section are engagement policy (when to fight what it
perceives), not perception. Don't write "flee when hurt" in a behaviour: the engine's
morale step does it for every behaviour, from the `flee_threshold` parameter, before the
behaviour runs.

`config` is the monster's resolved parameters (`AISystem.params_for`): the universal
`defaults` and the behaviour's section of `data/balance/ai_behaviors.yaml`, overridden
by the monster's `ai:` block in `monsters.yaml`, overridden by an `ai_params` stat on
that monster. Monster AI data is validated at game start: an unknown `ai.type`, an `ai:`
key that is neither universal (the keys of `defaults`) nor a key of the behaviour's
section, or an `enabled: true` ability with no `@ability` stops the game with a
`ContentValidationError`.

> **Design (ADR-019, [architecture/AI_ARCHITECTURE.md](architecture/AI_ARCHITECTURE.md)):**
> a behaviour is tactics only: where to stand. The engine owns perception, morale, speed
> and ability use; ranged attacks and summons are abilities (see "Add an ability"). A
> behaviour runs once per *action*, and a monster takes `move_speed` actions per round on
> average.

```python
# src/core/content/ai/sentry.py
from ...extensions import ai_behavior


@ai_behavior("sentry")
def sentry(ai, monster, config):
    """Stands still; shoots anything that comes into view."""
    player = ai.perceive(monster, config)
    if player and ai.distance(monster, player) <= config.get('range', 6) and ai.in_sight(monster, player):
        ai.attack(monster, player, ranged=True)
```

```yaml
# data/balance/ai_behaviors.yaml
  sentry:
    description: "Stationary shooter"
    range: 6
```

Then give a monster `ai: type: "sentry"` in `data/entities/monsters.yaml`. Look at
`content/ai/classic.py`, `berserker.py`, `sniper.py` and `summoner.py` for worked
examples. Keep per-monster state in `monster.set_stat(...)` (stats are saved). A sentry
that shoots is better written as tactics plus the `ranged_attack` ability, as the sniper
is: then any monster can be given the shot without a new behaviour.

## Add an ability

Any actor can use an ability: a player (key **z**) or a monster (the AI). An ability
function does only the effect: `(context, actor, config, target=None) -> ActionOutcome`.
`target` is who the user aims at, or `None` to let the ability choose; the helpers in
`core/targeting.py` (`aim`, `valid_target`, `nearest_hostile_in_sight`) pick among the
actor's hostiles (`context.hostiles_of`) using the game's range metric and line of sight.
`AbilityAction` checks the actor has it and that it is off cooldown, runs your function,
and starts the cooldown (`config['cooldown']`) if you returned a success. Return
`ActionOutcome.failure("reason")` to refuse without spending a turn.

`should_use(context, actor, config, target) -> bool` tells the monster AI when using it
is worthwhile. An ability without one is never used by monsters.

```python
# src/core/content/abilities/second_wind.py
from ...base.action import ActionOutcome
from ...extensions import ability


def _winded(context, actor, config, target):
    return actor.hp < actor.max_hp // 2


@ability("second_wind", should_use=_winded)
def second_wind(context, actor, config, target=None) -> ActionOutcome:
    if actor.hp >= actor.max_hp // 2:
        return ActionOutcome.failure("You still have wind left.")
    healed = actor.heal(config['amount'])
    outcome = ActionOutcome.success(took_turn=True)
    outcome.messages.append(f"{actor.name} catches a second wind (+{healed} HP).")
    return outcome
```

For a **player class**:
1. Add its numbers to `data/balance/formulas.yaml` under `abilities:` (`second_wind: {amount: 8, cooldown: 30}`).
2. Add `"second_wind"` to a class's `abilities` list in `src/core/character_class.py`.
3. Players press **z** to use their first active ability (`handle_player_action('ability')`, or `ability='second_wind'` to pick one).

For a **monster**, enable it in its `abilities:` block in `monsters.yaml`; keys there
override the shared `formulas.yaml` numbers:

```yaml
  troll:
    abilities:
      second_wind:
        enabled: true
        amount: 12
        cooldown: 20
```

A **behaviour** can also bring abilities to every monster that uses it (`abilities:` in
its `ai_behaviors.yaml` section, e.g. the sniper's `ranged_attack`, the summoner's
`summon`); a monster can disable one with `enabled: false`. Each action, after morale,
the engine uses the first ready ability whose `should_use` says yes against the player
the monster perceives, and only otherwise runs its behaviour (`AISystem.abilities_for`,
`_use_ability`). Monster AI validation fails the game at start if an enabled or brought
ability has no `@ability`.

`content/abilities/force_bolt.py`, `heal.py`, `ranged_attack.py` and `summon.py` are the
worked examples.

## Add a passive combat effect

`@damage_modifier("name")` registers `fn(actor, target, damage) -> (new_damage, verb) | None`.
`AttackAction` applies it for any player who has `"name"` in their class abilities.
Return `None` when it doesn't apply to this hit. `content/abilities/backstab.py` is
the example.

## Add an event handler

An event handler is a class built once per game as `cls(context)`; each method
marked `@on(...)` is subscribed to the `EventBus`. State lives on the instance, so
games never share it.

```python
# src/core/content/events/first_blood.py
from ...events import GameEventType
from ...extensions import event_handler, on
from .common import player_kill


@event_handler
class FirstBlood:
    def __init__(self, context):
        self.context = context
        self.done = False

    @on(GameEventType.ENTITY_DIED)
    def on_entity_died(self, event):
        if not self.done and player_kill(self.context, event):
            self.done = True
            self.context.add_message("First blood!")
```

Events the single-player game publishes: `game_started`, `turn_ended` (data `turn`),
`floor_changed` (`from_floor`, `to_floor`), `entity_died` (`entity_id`, `entity_name`,
`killer_id`), `attack_resolved`, `equipment_crafted`, `ore_mined`, `ore_surveyed`
(see `GameEventType` for the full list and the `create_*_event` helpers).
`killer_id` is an entity id (a UUID), never a fixed string: use `player_kill()` from
`content/events/common.py` to ask "did a player do this?".

Shipped handlers to copy from: `achievements.py`, `quests.py`, `kill_streaks.py`.
Their state is per game and is not written to save files.

## Testing content

- Call a behaviour through a real game: see `tests/unit/content/test_ai_content.py`
  (`spawn(game, "berserker", 3)`, then `run_ai(game, turns)`).
- Publish a synthetic event and check the handler's state:
  `game.event_bus.publish(GameEvent(GameEventType.ENTITY_DIED, {...}))`; see
  `tests/unit/content/test_event_content.py`.
- `tests/unit/test_extensions.py` already checks that every shipped content module
  loads, that every ability in a class template is registered, and that every
  ability has tuning numbers, so a typo shows up there.
- Use the `sure_hit` fixture (`tests/conftest.py`) when a test is about something
  other than the combat dice.
- To measure a balance change: `python3 scripts/sim_duels.py` (see
  [MECHANICS_REFERENCE.md](MECHANICS_REFERENCE.md)).

## Rules of the road

- **Keep per-game state on the instance or on entity stats** (`entity.set_stat`),
  never in module globals; two games (or a loaded save) must not share it.
- **Use the toolkit and `GameContext`**, not engine internals, so engine changes
  don't break content.
- **Put tuning numbers in YAML**, not in the function, so balance can change
  without code.
- **Don't touch the combat dice or turn loop from content.** Those stay in the
  engine so they are deterministic and covered by tests.
- **Multiplayer:** the server's `AISystem` loads the same behaviours, but the
  server does not install event handlers or publish `turn_ended` /
  `floor_changed` / `game_started` yet (VB-55); content events are single-player
  for now.
