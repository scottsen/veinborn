"""Regeneration: heal `magnitude` HP every turn for the effect's duration."""
from ...extensions import status_effect


@status_effect("regeneration", label="Regeneration", per_turn=True)
def regeneration(context, actor, effect):
    actor.heal(effect['magnitude'])
