from textual import events
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.message import Message
from textual.widgets import DataTable, Input, Static
from textual.widgets.data_table import CellDoesNotExist, RowDoesNotExist

from src.models.cards import CardListing
from src.usecases.collections import (
    add_items,
    get_working_collection,
    is_in_collection,
    make_collection_items_from_listings,
)
from src.usecases.search_cards import search_cards


class ResultsTable(DataTable):
    class ToggleRequested(Message):
        pass

    def on_key(self, event: events.Key) -> None:
        if event.key in {" ", "space"}:
            self.post_message(self.ToggleRequested())
            event.stop()


class SearchScreen(Container):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._row_to_listing: dict[str, "CardListing"] = {}
        self._selected_row_keys: set[str] = set()
        self._column_keys: dict[str, str] = {}

    def compose(self) -> ComposeResult:
        with Horizontal(classes="split", id="search-split"):
            with Container(
                classes="panel split-panel split-panel-left", id="search-main"
            ):
                yield Static("Search", classes="panel-title")
                yield Input(placeholder="Dark Magician", id="search-input")
                yield Static("Press Enter to search, / to edit query", classes="muted")
                yield Static("", classes="spacer")
                yield ResultsTable(id="results-table")
                yield Static(
                    "Space: select  a: add  u: undo  i: image  +/-: qty",
                    classes="muted",
                )
            with Container(classes="panel split-panel", id="search-side"):
                yield Static("Working Collection", classes="panel-title")
                yield Container(id="working-collection-list")
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

    def on_results_table_toggle_requested(
        self, message: ResultsTable.ToggleRequested
    ) -> None:
        root_screen = self.screen
        if isinstance(root_screen, RootScreen):
            root_screen.action_toggle_select()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id != "search-input":
            return

        query = event.input.value
        root_screen = self.screen
        if not isinstance(root_screen, RootScreen):
            return

        root_screen.mode = "NAV"
        root_screen.hints = "Searching..."
        root_screen._update_status()

        listings = await search_cards(query)

        self._render_results(listings)

        if listings:
            root_screen.hints = f"Found {len(listings)} listings"
        else:
            root_screen.hints = "No results"
        root_screen._update_status()

        event.input.blur()

    def _render_results(self, listings: list["CardListing"]) -> None:
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

    def _make_row_key(self, listing: "CardListing") -> str:
        return f"{listing.code}:{listing.condition}"

    def _normalize_row_key(self, raw_key: object) -> str:
        if isinstance(raw_key, str):
            return raw_key
        value = getattr(raw_key, "value", None)
        if isinstance(value, str):
            return value
        return str(raw_key)

    def _format_display_name(self, row_key: str, listing: "CardListing") -> str:
        prefix = ""
        if is_in_collection(self._make_row_key(listing)):
            prefix += "✓ "
        if row_key in self._selected_row_keys:
            prefix += "> "
        return f"{prefix}{listing.name}"

    def _update_row_display(self, row_key: str, listing: "CardListing") -> None:
        table = self.query_one("#results-table", ResultsTable)
        display_name = self._format_display_name(row_key, listing)
        try:
            table.update_cell(row_key, "Card Name", display_name)
        except (CellDoesNotExist, RowDoesNotExist):
            return

    def _render_working_collection(self) -> None:
        panel = self.query_one("#working-collection-list", Container)

        for child in list(panel.children):
            child.remove()

        items = get_working_collection()
        if not items:
            panel.mount(Static("No items in collection", classes="muted"))
            return

        for item in items:
            text = f"{item.name} ({item.code}) x{item.qty}"
            panel.mount(Static(text, classes="list-item"))

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

        listings: list["CardListing"] = []
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
