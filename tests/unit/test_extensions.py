"""The extension registries and content discovery (core.extensions, core.content)."""

import pytest

from core import content
from core.events import EventBus, GameEvent, GameEventType
from core.extensions import (
    ExtensionError, Registry, ai_behaviors, abilities, damage_modifiers, event_handlers,
    event_handler, on, install_event_handlers, uninstall_event_handlers,
)

pytestmark = pytest.mark.unit


# --- Registry ---------------------------------------------------------------

def test_register_and_get():
    registry = Registry("thing")
    registry.register("a", 1)
    assert registry.get("a") == 1 and "a" in registry and registry.names() == ["a"]


def test_duplicate_name_is_an_error_naming_the_first_owner():
    registry = Registry("thing")
    registry.register("a", 1)
    with pytest.raises(ExtensionError, match="already registered"):
        registry.register("a", 2)
    assert registry.get("a") == 1


def test_replace_overrides():
    registry = Registry("thing")
    registry.register("a", 1)
    registry.register("a", 2, replace=True)
    assert registry.get("a") == 2


@pytest.mark.parametrize("bad", ["", None, 5])
def test_names_must_be_non_empty_strings(bad):
    with pytest.raises(ExtensionError):
        Registry("thing").register(bad, 1)


# --- content discovery --------------------------------------------------------

def test_all_shipped_content_is_discovered():
    assert {"aggressive", "defensive", "passive", "coward", "guard",
            "berserker", "sniper", "summoner"} <= set(ai_behaviors.names())
    assert {"force_bolt", "heal"} <= set(abilities.names())
    assert "backstab" in damage_modifiers
    assert {"AchievementTracker", "QuestTracker", "KillStreaks"} <= set(event_handlers.names())


def test_loading_content_twice_is_harmless():
    before = ai_behaviors.names()
    content.load_content()
    content.load_content()
    assert ai_behaviors.names() == before


def test_no_shipped_content_module_failed_to_load():
    ai_behaviors.names()  # force the load
    assert content.failed_modules == {}


def test_every_ability_in_a_class_template_is_registered_or_a_modifier():
    from core.character_class import CLASS_TEMPLATES
    known = set(abilities.names()) | set(damage_modifiers.names())
    for template in CLASS_TEMPLATES.values():
        assert set(template.abilities) <= known, template.name


def test_every_ability_has_tuning_in_formulas_yaml():
    from core.config.config_loader import ConfigLoader
    config = ConfigLoader.get_config()
    for name in set(abilities.names()) | set(damage_modifiers.names()):
        assert config.get_ability_config(name) is not None


# --- event handler lifecycle ----------------------------------------------------

class _Ctx:
    pass


def _temp_handler_class(registry_name, log):
    @event_handler(name=registry_name, replace=True)
    class Temp:
        def __init__(self, context):
            self.context = context

        @on(GameEventType.TURN_ENDED)
        def seen(self, event):
            log.append(event.turn)

        @on(GameEventType.ENTITY_DIED, GameEventType.FLOOR_CHANGED)
        def multi(self, event):
            log.append(event.event_type)
    return Temp


@pytest.fixture
def temp_handlers():
    names = []
    yield names
    for name in names:
        event_handlers.unregister(name)


def test_install_subscribes_every_marked_method(temp_handlers):
    log = []
    temp_handlers.append("_Temp")
    _temp_handler_class("_Temp", log)
    bus = EventBus()
    install_event_handlers(_Ctx(), bus)

    bus.publish(GameEvent(GameEventType.TURN_ENDED, {}, turn=4))
    bus.publish(GameEvent(GameEventType.ENTITY_DIED, {}))
    bus.publish(GameEvent(GameEventType.FLOOR_CHANGED, {}))
    assert log == [4, GameEventType.ENTITY_DIED, GameEventType.FLOOR_CHANGED]


def test_uninstall_stops_delivery_and_reinstall_does_not_double(temp_handlers):
    log = []
    temp_handlers.append("_Temp")
    _temp_handler_class("_Temp", log)
    bus = EventBus()
    first = install_event_handlers(_Ctx(), bus)
    uninstall_event_handlers(first, bus)
    install_event_handlers(_Ctx(), bus)

    bus.publish(GameEvent(GameEventType.TURN_ENDED, {}, turn=1))
    assert log == [1]  # delivered once, not twice


def test_handler_that_cannot_construct_is_skipped_not_fatal(temp_handlers):
    temp_handlers.append("_Broken")

    @event_handler(name="_Broken", replace=True)
    class Broken:
        def __init__(self, context):
            raise RuntimeError("boom")

    instances = install_event_handlers(_Ctx(), EventBus())
    assert not any(isinstance(i, Broken) for i in instances)
    assert instances  # the real handlers still installed


def test_handler_state_is_per_game_instance():
    from core.content.events.achievements import AchievementTracker
    a, b = AchievementTracker(_Ctx()), AchievementTracker(_Ctx())
    a.stats["kills"] = 99
    assert b.stats["kills"] == 0
