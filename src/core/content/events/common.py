"""Helpers shared by event-handler content."""

from ...base.entity import EntityType


def player_kill(context, event):
    """The player who dealt the killing blow in an ENTITY_DIED event, else None."""
    killer = context.get_entity(event.data.get('killer_id'))
    if killer is not None and killer.entity_type == EntityType.PLAYER:
        return killer
    return None


def victim_content_id(context, event):
    """The monster id (monsters.yaml key) of the entity that died, if still known."""
    victim = context.get_entity(event.data.get('entity_id'))
    return getattr(victim, 'content_id', None)
