import logging
from pathlib import Path
from typing import Literal

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Input

from src.cli.screens import CollectionsScreen, HomeScreen, ImportScreen, SearchScreen
from src.cli.screens.confirm_prompt_screen import ConfirmPromptScreen
from src.cli.screens.input_prompt_screen import InputPromptScreen
from src.cli.ui.messages import (
    AddSelectedRequested,
    BackRequested,
    NavigateRequested,
    SearchInputFocused,
    SearchSubmitted,
    UndoRequested,
)
from src.cli.ui.mode_state import ModeState
from src.cli.widgets import StatusBar, TitleBar
from src.usecases.collections import (
    delete_collection,
    get_working_collection_id,
    get_working_collection_name,
    rename_collection,
    save_working_collection,
    set_working_collection_name,
    start_new_collection,
    undo_last,
)
from src.usecases.search_cards import search_cards


LOG = logging.getLogger(__name__)


def _user_message(operation: str, error: Exception) -> str:
    LOG.exception("%s failed", operation)

    if str(error).strip():
        return f"{operation} failed: {error}"
    return f"{operation} failed. Please try again."


CSS_FILE = Path(__file__).parent / "app.tcss"

DEFAULT_HINTS = "s: search  i: import  c: collections  q: quit"
SEARCH_HINTS = "Space: select  a: add  u: undo  i: image  /: search"
SELECT_HINTS = "SELECT: Space: toggle  a: add  u: undo  i: image  /: search  Esc: back"


