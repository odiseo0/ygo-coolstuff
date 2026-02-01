from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Static


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
