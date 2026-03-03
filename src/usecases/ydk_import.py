import asyncio

from src.services.scraper import scrape_cards
from src.services.ygopro_api import get_card_by_id
from src.usecases.file_parser import parse_file, parse_ydk_file


async def import_ydk_file(file_path: str) -> list[str]:
    card_ids = await parse_ydk_file(file_path)
    cards = await asyncio.gather(*[get_card_by_id(card) for card in card_ids])

    return await scrape_cards([card["name"] for card in cards])


async def import_txt_file(file_path: str) -> list[str]:
    card_names = await parse_file(file_path)
    return await scrape_cards(card_names)
