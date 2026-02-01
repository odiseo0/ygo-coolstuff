from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Static


class TitleBar(Container):
    def compose(self) -> ComposeResult:
        with Horizontal(id="title-bar"):
            yield Static("CoolStuffInc Card Scraper", id="title-left")
            yield Static("Local", id="title-right")
