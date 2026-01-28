from dataclasses import dataclass


@dataclass
class CardListing:
    name: str
    code: str
    price: str
    rarity: str
    condition: str
