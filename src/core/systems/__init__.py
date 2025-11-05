"""
Game systems - modular logic processors.

Systems operate on entities and execute actions.
They provide clean separation of concerns and are easy to test.
"""

from .ai_system import AISystem

__all__ = [
    'AISystem',
]
