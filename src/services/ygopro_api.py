from collections.abc import Mapping, Sequence
from typing import TypedDict
from urllib.parse import quote_plus

from httpx import AsyncClient, HTTPStatusError, RequestError

from src.utils.constants import YGO_API_URL


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
        response = await client.get(f"{YGO_API_URL}?fname=" + query.strip())

    return response.json()


async def get_card_by_id(id: int) -> YGROPROResponse:
    async with AsyncClient() as client:
        response = await client.get(f"{YGO_API_URL}?id={id}")

    return response.json()


async def safe_get_card_by_id(id: int) -> YGROPROResponse | None:
    try:
        return await get_card_by_id(id)
    except Exception:
        return None


async def get_cards_by_ids(ids: list[int]) -> list[YGOPROCard]:
    if not ids:
        return []

    joined_ids = ",".join(str(id) for id in ids)

    try:
        async with AsyncClient() as client:
            response = await client.get(f"{YGO_API_URL}?id={joined_ids}")
            response.raise_for_status()
    except (HTTPStatusError, RequestError) as _:
        return []

    try:
        payload = response.json()
    except Exception:
        return []

    data = payload.get("data")

    if not isinstance(data, list):
        return []

    cards: list[YGOPROCard] = []

    for entry in data:
        if isinstance(entry, dict):
            cards.append(entry)

    return cards


async def get_card_image_url_by_name(name: str) -> str | None:
    query = name.strip()

    if not query:
        return None

    encoded_name = quote_plus(query)

    try:
        async with AsyncClient() as client:
            response = await client.get(f"{YGO_API_URL}?name={encoded_name}")
            response.raise_for_status()
    except (HTTPStatusError, RequestError):
        return None

    try:
        payload = response.json()
    except Exception:
        return None

    if not isinstance(payload, Mapping):
        return None

    data = payload.get("data")

    if not isinstance(data, Sequence) or not data:
        return None

    first_entry = data[0]

    if not isinstance(first_entry, Mapping):
        return None

    card_images = first_entry.get("card_images")

    if not isinstance(card_images, Sequence) or not card_images:
        return None

    first_image = card_images[1]

    if not isinstance(first_image, Mapping):
        return None

    image_url = first_image.get("image_url")

    if not isinstance(image_url, str):
        return None

    cleaned_url = image_url.strip()

    if not cleaned_url:
        return None

    return cleaned_url
