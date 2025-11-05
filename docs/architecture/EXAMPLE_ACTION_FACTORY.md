# Action Factory Pattern Example

**Context**: TIA AST identified `handle_player_action` as complex (complexity: 19)
**Opportunity**: Reduce to complexity ~8 with Action Factory pattern
**Status**: Example/proposal - not implemented yet

---

## Current Code (Complexity: 19)

```python
# src/core/game.py:123-228
def handle_player_action(self, action_type: str, **kwargs) -> bool:
    """Handle player action and process turn."""
    if self.state.game_over:
        return False

    # Create action based on type
    action = None
    actor_id = self.state.player.entity_id

    if action_type == 'move':
        action = MoveAction(actor_id, kwargs['dx'], kwargs['dy'])

    elif action_type == 'survey':
        # Find adjacent ore vein
        ore_vein = self._find_adjacent_ore_vein()
        if ore_vein:
            action = SurveyAction(actor_id, ore_vein.entity_id)
        else:
            logger.debug("Survey action failed: no adjacent ore vein")
            self.state.add_message("No ore vein nearby to survey")
            return False

    elif action_type == 'mine':
        # Find adjacent ore vein
        ore_vein = self._find_adjacent_ore_vein()
        if ore_vein:
            # Check if already mining (resume)
            mining_data = self.state.player.get_stat('mining_action')
            if mining_data:
                action = MineAction.from_dict(mining_data)
            else:
                action = MineAction(actor_id, ore_vein.entity_id)
        else:
            logger.debug("Mine action failed: no adjacent ore vein")
            self.state.add_message("No ore vein nearby to mine")
            return False

    elif action_type == 'descend':
        action = DescendAction(actor_id)

    elif action_type == 'wait':
        logger.debug("Player waiting (rest to heal)")
        from core.base.action import ActionOutcome
        outcome = ActionOutcome.success(took_turn=True, message="")
        self._process_turn()
        return True

    if not action:
        logger.warning(f"Unknown action type: {action_type}")
        return False

    # Execute action
    outcome = action.execute(self.context)

    # ... rest of outcome processing ...
```

**Issues:**
- ⚠️  105 lines long
- ⚠️  Complexity: 19
- ⚠️  Every new action = modify this function
- ⚠️  Mixed concerns (creation + validation + execution)
- ⚠️  Violates Open/Closed Principle

---

## Proposed Solution: Action Factory

### Step 1: Create ActionFactory

