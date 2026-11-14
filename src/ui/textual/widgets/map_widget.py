"""Map display widget for Veinborn."""
from textual.widget import Widget
from textual.strip import Strip
from rich.segment import Segment
from rich.style import Style

from core.world import TileType
from core.fog import UNSEEN


# Terrain display styles
TERRAIN_STYLES = {
    'wall': Style(color="white"),
    'floor': Style(color="grey50", dim=True),
    'door': Style(color="cyan"),
    'stairs': Style(color="cyan", bold=True),
    'stairs_up': Style(color="cyan", bold=True),
    'stairs_down': Style(color="cyan", bold=True),
}


class MapWidget(Widget):
    """Widget that displays the game map."""

    # Character mappings for display
    MAP_CHARS = {
        TileType.WALL: '█',
        TileType.FLOOR: '·',
        TileType.DOOR: '+',
        TileType.STAIRS_UP: '<',
        TileType.STAIRS_DOWN: '>',
    }

    DEFAULT_CSS = """
    MapWidget {
        width: 100%;
        height: 100%;
        background: $surface;
        border: solid $primary;
    }
    """

    # Draw order when entities share a tile: first match wins (the viewer is drawn before all).
    # 'player' here is another seat in a multiplayer party.
    ENTITY_PRIORITY = ('player', 'monster', 'ore_vein', 'forge', 'item', 'npc')
    # Allies share the viewer's glyph; a colour of their own tells them apart
    ALLY_COLOR = 'bright_cyan'

    def __init__(self, snapshot=None, **kwargs):
        super().__init__(**kwargs)
        self.snapshot = snapshot

    def show(self, snapshot) -> None:
        """Draw this snapshot (one per UI refresh, so a redraw walks the entities once)."""
        self.snapshot = snapshot
        self.refresh()

    def render_line(self, y: int) -> Strip:
        """Render a single line of the map."""
        # Use actual widget size for viewport (dynamic)
        viewport_width = self.size.width

        snap = self.snapshot
        if snap is None:
            return Strip([Segment(" " * viewport_width)])

        # Calculate viewport offset
        start_x, start_y = self._get_viewport_offset(snap)
        world_y = start_y + y

        # Check if line is out of bounds
        if world_y >= snap.map.height:
            return Strip([Segment(" " * viewport_width)])

        # Render each cell in the line
        return Strip([self._render_cell(start_x + x, world_y, snap) for x in range(viewport_width)])

    def _get_viewport_offset(self, snap):
        """Calculate viewport offset centered on player."""
        viewport_width = self.size.width
        viewport_height = self.size.height

        start_x = max(0, min(snap.player.x - viewport_width // 2,
                            snap.map.width - viewport_width))
        start_y = max(0, min(snap.player.y - viewport_height // 2,
                            snap.map.height - viewport_height))
        return start_x, start_y

    def _render_cell(self, world_x, world_y, snap):
        """Render a single map cell."""
        # Out of bounds
        if world_x >= snap.map.width:
            return Segment(" ")

        # Player position (priority rendering)
        player = snap.player
        if world_x == player.x and world_y == player.y:
            return Segment(player.symbol, Style(color=player.color, bold=True))

        # Entities at this position, in priority order
        for entity_type in self.ENTITY_PRIORITY:
            entity = snap.entity_at(world_x, world_y, entity_type)
            if entity:
                color = self.ALLY_COLOR if entity_type == 'player' else entity.color
                return Segment(entity.symbol, Style(color=color, bold=True))

        # Render terrain
        if 0 <= world_x < snap.map.width and 0 <= world_y < snap.map.height:
            tile_char = snap.map.tiles[world_y][world_x]
            if tile_char == UNSEEN:                    # fog: never seen
                return Segment(" ")
            tile_type = TileType(tile_char)
            char = self.MAP_CHARS.get(tile_type, '?')
            style = self._get_terrain_style(tile_type)
            if snap.map.lit and snap.map.lit[world_y][world_x] == '0':
                style = style + Style(dim=True)        # fog: remembered, not in sight
            return Segment(char, style)

        return Segment(" ")

    def _get_terrain_style(self, tile_type):
        """Get display style for terrain tile."""
        # Convert TileType enum to string for lookup
        type_name = tile_type.name.lower()
        return TERRAIN_STYLES.get(type_name, Style(color="cyan"))
