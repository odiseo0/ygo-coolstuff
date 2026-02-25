from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Static

from src.usecases.home_summary import get_home_summary


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
                    yield Static("—", id="home-recent-collections", classes="list-item")
                with Container(classes="panel column-panel"):
                    yield Static("Status", classes="panel-title")
                    yield Static("—", id="home-status", classes="muted")

    async def refresh_home(self) -> None:
        summary = await get_home_summary()
        recent_node = self.query_one("#home-recent-collections", Static)
        status_node = self.query_one("#home-status", Static)

        if summary.recent_collections:
            lines = [c.name for c in summary.recent_collections]
            recent_node.update("\n".join(lines))
        else:
            recent_node.update(
                "No collections" if summary.db_status == "ready" else "—"
            )

        status_lines = [
            f"DB: {summary.db_status}",
            f"Working: {summary.working_name}",
            f"Items: {summary.working_item_count}  Total qty: {summary.working_total_qty}",
        ]
        status_node.update("\n".join(status_lines))
