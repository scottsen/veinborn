# UI Framework: Textual

**Status:** Architectural Decision
**Date:** 2025-10-14
**Decision:** Textual is the standard UI framework for Brogue

## Executive Summary

**Textual** is the chosen UI framework for Brogue, replacing the initial Blessed implementation. This decision prioritizes cross-platform compatibility, modern development experience, and scalability for complex UI features.

## Why Textual?

### Cross-Platform Excellence
- **Best Windows Support**: Works flawlessly across Windows Terminal, cmd.exe, and PowerShell
- **Unix/Linux**: Excellent native support
- **macOS**: Full compatibility with Terminal.app and iTerm2
- **Abstraction Layer**: Handles platform differences automatically

### Perfect for Roguelike Development
- **Grid-based layouts**: Natural for dungeon maps
- **Rich widget library**: Inventory panels, skill trees, crafting menus
- **CSS-like styling**: Easy theming and visual consistency
- **Reactive model**: Efficient updates for turn-based gameplay

### Developer Experience
- **Modern Python**: Async/await architecture
- **Excellent documentation**: Comprehensive guides and examples
- **Active development**: Regular updates (2024+)
- **Built-in debugging**: DevTools for UI inspection

### Feature Alignment with Brogue
- **Complex UI needs**: Memory system UI, weapon evolution displays, crafting interfaces
- **Modal dialogs**: Inventory, character sheets, help screens
- **Animations**: Smooth transitions for combat and effects
- **Themes**: Dark mode and accessibility options

## Comparison with Blessed

| Feature | Blessed (Current) | Textual (Target) |
|---------|------------------|------------------|
| Platform Support | Good (requires Windows Terminal) | Excellent (works everywhere) |
| Widget Library | Manual implementation | Built-in (buttons, tables, trees) |
| Layout System | Manual positioning | Automatic (Grid, Flex) |
| Styling | Direct terminal codes | CSS-like system |
| Learning Curve | Gentle | Moderate (async required) |
| Maintenance | Manual everything | Framework handles complexity |
| Windows Players | Limited reach | Maximum compatibility |

## Migration Strategy

### Phase 1: Parallel Development
- Keep Blessed implementation working
- Build Textual prototype alongside
- Compare performance and feel

### Phase 2: Feature Parity
- Implement core game UI in Textual
- Match existing Blessed functionality
- Add Textual-specific enhancements

### Phase 3: Cutover
- Make Textual the default
- Archive Blessed implementation
- Update all documentation

### Phase 4: Enhancement
- Leverage Textual features for complex UI
- Add inventory management screens
- Implement memory system visualization
- Create crafting interface

## Implementation Guidelines

### Project Structure
```
src/ui/
├── textual/           # New Textual-based UI
│   ├── app.py        # Main Textual app
│   ├── screens/      # Game screens (main, inventory, etc.)
│   ├── widgets/      # Custom widgets (map, status, etc.)
│   └── styles/       # CSS files for theming
└── blessed/          # Legacy Blessed implementation (archived)
    └── display.py    # Current implementation
```

### Code Standards
- Use async/await for all Textual code
- Leverage CSS for all styling
- Build reusable widgets
- Follow Textual best practices
- Document component hierarchy

### Testing Approach
- Test on all target platforms (Linux, macOS, Windows)
- Verify keyboard handling across terminals
- Check Unicode character rendering
- Validate color scheme consistency

## Technical Requirements

### Dependencies
```bash
# Primary UI framework
textual>=0.40.0

# Optional but recommended
textual-dev>=1.0.0  # Development tools
```

### Minimum Python Version
- Python 3.8+ (for Textual compatibility)
- Async/await support required

### Terminal Requirements
- 256 color support (standard on modern terminals)
- Unicode support (UTF-8)
- Minimum 80x24 characters (same as current)

## Benefits for Brogue Specifically

### Immediate Wins
1. **Windows Players**: No longer need Windows Terminal or WSL
2. **Inventory UI**: Built-in table/list widgets perfect for items
3. **Help System**: Modal dialogs for controls and tutorials
4. **Debugging**: Visual inspection tools during development

### Future Enhancements
1. **Memory System UI**: Tree widgets for skill progression
2. **Weapon Evolution Display**: Rich visual representation
3. **Crafting Interface**: Drag-and-drop style interactions
4. **Settings Menu**: Easy configuration UI
5. **Achievement Tracking**: Visual progress indicators

### Developer Velocity
- Faster UI iteration with CSS
- Less boilerplate code
- Built-in responsive layout
- Better code organization

## Resources

### Official Documentation
- [Textual Docs](https://textual.textualize.io/)
- [Widget Gallery](https://textual.textualize.io/widget_gallery/)
- [Tutorial](https://textual.textualize.io/tutorial/)

### Roguelike-Specific Examples
- Grid-based game layouts
- Turn-based input handling
- Map viewport implementations
- Inventory management patterns

### Community
- [Textual Discord](https://discord.gg/Enf6Z3qhVr)
- [GitHub Discussions](https://github.com/Textualize/textual/discussions)
- Active community with game dev experience

## Decision Rationale

This decision was made to ensure:
1. **Maximum player reach** across all platforms
2. **Sustainable development** with modern tooling
3. **Scalable UI** for complex game features
4. **Professional quality** that matches Brogue's vision

The extra complexity of async/await is offset by:
- Better abstraction of terminal differences
- Rich widget library saving development time
- Professional-grade UI capabilities
- Future-proof architecture

## Timeline

- **2025-10-14**: Decision documented, migration planning begins
- **TBD**: Textual prototype development
- **TBD**: Feature parity achieved
- **TBD**: Production cutover
- **TBD**: Enhanced UI features leveraging Textual

---

**This is the way for Brogue UI development going forward.**
