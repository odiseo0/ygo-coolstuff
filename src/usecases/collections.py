from dataclasses import dataclass

from src.models.cards import CardListing, CollectionItem


@dataclass
class _UndoAction:
    changes: list[tuple[str, int]]


_WORKING_COLLECTION: dict[str, CollectionItem] = {}
_UNDO_STACK: list[_UndoAction] = []


def _ensure_positive_quantity(qty: int) -> int:
    return max(qty, 0)


def _make_collection_item(listing: CardListing, qty: int = 1) -> CollectionItem:
    qty_safe = _ensure_positive_quantity(qty)
    return CollectionItem(
        name=listing.name,
        code=listing.code,
        qty=qty_safe,
        price=listing.price,
        rarity=listing.rarity,
        condition=listing.condition,
        stock=listing.stock,
    )


def add_items_from_listings(listings: list[CardListing], qty: int = 1) -> None:
    items = [_make_collection_item(listing, qty) for listing in listings]
    add_items(items)


def add_items(items: list[CollectionItem]) -> None:
    if not items:
        return

    changes: list[tuple[str, int]] = []

    for item in items:
        key = item.key
        existing = _WORKING_COLLECTION.get(key)
        previous_qty = existing.qty if existing is not None else 0
        changes.append((key, previous_qty))

        if existing is None:
            _WORKING_COLLECTION[key] = CollectionItem(
                name=item.name,
                code=item.code,
                qty=_ensure_positive_quantity(item.qty),
                price=item.price,
                rarity=item.rarity,
                condition=item.condition,
                stock=item.stock,
            )
        else:
            existing.qty = _ensure_positive_quantity(existing.qty + item.qty)

    _UNDO_STACK.append(_UndoAction(changes=changes))


def remove_items(items: list[CollectionItem]) -> None:
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

    _UNDO_STACK.append(_UndoAction(changes=changes))


def get_working_collection() -> list[CollectionItem]:
    return sorted(
        _WORKING_COLLECTION.values(),
        key=lambda item: (item.name, item.code, item.condition),
    )


def undo_last() -> None:
    if not _UNDO_STACK:
        return

    action = _UNDO_STACK.pop()

    for key, previous_qty in action.changes:
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
    listings: list[CardListing],
    qty: int = 1,
) -> list[CollectionItem]:
    qty_safe = _ensure_positive_quantity(qty)
    return [
        CollectionItem(
            name=listing.name,
            code=listing.code,
            qty=qty_safe,
            price=listing.price,
            rarity=listing.rarity,
            condition=listing.condition,
            stock=listing.stock,
        )
        for listing in listings
    ]
