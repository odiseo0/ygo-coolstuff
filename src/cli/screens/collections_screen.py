from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Static


class CollectionsScreen(Container):
    def compose(self) -> ComposeResult:
        with Horizontal(classes="split-collection", id="collections-split"):
            with Container(
                classes="panel split-panel split-panel-left", id="collections-list"
            ):
                yield Static("Collections", classes="panel-title")
                yield Static("Edison - March 2026", classes="list-item row-selected")
                yield Static("Goat staples", classes="list-item")
                yield Static("Blue-Eyes build", classes="list-item")
                yield Static(
                    "Enter: load  n: new  r: rename  d: delete", classes="muted"
                )
            with Container(classes="panel split-panel", id="collections-detail"):
                yield Static("Details", classes="panel-title")
                with Container(classes="table"):
                    yield Static(
                        "Card Name                 Code         Qty",
                        classes="table-header",
                    )
                    yield Static(
                        "Blackwing - Bora          CRMS-EN017   2",
                        classes="table-row",
                    )
                    yield Static(
                        "Black Whirlwind           RGBT-EN089   3",
                        classes="table-row",
                    )
