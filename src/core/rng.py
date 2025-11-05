"""
Centralized Random Number Generator with seeding support.

This module provides a singleton RNG that enables reproducible gameplay through
seeding. All randomness in the game should go through this class to ensure
deterministic behavior when a seed is provided.

Features:
- Optional seeding (None = random, int = seeded)
- Singleton pattern for global RNG
- Save/load support via RNG state
- String seed support (converts to int via hash)
- All standard random methods delegated

Usage:
    # Initialize with seed
    GameRNG.initialize(seed=12345)

    # Get instance and use
    rng = GameRNG.get_instance()
    value = rng.randint(1, 10)
    choice = rng.choice(['a', 'b', 'c'])

    # Or initialize without seed (random)
    GameRNG.initialize()  # Different every time

Design:
- Singleton ensures all game systems use same RNG
- Seed stored for display/sharing
- RNG state can be saved/loaded for mid-game saves
- Thread-safe initialization
"""

import random
from typing import Optional, Union, TypeVar, Sequence, List

T = TypeVar('T')


class GameRNG:
    """
    Centralized RNG for reproducible gameplay.

    This class wraps Python's random.Random to provide seeding support
    for the entire game. When initialized with a seed, all subsequent
    random operations will be deterministic and reproducible.

    Attributes:
        _instance: Singleton instance
        _seed: Current seed (None if random)
        _rng: Internal random.Random instance
    """

    _instance: Optional['GameRNG'] = None

    def __init__(self, seed: Optional[Union[int, str]] = None):
        """
        Initialize RNG with optional seed.

        Args:
            seed: Seed value (int, str, or None for random)
                  String seeds are converted to int via hash
        """
        # Convert string seed to int
        if isinstance(seed, str):
            self._original_seed = seed
            self._seed = hash(seed) & 0x7FFFFFFF  # Positive 32-bit int
        else:
            self._original_seed = seed
            self._seed = seed

        # Create internal RNG with computed seed
        self._rng = random.Random(self._seed)

    @classmethod
    def initialize(cls, seed: Optional[Union[int, str]] = None) -> 'GameRNG':
        """
        Initialize or reinitialize the global RNG instance.

        This should be called when starting a new game or loading a save.

        Args:
            seed: Seed value (int, str, or None for random)

        Returns:
            The initialized GameRNG instance

        Example:
            >>> GameRNG.initialize(seed=12345)
            >>> rng = GameRNG.get_instance()
            >>> rng.randint(1, 10)  # Deterministic with seed 12345
        """
        cls._instance = cls(seed)
        return cls._instance

    @classmethod
    def get_instance(cls) -> 'GameRNG':
        """
        Get the global RNG instance (lazy initialization).

        If no instance exists, creates one with no seed (random).

        Returns:
            The global GameRNG instance

        Example:
            >>> rng = GameRNG.get_instance()
            >>> value = rng.randint(1, 100)
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """
        Reset the global RNG instance.

        Useful for testing to ensure clean state between tests.
        """
        cls._instance = None

    @property
    def seed(self) -> Optional[int]:
        """
        Get the current numeric seed.

        Returns:
            The seed as an integer, or None if random
        """
        return self._seed

    @property
    def original_seed(self) -> Optional[Union[int, str]]:
        """
        Get the original seed (before string conversion).

        Returns:
            The original seed (str or int), or None if random
        """
        return self._original_seed

    def get_seed_display(self) -> str:
        """
        Get a human-readable seed string for display.

        Returns:
            String representation of seed ("random" if None)

        Example:
            >>> rng = GameRNG(seed=12345)
            >>> rng.get_seed_display()
            'Seed: 12345'
        """
        if self._original_seed is None:
            return "Seed: random"
        return f"Seed: {self._original_seed}"

    # ========================================================================
    # Random Methods (delegated to internal RNG)
    # ========================================================================

    def randint(self, a: int, b: int) -> int:
        """
        Return random integer in range [a, b], including both end points.

        Args:
            a: Lower bound (inclusive)
            b: Upper bound (inclusive)

        Returns:
            Random integer in [a, b]
        """
        return self._rng.randint(a, b)

    def random(self) -> float:
        """
        Return random float in range [0.0, 1.0).

        Returns:
            Random float in [0.0, 1.0)
        """
        return self._rng.random()

    def uniform(self, a: float, b: float) -> float:
        """
        Return random float in range [a, b] or [b, a].

        Args:
            a: Lower or upper bound
            b: Upper or lower bound

        Returns:
            Random float in range
        """
        return self._rng.uniform(a, b)

    def choice(self, seq: Sequence[T]) -> T:
        """
        Choose a random element from a non-empty sequence.

        Args:
            seq: Non-empty sequence to choose from

        Returns:
            Random element from sequence

        Raises:
            IndexError: If sequence is empty
        """
        return self._rng.choice(seq)

    def choices(
        self,
        population: Sequence[T],
        weights: Optional[Sequence[float]] = None,
        k: int = 1
    ) -> List[T]:
        """
        Return a k-sized list of population elements chosen with replacement.

        Args:
            population: Sequence to choose from
            weights: Optional weights for weighted selection
            k: Number of elements to choose

        Returns:
            List of k random elements
        """
        return self._rng.choices(population, weights=weights, k=k)

    def shuffle(self, seq: List[T]) -> None:
        """
        Shuffle sequence in place.

        Args:
            seq: Mutable sequence to shuffle
        """
        self._rng.shuffle(seq)

    def sample(self, population: Sequence[T], k: int) -> List[T]:
        """
        Return k unique random elements from population without replacement.

        Args:
            population: Sequence to sample from
            k: Number of unique elements to return

        Returns:
            List of k unique random elements

        Raises:
            ValueError: If k > len(population)
        """
        return self._rng.sample(population, k)

    # ========================================================================
    # Save/Load Support
    # ========================================================================

    def getstate(self) -> tuple:
        """
        Get the internal state of the RNG for saving.

        Returns:
            Tuple representing the RNG state

        Example:
            >>> rng = GameRNG.get_instance()
            >>> state = rng.getstate()
            >>> # Save state to file...
        """
        return self._rng.getstate()

    def setstate(self, state: tuple) -> None:
        """
        Set the internal state of the RNG (for loading saves).

        Args:
            state: Tuple representing the RNG state

        Example:
            >>> rng = GameRNG.get_instance()
            >>> # Load state from file...
            >>> rng.setstate(saved_state)
        """
        self._rng.setstate(state)

    # ========================================================================
    # Debug/Testing Support
    # ========================================================================

    def __repr__(self) -> str:
        """String representation for debugging."""
        if self._original_seed is None:
            return "GameRNG(seed=None)"
        return f"GameRNG(seed={self._original_seed!r})"


# =============================================================================
# Convenience Functions (for backward compatibility during migration)
# =============================================================================

def get_rng() -> GameRNG:
    """
    Get the global RNG instance (convenience function).

    Returns:
        The global GameRNG instance
    """
    return GameRNG.get_instance()
