"""
Tests for GameRNG (Random Number Generator with seeding).

Tests:
- Initialization with different seed types
- Determinism (same seed = same sequence)
- Uniqueness (different seeds = different sequences)
- All random methods
- Save/load state preservation
- Singleton behavior
- String seed conversion
"""

import pytest
from src.core.rng import GameRNG


class TestGameRNGInitialization:
    """Test RNG initialization with different seed types."""

    def test_initialize_with_no_seed(self):
        """Test initialization without seed (random)."""
        rng = GameRNG.initialize()
        assert rng is not None
        assert rng.seed is None
        assert rng.original_seed is None

    def test_initialize_with_int_seed(self):
        """Test initialization with integer seed."""
        rng = GameRNG.initialize(seed=12345)
        assert rng.seed == 12345
        assert rng.original_seed == 12345

    def test_initialize_with_string_seed(self):
        """Test initialization with string seed."""
        rng = GameRNG.initialize(seed="epic-run")
        assert rng.original_seed == "epic-run"
        assert isinstance(rng.seed, int)
        assert rng.seed > 0  # Positive integer

    def test_get_instance_returns_same_instance(self):
        """Test singleton behavior."""
        GameRNG.initialize(seed=123)
        rng1 = GameRNG.get_instance()
        rng2 = GameRNG.get_instance()
        assert rng1 is rng2

    def test_reset_clears_instance(self):
        """Test reset clears singleton."""
        GameRNG.initialize(seed=123)
        GameRNG.reset()
        # After reset, get_instance creates new instance
        rng = GameRNG.get_instance()
        assert rng.seed is None  # New instance has no seed


class TestGameRNGDeterminism:
    """Test that same seed produces same random sequence."""

    def test_same_seed_same_sequence(self):
        """Test same seed produces identical random sequences."""
        # Run 1
        GameRNG.initialize(seed=12345)
        rng1 = GameRNG.get_instance()
        seq1 = [rng1.randint(1, 100) for _ in range(20)]

        # Run 2
        GameRNG.initialize(seed=12345)
        rng2 = GameRNG.get_instance()
        seq2 = [rng2.randint(1, 100) for _ in range(20)]

        # Should be identical
        assert seq1 == seq2

    def test_different_seeds_different_sequences(self):
        """Test different seeds produce different sequences."""
        # Seed 1
        GameRNG.initialize(seed=111)
        rng1 = GameRNG.get_instance()
        seq1 = [rng1.randint(1, 1000) for _ in range(50)]

        # Seed 2
        GameRNG.initialize(seed=222)
        rng2 = GameRNG.get_instance()
        seq2 = [rng2.randint(1, 1000) for _ in range(50)]

        # Should be different (statistically very unlikely to be same)
        assert seq1 != seq2

    def test_string_seed_determinism(self):
        """Test string seeds are deterministic."""
        # Run 1
        GameRNG.initialize(seed="my-awesome-run")
        rng1 = GameRNG.get_instance()
        seq1 = [rng1.random() for _ in range(10)]

        # Run 2
        GameRNG.initialize(seed="my-awesome-run")
        rng2 = GameRNG.get_instance()
        seq2 = [rng2.random() for _ in range(10)]

        # Same string seed = same sequence
        assert seq1 == seq2


class TestGameRNGMethods:
    """Test all RNG methods work correctly."""

    def setup_method(self):
        """Reset RNG before each test."""
        GameRNG.reset()

    def test_randint(self):
        """Test randint generates integers in range."""
        rng = GameRNG.initialize(seed=123)
        values = [rng.randint(1, 10) for _ in range(100)]

        # All values in range
        assert all(1 <= v <= 10 for v in values)

        # Check we get variety (not all same)
        assert len(set(values)) > 1

    def test_random(self):
        """Test random generates floats in [0, 1)."""
        rng = GameRNG.initialize(seed=456)
        values = [rng.random() for _ in range(100)]

        # All values in range
        assert all(0.0 <= v < 1.0 for v in values)

        # Check we get variety
        assert len(set(values)) > 10  # Should have many unique values

    def test_uniform(self):
        """Test uniform generates floats in range."""
        rng = GameRNG.initialize(seed=789)
        values = [rng.uniform(10.0, 20.0) for _ in range(100)]

        # All values in range
        assert all(10.0 <= v <= 20.0 for v in values)

        # Check we get variety
        assert len(set(values)) > 10

    def test_choice(self):
        """Test choice selects from sequence."""
        rng = GameRNG.initialize(seed=101)
        items = ['a', 'b', 'c', 'd', 'e']
        choices = [rng.choice(items) for _ in range(50)]

        # All choices are from items
        assert all(c in items for c in choices)

        # Check we get variety (not all same)
        assert len(set(choices)) > 1

    def test_choices_with_weights(self):
        """Test choices with weights."""
        rng = GameRNG.initialize(seed=202)
        population = ['common', 'rare', 'epic']
        weights = [70, 20, 10]  # Common most likely

        results = rng.choices(population, weights=weights, k=100)

        # All from population
        assert all(r in population for r in results)

        # 'common' should appear most often (due to weights)
        assert results.count('common') > results.count('rare')
        assert results.count('rare') > results.count('epic')

    def test_shuffle(self):
        """Test shuffle randomizes sequence."""
        rng = GameRNG.initialize(seed=303)
        items = list(range(20))
        original = items.copy()

        rng.shuffle(items)

        # Same elements, different order
        assert set(items) == set(original)
        assert items != original  # Should be shuffled

    def test_sample(self):
        """Test sample returns unique elements."""
        rng = GameRNG.initialize(seed=404)
        population = list(range(100))

        sample = rng.sample(population, k=10)

        # Correct size
        assert len(sample) == 10

        # All unique
        assert len(set(sample)) == 10

        # All from population
        assert all(s in population for s in sample)


