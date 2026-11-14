"""Wire protocol shared by the multiplayer server and its clients.

Clients import this package and `core.snapshot` (the state they render); they do
not import `server`.
"""

#: Bumped whenever a message changes in a way an older peer cannot read.
PROTOCOL_VERSION = 10  # 10: AbilityView.aimed/targets (choose a bolt's target); 9: EntityView.info (survey numbers, monster attack/defense, item stats: examine); 8: ItemView.stats, PlayerView.accuracy/spell_power (all gear stats visible); 7: RecipeView.kind/required_slots/optional_slots/part_ids/part_choices, ItemView.part (crafting v2 parts and assemblies); 6: PlayerView.forge_id/recipes (RecipeView), ItemView.usable/ore; 5: PlayerView.effects; 4: fog of war (MapView.lit, UNSEEN tiles, Snapshot.reveal_map, create_game reveal_map); 3: PartyMemberView.grace_left; 2: ItemView slot/bonus, EntityView item_type, Snapshot.message_count, intent rid + intent_result
