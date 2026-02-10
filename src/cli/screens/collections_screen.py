from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import OptionList, Static
from textual.widgets.option_list import Option

from src.models.db_models import Collection
from src.usecases.collections import (
    list_collections,
    load_collection,
    load_working_collection,
)


class CollectionsScreen(Container):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._collections: list[Collection] = []
        self._loading_list = True
        self._loading_detail = False
        self._selected_collection_id: int | None = None
        self._detail_collection: Collection | None = None

    def compose(self) -> ComposeResult:
        with Horizontal(classes="split-collection", id="collections-split"):
            with Container(
                classes="panel split-panel split-panel-left", id="collections-list"
            ):
                yield Static("Collections", classes="panel-title")
                yield Static("Loading…", classes="muted", id="collections-list-status")
                yield OptionList(id="collections-option-list")
                yield Static(
                    "Enter: load  n: new  r: rename  d: delete", classes="muted"
                )
            with Container(classes="panel split-panel", id="collections-detail"):
                yield Static(
                    "Details", classes="panel-title", id="collections-detail-title"
                )
                yield Container(id="collections-detail-content")

    async def on_mount(self) -> None:
        await self._refresh_list()

    async def _refresh_list(self) -> None:
        self._loading_list = True
        self._render_list_state()
        self._collections = await list_collections()
        self._loading_list = False
        option_list = self.query_one("#collections-option-list", OptionList)
        option_list.clear_options()

        if not self._collections:
            self._render_list_state()
            return

        options = [
            Option(f"{c.name} (id:{c.id})", id=str(c.id)) for c in self._collections
        ]

        option_list.add_options(options)

        if option_list.option_count > 0:
            option_list.highlighted = 0

        self._render_list_state()

    def _render_list_state(self) -> None:
        status = self.query_one("#collections-list-status", Static)

        if self._loading_list:
            status.update("Loading…")
        elif not self._collections:
            status.update("No collections")
        else:
            status.update("")

    async def _load_detail(self, collection_id: int) -> None:
        self._loading_detail = True
        self._selected_collection_id = collection_id
        self._render_detail_content()
        coll = await load_collection(collection_id)
        await load_working_collection(collection_id)
        self._loading_detail = False
        self._detail_collection = coll
        self._render_detail_content()

    def _render_detail_content(self) -> None:
        content = self.query_one("#collections-detail-content", Container)
        for child in list(content.children):
            child.remove()

        title = self.query_one("#collections-detail-title", Static)

        if self._loading_detail:
            title.update("Details")
            content.mount(Static("Loading…", classes="muted"))
            return

        if self._detail_collection is None:
            title.update("Details")
            content.mount(Static("Select a collection", classes="muted"))
            return

        title.update(self._detail_collection.name)

        if not self._detail_collection.items:
            content.mount(Static("No items in this collection", classes="muted"))
            return

        content.mount(
            Static(
                "Card Name                 Code         Qty",
                classes="table-header",
            )
        )

        for item in self._detail_collection.items:
            row = Static(
                f"{item.card_name[:24]:<24}  {item.card_code:<12}  {item.card_quantity}",
                classes="table-row",
            )
            content.mount(row)

    def get_selected_collection_id(self) -> int | None:
        return self._selected_collection_id

    def get_selected_collection_name(self) -> str:
        if self._detail_collection is not None:
            return self._detail_collection.name

        for c in self._collections:
            if c.id == self._selected_collection_id:
                return c.name

        return ""

    async def refresh_after_rename_or_delete(
        self, collection_id_to_reselect: int | None = None
    ) -> None:
        await self._refresh_list()
        self._detail_collection = None
        self._selected_collection_id = None
        if collection_id_to_reselect is not None:
            option_list = self.query_one("#collections-option-list", OptionList)
            for i, c in enumerate(self._collections):
                if c.id == collection_id_to_reselect:
                    option_list.highlighted = i
                    break
            await self._load_detail(collection_id_to_reselect)
        else:
            self._render_detail_content()

    def _on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        try:
            collection_id = int(event.option_id)
        except (ValueError, TypeError):
            return

        self.run_worker(self._load_detail(collection_id), exclusive=True)
