"""
Extension points: how content plugs into the engine.

Game content (AI behaviours, class abilities, combat modifiers, item effects,
event handlers) lives in modules under ``core/content/`` and registers itself with a
decorator. The engine looks content up by name, so adding content means adding
one file; no core file changes. See docs/EXTENDING.md for worked examples.

    from ..extensions import ai_behavior

    @ai_behavior("sentry")
    def sentry(ai, monster, config):
        ...

Registries
----------
``ai_behaviors``      name -> fn(ai, monster, config)            (AISystem)
``abilities``         name -> fn(context, actor, config)         (AbilityAction)
``damage_modifiers``  name -> fn(actor, target, damage)          (AttackAction)
``item_effects``      name -> fn(context, actor, item)           (UseItemAction)
``event_handlers``    name -> class(context)                     (Game)

Every registry loads ``core.content`` on first lookup, so callers never have to
remember to import content. Registering the same name twice is an error unless
``replace=True`` (tests and deliberate overrides).
"""

import logging
from typing import Any, Callable, Dict, Iterator, List, Optional

from .events import EventBus, GameEventType

logger = logging.getLogger(__name__)

_EVENTS_ATTR = "_veinborn_event_types"


class ExtensionError(Exception):
    """Raised for invalid registrations (duplicate or empty names)."""


class Registry:
    """A name -> object map for one kind of content."""

    def __init__(self, kind: str):
        self.kind = kind
        self._items: Dict[str, Any] = {}

    def register(self, name: str, obj: Any, *, replace: bool = False) -> Any:
        if not name or not isinstance(name, str):
            raise ExtensionError(f"{self.kind} needs a non-empty string name, got {name!r}")
        if name in self._items and not replace:
            raise ExtensionError(
                f"{self.kind} '{name}' is already registered "
                f"(by {self._items[name]!r}); pass replace=True to override it"
            )
        self._items[name] = obj
        logger.debug(f"Registered {self.kind}: {name}")
        return obj

    def unregister(self, name: str) -> None:
        self._items.pop(name, None)

    def get(self, name: str, default: Any = None) -> Any:
        _ensure_content_loaded()
        return self._items.get(name, default)

    def names(self) -> List[str]:
        _ensure_content_loaded()
        return sorted(self._items)

    def items(self):
        _ensure_content_loaded()
        return sorted(self._items.items())

    def __contains__(self, name: str) -> bool:
        _ensure_content_loaded()
        return name in self._items

    def __iter__(self) -> Iterator[str]:
        return iter(self.names())

    def __len__(self) -> int:
        _ensure_content_loaded()
        return len(self._items)


ai_behaviors = Registry("AI behavior")
abilities = Registry("ability")
damage_modifiers = Registry("damage modifier")
item_effects = Registry("item effect")
event_handlers = Registry("event handler")


def _ensure_content_loaded() -> None:
    from .content import load_content
    load_content()


# ---------------------------------------------------------------------------
# Decorators
# ---------------------------------------------------------------------------

def ai_behavior(name: str, *, replace: bool = False) -> Callable:
    """Register ``fn(ai, monster, config)`` as AI behaviour ``name``.

    ``ai`` is the AISystem (its public methods are the toolkit: nearest_player,
    attack, move_towards, flee_from, wander, ...). ``config`` is the behaviour's
    section of ai_behaviors.yaml. A monster uses it via ``ai: type: name`` in
    monsters.yaml.
    """
    def decorator(fn: Callable) -> Callable:
        ai_behaviors.register(name, fn, replace=replace)
        return fn
    return decorator


