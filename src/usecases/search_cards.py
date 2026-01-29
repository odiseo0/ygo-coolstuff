from src.models.cards import CardListing
from src.services.scraper import scrape_cards


async def search_cards(query: str) -> list[CardListing]:
    normalized_query = query.strip()

    if not normalized_query:
        return []

    return await scrape_cards([normalized_query])
