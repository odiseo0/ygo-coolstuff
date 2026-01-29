from pathlib import Path
from typing import TYPE_CHECKING

from textual import events
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import DataTable, Input, Static
from textual.widgets.data_table import CellDoesNotExist, RowDoesNotExist

from src.models.cards import CardListing
from src.usecases.collections import (
    add_items,
    get_working_collection,
    is_in_collection,
    make_collection_items_from_listings,
    undo_last,
)
from src.usecases.search_cards import search_cards


if TYPE_CHECKING:
    pass


CSS_FILE = Path(__file__).parent / "app.tcss"


class TitleBar(Container):
    def compose(self) -> ComposeResult:
        with Horizontal(id="title-bar"):
            yield Static("CoolStuffInc Card Scraper", id="title-left")
            yield Static("Local", id="title-right")


class StatusBar(Container):
    def compose(self) -> ComposeResult:
        with Horizontal(id="status-bar"):
            yield Static("NAV", id="status-left")
            yield Static("Home", id="status-center")
            yield Static(
                "s: search  i: import  c: collections  q: quit", id="status-right"
            )

    def update_status(self, mode: str, breadcrumb: str, hints: str) -> None:
        self.query_one("#status-left", Static).update(mode)
        self.query_one("#status-center", Static).update(breadcrumb)
        self.query_one("#status-right", Static).update(hints)


class HomeScreen(Container):
    def compose(self) -> ComposeResult:
        with Container(classes="panel", id="home-panel"):
            yield Static("Home", classes="panel-title")
            with Horizontal(classes="columns"):
                with Container(classes="panel column-panel column-panel-left"):
                    yield Static("Quick Actions", classes="panel-title")
                    yield Static("s  Search", classes="list-item")
                    yield Static("i  Import", classes="list-item")
                    yield Static("c  Collections", classes="list-item")
                    yield Static("?  Help", classes="list-item")
                with Container(classes="panel column-panel column-panel-left"):
                    yield Static("Recent Collections", classes="panel-title")
                    yield Static("March 2026 - Edison set", classes="list-item")
                    yield Static("Goat format staples", classes="list-item")
                    yield Static("Blue-Eyes build", classes="list-item")
                with Container(classes="panel column-panel"):
                    yield Static("Status", classes="panel-title")
                    yield Static("Last scrape: 2 hours ago", classes="muted")
                    yield Static("DB: ready", classes="muted")


class ResultsTable(DataTable):
    class ToggleRequested(Message):
        pass

    def on_key(self, event: events.Key) -> None:
        if event.key in {" ", "space"}:
            self.post_message(self.ToggleRequested())
            event.stop()


