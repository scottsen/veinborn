"""
Tests for AI system - monster behavior.

Current MVP AI is simple aggressive chase-and-attack.
State machine AI (idle/chasing/wandering) is a future enhancement.
"""

import pytest
from src.core.systems.ai_system import AISystem


pytestmark = pytest.mark.unit


class TestAISystemInitialization:
    """Test AI system initialization."""

    def test_ai_system_creates_successfully(self, game_context):
        """AI system initializes with context."""
        ai_system = AISystem(game_context)

        assert ai_system is not None
        assert ai_system.context == game_context
