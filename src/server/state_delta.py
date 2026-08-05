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

        # Check floor changes (VB-4: previously never diffed, so clients had
        # no way to learn current_floor advanced)
        if old_state.get("current_floor") != new_state.get("current_floor"):
            changes["current_floor"] = new_state.get("current_floor")

        # Check map changes (the map only regenerates on floor transitions,
        # so this naturally stays empty except right after a descend)
        if old_state.get("map") != new_state.get("map"):
            changes["map"] = new_state.get("map")

        # Check monster/ore-vein/forge changes (VB-4: previously dropped
        # entirely - same add/update/remove pattern as players, keyed by
        # entity_id instead of player_id)
        monster_changes = StateDelta._compute_entity_list_delta(
            old_state.get("monsters", []), new_state.get("monsters", [])
        )
        if monster_changes:
            changes["monsters"] = monster_changes

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
    def _compute_entity_list_delta(old_entities: List[Dict], new_entities: List[Dict]) -> List[Dict]:
        """Compute add/update/remove changes for a list of entity dicts.

        Used for monsters/ore veins/forges (Entity.to_dict() output), keyed
        by entity_id. Since entity_id is a fresh UUID per spawn, a floor
        transition (which respawns all entities) naturally falls out as a
        full remove-then-add set with no special-casing needed.

        Args:
            old_entities: Previous entity dicts
            new_entities: New entity dicts

        Returns:
            List of change records (empty if no changes)
        """
        old_by_id = {e["entity_id"]: e for e in old_entities}
        new_by_id = {e["entity_id"]: e for e in new_entities}

        changes = []
        for entity_id, new_entity in new_by_id.items():
            old_entity = old_by_id.get(entity_id)
            if old_entity is None:
                changes.append({"type": "entity_added", "entity": new_entity})
            else:
                entity_delta = StateDelta._compute_entity_delta(old_entity, new_entity)
                if entity_delta:
                    changes.append({
                        "type": "entity_updated",
                        "entity_id": entity_id,
                        "changes": entity_delta
                    })

        for entity_id in old_by_id:
            if entity_id not in new_by_id:
                changes.append({"type": "entity_removed", "entity_id": entity_id})

        return changes

    @staticmethod
    def _compute_entity_delta(old_entity: Dict, new_entity: Dict) -> Optional[Dict]:
        """Compute delta for a single monster/ore-vein/forge entity.

        Args:
            old_entity: Old entity dict (Entity.to_dict() output)
            new_entity: New entity dict

        Returns:
            Delta dict or None if no changes
        """
        delta = {}
        for key in ("x", "y", "hp", "max_hp", "is_alive", "is_active", "stats"):
            if old_entity.get(key) != new_entity.get(key):
                delta[key] = new_entity.get(key)
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

        # Apply floor change
        if "current_floor" in changes:
            new_state["current_floor"] = changes["current_floor"]

        # Apply map change
        if "map" in changes:
            new_state["map"] = changes["map"]

        # Apply monster/ore-vein/forge changes
        if "monsters" in changes:
            current_monsters = {m["entity_id"]: m for m in new_state.get("monsters", [])}

            for change in changes["monsters"]:
                change_type = change.get("type")

                if change_type == "entity_added":
                    entity = change["entity"]
                    current_monsters[entity["entity_id"]] = entity

                elif change_type == "entity_updated":
                    entity_id = change["entity_id"]
                    if entity_id in current_monsters:
                        entity = current_monsters[entity_id]
                        for key, value in change["changes"].items():
                            entity[key] = value

                elif change_type == "entity_removed":
                    current_monsters.pop(change["entity_id"], None)

            new_state["monsters"] = list(current_monsters.values())

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