class TestGameRNGSaveLoad:
    """Test RNG state save/load functionality."""

    def test_getstate_setstate(self):
        """Test saving and restoring RNG state."""
        # Create RNG and generate some values
        GameRNG.initialize(seed=12345)
        rng = GameRNG.get_instance()

        # Generate some values
        before = [rng.randint(1, 100) for _ in range(10)]

        # Save state
        state = rng.getstate()

        # Generate more values
        middle = [rng.randint(1, 100) for _ in range(10)]

        # Restore state
        rng.setstate(state)

        # Generate values again (should match middle)
        after = [rng.randint(1, 100) for _ in range(10)]

        # After restoring state, should get same sequence as middle
        assert after == middle

    def test_state_preservation_across_reinit(self):
        """Test that reinitializing with same seed gives same initial state."""
        # Init 1
        GameRNG.initialize(seed=55555)
        rng1 = GameRNG.get_instance()
        seq1 = [rng1.randint(1, 100) for _ in range(20)]

        # Init 2 (same seed)
        GameRNG.initialize(seed=55555)
        rng2 = GameRNG.get_instance()
        seq2 = [rng2.randint(1, 100) for _ in range(20)]

        # Should match
        assert seq1 == seq2


class TestGameRNGDisplay:
    """Test display and debugging features."""

    def test_get_seed_display_with_int(self):
        """Test seed display with integer seed."""
        rng = GameRNG.initialize(seed=12345)
        assert rng.get_seed_display() == "Seed: 12345"

    def test_get_seed_display_with_string(self):
        """Test seed display with string seed."""
        rng = GameRNG.initialize(seed="epic-run-2025")
        assert rng.get_seed_display() == "Seed: epic-run-2025"

    def test_get_seed_display_with_none(self):
        """Test seed display with no seed."""
        rng = GameRNG.initialize()
        assert rng.get_seed_display() == "Seed: random"

    def test_repr(self):
        """Test string representation."""
        rng = GameRNG(seed=123)
        assert "123" in repr(rng)

        rng2 = GameRNG(seed="test")
        assert "test" in repr(rng2)

        rng3 = GameRNG()
        assert "None" in repr(rng3)


class TestGameRNGEdgeCases:
    """Test edge cases and error conditions."""

    def test_choice_empty_sequence_raises(self):
        """Test choice on empty sequence raises error."""
        rng = GameRNG.initialize(seed=123)
        with pytest.raises(IndexError):
            rng.choice([])

    def test_sample_k_larger_than_population_raises(self):
        """Test sample with k > population size raises error."""
        rng = GameRNG.initialize(seed=456)
        with pytest.raises(ValueError):
            rng.sample([1, 2, 3], k=10)

    def test_randint_with_a_greater_than_b(self):
        """Test randint raises error when a > b."""
        rng = GameRNG.initialize(seed=789)
        # Python's randint raises ValueError if a > b
        with pytest.raises(ValueError):
            rng.randint(10, 1)


class TestGameRNGIntegration:
    """Integration tests for RNG with game systems."""

    def test_same_seed_same_map_layout(self):
        """
        Test that same seed produces same map layout.

        This is an integration test that verifies the RNG works
        correctly with the actual game systems.
        """
        from src.core.game import Game

        # Game 1
        game1 = Game()
        game1.start_new_game(seed=99999)
        monsters1 = [m.name for m in game1.context.get_entities_by_type(1)]
        ore_types1 = [o.stats.get('ore_type') for o in game1.context.get_entities_by_type(2)]

        # Game 2 (same seed)
        game2 = Game()
        game2.start_new_game(seed=99999)
        monsters2 = [m.name for m in game2.context.get_entities_by_type(1)]
        ore_types2 = [o.stats.get('ore_type') for o in game2.context.get_entities_by_type(2)]

        # Same seed = same monsters and ore
        assert monsters1 == monsters2
        assert ore_types1 == ore_types2

    def test_different_seeds_different_maps(self):
        """Test that different seeds produce different maps."""
        from src.core.game import Game

        # Game 1
        game1 = Game()
        game1.start_new_game(seed=111111)
        # Get room positions (deterministic part of map generation)
        rooms1 = [(r.x, r.y, r.width, r.height) for r in game1.state.dungeon_map.rooms]

        # Game 2 (different seed)
        game2 = Game()
        game2.start_new_game(seed=222222)
        rooms2 = [(r.x, r.y, r.width, r.height) for r in game2.state.dungeon_map.rooms]

        # Different seeds = different room layouts
        assert rooms1 != rooms2

    def test_seed_stored_in_game_state(self):
        """Test that seed is properly stored in GameState."""
pytestmark = pytest.mark.unit

        from src.core.game import Game

        game = Game()
        game.start_new_game(seed=12345)

        # Check seed is stored
        assert game.state.seed == 12345

    def test_string_seed_stored_correctly(self):
        """Test that string seed is stored with original form."""
        from src.core.game import Game

        game = Game()
        game.start_new_game(seed="my-awesome-seed")

        # Check original seed is preserved
        assert game.state.seed == "my-awesome-seed"
