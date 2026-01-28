import re
from pathlib import Path

import aiofiles


async def parse_cards_file(file_path: str) -> list[str]:
    card_pattern = re.compile(r"^\d+x\s+(.+)$")
    cards: list[str] = []
    seen: set[str] = set[str]()

    file = Path(file_path)
    if not file.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")

    async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
        async for line in f:
            line = line.strip()
            if not line or line.endswith(":"):
                continue

            match = card_pattern.match(line)
            if match:
                card_name = match.group(1).strip()
                if card_name not in seen:
                    cards.append(card_name)
                    seen.add(card_name)

    return cards
