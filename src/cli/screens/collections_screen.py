from decimal import Decimal

from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import DataTable, OptionList, Static
from textual.widgets.option_list import Option

from src.models.db_models import Collection
from src.usecases.collections import (
    get_working_collection_id,
    list_collections,
    load_collection_into_working,
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

    async def refresh_collection(self) -> None:
        await self._refresh_list()

    async def _refresh_list(self) -> None:
        option_list = self.query_one("#collections-option-list", OptionList)
        prior_highlighted = option_list.highlighted
        reselect_id = self._selected_collection_id

        self._loading_list = True
        self._render_list_state()
        self._collections = await list_collections()
        self._loading_list = False
        option_list.clear_options()

        if not self._collections:
            self._selected_collection_id = None
            self._detail_collection = None
            self._render_list_state()
            self._render_detail_content()
            return

        working_id = get_working_collection_id()
        options = []

        for c in self._collections:
            prefix = "* " if working_id is not None and c.id == working_id else ""
            options.append(Option(f"{prefix}{c.name}", id=str(c.id)))

        option_list.add_options(options)

        highlight_idx = 0

        if reselect_id is not None:
            for i, c in enumerate(self._collections):
                if c.id == reselect_id:
                    highlight_idx = i
                    break

        elif prior_highlighted is not None and 0 <= prior_highlighted < len(
            self._collections
        ):
            highlight_idx = prior_highlighted

        option_list.highlighted = highlight_idx
        self._render_list_state()

    def _render_list_state(self) -> None:
        status = self.query_one("#collections-list-status", Static)

        if self._loading_list:
            status.update("Loading…")
        elif not self._collections:
            status.update("No collections yet. Press n to save your working draft.")
        else:
            status.update("")

    async def _load_detail(self, collection_id: int) -> None:
        previous_detail = self._detail_collection
        previous_id = self._selected_collection_id
        self._loading_detail = True
        self._selected_collection_id = collection_id
        self._render_detail_content()

        try:
            coll = await load_collection_into_working(collection_id)
        except Exception:
            self._loading_detail = False
            self._selected_collection_id = previous_id
            self._detail_collection = previous_detail
            self._render_detail_content()
            root = self.app.screen

            if hasattr(root, "_notify"):
                root._notify(
                    "Collection could not be loaded. Please try again.", "warning"
                )
            else:
                self.app.notify(
                    "Collection could not be loaded. Please try again.",
                    severity="warning",
                )
            return

        self._loading_detail = False
        self._detail_collection = coll

        if coll is None:
            self._selected_collection_id = previous_id
            self._detail_collection = previous_detail
            root = self.app.screen

            if hasattr(root, "_notify"):
                root._notify("Collection not found or could not be loaded.", "warning")
            else:
                self.app.notify(
                    "Collection not found or could not be loaded.",
                    severity="warning",
                )
        else:
            root = self.app.screen

            if hasattr(root, "_refresh_screens_after_draft_change"):
                root._refresh_screens_after_draft_change()

        self._render_detail_content()

    def _build_items_table(self, coll: Collection) -> DataTable:
        table = DataTable(id="collections-detail-table")
        table.show_header = True
        table.cursor_type = "row"
        table.show_cursor = False
        table.zebra_stripes = True

        table.add_columns("Card Name", "Code", "Rarity", "Price", "Qty", "Total Price")

        for item in coll.items:
            table.add_row(
                item.card_name.split(" - ", 1)[0],
                item.card_code,
                item.card_rarity,
                item.card_price,
                str(item.card_quantity),
                "${:,.2f}".format(
                    item.card_quantity
                    * Decimal(item.card_price.replace("$", "").replace(",", "."))
                ),
            )

        return table

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

        coll = self._detail_collection
        title.update(coll.name)

        item_count = len(coll.items)
        total_qty = sum(i.card_quantity for i in coll.items)
        summary = Static(
            f"{item_count} Item(s) · {total_qty} Total · ${str(sum(i.card_quantity * Decimal(i.card_price.replace("$", "").replace(",", ".")) for i in coll.items))} USD",
            classes="muted",
        )
        content.mount(summary)

        if not coll.items:
            content.mount(Static("No items", classes="muted"))
            return

        table = self._build_items_table(coll)
        content.mount(table)

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
        if collection_id_to_reselect is not None:
            self._selected_collection_id = collection_id_to_reselect
        await self._refresh_list()

        if collection_id_to_reselect is not None:
            self._detail_collection = None
            await self._load_detail(collection_id_to_reselect)
        else:
            self._detail_collection = None
            self._selected_collection_id = None
            self._render_detail_content()

    @on(OptionList.OptionSelected)
    def _on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        try:
            collection_id = int(event.option_id)
        except (ValueError, TypeError):
            return

        self.run_worker(self._load_detail(collection_id), exclusive=True)
