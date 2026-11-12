"""Floor bands (src/core/config/floor_bands.py): range-keyed balance tables."""

import copy

import pytest

from core.config import ConfigLoader, GameConfig
from core.config.floor_bands import band_for_floor, parse_band, validate_bands
from core.entity_loader import EntityLoader
from core.exceptions import ContentValidationError
from core.spawning.entity_spawner import EntitySpawner

pytestmark = pytest.mark.unit


def test_parse_band_key_forms():
    assert parse_band('floor_1') == (1, 1)
    assert parse_band('floors_3_5') == (3, 5)
    assert parse_band('floors_16_plus') == (16, None)


@pytest.mark.parametrize('key', ['floor_one', 'floors_5_3', 'floors_3', 'late_game', 'description'])
def test_parse_band_rejects_non_band_keys(key):
    with pytest.raises(ContentValidationError):
        parse_band(key)


@pytest.mark.parametrize('table, problem', [
    ({'floors_2_plus': 1}, 'uncovered'),                       # does not start at 1
    ({'floor_1': 1, 'floors_3_plus': 1}, 'uncovered'),         # gap at 2
    ({'floors_1_3': 1, 'floors_3_plus': 1}, 'overlaps'),       # 3 twice
    ({'floor_1': 1, 'floors_2_5': 1}, 'open-ended'),           # nothing past 5
    ({'floors_1_plus': 1, 'floors_5_plus': 1}, 'open-ended'),  # band after an open one
])
def test_validate_bands_rejects_bad_coverage(table, problem):
    with pytest.raises(ContentValidationError, match=problem):
        validate_bands(table, 'test')


def test_band_for_floor_is_key_order_independent():
    table = {'floors_6_plus': 'deep', 'floor_1': 'first', 'floors_2_5': 'mid'}
    validate_bands(table, 'test')
    assert [band_for_floor(table, f) for f in (1, 2, 5, 6, 100)] == ['first', 'mid', 'mid', 'deep', 'deep']


def test_shipped_tables_cover_every_floor_to_victory():
    config = ConfigLoader.get_config()
    victory = config.game_constants['progression']['victory_floor']
    for floor in range(1, victory + 1):
        assert config.get_monster_count_for_floor(floor) > 0
        assert config.get_monster_spawn_weights(floor)
        assert config.get_ore_spawn_weights(floor)


def test_a_new_band_needs_only_yaml():
    """Splitting floors_16_plus into two bands changes the deep floors with no code change."""
    base = ConfigLoader.get_config()
    spawns = copy.deepcopy(base.monster_spawns)
    weights = spawns['spawn_weights']
    weights['floors_16_30'] = weights.pop('floors_16_plus')
    weights['floors_31_plus'] = {'golem': 1}
    config = GameConfig(**{**base.__dict__, 'monster_spawns': spawns})
    assert config.get_monster_spawn_weights(20) == base.get_monster_spawn_weights(20)
    assert config.get_monster_spawn_weights(31) == {'golem': 1}


def test_config_rejects_a_gap_at_load():
    base = ConfigLoader.get_config()
    spawns = copy.deepcopy(base.monster_spawns)
    spawns['spawn_weights']['floors_17_plus'] = spawns['spawn_weights'].pop('floors_16_plus')
    with pytest.raises(ContentValidationError, match='floors 16-16 uncovered'):
        GameConfig(**{**base.__dict__, 'monster_spawns': spawns})


def test_spawner_rejects_an_undefined_monster_id():
    base = ConfigLoader.get_config()
    spawns = copy.deepcopy(base.monster_spawns)
    spawns['spawn_weights']['floor_1']['gobln'] = 5
    config = GameConfig(**{**base.__dict__, 'monster_spawns': spawns})
    with pytest.raises(ContentValidationError, match='gobln'):
        EntitySpawner(config, EntityLoader())