def ability(name: str, *, replace: bool = False, should_use: Optional[Callable] = None) -> Callable:
    """Register ``fn(context, actor, config, target=None) -> ActionOutcome`` as ability ``name``.

    Any actor can use an ability: players (key z; config from formulas.yaml
    ``abilities.<name>``) and monsters (the AI; config resolved from the
    monster's behaviour and ``abilities:`` block). ``target`` is who the user
    aims at, or None to let the ability choose (``core.targeting``).

    The function only produces the effect. AbilityAction handles who may use
    it, the cooldown (``config['cooldown']``) and starting that cooldown when
    the outcome succeeds. Return ``ActionOutcome.failure(msg)`` to refuse
    without spending a turn.

    ``should_use(context, actor, config, target) -> bool`` tells the monster
    AI when using it is worthwhile; an ability without one is never used by
    monsters.
    """
    def decorator(fn: Callable) -> Callable:
        fn.should_use = should_use
        abilities.register(name, fn, replace=replace)
        return fn
    return decorator


def damage_modifier(name: str, *, replace: bool = False) -> Callable:
    """Register ``fn(actor, target, damage) -> (new_damage, verb) | None``.

    Applied by AttackAction to every player who has ability ``name`` in their
    class abilities. Return None when the modifier doesn't apply to this hit.
    ``verb`` replaces "hits" in the combat message (e.g. "backstabs").
    """
    def decorator(fn: Callable) -> Callable:
        damage_modifiers.register(name, fn, replace=replace)
        return fn
    return decorator


def item_effect(name: str, *, replace: bool = False) -> Callable:
    """Register ``fn(context, actor, item) -> ActionOutcome`` as item effect ``name``.

    An item uses the effect named by its ``effect:`` field in items.yaml (stored
    on the item entity as the ``effect`` stat); its numbers are the item's stats
    (``heal_amount``, ...). UseItemAction finds the item, calls the effect, and
    consumes the item only when the outcome succeeds. Return
    ``ActionOutcome.failure(msg)`` to refuse and keep the item.
    """
    def decorator(fn: Callable) -> Callable:
        item_effects.register(name, fn, replace=replace)
        return fn
    return decorator


def event_handler(cls=None, *, name: Optional[str] = None, replace: bool = False):
    """Register a class as a per-game event handler.

    One instance is created per game as ``cls(context)``; every method
    decorated with ``@on(...)`` is subscribed to the EventBus. Per-game state
    lives on the instance, so two games never share it.
    """
    def decorator(klass):
        event_handlers.register(name or klass.__name__, klass, replace=replace)
        return klass
    return decorator(cls) if cls is not None else decorator


def on(*event_types: GameEventType) -> Callable:
    """Mark a method of an @event_handler class as a handler for these events."""
    def decorator(fn: Callable) -> Callable:
        setattr(fn, _EVENTS_ATTR, tuple(event_types))
        return fn
    return decorator


# ---------------------------------------------------------------------------
# Event handler lifecycle
# ---------------------------------------------------------------------------

def _handler_methods(instance):
    for attr in dir(type(instance)):
        method = getattr(instance, attr)
        event_types = getattr(method, _EVENTS_ATTR, None)
        if event_types:
            yield method, event_types


def install_event_handlers(context, event_bus: EventBus) -> List[Any]:
    """Create one instance of every registered handler class and subscribe it.

    A handler that fails to construct is logged and skipped; it never stops the
    game from starting. Returns the instances (keep them: the bus holds only
    bound methods, and tests inspect them).
    """
    instances = []
    for name, klass in event_handlers.items():
        try:
            instance = klass(context)
        except Exception:
            logger.exception(f"Event handler '{name}' failed to initialise; skipped")
            continue
        for method, event_types in _handler_methods(instance):
            for event_type in event_types:
                event_bus.subscribe(
                    event_type, method, subscriber_name=f"{name}.{method.__name__}"
                )
        instances.append(instance)
    logger.info(f"Installed {len(instances)} event handler(s): {[type(i).__name__ for i in instances]}")
    return instances


def uninstall_event_handlers(instances: List[Any], event_bus: EventBus) -> None:
    """Unsubscribe instances made by install_event_handlers (before re-installing)."""
    for instance in instances:
        for method, event_types in _handler_methods(instance):
            for event_type in event_types:
                event_bus.unsubscribe(event_type, method)