```python
# NEW FILE: src/core/actions/action_factory.py
"""
Action Factory - centralized action creation.

Responsibilities:
- Create actions from string types
- Handle action-specific setup
- Validate action prerequisites
- Register new actions without modifying code

Design:
- Open/Closed Principle (add actions, don't modify)
- Single Responsibility (action creation only)
- Strategy Pattern (delegates to action handlers)
"""

import logging
from typing import Dict, Callable, Optional, Any
from dataclasses import dataclass

from ..base.action import Action
from ..base.game_context import GameContext
from .move_action import MoveAction
from .attack_action import AttackAction
from .survey_action import SurveyAction
from .mine_action import MineAction
from .descend_action import DescendAction

logger = logging.getLogger(__name__)


@dataclass
class ActionHandler:
    """
    Handler for creating a specific action type.

    Encapsulates the logic needed to:
    - Validate prerequisites
    - Find required entities
    - Create the action
    """
    name: str
    create_fn: Callable[[GameContext, dict], Optional[Action]]
    description: str


class ActionFactory:
    """
    Factory for creating game actions.

    Usage:
        factory = ActionFactory(game_context)
        action = factory.create('move', dx=1, dy=0)
        if action:
            outcome = action.execute(context)

    Benefits:
    - Add new actions without modifying this class
    - Testable action creation logic
    - Clear separation of concerns
    - Open/Closed Principle
    """

    def __init__(self, context: GameContext):
        """
        Initialize factory with game context.

        Args:
            context: Game context for action creation
        """
        self.context = context
        self._handlers: Dict[str, ActionHandler] = {}

        # Register standard actions
        self._register_standard_actions()

    def create(self, action_type: str, **kwargs) -> Optional[Action]:
        """
        Create an action from string type.

        Args:
            action_type: Type of action ('move', 'mine', etc.)
            **kwargs: Action-specific parameters

        Returns:
            Action instance or None if creation failed
        """
        handler = self._handlers.get(action_type)

        if not handler:
            logger.warning(f"Unknown action type: {action_type}")
            return None

        try:
            action = handler.create_fn(self.context, kwargs)
            if action:
                logger.debug(
                    f"Created action: {action_type}",
                    extra={'action_class': action.__class__.__name__}
                )
            return action
        except Exception as e:
            logger.error(
                f"Failed to create action: {action_type}",
                extra={'error': str(e)},
                exc_info=True
            )
            return None

    def register_handler(self, action_type: str, handler: ActionHandler) -> None:
        """
        Register a custom action handler.

        Allows extending the factory without modifying this file.

        Args:
            action_type: String identifier for action
            handler: ActionHandler instance
        """
        self._handlers[action_type] = handler
        logger.debug(f"Registered action handler: {action_type}")

    def get_available_actions(self) -> Dict[str, str]:
        """
        Get all available action types.

        Returns:
            Dict of action_type -> description
        """
        return {
            action_type: handler.description
            for action_type, handler in self._handlers.items()
        }

    # ----- Action Creation Handlers -----

    def _register_standard_actions(self) -> None:
        """Register the standard game actions."""

        # Move action
        self._handlers['move'] = ActionHandler(
            name='move',
            create_fn=self._create_move_action,
            description='Move in a direction'
        )

        # Survey action
        self._handlers['survey'] = ActionHandler(
            name='survey',
            create_fn=self._create_survey_action,
            description='Survey adjacent ore vein'
        )

        # Mine action
        self._handlers['mine'] = ActionHandler(
            name='mine',
            create_fn=self._create_mine_action,
            description='Mine adjacent ore vein'
        )

        # Descend action
        self._handlers['descend'] = ActionHandler(
            name='descend',
            create_fn=self._create_descend_action,
            description='Descend to next floor'
        )

        # Wait action
        self._handlers['wait'] = ActionHandler(
            name='wait',
            create_fn=self._create_wait_action,
            description='Wait and rest (heal HP)'
        )

    def _create_move_action(self, context: GameContext, kwargs: dict) -> Optional[Action]:
        """Create a move action."""
        actor_id = context.get_player().entity_id
        dx = kwargs.get('dx', 0)
        dy = kwargs.get('dy', 0)
        return MoveAction(actor_id, dx, dy)

    def _create_survey_action(self, context: GameContext, kwargs: dict) -> Optional[Action]:
        """Create a survey action (requires adjacent ore vein)."""
        actor_id = context.get_player().entity_id

        # Find adjacent ore vein
        ore_vein = self._find_adjacent_ore_vein(context)
        if not ore_vein:
            context.game_state.add_message("No ore vein nearby to survey")
            return None

        return SurveyAction(actor_id, ore_vein.entity_id)

    def _create_mine_action(self, context: GameContext, kwargs: dict) -> Optional[Action]:
        """Create a mine action (requires adjacent ore vein)."""
        actor_id = context.get_player().entity_id

        # Check if resuming existing mining action
        player = context.get_player()
        mining_data = player.get_stat('mining_action')
        if mining_data:
            logger.debug("Resuming multi-turn mining action")
            return MineAction.from_dict(mining_data)

        # Find adjacent ore vein
        ore_vein = self._find_adjacent_ore_vein(context)
        if not ore_vein:
            context.game_state.add_message("No ore vein nearby to mine")
            return None

        return MineAction(actor_id, ore_vein.entity_id)

    def _create_descend_action(self, context: GameContext, kwargs: dict) -> Optional[Action]:
        """Create a descend action."""
        actor_id = context.get_player().entity_id
        return DescendAction(actor_id)

    def _create_wait_action(self, context: GameContext, kwargs: dict) -> Optional[Action]:
        """
        Create a wait action.

        Note: Wait is special - doesn't use Action pattern,
        just returns None to signal "consume turn but do nothing"
        """
        # Wait action is handled specially in handle_player_action
        # Just return None to indicate "consume turn"
        return None

    def _find_adjacent_ore_vein(self, context: GameContext):
        """
        Find ore vein adjacent to player.

        Helper method extracted from Game class.
        """
        from ..base.entity import EntityType

        player = context.get_player()
        ore_veins = context.get_entities_by_type(EntityType.ORE_VEIN)

        for ore_vein in ore_veins:
            if player.is_adjacent(ore_vein):
                return ore_vein

        return None
```

