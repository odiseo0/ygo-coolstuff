from dataclasses import dataclass

from src.models.db_models import Collection
from src.usecases.collections import (
    get_working_collection,
    get_working_collection_name,
    list_collections,
)


RECENT_COLLECTIONS_LIMIT = 5


@dataclass
class HomeSummary:
    recent_collections: list[Collection]
    collection_count: int
    working_name: str
    working_item_count: int
    working_total_qty: int
    db_status: str


async def get_home_summary() -> HomeSummary:
    try:
        all_collections = await list_collections()
    except Exception:
        items = get_working_collection()
        return HomeSummary(
            recent_collections=[],
            collection_count=0,
            working_name=get_working_collection_name(),
            working_item_count=len(items),
            working_total_qty=sum(item.qty for item in items),
            db_status="error",
        )

    sorted_collections = sorted(all_collections, key=lambda c: c.id, reverse=True)
    recent = sorted_collections[:RECENT_COLLECTIONS_LIMIT]
    items = get_working_collection()
    total_qty = sum(item.qty for item in items)

    return HomeSummary(
        recent_collections=recent,
        collection_count=len(all_collections),
        working_name=get_working_collection_name(),
        working_item_count=len(items),
        working_total_qty=total_qty,
        db_status="ready",
    )
