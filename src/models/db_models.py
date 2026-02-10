from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from pathlib import Path

from aiosqlite import connect
from aiosqlite.core import Connection

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_DB_PATH = _PROJECT_ROOT / "db" / "card_database.db"


@dataclass
class CollectionItem:
    id: int | None = None
    collection_id: int = 0
    card_id: int | None = None  # yugioh card id
    card_name: str = ""
    card_set: str = ""
    card_code: str = ""
    card_price: str = ""
    card_rarity: str = ""
    card_condition: str = ""
    card_quantity: int = 0


@dataclass(init=False)
class Collection:
    id: int
    name: str
    items: list[CollectionItem] = field(default_factory=list)


@asynccontextmanager
async def session() -> AsyncIterator[Connection]:
    async with connect(str(_DB_PATH)) as db:
        yield db


async def get_collection(collection_id: int) -> Collection | None:
    async with session() as db:
        async with db.execute(
            "SELECT * FROM collections WHERE id = ?", (collection_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None

            collection = Collection(id=row[0], name=row[1])
            collection.items = await get_collection_items(collection_id)
            return collection


async def get_collections() -> list[Collection]:
    async with session() as db:
        async with db.execute("SELECT * FROM collections") as cursor:
            rows = await cursor.fetchall()
            return [Collection(id=row[0], name=row[1]) for row in rows]


async def get_collection_items(collection_id: int) -> list[CollectionItem]:
    async with session() as db:
        async with db.execute(
            "SELECT * FROM collection_items WHERE collection_id = ?", (collection_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [
                CollectionItem(
                    id=row[0],
                    collection_id=row[1],
                    card_id=row[2],
                    card_name=row[3],
                    card_set=row[4],
                    card_code=row[5],
                    card_price=row[6],
                    card_rarity=row[7],
                    card_condition=row[8],
                    card_quantity=row[9],
                )
                for row in rows
            ]


async def create_collection_item(collection_item: CollectionItem) -> CollectionItem:
    async with session() as db:
        await db.execute(
            "INSERT INTO collection_items (collection_id, card_id, card_name, card_set, card_code, card_price, card_rarity, card_condition, quantity) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                collection_item.collection_id,
                collection_item.card_id,
                collection_item.card_name,
                collection_item.card_set,
                collection_item.card_code,
                collection_item.card_price,
                collection_item.card_rarity,
                collection_item.card_condition,
                collection_item.card_quantity,
            ),
        )
        await db.commit()

        async with db.execute("SELECT last_insert_rowid()") as cursor:
            last_id = await cursor.fetchone()

        return CollectionItem(
            id=last_id[0],
            collection_id=collection_item.collection_id,
            card_id=collection_item.card_id,
            card_name=collection_item.card_name,
            card_set=collection_item.card_set,
            card_code=collection_item.card_code,
            card_price=collection_item.card_price,
            card_rarity=collection_item.card_rarity,
            card_condition=collection_item.card_condition,
            card_quantity=collection_item.card_quantity,
        )


async def update_collection_item(collection_item: CollectionItem) -> CollectionItem:
    async with session() as db:
        await db.execute(
            "UPDATE collection_items SET quantity = ? WHERE id = ?",
            (collection_item.card_quantity, collection_item.id),
        )
        await db.commit()
        return collection_item


async def delete_collection_item(collection_item_id: int) -> None:
    async with session() as db:
        await db.execute(
            "DELETE FROM collection_items WHERE id = ?", (collection_item_id,)
        )
        await db.commit()


async def delete_collection_items_by_collection_id(collection_id: int) -> None:
    async with session() as db:
        await db.execute(
            "DELETE FROM collection_items WHERE collection_id = ?", (collection_id,)
        )
        await db.commit()


async def create_many_collection_items(
    collection_id: int, items: list[CollectionItem]
) -> list[CollectionItem]:
    async with session() as db:
        cursor = await db.execute("SELECT MAX(id) FROM collection_items")
        old_max_id = await cursor.fetchone()
        await db.executemany(
            "INSERT INTO collection_items (collection_id, card_id, card_name, card_set, card_code, card_price, card_rarity, card_condition, quantity) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    collection_id,
                    item.card_id,
                    item.card_name,
                    item.card_set,
                    item.card_code,
                    item.card_price,
                    item.card_rarity,
                    item.card_condition,
                    item.card_quantity,
                )
                for item in items
            ],
        )
        await db.commit()
        async with db.execute(
            "SELECT * FROM collection_items WHERE id > ?", (old_max_id[0],)
        ) as cursor:
            rows = await cursor.fetchall()

        return [
            CollectionItem(
                id=row[0],
                collection_id=row[1],
                card_id=row[2],
                card_name=row[3],
                card_set=row[4],
                card_code=row[5],
                card_price=row[6],
                card_rarity=row[7],
                card_condition=row[8],
                card_quantity=row[9],
            )
            for row in rows
        ]


async def create_collection(name: str, items: list[CollectionItem]) -> Collection:
    new_items = []

    async with session() as db:
        await db.execute("INSERT INTO collections (name) VALUES (?)", (name,))
        await db.commit()

        async with db.execute("SELECT last_insert_rowid()") as cursor:
            last_id = await cursor.fetchone()

        if items:
            new_items = await create_many_collection_items(last_id[0], items)

        return Collection(id=last_id[0], name=name, items=new_items)


async def update_collection(collection: Collection) -> Collection:
    async with session() as db:
        await db.execute(
            "UPDATE collections SET name = ? WHERE id = ?",
            (collection.name, collection.id),
        )
        await db.commit()

        return Collection(id=collection.id, name=collection.name)


async def delete_collection(collection_id: int) -> None:
    async with session() as db:
        await db.execute("DELETE FROM collections WHERE id = ?", (collection_id,))
        await db.commit()
