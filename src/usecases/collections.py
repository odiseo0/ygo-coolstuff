from dataclasses import dataclass

from src.models import cards
from src.models.db_models import Collection
from src.models.db_models import CollectionItem as DbCollectionItem
from src.models.db_models import create_collection as create_collection_db
from src.models.db_models import create_collection_item as create_collection_item_db
from src.models.db_models import (
    create_many_collection_items as create_many_collection_items_db,
)
from src.models.db_models import delete_collection as delete_collection_db
from src.models.db_models import delete_collection_item as delete_collection_item_db
from src.models.db_models import (
    delete_collection_items_by_collection_id as delete_collection_items_by_collection_id_db,
)
from src.models.db_models import get_collection as get_collection_db
from src.models.db_models import get_collections as get_collections_db
from src.models.db_models import update_collection as update_collection_db
from src.models.db_models import update_collection_item as update_collection_item_db


@dataclass
class _UndoAction:
    changes: list[tuple[str, int]]
    restored_items: list[tuple[str, cards.CollectionItem]] | None = None


_WORKING_COLLECTION: dict[str, cards.CollectionItem] = {}
_UNDO_STACK: list[_UndoAction] = []
_WORKING_COLLECTION_NAME: str = "Working draft"
_WORKING_COLLECTION_ID: int | None = None


def _ensure_positive_quantity(qty: int) -> int:
    return max(qty, 0)


def cards_item_to_db_item(
    cards_item: cards.CollectionItem,
    collection_id: int,
    card_id: int | None = None,
) -> DbCollectionItem:
    return DbCollectionItem(
        collection_id=collection_id,
        card_id=card_id,
        card_name=cards_item.name,
        card_set=cards_item.set,
        card_code=cards_item.code,
        card_price=cards_item.price,
        card_rarity=cards_item.rarity,
        card_condition=cards_item.condition,
        card_quantity=cards_item.qty,
    )


def db_item_to_cards_item(db_item: DbCollectionItem) -> cards.CollectionItem:
    return cards.CollectionItem(
        name=db_item.card_name,
        set=db_item.card_set,
        code=db_item.card_code,
        qty=db_item.card_quantity,
        price=db_item.card_price,
        rarity=db_item.card_rarity,
        condition=db_item.card_condition,
        stock=0,
    )


def _make_collection_item(
    listing: cards.CardListing, qty: int = 1
) -> cards.CollectionItem:
    qty_safe = _ensure_positive_quantity(qty)
    return cards.CollectionItem(
        name=listing.name,
        set=listing.set,
        code=listing.code,
        qty=qty_safe,
        price=listing.price,
        rarity=listing.rarity,
        condition=listing.condition,
        stock=listing.stock,
    )


def add_items_from_listings(listings: list[cards.CardListing], qty: int = 1) -> None:
    items = [_make_collection_item(listing, qty) for listing in listings]
    add_items(items)


def add_items(items: list[cards.CollectionItem]) -> None:
    if not items:
        return

    changes: list[tuple[str, int]] = []

    for item in items:
        key = item.key
        existing = _WORKING_COLLECTION.get(key)
        previous_qty = existing.qty if existing is not None else 0
        changes.append((key, previous_qty))

        if existing is None:
            _WORKING_COLLECTION[key] = cards.CollectionItem(
                name=item.name,
                set=item.set,
                code=item.code,
                qty=_ensure_positive_quantity(item.qty),
                price=item.price,
                rarity=item.rarity,
                condition=item.condition,
                stock=item.stock,
            )
        else:
            existing.qty = _ensure_positive_quantity(existing.qty + item.qty)

    _UNDO_STACK.append(_UndoAction(changes=changes, restored_items=None))


def remove_items(items: list[cards.CollectionItem]) -> None:
    if not items:
        return

    changes: list[tuple[str, int]] = []

    for item in items:
        key = item.key
        existing = _WORKING_COLLECTION.get(key)
        previous_qty = existing.qty if existing is not None else 0
        changes.append((key, previous_qty))

        if existing is None:
            continue

        new_qty = _ensure_positive_quantity(existing.qty - item.qty)
        existing.qty = new_qty

    _UNDO_STACK.append(_UndoAction(changes=changes, restored_items=None))


def get_working_collection() -> list[cards.CollectionItem]:
    return sorted(
        _WORKING_COLLECTION.values(),
        key=lambda item: (item.name, item.code, item.condition),
    )


def undo_last() -> None:
    if not _UNDO_STACK:
        return

    action = _UNDO_STACK.pop()

    if action.restored_items:
        for key, item in action.restored_items:
            _WORKING_COLLECTION[key] = item

    for key, previous_qty in action.changes:
        if action.restored_items and any(k == key for k, _ in action.restored_items):
            continue

        if previous_qty <= 0:
            _WORKING_COLLECTION.pop(key, None)
            continue

        existing = _WORKING_COLLECTION.get(key)

        if existing is None:
            continue

        existing.qty = previous_qty


def is_in_collection(item_key: str) -> bool:
    item = _WORKING_COLLECTION.get(item_key)
    return bool(item is not None and item.qty > 0)


