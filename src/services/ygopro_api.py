from typing import TypedDict

from httpx import AsyncClient

from src.utils import to_slug


# docs: https://ygoprodeck.com/api-guide/
YGO_API_URL = "https://db.ygoprodeck.com/api/v7/cardinfo.php"


class YGOPROCardImage(TypedDict):
    id: int
    image_url: str
    image_url_small: str
    image_url_cropped: str


class YGOPROCard(TypedDict):
    id: int
    name: str
    type: str
    frameType: str
    card_images: list[dict]


class YGROPROResponse(TypedDict):
    data: list[YGOPROCard]
    error: str | None = None


async def fuzzy_search(query: str) -> list[YGROPROResponse]:
    async with AsyncClient() as client:
        response = await client.get(f"{YGO_API_URL}?fname=" + to_slug(query))

    return response.json()


async def get_card_by_id(id: int) -> YGOPROCard:
    async with AsyncClient() as client:
        response = await client.get(f"{YGO_API_URL}?id={id}")

    return response.json()
