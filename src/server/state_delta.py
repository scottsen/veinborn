"""State delta compression for multiplayer games.

This module provides efficient delta compression for game state updates,
reducing network bandwidth by only sending what changed.
"""

from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class StateDelta:
    """Computes and applies state deltas for efficient updates."""

    _COUNTER_KEYS = ("turn_count", "message_count", "round_number", "actions_this_round",
                     "actions_per_round", "waiting_on")
    _REPLACED_KEYS = ("current_floor", "map", "game_over", "victory")
    # State a delta has no way to express (lobby fields, entity ids, ...): if any of
    # these change, resend everything instead of silently dropping the change.
    _FULL_STATE_KEYS = ("initialized", "is_started", "is_finished", "is_multiplayer")
    _MESSAGE_WINDOW = 20  # Must match the recent_messages window the server broadcasts

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

        if any(old_state.get(k) != new_state.get(k) for k in StateDelta._FULL_STATE_KEYS):
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
            "actions_per_round": new_state.get("actions_per_round", 0),
            "waiting_on": new_state.get("waiting_on", []),
            "message_count": new_state.get("message_count", 0),
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

        # Check message changes (only send new messages). VB-20: recent_messages
        # is capped at 20 server-side, so once more than 20 messages have ever
        # been sent, both snapshots permanently have the same length and a
        # len(new) > len(old) check never fires again. Compare the monotonic
        # message_count instead -- it keeps growing even after recent_messages
        # stops.
        old_messages = old_state.get("recent_messages", [])
        new_messages = new_state.get("recent_messages", [])
        old_message_count = old_state.get("message_count", len(old_messages))
        new_message_count = new_state.get("message_count", len(new_messages))

        num_new = new_message_count - old_message_count
        if num_new > 0:
            changes["new_messages"] = new_messages[-num_new:]

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

        # Worn gear and ability cooldowns (VB-78: same data the sidebar shows)
        for key in ("equipment", "abilities"):
            if old_player.get(key) != new_player.get(key):
                delta[key] = new_player.get(key)

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

        Never mutates current_state or its nested dicts, so callers can keep
        earlier snapshots (replay/debug tooling) safely.

        Args:
            current_state: Current state
            delta: Delta to apply

        Returns:
            New state with delta applied
        """
        if delta.get("type") == "full":
            return delta["state"]

        if delta.get("no_changes"):
            return current_state

        new_state = current_state.copy()
        changes = delta.get("changes", {})

        for key in StateDelta._COUNTER_KEYS:
            if key in delta:
                new_state[key] = delta[key]

        if "players" in changes:
            new_state["players"] = StateDelta._apply_keyed_changes(
                new_state.get("players", []), changes["players"], "player"
            )

        if "monsters" in changes:
            new_state["monsters"] = StateDelta._apply_keyed_changes(
                new_state.get("monsters", []), changes["monsters"], "entity"
            )

        for key in StateDelta._REPLACED_KEYS:
            if key in changes:
                new_state[key] = changes[key]

        if "new_messages" in changes:
            all_messages = new_state.get("recent_messages", []) + changes["new_messages"]
            new_state["recent_messages"] = all_messages[-StateDelta._MESSAGE_WINDOW:]

        return new_state

    @staticmethod
    def _apply_keyed_changes(items: List[Dict], changes: List[Dict], kind: str) -> List[Dict]:
        """Apply added/updated/removed changes to a list of dicts keyed by '<kind>_id'.

        Updated items are replaced by a merged copy rather than mutated in place.
        """
        id_field = f"{kind}_id"
        by_id = {item[id_field]: item for item in items}

        for change in changes:
            change_type = change.get("type")

            if change_type == f"{kind}_added":
                added = change[kind]
                by_id[added[id_field]] = added

            elif change_type == f"{kind}_updated":
                item_id = change[id_field]
                if item_id in by_id:
                    by_id[item_id] = {**by_id[item_id], **change["changes"]}

            elif change_type == f"{kind}_removed":
                by_id.pop(change[id_field], None)

        return list(by_id.values())

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
