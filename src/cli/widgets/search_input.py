from textual.widgets import Input


KEYS_NOT_CONSUMED = frozenset(
    {
        "escape",
        "ctrl+s",
        "plus",
        "equals",
        "shift+equals",
        "minus",
        "+",
        "-",
        "=",
    }
)
CHARACTERS_NOT_CONSUMED = frozenset({"+", "-"})


class SearchInput(Input):
    def check_consume_key(self, key: str, character: str | None) -> bool:
        if key in KEYS_NOT_CONSUMED:
            return False

        if character is not None and character in CHARACTERS_NOT_CONSUMED:
            return False

        return character is not None and character.isprintable()
