"""Map display widget for Veinborn."""
from textual.widget import Widget
from textual.strip import Strip
from textual.geometry import Size
from rich.segment import Segment
from rich.style import Style

from core.world import TileType
from core.base.entity import EntityType


# Ore vein display styles
ORE_STYLES = {
    'copper': Style(color="yellow", bold=True),
    'iron': Style(color="bright_white", bold=True),
    'mithril': Style(color="bright_cyan", bold=True),
    'adamantite': Style(color="bright_magenta", bold=True),
}

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

    def __init__(self, game_state=None, **kwargs):
        super().__init__(**kwargs)
        self.game_state = game_state
        self.viewport_width = 60
        self.viewport_height = 20

    def render_line(self, y: int) -> Strip:
        """Render a single line of the map."""
        if not self.game_state:
            return Strip([Segment(" " * self.viewport_width)])

        player = self.game_state.player
        game_map = self.game_state.dungeon_map

        # Calculate viewport offset
        start_x, start_y = self._get_viewport_offset(player, game_map)
        world_y = start_y + y

        # Check if line is out of bounds
        if world_y >= game_map.height:
            return Strip([Segment(" " * self.viewport_width)])

        # Render each cell in the line
        segments = []
        for x in range(self.viewport_width):
            world_x = start_x + x
            segments.append(self._render_cell(world_x, world_y, player, game_map))

        return Strip(segments)

    def _get_viewport_offset(self, player, game_map):
        """Calculate viewport offset centered on player."""
        start_x = max(0, min(player.x - self.viewport_width // 2,
                            game_map.width - self.viewport_width))
        start_y = max(0, min(player.y - self.viewport_height // 2,
                            game_map.height - self.viewport_height))
        return start_x, start_y

    def _render_cell(self, world_x, world_y, player, game_map):
        """Render a single map cell."""
        # Out of bounds
        if world_x >= game_map.width:
            return Segment(" ")

        # Player position
        if world_x == player.x and world_y == player.y:
            return Segment("@", Style(color="bright_yellow", bold=True))

        # Check for entities at this position
        entity = self._get_entity_at(world_x, world_y, EntityType.MONSTER)
        if entity:
            char = entity.name[0].lower()
            return Segment(char, Style(color="bright_red", bold=True))

        entity = self._get_entity_at(world_x, world_y, EntityType.ORE_VEIN)
        if entity:
            return Segment('*', self._get_ore_vein_style(entity))

        # Render terrain
        if 0 <= world_x < game_map.width and 0 <= world_y < game_map.height:
            tile = game_map.tiles[world_x][world_y]
            char = self.MAP_CHARS.get(tile.tile_type, '?')
            style = self._get_terrain_style(tile.tile_type)
            return Segment(char, style)

        return Segment(" ")

    def _get_entity_at(self, x, y, entity_type):
        """Find entity of given type at position."""
        # Use new GameContext method (would need context passed, but we have direct access)
        for entity in self.game_state.entities.values():
            if entity.entity_type == entity_type and entity.x == x and entity.y == y:
                return entity
        return None

    def _get_ore_vein_style(self, ore_vein):
        """Get display style for ore vein based on type."""
        # Fuzzy match: check if any ore type is in the vein name
        vein_name_lower = ore_vein.name.lower()
        for ore_type, style in ORE_STYLES.items():
            if ore_type in vein_name_lower:
                return style
        return Style(color="white", bold=True)

    def _get_terrain_style(self, tile_type):
        """Get display style for terrain tile."""
        # Convert TileType enum to string for lookup
        type_name = tile_type.name.lower()
        return TERRAIN_STYLES.get(type_name, Style(color="cyan"))

    def get_content_height(self, container: Size, viewport: Size, width: int) -> int:
        """Get the height needed for the content."""
        return self.viewport_height

    def get_content_width(self, container: Size, viewport: Size) -> int:
        """Get the width needed for the content."""
        return self.viewport_width