def make_collection_items_from_listings(
    listings: list[cards.CardListing],
    qty: int = 1,
) -> list[cards.CollectionItem]:
    qty_safe = _ensure_positive_quantity(qty)
    return [
        cards.CollectionItem(
            name=listing.name,
            set=listing.set,
            code=listing.code,
            qty=qty_safe,
            price=listing.price,
            rarity=listing.rarity,
            condition=listing.condition,
            stock=listing.stock,
        )
        for listing in listings
    ]


def adjust_quantity(key: str, delta: int) -> bool:
    item = _WORKING_COLLECTION.get(key)

    if item is None:
        return False

    previous_qty = item.qty
    new_qty = _ensure_positive_quantity(item.qty + delta)

    if new_qty <= 0:
        restored = cards.CollectionItem(
            name=item.name,
            set=item.set,
            code=item.code,
            qty=previous_qty,
            price=item.price,
            rarity=item.rarity,
            condition=item.condition,
            stock=item.stock,
        )
        _WORKING_COLLECTION.pop(key, None)
        _UNDO_STACK.append(
            _UndoAction(
                changes=[(key, previous_qty)],
                restored_items=[(key, restored)],
            )
        )

        return True

    item.qty = new_qty
    _UNDO_STACK.append(_UndoAction(changes=[(key, previous_qty)]))

    return True


def remove_item(key: str) -> bool:
    item = _WORKING_COLLECTION.get(key)

    if item is None:
        return False

    previous_qty = item.qty
    restored = cards.CollectionItem(
        name=item.name,
        set=item.set,
        code=item.code,
        qty=previous_qty,
        price=item.price,
        rarity=item.rarity,
        condition=item.condition,
        stock=item.stock,
    )
    _WORKING_COLLECTION.pop(key, None)
    _UNDO_STACK.append(
        _UndoAction(changes=[(key, previous_qty)], restored_items=[(key, restored)])
    )

    return True


def get_working_collection_name() -> str:
    return _WORKING_COLLECTION_NAME


def set_working_collection_name(name: str) -> None:
    global _WORKING_COLLECTION_NAME
    _WORKING_COLLECTION_NAME = name


def get_working_collection_id() -> int | None:
    return _WORKING_COLLECTION_ID


async def list_collections() -> list[Collection]:
    return await get_collections_db()


async def load_collection(collection_id: int) -> Collection | None:
    return await get_collection_db(collection_id)


async def rename_collection(collection_id: int, name: str) -> Collection | None:
    global _WORKING_COLLECTION_NAME
    coll = await get_collection_db(collection_id)

    if coll is None:
        return None

    coll.name = name
    updated = await update_collection_db(coll)

    if _WORKING_COLLECTION_ID == collection_id:
        _WORKING_COLLECTION_NAME = name

    return updated


async def save_working_collection(name: str) -> Collection | None:
    global _WORKING_COLLECTION_ID, _WORKING_COLLECTION_NAME
    items = get_working_collection()
    db_items = [
        cards_item_to_db_item(cards_item, collection_id=0) for cards_item in items
    ]

    if _WORKING_COLLECTION_ID is not None:
        await delete_collection_items_by_collection_id_db(_WORKING_COLLECTION_ID)
        if db_items:
            await create_many_collection_items_db(_WORKING_COLLECTION_ID, db_items)
        existing = await get_collection_db(_WORKING_COLLECTION_ID)
        if existing is not None and existing.name != name:
            existing.name = name
            await update_collection_db(existing)
        _WORKING_COLLECTION_NAME = name
        coll = await get_collection_db(_WORKING_COLLECTION_ID)
        return coll

    coll = await create_collection_db(name, db_items)
    _WORKING_COLLECTION_ID = coll.id
    _WORKING_COLLECTION_NAME = name

    return coll


async def load_working_collection(collection_id: int) -> bool:
    global _WORKING_COLLECTION, _WORKING_COLLECTION_ID, _WORKING_COLLECTION_NAME
    coll = await load_collection(collection_id)

    if coll is None:
        return False

    _WORKING_COLLECTION.clear()

    for db_item in coll.items:
        cards_item = db_item_to_cards_item(db_item)
        _WORKING_COLLECTION[cards_item.key] = cards_item

    _WORKING_COLLECTION_ID = coll.id
    _WORKING_COLLECTION_NAME = coll.name
    _UNDO_STACK.clear()

    return True


async def create_collection(name: str) -> Collection:
    items = get_working_collection()
    db_items = [
        cards_item_to_db_item(cards_item, collection_id=0) for cards_item in items
    ]

    return await create_collection_db(name, db_items)


async def update_collection(collection: Collection) -> Collection:
    return await update_collection_db(collection)


async def delete_collection(collection_id: int) -> None:
    return await delete_collection_db(collection_id)


async def create_collection_item(collection_item: DbCollectionItem) -> DbCollectionItem:
    return await create_collection_item_db(collection_item)


async def update_collection_item(
    collection_item: DbCollectionItem,
) -> DbCollectionItem:
    return await update_collection_item_db(collection_item)


async def delete_collection_item(collection_item_id: int) -> None:
    return await delete_collection_item_db(collection_item_id)
