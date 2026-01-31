from dataclasses import dataclass


@dataclass(init=False)
class CardListing:
    name: str
    code: str
    price: str
    rarity: str
    condition: str
    stock: int = 0


@dataclass(init=False)
class CollectionItem:
    name: str
    code: str
    qty: int
    price: str
    rarity: str
    condition: str
    stock: int

    @property
    def key(self) -> str:
        return f"{self.code}:{self.condition}"
