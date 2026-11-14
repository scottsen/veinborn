"""Timed status effects on entities (VB-65 / VB-107).

An effect is ``{'name', 'turns_left', 'magnitude'}`` in ``actor.stats['effects']``, so it is
saved with the entity and needs no new persistence. What an effect does each turn is a
``@status_effect`` function (``core/content/status/``). ``TurnProcessor`` calls
``tick_effects`` for every living actor once per turn.

Applying an effect that is already active refreshes it: the longer duration and the larger
magnitude win, so drinking a second potion never stacks into something stronger than the
best one.
"""

import logging
from typing import List, Optional

from .extensions import status_effects

logger = logging.getLogger(__name__)


def effects_of(actor) -> List[dict]:
    """The actor's active effects (the live list; empty if none)."""
    return actor.stats.get('effects') or []


def has_effect(actor, name: str) -> bool:
    return any(e['name'] == name for e in effects_of(actor))


def add_effect(actor, name: str, turns: int, magnitude: int = 1) -> dict:
    """Start (or refresh) effect `name` for `turns` turns. Unknown names are an error."""
    if name not in status_effects:
        raise KeyError(f"unknown status effect {name!r}")
    effects = actor.stats.setdefault('effects', [])
    for effect in effects:
        if effect['name'] == name:
            effect['turns_left'] = max(effect['turns_left'], turns)
            effect['magnitude'] = max(effect['magnitude'], magnitude)
            return effect
    effect = {'name': name, 'turns_left': turns, 'magnitude': magnitude}
    effects.append(effect)
    return effect


def remove_effect(actor, name: str) -> None:
    effects = effects_of(actor)
    actor.stats['effects'] = [e for e in effects if e['name'] != name]


def tick_effects(context, actor) -> List[str]:
    """Run one turn of every effect on `actor`, count them down, drop the finished ones.

    Returns the messages the effects produced. An effect function that raises is logged and
    skipped for the turn; it still counts down, so a broken one cannot stick forever.
    """
    effects = effects_of(actor)
    if not effects:
        return []
    messages: List[str] = []
    for effect in list(effects):
        fn = status_effects.get(effect['name'])
        if fn is not None:
            try:
                message: Optional[str] = fn(context, actor, effect)
                if message:
                    messages.append(message)
            except Exception:
                logger.exception(f"status effect {effect['name']} failed on {actor.name}")
        effect['turns_left'] -= 1
        if effect['turns_left'] <= 0:
            effects.remove(effect)
            label = getattr(fn, 'label', effect['name'])
            messages.append(f"{actor.name}: {label} fades.")
    return messages
