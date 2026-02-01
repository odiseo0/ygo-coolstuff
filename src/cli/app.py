from pathlib import Path

from textual import events
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Input

from src.cli.screens import CollectionsScreen, HomeScreen, ImportScreen, SearchScreen
from src.cli.ui.messages import (
    AddSelectedRequested,
    BackRequested,
    NavigateRequested,
    SearchInputFocused,
    SearchSubmitted,
    SelectionToggled,
    UndoRequested,
)
from src.cli.ui.mode_state import ModeState
from src.cli.widgets import StatusBar, TitleBar
from src.usecases.collections import undo_last
from src.usecases.search_cards import search_cards


CSS_FILE = Path(__file__).parent / "app.tcss"

DEFAULT_HINTS = "s: search  i: import  c: collections  q: quit"
SEARCH_HINTS = "Space: select  a: add  u: undo  i: image  /: search"
SELECT_HINTS = (
    "SELECT: Space: toggle  a: add  u: undo  i: image  /: search  Esc: back"
)


class RootScreen(Screen):
    can_focus = True
    mode_state = reactive(
        ModeState(mode="NAV", breadcrumb="Home", hints=DEFAULT_HINTS)
    )

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
        self._sync_status()

    def watch_mode_state(self, state: ModeState) -> None:
        self._sync_status()

    def _sync_status(self) -> None:
        self.query_one(StatusBar).update_from_state(self.mode_state)

    def _set_mode_state(self, state: ModeState) -> None:
        self.mode_state = state

    def _show_screen(self, screen_id: str, breadcrumb: str, hints: str) -> None:
        for target in self.query(".screen"):
            target.add_class("is-hidden")
        self.query_one(f"#{screen_id}").remove_class("is-hidden")
        self._set_mode_state(
            ModeState(mode="NAV", breadcrumb=breadcrumb, hints=hints)
        )

    def on_navigate_requested(self, message: NavigateRequested) -> None:
        if message.screen_id == "search-screen":
            self._show_screen("search-screen", "Home > Search", SEARCH_HINTS)
        elif message.screen_id == "import-screen":
            self._show_screen(
                "import-screen",
                "Home > Import",
                "Enter: import  a: add all  Esc: back",
            )
        elif message.screen_id == "collections-screen":
            self._show_screen(
                "collections-screen",
                "Home > Collections",
                "Enter: load  n: new  r: rename  d: delete",
            )
        elif message.screen_id == "home-screen":
            self._show_screen("home-screen", "Home", DEFAULT_HINTS)

    def on_search_input_focused(self, _: SearchInputFocused) -> None:
        self.action_show_search()
        self.query_one("#search-input", Input).focus()
        self._set_mode_state(
            ModeState(
                mode="INSERT",
                breadcrumb=self.mode_state.breadcrumb,
                hints=self.mode_state.hints,
            )
        )

    async def on_search_submitted(self, message: SearchSubmitted) -> None:
        self._set_mode_state(
            ModeState(
                mode="NAV",
                breadcrumb=self.mode_state.breadcrumb,
                hints="Searching...",
            )
        )

        listings = await search_cards(message.query)

        search_screen = self.query_one("#search-screen", SearchScreen)
        search_screen.render_results(listings)

        if listings:
            hints = f"Found {len(listings)} listings"
        else:
            hints = "No results"
        self._set_mode_state(
            ModeState(
                mode="NAV",
                breadcrumb=self.mode_state.breadcrumb,
                hints=hints,
            )
        )

    def on_selection_toggled(self, _: SelectionToggled) -> None:
        search_screen = self.query_one("#search-screen", SearchScreen)
        did_toggle = search_screen.toggle_current_row_selection()

        if did_toggle:
            self._set_mode_state(
                ModeState(
                    mode="SELECT",
                    breadcrumb=self.mode_state.breadcrumb,
                    hints=SELECT_HINTS,
                )
            )

    def on_add_selected_requested(self, _: AddSelectedRequested) -> None:
        search_screen = self.query_one("#search-screen", SearchScreen)
        added_count = search_screen.add_selected_to_collection()

        if added_count == 0:
            hints = "No rows selected"
        else:
            hints = f"Added {added_count} item(s) to collection"
        self._set_mode_state(
            ModeState(
                mode="NAV",
                breadcrumb=self.mode_state.breadcrumb,
                hints=hints,
            )
        )

    def on_undo_requested(self, _: UndoRequested) -> None:
        undo_last()
        search_screen = self.query_one("#search-screen", SearchScreen)
        search_screen.refresh_after_collection_change()
        self._set_mode_state(
            ModeState(
                mode=self.mode_state.mode,
                breadcrumb=self.mode_state.breadcrumb,
                hints="Undo last collection change",
            )
        )

    def on_back_requested(self, _: BackRequested) -> None:
        self.action_back()

    def on_key(self, event: events.Key) -> None:
        if self.mode_state.mode == "INSERT" and event.key != "escape":
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
        elif event.key == "a":
            self.post_message(AddSelectedRequested())
            event.stop()
        elif event.key in {"space", " "}:
            search_screen = self.query_one("#search-screen", SearchScreen)
            if not search_screen.has_class("is-hidden"):
                did_toggle = search_screen.toggle_current_row_selection()
                if did_toggle:
                    self._set_mode_state(
                        ModeState(
                            mode="SELECT",
                            breadcrumb=self.mode_state.breadcrumb,
                            hints=SELECT_HINTS,
                        )
                    )
            event.stop()
        elif event.key == "u":
            self.post_message(UndoRequested())
            event.stop()
        elif event.key == "escape":
            self.post_message(BackRequested())
            event.stop()
        elif event.key == "q":
            self.action_quit()
            event.stop()

    def action_show_search(self) -> None:
        self._show_screen("search-screen", "Home > Search", SEARCH_HINTS)

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
        self.post_message(SearchInputFocused())

    def action_help(self) -> None:
        self.app.notify("Help overlay coming soon.", severity="information")

    def action_undo(self) -> None:
        self.post_message(UndoRequested())

    def action_add_selected(self) -> None:
        self.post_message(AddSelectedRequested())

    def action_toggle_select(self) -> None:
        search_screen = self.query_one("#search-screen", SearchScreen)
        if search_screen.has_class("is-hidden"):
            return
        did_toggle = search_screen.toggle_current_row_selection()
        if did_toggle:
            self._set_mode_state(
                ModeState(
                    mode="SELECT",
                    breadcrumb=self.mode_state.breadcrumb,
                    hints=SELECT_HINTS,
                )
            )

    def action_back(self) -> None:
        if not self.query_one("#home-screen").has_class("is-hidden"):
            self._set_mode_state(
                ModeState(mode="NAV", breadcrumb="Home", hints=DEFAULT_HINTS)
            )
            return
        self._show_screen("home-screen", "Home", DEFAULT_HINTS)

    def action_quit(self) -> None:
        self.app.exit()


class CardScraperApp(App):
    CSS_PATH = str(CSS_FILE)
    TITLE = "CoolStuffInc Card Scraper"

    async def on_mount(self) -> None:
        await self.push_screen(RootScreen())
