"""Shared loot tables by monster family and depth-gated drops (VB-107 / VB-70)."""

import collections

import pytest
import yaml
from pathlib import Path

from core.loot import LootGenerator
from core.rng import GameRNG

DATA = Path(__file__).resolve().parents[2] / "data"
FAMILIES = {
    "beast": ("bat", "wolf", "spider", "basilisk"),
    "undead": ("skeleton", "vampire"),
    "brute": ("ogre", "golem"),
    "arcane": ("imp", "mimic", "demon"),
}


@pytest.fixture(scope="module")
def gen():
    return LootGenerator.get_instance()


def test_every_monster_has_a_loot_table(gen):
    monsters = yaml.safe_load((DATA / "entities" / "monsters.yaml").read_text())
    ids = [k for k, v in (monsters.get("monsters") or monsters).items() if isinstance(v, dict) and "hp" in str(v)]
    assert len(ids) >= 19
    missing = [m for m in ids if gen.loot_tables.get(gen.table_id_for(m)) is None]
    assert missing == []


@pytest.mark.parametrize("family,members", FAMILIES.items())
def test_family_members_share_their_table(gen, family, members):
    for m in members:
        assert gen.table_id_for(m) == family


@pytest.mark.parametrize("family", FAMILIES)
def test_family_tables_drop_only_consumables(gen, family):
    table = gen.loot_tables[family]
    for category, data in table.items():
        if category == "description":
            continue
        for entry in data["items"]:
            assert gen.items[entry["id"]]["item_type"] in ("potion", "food"), (family, entry["id"])


def _drops(gen, monster, floor, n=3000, seed=11):
    rng = GameRNG(seed)
    counts = collections.Counter()
    for _ in range(n):
        for item in gen.generate_loot(monster, floor, rng=rng):
            counts[item.content_id] += 1
    return counts


def test_min_floor_gates_drops_by_depth(gen):
    shallow = _drops(gen, "imp", floor=1)
    mid = _drops(gen, "imp", floor=10)
    deep = _drops(gen, "imp", floor=30)
    assert set(shallow) == {"potion_healing"}
    assert "potion_regeneration" in mid and "potion_extra_healing" in mid and "potion_full_healing" not in mid
    assert "potion_full_healing" in deep


def test_drop_rate_matches_the_table(gen):
    n = 3000
    drops = _drops(gen, "skeleton", floor=1, n=n)
    rate = sum(drops.values()) / n
    assert 0.12 < rate < 0.18               # undead potions: 15%


def test_beasts_drop_meat(gen):
    drops = _drops(gen, "wolf", floor=1)
    assert set(drops) <= {"meat", "ration"} and drops["meat"] > drops["ration"] > 0


def test_a_category_with_no_item_open_at_this_floor_drops_nothing(gen):
    data = {"items": [{"id": "potion_full_healing", "weight": 1, "min_floor": 30}]}
    assert gen._select_item_from_category(data, GameRNG(1), floor_number=5) is None
    assert gen._select_item_from_category(data, GameRNG(1), floor_number=30) == "potion_full_healing"
