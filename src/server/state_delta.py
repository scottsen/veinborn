"""State delta compression for multiplayer games.

This module provides efficient delta compression for game state updates,
reducing network bandwidth by only sending what changed.
"""

from typing import Dict, Any, List, Optional, Set
import logging

logger = logging.getLogger(__name__)


class StateDelta:
    """Computes and applies state deltas for efficient updates."""

    @staticmethod
    def compute_delta(old_state: Optional[Dict], new_state: Dict) -> Dict:
        """Compute delta between two states.

        Args:
            old_state: Previous state (None for first state)
            new_state: New state

        Returns:
            Delta containing only changes
        """
        if old_state is None:
            # First state - send everything
            return {
                "type": "full",
                "state": new_state
            }

        delta = {
            "type": "delta",
            "changes": {},
            "turn_count": new_state.get("turn_count", 0),
            "round_number": new_state.get("round_number", 0),
            "actions_this_round": new_state.get("actions_this_round", 0),
        }

        # Track what changed
        changes = {}

        # Check player changes
        old_players = {p["player_id"]: p for p in old_state.get("players", [])}
        new_players = {p["player_id"]: p for p in new_state.get("players", [])}

        player_changes = []
        for player_id, new_player in new_players.items():
            old_player = old_players.get(player_id)
            if old_player is None:
                # New player joined
                player_changes.append({
                    "type": "player_added",
                    "player": new_player
                })
            else:
                # Check for changes
                player_delta = StateDelta._compute_player_delta(old_player, new_player)
                if player_delta:
                    player_changes.append({
                        "type": "player_updated",
                        "player_id": player_id,
                        "changes": player_delta
                    })

        # Check for removed players
        for player_id in old_players:
            if player_id not in new_players:
                player_changes.append({
                    "type": "player_removed",
                    "player_id": player_id
                })

        if player_changes:
            changes["players"] = player_changes

        # Check message changes (only send new messages)
        old_messages = old_state.get("recent_messages", [])
        new_messages = new_state.get("recent_messages", [])

        # Send only messages that weren't in the old state
        if len(new_messages) > len(old_messages):
            changes["new_messages"] = new_messages[len(old_messages):]

        # Check game_over and victory status
        if old_state.get("game_over") != new_state.get("game_over"):
            changes["game_over"] = new_state.get("game_over")

        if old_state.get("victory") != new_state.get("victory"):
            changes["victory"] = new_state.get("victory")

        delta["changes"] = changes

        # If no actual changes, indicate this
        if not changes:
            delta["no_changes"] = True

        logger.debug(f"Delta computed: {len(changes)} change categories")
        return delta

    @staticmethod
    def _compute_player_delta(old_player: Dict, new_player: Dict) -> Optional[Dict]:
        """Compute delta for a single player.

        Args:
            old_player: Old player state
            new_player: New player state

        Returns:
            Delta dict or None if no changes
        """
        delta = {}

        # Check position
        old_pos = old_player.get("position", {})
        new_pos = new_player.get("position", {})
        if old_pos != new_pos:
            delta["position"] = new_pos

        # Check health
        old_health = old_player.get("health", {})
        new_health = new_player.get("health", {})
        if old_health != new_health:
            delta["health"] = new_health

        # Check alive status
        if old_player.get("is_alive") != new_player.get("is_alive"):
            delta["is_alive"] = new_player.get("is_alive")

        # Check active status
        if old_player.get("is_active") != new_player.get("is_active"):
            delta["is_active"] = new_player.get("is_active")

        # Check stats (for level ups, equipment changes)
        old_stats = old_player.get("stats", {})
        new_stats = new_player.get("stats", {})
        if old_stats != new_stats:
            delta["stats"] = new_stats

        # Check inventory (for personal loot system)
        old_inventory = old_player.get("inventory", [])
        new_inventory = new_player.get("inventory", [])
        if old_inventory != new_inventory:
            delta["inventory"] = new_inventory

        return delta if delta else None

    @staticmethod
    def apply_delta(current_state: Dict, delta: Dict) -> Dict:
        """Apply a delta to a state.

        Args:
            current_state: Current state
            delta: Delta to apply

        Returns:
            New state with delta applied
        """
        if delta.get("type") == "full":
            # Full state replacement
            return delta["state"]

        if delta.get("no_changes"):
            # No changes, return current state
            return current_state

        # Create a copy of the current state
        new_state = current_state.copy()

        # Apply changes
        changes = delta.get("changes", {})

        # Update turn counters
        if "turn_count" in delta:
            new_state["turn_count"] = delta["turn_count"]
        if "round_number" in delta:
            new_state["round_number"] = delta["round_number"]
        if "actions_this_round" in delta:
            new_state["actions_this_round"] = delta["actions_this_round"]

        # Apply player changes
        if "players" in changes:
            current_players = {p["player_id"]: p for p in new_state.get("players", [])}

            for change in changes["players"]:
                change_type = change.get("type")

                if change_type == "player_added":
                    player = change["player"]
                    current_players[player["player_id"]] = player

                elif change_type == "player_updated":
                    player_id = change["player_id"]
                    if player_id in current_players:
                        player = current_players[player_id]
                        for key, value in change["changes"].items():
                            player[key] = value

                elif change_type == "player_removed":
                    player_id = change["player_id"]
                    current_players.pop(player_id, None)

            new_state["players"] = list(current_players.values())

        # Apply new messages
        if "new_messages" in changes:
            current_messages = new_state.get("recent_messages", [])
            new_messages = changes["new_messages"]
            # Append new messages and limit to last 20
            all_messages = current_messages + new_messages
            new_state["recent_messages"] = all_messages[-20:]

        # Apply game_over and victory changes
        if "game_over" in changes:
            new_state["game_over"] = changes["game_over"]
        if "victory" in changes:
            new_state["victory"] = changes["victory"]

        return new_state

    @staticmethod
    def estimate_compression_ratio(old_state: Optional[Dict], new_state: Dict, delta: Dict) -> float:
        """Estimate compression ratio achieved by delta.

        Args:
            old_state: Old state
            new_state: New state
            delta: Computed delta

        Returns:
            Compression ratio (original size / delta size)
        """
        import json

        full_size = len(json.dumps(new_state))
        delta_size = len(json.dumps(delta))

        if delta_size == 0:
            return 1.0

        ratio = full_size / delta_size
        logger.debug(f"Compression: {full_size} bytes -> {delta_size} bytes (ratio: {ratio:.2f}x)")
        return ratio
