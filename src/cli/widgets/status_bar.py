from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Static

from src.cli.ui.mode_state import ModeState


class StatusBar(Container):
    def compose(self) -> ComposeResult:
        with Horizontal(id="status-bar"):
            yield Static(
                "s: search  i: import  c: collections  q: quit", id="status-left"
            )
            yield Static("", id="status-center")
            yield Static("Mode: NAV", id="status-right", classes="muted")

    def update_from_state(self, state: ModeState) -> None:
        self.query_one("#status-left", Static).update(state.hints)
        self.query_one("#status-center", Static).update(state.breadcrumb)
        self.query_one("#status-right", Static).update(f"Mode: {state.mode}")
