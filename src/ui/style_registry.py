"""
Style Registry - Eliminates long if/elif chains for styling.

Instead of:
    if 'copper' in ore_name:
        return Style(color="yellow", bold=True)
    elif 'iron' in ore_name:
        return Style(color="bright_white", bold=True)
    # ... 10 more conditions

Use:
    ORE_STYLES.get(ore_name, default_style)
"""

from rich.style import Style
from typing import Optional, Dict


class StyleRegistry:
    """Registry for styling with fuzzy matching support."""

    def __init__(self):
        self._styles: Dict[str, Style] = {}

    def register(self, key: str, style: Style) -> None:
        """
        Register a style for a key.

        Args:
            key: Lookup key (will be lowercased)
            style: Rich Style object
        """
        self._styles[key.lower()] = style

    def get(self, key: str, default: Optional[Style] = None) -> Style:
        """
        Get style by key with fuzzy matching.

        Matching strategy:
        1. Exact match (case-insensitive)
        2. Partial match (key contains registered key)
        3. Default style if provided, otherwise plain Style()

        Args:
            key: Lookup key (e.g., ore name, tile type)
            default: Default style if no match found

        Returns:
            Matching Style or default
        """
        key_lower = key.lower()

        # Exact match
        if key_lower in self._styles:
            return self._styles[key_lower]

        # Partial match (e.g., "Copper Ore Vein" matches "copper")
        for registered_key, style in self._styles.items():
            if registered_key in key_lower:
                return style

        # Default
        return default if default else Style()


# ============================================================================
# Pre-configured Style Registries
# ============================================================================

# Ore vein colors
ORE_STYLES = StyleRegistry()
ORE_STYLES.register('copper', Style(color="yellow", bold=True))
ORE_STYLES.register('iron', Style(color="bright_white", bold=True))
ORE_STYLES.register('mithril', Style(color="bright_cyan", bold=True))
ORE_STYLES.register('adamantite', Style(color="bright_magenta", bold=True))

# Terrain colors
TERRAIN_STYLES = StyleRegistry()
TERRAIN_STYLES.register('wall', Style(color="white"))
TERRAIN_STYLES.register('floor', Style(color="grey50", dim=True))
TERRAIN_STYLES.register('door', Style(color="cyan"))
TERRAIN_STYLES.register('stairs', Style(color="cyan", bold=True))
