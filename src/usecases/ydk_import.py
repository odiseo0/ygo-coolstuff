import logging
from pathlib import Path

from src.models.cards import CardListing
from src.services.scraper import scrape_cards
from src.services.ygopro_api import YGOPROCard, get_cards_by_ids, safe_get_card_by_id
from src.usecases.file_parser import parse_file, parse_ydk_file


LOG = logging.getLogger(__name__)

YGOPRO_BATCH_SIZE = 40


class ImportDeckError(Exception):
    """Raised when importing a deck file fails in a non-recoverable way."""


async def _resolve_card_names_from_ids(card_ids: list[str]) -> tuple[list[str], list[str]]:
    if not card_ids:
        return [], []

    names: list[str] = []
    failed_ids: list[str] = []

    int_ids: list[int] = []

    for card_id in card_ids:
        try:
            int_ids.append(int(card_id))
        except ValueError:
            failed_ids.append(card_id)

    for index in range(0, len(int_ids), YGOPRO_BATCH_SIZE):
        batch = int_ids[index : index + YGOPRO_BATCH_SIZE]

        try:
            batch_cards = await get_cards_by_ids(batch)
        except Exception:
            LOG.exception(
                "import_ydk_file: batch lookup failed for ids %s, falling back to single requests",
                batch,
            )
            batch_cards = []

        if not batch_cards:
            for card_id in batch:
                payload = await safe_get_card_by_id(card_id)

                if payload is None:
                    failed_ids.append(str(card_id))
                    continue

                data = payload.get("data")

                if not isinstance(data, list) or not data:
                    failed_ids.append(str(card_id))
                    continue

                card = data[0]
                name = card.get("name")

                if isinstance(name, str):
                    names.append(name)
                else:
                    failed_ids.append(str(card_id))

            continue

        by_id: dict[int, YGOPROCard] = {}

        for card in batch_cards:
            card_id = card.get("id")

            if isinstance(card_id, int):
                by_id[card_id] = card

        for card_id in batch:
            card = by_id.get(card_id)

            if card is None:
                failed_ids.append(str(card_id))
                continue

            name = card.get("name")

            if isinstance(name, str):
                names.append(name)
            else:
                failed_ids.append(str(card_id))

    return names, failed_ids


async def import_ydk_file(file_path: str) -> list[CardListing]:
    card_ids = await parse_ydk_file(file_path)

    if not card_ids:
        LOG.info("import_ydk_file: no card ids parsed from %s", file_path)
        return []

    names, failed_ids = await _resolve_card_names_from_ids(card_ids)

    if failed_ids:
        LOG.warning(
            "import_ydk_file: skipped %s id(s) while importing %s",
            len(failed_ids),
            file_path,
        )

    if not names:
        LOG.info("import_ydk_file: no resolvable card names for %s", file_path)
        return []

    listings = await scrape_cards(names)

    return listings


async def import_txt_file(file_path: str) -> list[CardListing]:
    card_names = await parse_file(file_path)

    if not card_names:
        LOG.info("import_txt_file: no card names parsed from %s", file_path)
        return []

    listings = await scrape_cards(card_names)

    return listings


async def import_deck_file(path: str) -> list[CardListing]:
    file_path = Path(path)
    suffix = file_path.suffix.lower()

    if suffix == ".ydk":
        return await import_ydk_file(path)

    if suffix == ".txt":
        return await import_txt_file(path)

    raise ImportDeckError(f"Unsupported deck file type: {suffix}")
