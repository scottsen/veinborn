"""Strength: +`magnitude` attack for the effect's duration (the strength potion).

Nothing to do each turn: Player.get_total_attack reads the effect while it lasts.
"""
from ...extensions import status_effect


@status_effect("strength", label="Strength")
def strength(context, actor, effect):
    return None