class RootScreen(Screen):
    can_focus = True
    mode_state = reactive(ModeState(mode="NAV", breadcrumb="Home", hints=DEFAULT_HINTS))

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
        Binding("escape", "blur_or_back", "Blur/Back", priority=True),
        Binding("ctrl+s", "save_working", "Save", priority=True),
        Binding("+,plus,shift+equals,equals", "qty_up", "Qty +", priority=True),
        Binding("-,minus", "qty_down", "Qty -", priority=True),
        ("e", "rename_draft", "Rename draft"),
        ("d", "remove_or_delete", "Remove/Delete"),
        ("r", "rename_collection", "Rename collection"),
        ("n", "new_collection", "New collection"),
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
        home_screen = self.query_one("#home-screen", HomeScreen)
        self.run_worker(home_screen.refresh_home(), exclusive=False)

    def watch_mode_state(self, state: ModeState) -> None:
        self._sync_status()

    def _sync_status(self) -> None:
        self.query_one(StatusBar).update_from_state(self.mode_state)

    def _set_mode_state(self, state: ModeState) -> None:
        self.mode_state = state

    def _notify(
        self,
        message: str,
        kind: Literal["success", "info", "warning", "error"] = "info",
        title: str | None = None,
    ) -> None:
        severity_map = {
            "success": "information",
            "info": "information",
            "warning": "warning",
            "error": "error",
        }
        severity = severity_map[kind]

        if kind == "error" and title is None:
            title = "Error"

        self.notify(message, severity=severity, title=title)

    def _refresh_screens_after_draft_change(
        self, reselect_collection_id: int | None = None
    ) -> None:
        self.query_one("#search-screen", SearchScreen).refresh_after_collection_change()
        home_screen = self.query_one("#home-screen", HomeScreen)
        self.run_worker(home_screen.refresh_home(), exclusive=False)
        collections_screen = self.query_one("#collections-screen", CollectionsScreen)

        if reselect_collection_id is not None:
            self.run_worker(
                collections_screen.refresh_after_rename_or_delete(
                    reselect_collection_id
                ),
                exclusive=True,
            )
        else:
            self.run_worker(collections_screen.refresh_collection(), exclusive=True)

    def _show_screen(self, screen_id: str, breadcrumb: str, hints: str) -> None:
        for target in self.query(".screen"):
            target.add_class("is-hidden")

        self.query_one(f"#{screen_id}").remove_class("is-hidden")

        if screen_id == "search-screen":
            self.query_one(
                "#search-screen", SearchScreen
            ).refresh_after_collection_change()

        if screen_id == "home-screen":
            home_screen = self.query_one("#home-screen", HomeScreen)
            self.run_worker(home_screen.refresh_home(), exclusive=False)

        self._set_mode_state(ModeState(mode="NAV", breadcrumb=breadcrumb, hints=hints))

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

        try:
            listings = await search_cards(message.query)
        except Exception as e:
            self._notify(_user_message("Search", e), "error")
            self._set_mode_state(
                ModeState(
                    mode="NAV",
                    breadcrumb=self.mode_state.breadcrumb,
                    hints=SEARCH_HINTS,
                )
            )
            return

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

    def on_add_selected_requested(self, _: AddSelectedRequested) -> None:
        search_screen = self.query_one("#search-screen", SearchScreen)
        added_count = search_screen.add_selected_to_collection()

        if added_count > 0:
            self._refresh_screens_after_draft_change()
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
        self._refresh_screens_after_draft_change()
        self._set_mode_state(
            ModeState(
                mode=self.mode_state.mode,
                breadcrumb=self.mode_state.breadcrumb,
                hints="Undo last collection change",
            )
        )

    def on_back_requested(self, _: BackRequested) -> None:
        self.action_back()

    def action_blur_or_back(self) -> None:
        focused = self.app.focused
        search_input = self.query_one("#search-input", Input)

        if (
            not self.query_one("#search-screen", SearchScreen).has_class("is-hidden")
            and focused is search_input
        ):
            search_input.blur()
            self._set_mode_state(
                ModeState(
                    mode="NAV",
                    breadcrumb=self.mode_state.breadcrumb,
                    hints=SEARCH_HINTS,
                )
            )
            return

        self.post_message(BackRequested())

    def action_save_working(self) -> None:
        if self.query_one("#search-screen", SearchScreen).has_class("is-hidden"):
            return

        name = get_working_collection_name()
        self.app.push_screen(
            InputPromptScreen("Save collection as", initial=name),
            self._on_save_collection_done,
        )

    def action_qty_up(self) -> None:
        search_screen = self.query_one("#search-screen", SearchScreen)

        if search_screen.has_class("is-hidden"):
            return

        if search_screen.adjust_selected_quantity(1):
            self._refresh_screens_after_draft_change()
        else:
            self._notify("Select a working item to adjust.", "info")

    def action_qty_down(self) -> None:
        search_screen = self.query_one("#search-screen", SearchScreen)

        if search_screen.has_class("is-hidden"):
            return

        if search_screen.adjust_selected_quantity(-1):
            self._refresh_screens_after_draft_change()
        else:
            self._notify("Select a working item to adjust.", "info")

    def action_rename_draft(self) -> None:
        if self.query_one("#search-screen", SearchScreen).has_class("is-hidden"):
            return

        name = get_working_collection_name()
        self.app.push_screen(
            InputPromptScreen("Rename working collection", initial=name),
            self._on_draft_rename_done,
        )

    def action_remove_or_delete(self) -> None:
        collections_screen = self.query_one("#collections-screen", CollectionsScreen)
        search_screen = self.query_one("#search-screen", SearchScreen)

        if not collections_screen.has_class("is-hidden"):
            cid = collections_screen.get_selected_collection_id()

            if cid is not None:
                name = collections_screen.get_selected_collection_name()
                self.app.push_screen(
                    ConfirmPromptScreen(
                        f'Delete collection "{name}"? This cannot be undone.'
                    ),
                    lambda confirmed: self._on_delete_confirmed(confirmed, cid),
                )
            return

        if not search_screen.has_class("is-hidden"):
            if search_screen.remove_selected_item():
                self._refresh_screens_after_draft_change()

    def action_rename_collection(self) -> None:
        collections_screen = self.query_one("#collections-screen", CollectionsScreen)

        if collections_screen.has_class("is-hidden"):
            return

        cid = collections_screen.get_selected_collection_id()

        if cid is None:
            return

        name = collections_screen.get_selected_collection_name()
        self.app.push_screen(
            InputPromptScreen("Rename collection", initial=name),
            lambda result: self._on_collection_rename_done(result, cid),
        )

    def action_new_collection(self) -> None:
        if self.query_one("#collections-screen", CollectionsScreen).has_class(
            "is-hidden"
        ):
            return

        name = get_working_collection_name()
        self.app.push_screen(
            InputPromptScreen("New collection name", initial=name),
            self._on_new_collection_done,
        )

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
        collections_screen = self.query_one("#collections-screen", CollectionsScreen)
        self.run_worker(collections_screen.refresh_collection(), exclusive=True)
        self.query_one("#collections-option-list").focus()

    def action_focus_search(self) -> None:
        self.post_message(SearchInputFocused())

    def action_help(self) -> None:
        self._notify("Help overlay coming soon.", "info")

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

    def _on_draft_rename_done(self, result: str | None) -> None:
        if result is None or not result.strip():
            return

        name = result.strip()
        wid = get_working_collection_id()

        if wid is not None:
            self.run_worker(self._do_draft_rename(wid, name), exclusive=False)
            return

        set_working_collection_name(name)
        self._refresh_screens_after_draft_change()

    async def _do_draft_rename(self, collection_id: int, name: str) -> None:
        try:
            await rename_collection(collection_id, name)
        except Exception as e:
            self._notify(_user_message("Rename draft", e), "error")
            return

        set_working_collection_name(name)
        self._refresh_screens_after_draft_change()

    def _on_collection_rename_done(
        self, result: str | None, collection_id: int
    ) -> None:
        if result is None or not result.strip():
            return

        self.run_worker(
            self._do_rename_collection(collection_id, result.strip()),
            exclusive=False,
        )

    async def _do_rename_collection(self, collection_id: int, name: str) -> None:
        try:
            await rename_collection(collection_id, name)
        except Exception as e:
            self._notify(_user_message("Rename collection", e), "error")
            return

        collections_screen = self.query_one("#collections-screen", CollectionsScreen)
        await collections_screen.refresh_after_rename_or_delete(collection_id)

    def _on_new_collection_done(self, result: str | None) -> None:
        if result is None or not result.strip():
            return

        self._do_start_new_collection(result.strip())

    def _on_save_collection_done(self, result: str | None) -> None:
        if result is None or not result.strip():
            return

        self.run_worker(
            self._do_save_working_collection(result.strip()), exclusive=False
        )

    def _on_delete_confirmed(self, confirmed: bool, collection_id: int) -> None:
        if not confirmed:
            return

        self.run_worker(self._do_delete_collection(collection_id), exclusive=False)

    def _do_start_new_collection(self, name: str) -> None:
        start_new_collection(name)
        self._notify("New empty draft. Press Ctrl+S to save.", "info")
        self._refresh_screens_after_draft_change()

    async def _do_save_working_collection(self, name: str) -> None:
        try:
            await save_working_collection(name)
        except Exception as e:
            self._notify(_user_message("Save", e), "error")
            return

        self._notify("Collection saved", "success")
        self._refresh_screens_after_draft_change(get_working_collection_id())

    async def _do_delete_collection(self, collection_id: int) -> None:
        try:
            await delete_collection(collection_id)
        except Exception as e:
            self._notify(_user_message("Delete collection", e), "error")
            return

        self._refresh_screens_after_draft_change()


class CardScraperApp(App):
    CSS_PATH = str(CSS_FILE)
    TITLE = "CoolStuffInc Card Scraper"

    async def on_mount(self) -> None:
        await self.push_screen(RootScreen())