### Step 2: Refactor Game.handle_player_action

```python
# UPDATED: src/core/game.py
from .actions.action_factory import ActionFactory

class Game:
    def __init__(self):
        # ... existing initialization ...

        # Create action factory (after context is available)
        self.action_factory: Optional[ActionFactory] = None

    def start_new_game(self) -> None:
        # ... existing code ...

        # Create action factory
        self.action_factory = ActionFactory(self.context)

        # ... rest of initialization ...

    def handle_player_action(self, action_type: str, **kwargs) -> bool:
        """
        Handle player action and process turn.

        Simplified with ActionFactory - reduced from 105 to ~40 lines!
        """
        if self.state.game_over:
            return False

        # Special case: wait action
        if action_type == 'wait':
            logger.debug("Player waiting (rest to heal)")
            self._process_turn()
            return True

        # Create action via factory
        action = self.action_factory.create(action_type, **kwargs)

        if not action:
            # Factory already logged and added messages
            return False

        # Execute action
        logger.debug(
            f"Executing action: {action_type}",
            extra={
                'action_class': action.__class__.__name__,
                'turn': self.state.turn_count,
            }
        )
        outcome = action.execute(self.context)

        if not outcome.success:
            logger.info(
                f"Action failed: {action_type}",
                extra={
                    'action_class': action.__class__.__name__,
                    'failure_message': outcome.message,
                }
            )

        # Check for floor transition event
        for event in outcome.events:
            if event.get('type') == 'descend_floor':
                self.descend_floor()

        # Add messages
        for msg in outcome.messages:
            self.state.add_message(msg)

        # Process turn if action consumed time
        if outcome.took_turn:
            self._process_turn()
            return True

        return False

    # NOTE: _find_adjacent_ore_vein moved to ActionFactory
```

---

## Benefits Analysis

### Quantitative Improvements

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| handle_player_action lines | 105 | ~40 | **-62%** |
| Complexity | 19 | ~8 | **-58%** |
| Nesting depth | 5 | 2 | **-60%** |
| If/elif chains | 1 big chain | 0 | **-100%** |

### Qualitative Improvements

**Before (if/elif chain):**
- ❌ Adding action = modify handle_player_action
- ❌ Action creation logic mixed with game logic
- ❌ Hard to test action creation separately
- ❌ Violates Open/Closed Principle

**After (Factory pattern):**
- ✅ Adding action = register new handler
- ✅ Action creation isolated in factory
- ✅ Easy to test each handler
- ✅ Follows Open/Closed Principle

### SOLID Principles

**Single Responsibility:**
- Game: Orchestration only
- ActionFactory: Action creation only
- Each ActionHandler: One action type only

**Open/Closed:**
```python
# Adding new action - NO modification to existing code!
def create_craft_action(context, kwargs):
    # ... custom logic ...
    return CraftAction(...)

game.action_factory.register_handler(
    'craft',
    ActionHandler('craft', create_craft_action, 'Craft an item')
)
```

**Dependency Inversion:**
- Game depends on ActionFactory abstraction
- ActionFactory depends on Action interface
- No tight coupling to specific actions

---

## Adding New Actions

### Before (Modify Game class)

```python
# Edit src/core/game.py
def handle_player_action(self, action_type: str, **kwargs) -> bool:
    # ... existing code ...

    # ADD NEW ELIF BLOCK (modifying existing function!)
    elif action_type == 'craft':
        # 15 lines of craft-specific logic
        action = CraftAction(...)

    # ... rest of function ...
```

**Risk:** Might break existing actions, must test everything

### After (Register new handler)

