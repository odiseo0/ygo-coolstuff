from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Static


class ConfirmPromptScreen(ModalScreen[bool]):
    BINDINGS = [
        ("y", "confirm"),
        ("n", "cancel"),
        ("escape", "cancel"),
    ]

    def __init__(self, message: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._message = message

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static(self._message, classes="panel-title")
            yield Static("y: yes  n: no  Esc: cancel", classes="muted")

    def action_confirm(self) -> None:
        self.dismiss(True)

    def action_cancel(self) -> None:
        self.dismiss(False)
