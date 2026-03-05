from src.models.cards import CardListing
from src.services.scraper import scrape_cards
from src.services.ygopro_api import fuzzy_search as ygopro_fuzzy_search
from src.utils.utils import to_slug


async def _ygopro_candidate_names(query: str) -> list[str]:
    normalized_query = query.strip()

    try:
        payload = await ygopro_fuzzy_search(normalized_query)
    except Exception:
        return []

    names: set[str] = set()

    if isinstance(payload, dict):
        data = payload.get("data")

        if isinstance(data, list):
            for entry in data:
                if not isinstance(entry, dict):
                    continue

                name = entry.get("name")

                if isinstance(name, str):
                    names.add(name)

    elif isinstance(payload, list):
        for item in payload:
            if not isinstance(item, dict):
                continue

            data = item.get("data")

            if isinstance(data, list):
                for entry in data:
                    if not isinstance(entry, dict):
                        continue

                    name = entry.get("name")

                    if isinstance(name, str):
                        names.add(name)

    return sorted(names)


async def search_cards(query: str) -> list[CardListing]:
    raw_query = query.strip()

    if not raw_query:
        return []

    candidate_names = await _ygopro_candidate_names(raw_query)

    if candidate_names:
        limited_names = candidate_names[:25]
        return await scrape_cards(limited_names)

    normalized_query = to_slug(raw_query)

    if not normalized_query:
        return []

    return await scrape_cards([normalized_query])