class RootScreen(Screen):
    can_focus = True
    mode = reactive("NAV")
    breadcrumb = reactive("Home")
    hints = reactive("s: search  i: import  c: collections  q: quit")

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("s", "show_search", "Search"),
        ("i", "show_import", "Import"),
        ("c", "show_collections", "Collections"),
        ("/", "focus_search", "Search"),
        ("?", "help", "Help"),
        ("u", "undo", "Undo"),
        ("a", "add_selected", "Add to collection"),
        ("space", "toggle_select", "Select row"),
        ("escape", "back", "Back"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="app-root"):
            yield TitleBar()
            with Container(id="content"):
                yield HomeScreen(id="home-screen", classes="screen")
                yield SearchScreen(id="search-screen", classes="screen is-hidden")
                yield CollectionsScreen(
                    id="collections-screen", classes="screen is-hidden"
                )
                yield ImportScreen(id="import-screen", classes="screen is-hidden")
            yield StatusBar()

    def on_mount(self) -> None:
        self.focus()
        self._update_status()

    def on_key(self, event: events.Key) -> None:
        if self.mode == "INSERT" and event.key not in {"escape"}:
            return
        if event.key == "s":
            self.action_show_search()
            event.stop()
        elif event.key == "i":
            self.action_show_import()
            event.stop()
        elif event.key == "c":
            self.action_show_collections()
            event.stop()
        elif event.key == "/":
            self.action_focus_search()
            event.stop()
        elif event.key == "a":
            self.action_add_selected()
            event.stop()
        elif event.key in {"space", " "}:
            self.action_toggle_select()
            event.stop()
        elif event.key == "u":
            self.action_undo()
            event.stop()
        elif event.key == "escape":
            self.action_back()
            event.stop()
        elif event.key == "q":
            self.action_quit()
            event.stop()

    def watch_mode(self, mode: str) -> None:
        self._update_status()

    def watch_breadcrumb(self, breadcrumb: str) -> None:
        self._update_status()

    def watch_hints(self, hints: str) -> None:
        self._update_status()

    def _update_status(self) -> None:
        self.query_one(StatusBar).update_status(self.mode, self.breadcrumb, self.hints)

    def _set_mode(self, mode: str) -> None:
        self.mode = mode

    def _show_screen(self, screen_id: str, breadcrumb: str, hints: str) -> None:
        for target in self.query(".screen"):
            target.add_class("is-hidden")
        self.query_one(f"#{screen_id}").remove_class("is-hidden")
        self.breadcrumb = breadcrumb
        self.hints = hints
        self._set_mode("NAV")

    def action_show_search(self) -> None:
        self._show_screen(
            "search-screen",
            "Home > Search",
            "Space: select  a: add  u: undo  i: image  /: search",
        )

    def action_show_import(self) -> None:
        self._show_screen(
            "import-screen",
            "Home > Import",
            "Enter: import  a: add all  Esc: back",
        )

    def action_show_collections(self) -> None:
        self._show_screen(
            "collections-screen",
            "Home > Collections",
            "Enter: load  n: new  r: rename  d: delete",
        )

    def action_focus_search(self) -> None:
        self.action_show_search()
        self.query_one("#search-input", Input).focus()
        self._set_mode("INSERT")

    def action_help(self) -> None:
        self.app.notify("Help overlay coming soon.", severity="information")

    def action_undo(self) -> None:
        undo_last()

        search_screen = self.query_one("#search-screen", SearchScreen)
        search_screen.refresh_after_collection_change()

        self.hints = "Undo last collection change"
        self._update_status()

    def action_add_selected(self) -> None:
        search_screen = self.query_one("#search-screen", SearchScreen)
        added_count = search_screen.add_selected_to_collection()

        if added_count == 0:
            self.hints = "No rows selected"
        else:
            self.hints = f"Added {added_count} item(s) to collection"
        self._set_mode("NAV")
        self._update_status()

    def action_toggle_select(self) -> None:
        search_screen = self.query_one("#search-screen", SearchScreen)
        did_toggle = search_screen.toggle_current_row_selection()

        if did_toggle:
            self._set_mode("SELECT")
            self.hints = (
                "SELECT: Space: toggle  a: add  u: undo  i: image  /: search  Esc: back"
            )
            self._update_status()

    def action_back(self) -> None:
        if not self.query_one("#home-screen").has_class("is-hidden"):
            self._set_mode("NAV")
            return
        self._show_screen(
            "home-screen",
            "Home",
            "s: search  i: import  c: collections  q: quit",
        )

    def action_quit(self) -> None:
        self.app.exit()


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


class CollectionsScreen(Container):
    def compose(self) -> ComposeResult:
        with Horizontal(classes="split-collection", id="collections-split"):
            with Container(
                classes="panel split-panel split-panel-left", id="collections-list"
            ):
                yield Static("Collections", classes="panel-title")
                yield Static("Edison - March 2026", classes="list-item row-selected")
                yield Static("Goat staples", classes="list-item")
                yield Static("Blue-Eyes build", classes="list-item")
                yield Static(
                    "Enter: load  n: new  r: rename  d: delete", classes="muted"
                )
            with Container(classes="panel split-panel", id="collections-detail"):
                yield Static("Details", classes="panel-title")
                with Container(classes="table"):
                    yield Static(
                        "Card Name                 Code         Qty",
                        classes="table-header",
                    )
                    yield Static(
                        "Blackwing - Bora          CRMS-EN017   2",
                        classes="table-row",
                    )
                    yield Static(
                        "Black Whirlwind           RGBT-EN089   3",
                        classes="table-row",
                    )


class ImportScreen(Container):
    def compose(self) -> ComposeResult:
        with Horizontal(classes="split-equal", id="import-split"):
            with Container(
                classes="panel split-panel split-panel-left", id="import-list"
            ):
                yield Static("Import (.txt / .ydk)", classes="panel-title")
                yield Static("cards.txt", classes="list-item row-selected")
                yield Static("decklist.ydk", classes="list-item")
                yield Static("goat.txt", classes="list-item")
                yield Static("Enter: import  Esc: back", classes="muted")
            with Container(classes="panel split-panel", id="import-preview"):
                yield Static("Preview", classes="panel-title")
                yield Static("3x Dark Magician", classes="list-item")
                yield Static("2x Magician's Rod", classes="list-item")
                yield Static("2x Dark Magical Circle", classes="list-item")


class CardScraperApp(App):
    CSS_PATH = str(CSS_FILE)
    TITLE = "CoolStuffInc Card Scraper"

    async def on_mount(self) -> None:
        await self.push_screen(RootScreen())
