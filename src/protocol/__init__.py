"""Wire protocol shared by the multiplayer server and its clients.

Clients import this package and `core.snapshot` (the state they render); they do
not import `server`.
"""

#: Bumped whenever a message changes in a way an older peer cannot read.
PROTOCOL_VERSION = 4  # 4: fog of war (MapView.lit, UNSEEN tiles, Snapshot.reveal_map, create_game reveal_map); 3: PartyMemberView.grace_left; 2: ItemView slot/bonus, EntityView item_type, Snapshot.message_count, intent rid + intent_result
