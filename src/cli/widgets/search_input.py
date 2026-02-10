"""Search input that does not consume priority keys so screen bindings can handle them."""

from textual.widgets import Input

KEYS_NOT_CONSUMED = frozenset(
    {"escape", "ctrl+s", "plus", "equals", "shift+equals", "minus"}
)


class SearchInput(Input):
    """Input that yields escape, ctrl+s, +, - to screen bindings even when focused."""

    def check_consume_key(self, key: str, character: str | None) -> bool:
        if key in KEYS_NOT_CONSUMED:
            return False
        return character is not None and character.isprintable()
