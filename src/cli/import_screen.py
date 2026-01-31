from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Static


class ImportScreen(Container):
    def compose(self) -> ComposeResult:
        with Horizontal(classes="split-equal", id="import-split"):
            with Container(
                classes="panel split-panel split-panel-left", id="import-list"
            ):
                yield Static("Import (.txt / .ydk)", classes="panel-title")
                yield Static("cards.txt", classes="list-item row-selected")
                yield Static("decklist.ydk", classes="list-item")
                yield Static("goat.txt", classes="list-item")
                yield Static("Enter: import  Esc: back", classes="muted")
            with Container(classes="panel split-panel", id="import-preview"):
                yield Static("Preview", classes="panel-title")
                yield Static("3x Dark Magician", classes="list-item")
                yield Static("2x Magician's Rod", classes="list-item")
                yield Static("2x Dark Magical Circle", classes="list-item")
