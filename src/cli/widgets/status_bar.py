from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Static

from src.cli.ui.mode_state import ModeState


class StatusBar(Container):
    def compose(self) -> ComposeResult:
        with Horizontal(id="status-bar"):
            yield Static("NAV", id="status-left")
            yield Static("Home", id="status-center")
            yield Static(
                "s: search  i: import  c: collections  q: quit", id="status-right"
            )

    def update_from_state(self, state: ModeState) -> None:
        self.query_one("#status-left", Static).update(state.mode)
        self.query_one("#status-center", Static).update(state.breadcrumb)
        self.query_one("#status-right", Static).update(state.hints)
