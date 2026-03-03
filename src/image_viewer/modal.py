from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen

from src.image_viewer.widget import CardImageViewer


class CardImageModal(ModalScreen[None]):
    BINDINGS = [
        Binding("escape", "close", "Close", priority=True),
        Binding("q", "close", "Close", priority=True),
        Binding("i", "close", "Close", priority=True),
    ]

    DEFAULT_CSS = """
    CardImageModal {
        align: center middle;
        background: #00000099;
    }

    CardImageModal > CardImageViewer {
        width: 85%;
        height: 85%;
        border: round white;
    }
    """

    def __init__(self, image_url: str, *, id: str | None = None) -> None:
        super().__init__(id=id)
        self.image_url = image_url

    def compose(self) -> ComposeResult:
        yield CardImageViewer(url=self.image_url)

    def action_close(self) -> None:
        self.dismiss(None)
