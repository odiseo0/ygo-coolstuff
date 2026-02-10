from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Input, Static


class InputPromptScreen(ModalScreen[str | None]):
    BINDINGS = [("escape", "cancel")]

    def __init__(
        self,
        title: str,
        initial: str = "",
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self._title = title
        self._initial = initial

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static(self._title, classes="panel-title")
            yield Input(value=self._initial, id="prompt-input")

    def on_mount(self) -> None:
        self.query_one("#prompt-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "prompt-input":
            self.dismiss(event.input.value)

    def action_cancel(self) -> None:
        self.dismiss(None)
