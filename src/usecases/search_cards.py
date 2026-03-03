from src.models.cards import CardListing
from src.services.scraper import scrape_cards
from src.utils.utils import to_slug


async def search_cards(query: str) -> list[CardListing]:
    normalized_query = to_slug(query)

    if not normalized_query:
        return []

    return await scrape_cards([normalized_query])
