from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Input, OptionList, Static
from textual.widgets.data_table import CellDoesNotExist, RowDoesNotExist
from textual.widgets.option_list import Option

from src.cli.ui.messages import SearchSubmitted
from src.cli.widgets.results_table import ResultsTable
from src.cli.widgets.search_input import SearchInput
from src.models.cards import CardListing
from src.usecases.collections import (
    add_items,
    adjust_quantity,
    get_working_collection,
    get_working_collection_name,
    is_in_collection,
    make_collection_items_from_listings,
    remove_item,
)


class SearchScreen(Container):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._row_to_listing: dict[str, CardListing] = {}
        self._selected_row_keys: set[str] = set()
        self._working_list_keys: list[str] = []

    def compose(self) -> ComposeResult:
        with Horizontal(classes="split", id="search-split"):
            with Container(
                classes="panel split-panel split-panel-left", id="search-main"
            ):
                yield Static("Search", classes="panel-title")
                yield SearchInput(placeholder="Dark Magician", id="search-input")
                yield Static("Press Enter to search, / to edit query", classes="muted")
                yield Static("", classes="spacer")
                yield ResultsTable(id="results-table")
                yield Static(
                    "Space: select  a: add  u: undo  i: image  +/-: qty",
                    classes="muted",
                )
            with Container(classes="panel split-panel", id="search-side"):
                yield Static("Working Collection", classes="panel-title")
                yield Static("", id="working-collection-name", classes="muted")
                yield OptionList(id="working-collection-list")
                yield Static("Ctrl+s: save  d: remove  e: rename", classes="muted")

    def on_mount(self) -> None:
        table = self.query_one("#results-table", ResultsTable)
        table.cursor_type = "row"
        table.zebra_stripes = False
        table.add_column("Card Name", width=65)
        table.add_column("Code", width=15)
        table.add_column("Price", width=12)
        table.add_column("Rarity", width=20)
        table.add_column("Condition", width=12)
        table.add_column("Stock", width=12)
        self.update_working_collection_name()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id != "search-input":
            return

        query = event.input.value.strip()
        self.post_message(SearchSubmitted(query))
        event.input.blur()

    def render_results(self, listings: list[CardListing]) -> None:
        self._render_results(listings)

    def _render_results(self, listings: list[CardListing]) -> None:
        table = self.query_one("#results-table", ResultsTable)
        table.clear(columns=False)
        self._row_to_listing.clear()
        self._selected_row_keys.clear()

        if not listings:
            table.add_row("No results", "", "", "", "", "", key="__no-results__")
            return

        used_row_keys: set[str] = set()

        for listing in listings:
            base_key = self._make_row_key(listing)
            row_key = base_key
            suffix = 1

            while row_key in used_row_keys:
                suffix += 1
                row_key = f"{base_key}#{suffix}"

            used_row_keys.add(row_key)
            self._row_to_listing[row_key] = listing

            display_name = self._format_display_name(row_key, listing)

            table.add_row(
                display_name,
                listing.code,
                listing.price,
                listing.rarity,
                listing.condition,
                str(listing.stock),
                key=row_key,
            )

        table.focus()

        if table.row_count > 0:
            table.move_cursor(row=0, column=0, scroll=True)

        self._render_working_collection()

    def _make_row_key(self, listing: CardListing) -> str:
        return f"{listing.code}:{listing.condition}"

    def _normalize_row_key(self, raw_key: object) -> str:
        if isinstance(raw_key, str):
            return raw_key

        value = getattr(raw_key, "value", None)

        if isinstance(value, str):
            return value

        return str(raw_key)

    def _format_display_name(self, row_key: str, listing: CardListing) -> str:
        prefix = ""
        if is_in_collection(self._make_row_key(listing)):
            prefix += "✓ "

        if row_key in self._selected_row_keys:
            prefix += "> "

        return f"{prefix}{listing.name}"

    def _update_row_display(self, row_key: str, listing: CardListing) -> None:
        table = self.query_one("#results-table", ResultsTable)
        display_name = self._format_display_name(row_key, listing)

        try:
            table.update_cell(row_key, "Card Name", display_name)
        except (CellDoesNotExist, RowDoesNotExist):
            return

    def update_working_collection_name(self) -> None:
        label = self.query_one("#working-collection-name", Static)
        label.update(f"Working Collection: {get_working_collection_name()}")

    def _render_working_collection(self) -> None:
        self.update_working_collection_name()
        option_list = self.query_one("#working-collection-list", OptionList)
        items = get_working_collection()
        keys = [item.key for item in items]

        prev_highlighted = option_list.highlighted
        prev_key: str | None = None
        if prev_highlighted is not None and 0 <= prev_highlighted < len(
            self._working_list_keys
        ):
            prev_key = self._working_list_keys[prev_highlighted]

        option_list.clear_options()
        self._working_list_keys = keys

        if not items:
            option_list.highlighted = None
            return

        option_list.add_options(
            [
                Option(f"{item.name} ({item.code}) x{item.qty}", id=item.key)
                for item in items
            ]
        )
        if prev_key is not None and prev_key in keys:
            option_list.highlighted = keys.index(prev_key)
        else:
            option_list.highlighted = 0

    def refresh_after_collection_change(self) -> None:
        _ = self.query_one("#results-table", ResultsTable)

        for row_key, listing in self._row_to_listing.items():
            self._update_row_display(row_key, listing)

        self._render_working_collection()

    def toggle_current_row_selection(self) -> bool:
        table = self.query_one("#results-table", ResultsTable)

        if table.row_count == 0:
            return False

        table.focus()
        cursor_row = table.cursor_row
        ordered_rows = table.ordered_rows

        if cursor_row < 0 and ordered_rows:
            table.move_cursor(row=0, column=0, scroll=True)
            cursor_row = table.cursor_row

        if cursor_row < 0 or cursor_row >= len(ordered_rows):
            return False

        row_key = self._normalize_row_key(ordered_rows[cursor_row].key)

        if row_key not in self._row_to_listing:
            return False

        if row_key in self._selected_row_keys:
            self._selected_row_keys.remove(row_key)
        else:
            self._selected_row_keys.add(row_key)

        listing = self._row_to_listing.get(row_key)

        if listing is not None:
            self._update_row_display(row_key, listing)

        return True

    def add_selected_to_collection(self) -> int:
        if not self._selected_row_keys:
            return 0

        listings: list[CardListing] = []

        for row_key in self._selected_row_keys:
            listing = self._row_to_listing.get(row_key)
            if listing is not None:
                listings.append(listing)

        if not listings:
            self._selected_row_keys.clear()
            return 0

        items = make_collection_items_from_listings(listings, qty=1)
        add_items(items)

        self._selected_row_keys.clear()
        self.refresh_after_collection_change()

        return len(items)

    def get_selected_working_item_key(self) -> str | None:
        option_list = self.query_one("#working-collection-list", OptionList)
        hi = option_list.highlighted
        if hi is not None and 0 <= hi < len(self._working_list_keys):
            return self._working_list_keys[hi]
        return None

    def get_current_working_item_key(self) -> str | None:
        table = self.query_one("#results-table", ResultsTable)

        if table.row_count == 0:
            return None

        cursor_row = table.cursor_row
        ordered_rows = table.ordered_rows

        if cursor_row < 0 and ordered_rows:
            table.move_cursor(row=0, column=0, scroll=True)
            cursor_row = table.cursor_row

        if cursor_row < 0 or cursor_row >= len(ordered_rows):
            return None

        row_key = self._normalize_row_key(ordered_rows[cursor_row].key)

        if row_key not in self._row_to_listing:
            return None

        if not is_in_collection(row_key):
            return None

        return row_key

    def _key_for_adjust_or_remove(self) -> str | None:
        key = self.get_selected_working_item_key()
        if key is not None and is_in_collection(key):
            return key
        return self.get_current_working_item_key()

    def adjust_selected_quantity(self, delta: int) -> bool:
        key = self._key_for_adjust_or_remove()

        if key is None:
            return False

        return adjust_quantity(key, delta)

    def remove_selected_item(self) -> bool:
        key = self._key_for_adjust_or_remove()

        if key is None:
            return False

        return remove_item(key)
