from textual import events
from textual.widgets import DataTable

from src.cli.ui.messages import SelectionToggled


class ResultsTable(DataTable):
    def on_key(self, event: events.Key) -> None:
        if event.key in {" ", "space"}:
            self.post_message(SelectionToggled())
            event.stop()
