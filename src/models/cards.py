from dataclasses import dataclass


@dataclass
class CardListing:
    name: str
    code: str
    price: str
    rarity: str
    condition: str
    stock: int = 0


@dataclass
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
