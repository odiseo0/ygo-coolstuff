from pathlib import Path

from textual import events
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Input, Static

from src.usecases.collections import undo_last


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


class CardScraperApp(App):
    CSS_PATH = str(CSS_FILE)
    TITLE = "CoolStuffInc Card Scraper"

    async def on_mount(self) -> None:
        await self.push_screen(RootScreen())