```python
# NEW FILE: src/core/actions/craft_action.py
class CraftAction(Action):
    # ... action implementation ...

# In game initialization or plugin system:
def create_craft_action(context, kwargs):
    recipe_id = kwargs.get('recipe_id')
    # ... validation ...
    return CraftAction(actor_id, recipe_id)

game.action_factory.register_handler(
    'craft',
    ActionHandler('craft', create_craft_action, 'Craft an item from recipe')
)
```

**Risk:** Isolated to new code only, existing actions unchanged

---

## Testing

### Before (Hard to test)

```python
# Must test through entire game instance
def test_mine_action_creation():
    game = Game()
    game.start_new_game()
    # ... set up ore vein ...
    result = game.handle_player_action('mine')
    # Hard to isolate just the creation logic
```

### After (Easy to test)

```python
# Test action creation in isolation
def test_mine_action_creation():
    context = MockGameContext()
    factory = ActionFactory(context)

    # Test with ore vein
    context.add_adjacent_ore_vein()
    action = factory.create('mine')
    assert action is not None
    assert isinstance(action, MineAction)

    # Test without ore vein
    context.clear_ore_veins()
    action = factory.create('mine')
    assert action is None

# Test game orchestration separately
def test_handle_player_action():
    game = Game()
    game.start_new_game()

    # Mock the factory
    game.action_factory = MockActionFactory()

    # Test orchestration logic only
    # ...
```

---

## Migration Path

If you want to implement this (optional!):

### Phase 1: Create Factory (No Breaking Changes)

1. Create `src/core/actions/action_factory.py`
2. Write tests for ActionFactory
3. Commit: "Add ActionFactory (not used yet)"

### Phase 2: Integrate Factory

1. Add `self.action_factory` to Game
2. Update `handle_player_action` to use factory
3. Remove `_find_adjacent_ore_vein` from Game (moved to factory)
4. Test thoroughly
5. Commit: "Refactor: Use ActionFactory in Game"

### Phase 3: Validate

```bash
# Check complexity improvement
tia ast metrics src/core/game.py

# Should show:
# Before: Complexity 19
# After:  Complexity ~8

# Validate no regressions
python3 run_textual.py
# Play test - all actions should work
```

---

## Alternative: Command Pattern

Another option is the **Command Pattern** which is similar but more formal:

```python
class IActionCommand(ABC):
    @abstractmethod
    def can_execute(self, context: GameContext) -> bool:
        """Check if action can be executed."""

    @abstractmethod
    def execute(self, context: GameContext) -> Action:
        """Create and return the action."""

class MoveCommand(IActionCommand):
    def can_execute(self, context):
        return True  # Always can move

    def execute(self, context):
        return MoveAction(...)

class MineCommand(IActionCommand):
    def can_execute(self, context):
        return context.has_adjacent_ore_vein()

    def execute(self, context):
        return MineAction(...)
```

**Pros:** More formal, testable prerequisites
**Cons:** More boilerplate

---

## Recommendation

**Should you implement this?**

**Reasons TO implement:**
- ✅ Reduces complexity from 19 → 8
- ✅ Makes Game class "excellent" instead of "good"
- ✅ Makes adding new actions easier
- ✅ Better follows SOLID principles
- ✅ Easier to test

**Reasons NOT to implement (yet):**
- ⚠️  Current code works perfectly
- ⚠️  Complexity 19 is still "good" (not "poor")
- ⚠️  Phase 3 might change action system anyway
- ⚠️  Don't fix what isn't broken

**My take:** Consider this for **Phase 4 (Code Quality Polish)**, not urgent now.

Current priorities:
1. Commit Phase 2 ✅
2. Start Phase 3 (Data-Driven Entities)
3. Phase 4: Action Factory + other polish

---

## Summary

**The Insight:**
- TIA AST flagged `handle_player_action` as complex (19)
- Code review showed if/elif chain anti-pattern
- Factory Pattern is the standard solution

**The Solution:**
- Extract action creation to ActionFactory
- Reduce complexity from 19 → 8
- Follow Open/Closed Principle
- Make adding actions trivial

**The Decision:**
- Optional improvement, not required
- Current code is "good" (not broken)
- Consider for Phase 4 polish

---

**Status:** Example/proposal - implementation optional
**Priority:** Low (nice-to-have, not need-to-have)
**Next Steps:** Your call - commit current work first, decide later
