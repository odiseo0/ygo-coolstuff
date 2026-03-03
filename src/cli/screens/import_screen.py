from pathlib import Path

from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import OptionList, Static
from textual.widgets.option_list import Option

from src.cli.ui.messages import ImportRequested


MAX_PREVIEW_LINES = 30
MAX_PREVIEW_LINE_LENGTH = 120


class ImportScreen(Container):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._files: list[Path] = []
        self._selected_index: int | None = None

    def compose(self) -> ComposeResult:
        with Horizontal(classes="split-equal", id="import-split"):
            with Container(
                classes="panel split-panel split-panel-left", id="import-list"
            ):
                yield Static("Import (.txt / .ydk)", classes="panel-title")
                yield Static("", id="import-list-status", classes="muted")
                yield OptionList(id="import-file-list")
                yield Static("Enter: import  Esc: back", classes="muted")
            with Container(classes="panel split-panel", id="import-preview"):
                yield Static("Preview", classes="panel-title", id="import-preview-title")
                yield Container(id="import-preview-content")

    def on_mount(self) -> None:
        self._refresh_file_list()
        option_list = self.query_one("#import-file-list", OptionList)

        if self._files:
            option_list.focus()

    def _discover_files(self) -> list[Path]:
        root = Path.cwd()
        candidates: list[Path] = []

        for entry in root.iterdir():
            if not entry.is_file():
                continue

            suffix = entry.suffix.lower()

            if suffix in {".txt", ".ydk"}:
                candidates.append(entry)

        return sorted(candidates, key=lambda path: path.name.lower())

    def _refresh_file_list(self) -> None:
        self._files = self._discover_files()
        option_list = self.query_one("#import-file-list", OptionList)
        status = self.query_one("#import-list-status", Static)

        option_list.clear_options()

        if not self._files:
            self._selected_index = None
            status.update("No .txt or .ydk files found in the current directory.")
            self._render_preview_for_selected()
            return

        status.update("")
        options: list[Option] = []

        for file_path in self._files:
            options.append(Option(file_path.name, id=str(file_path)))

        option_list.add_options(options)

        if self._selected_index is None or not (0 <= self._selected_index < len(self._files)):
            self._selected_index = 0

        option_list.highlighted = self._selected_index
        self._render_preview_for_selected()

    def _set_selected_by_path(self, path_str: str) -> None:
        for idx, file_path in enumerate(self._files):
            if str(file_path) == path_str:
                self._selected_index = idx
                option_list = self.query_one("#import-file-list", OptionList)
                option_list.highlighted = idx
                return

    def _render_preview_for_selected(self) -> None:
        content = self.query_one("#import-preview-content", Container)

        for child in list(content.children):
            child.remove()

        if self._selected_index is None or not self._files:
            content.mount(Static("No file selected", classes="muted"))
            return

        file_path = self._files[self._selected_index]

        lines: list[str] = []

        try:
            with file_path.open("r", encoding="utf-8", errors="replace") as handle:
                for _ in range(MAX_PREVIEW_LINES):
                    line = handle.readline()

                    if not line:
                        break

                    line = line.rstrip("\r\n")

                    if len(line) > MAX_PREVIEW_LINE_LENGTH:
                        line = f"{line[: MAX_PREVIEW_LINE_LENGTH - 1]}…"

                    lines.append(line)
        except OSError as error:
            content.mount(
                Static(f"Could not read file: {error}", classes="muted"),
            )
            return

        if not lines:
            content.mount(Static("File is empty.", classes="muted"))
            return

        for line in lines:
            content.mount(Static(line, classes="list-item"))

    @on(OptionList.OptionHighlighted, "#import-file-list")
    def _on_file_highlighted(self, event: OptionList.OptionHighlighted) -> None:
        if not self._files:
            return

        path_str = event.option_id

        if not isinstance(path_str, str):
            return

        self._set_selected_by_path(path_str)
        self._render_preview_for_selected()

    @on(OptionList.OptionSelected, "#import-file-list")
    def _on_file_selected(self, event: OptionList.OptionSelected) -> None:
        if not self._files:
            return

        path_str = event.option_id

        if not isinstance(path_str, str):
            return

        self._set_selected_by_path(path_str)
        self._render_preview_for_selected()
        self.post_message(ImportRequested(path_str))
