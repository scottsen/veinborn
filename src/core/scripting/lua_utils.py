"""
Shared helpers for reading values out of Lua tables from Python.

lupa raises KeyError/TypeError (not a consistent one or the other) when a
key is missing or the "table" isn't actually indexable — every call site
that reads an optional Lua field ends up re-writing the same
try/except/default dance. `lua_table_get` centralizes that.
"""
from typing import Any, Callable, List, Optional


def lua_table_get(
    table: Any,
    key: Any,
    default: Optional[Any] = None,
    coerce: Optional[Callable[[Any], Any]] = None,
) -> Any:
    """
    Safely read `key` from a Lua table, tolerating missing keys and
    non-table values.

    Args:
        table: Lua table (or any indexable/None value)
        key: Key to read
        default: Value to return if the key is absent or table isn't indexable
        coerce: Optional function applied to a found, non-None value (e.g. `bool`, `str`)

    Returns:
        The (optionally coerced) value, or `default`
    """
    try:
        value = table[key]
    except (KeyError, TypeError):
        return default

    if value is None:
        return default

    return coerce(value) if coerce is not None else value


def lua_array_to_list(
    lua_array: Any, transform: Optional[Callable[[Any], Any]] = None
) -> List[Any]:
    """
    Convert a 1-indexed Lua array table to a Python list, skipping falsy
    entries (Lua's `nil`/`false` holes in an otherwise-sequential table).

    Args:
        lua_array: Lua array table, or any falsy value (treated as empty)
        transform: Optional function applied to each non-falsy element

    Returns:
        Python list of (optionally transformed) elements
    """
    if not lua_array:
        return []

    result = []
    for i in range(1, len(lua_array) + 1):
        item = lua_array[i]
        if item:
            result.append(transform(item) if transform is not None else item)
    return result
