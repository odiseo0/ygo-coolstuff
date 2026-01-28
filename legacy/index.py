import asyncio
import csv
import re
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from urllib.parse import quote

import aiofiles
from bs4 import BeautifulSoup
from httpx import AsyncClient, HTTPStatusError, RequestError


BASE_URL = "https://www.coolstuffinc.com/p/YuGiOh/"
REQUEST_TIMEOUT_SECONDS = 15
DELAY_BETWEEN_REQUESTS_SECONDS = 1.5
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

INPUT_FILE = "cards.txt"
OUTPUT_FILE = "results.csv"


@dataclass
class CardListing:
    name: str
    code: str
    price: str
    rarity: str
    condition: str


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


async def fetch_card_page(client: AsyncClient, url: str) -> str | None:
    try:
        response = await client.get(url)
        response.raise_for_status()
        return response.text
    except HTTPStatusError as error:
        if error.response.status_code == 404:
            print(f"not found {url}")
        else:
            print(f"HTTP error: {error.response.status_code}")
        return None
    except RequestError as error:
        print(f"request error: {error}")
        return None


def parse_card_listings(html: str, card_name: str) -> list[CardListing]:
    soup = BeautifulSoup(html, "html.parser")
    listings: list[CardListing] = []

    product_rows = soup.select("div.products-container div.row")

    if not product_rows:
        # try finding by the product structure
        product_rows = soup.select("div.row.product-row")

    if not product_rows:
        # try find all rows that contain pricing info
        product_rows = soup.find_all("div", class_="row")

    for row in product_rows:
        try:
            listing = extract_listing_from_row(row, card_name)
            if listing:
                listings.append(listing)
        except Exception:
            continue

    if not listings:
        listings = parse_listings_from_text(soup, card_name)

    return deduplicate_listings(listings)


def deduplicate_listings(listings: list[CardListing]) -> list[CardListing]:
    seen: set[tuple[str, str, str, str]] = set[tuple[str, str, str, str]]()
    unique: list[CardListing] = []

    for listing in listings:
        key = (listing.code, listing.condition, listing.price)
        if key not in seen:
            seen.add(key)
            unique.append(listing)

    return unique


def extract_listing_from_row(row, card_name: str) -> CardListing | None:
    row_text = row.get_text()

    if "$" not in row_text:
        return None

    # number pattern, e.g: "YS18-EN014"
    code_pattern = re.compile(r"[A-Z]{2,4}\d*-[A-Z]{2,3}\d+")
    code_match = code_pattern.search(row_text)
    if not code_match:
        return None

    code = code_match.group(0)

    rarity = "Unknown"
    rarity_match = re.search(
        r"Rarity:\s*([A-Za-z\s]+?)(?:\s*Card #|\s*\(|\s*Only|\s*In Stock|\s*Out)",
        row_text,
    )

    if rarity_match:
        rarity = rarity_match.group(1).strip()

    condition = "Unknown"
    if "Near Mint" in row_text:
        condition = "Near Mint"
    elif "Played" in row_text:
        condition = "Played"

    price = "N/A"
    price_match = re.search(r"\$\s*(\d+\.?\d*)", row_text)

    if price_match:
        price = f"${price_match.group(1)}"

    return CardListing(
        name=card_name,
        code=code,
        price=price,
        rarity=rarity,
        condition=condition,
    )


def parse_listings_from_text(soup: BeautifulSoup, card_name: str) -> list[CardListing]:
    listings: list[CardListing] = []
    full_text = soup.get_text()

    code_pattern = re.compile(r"Card #:\s*([A-Z]{2,4}\d*-[A-Z]{2,3}\d+)")

    codes = code_pattern.findall(full_text)

    for code in codes:
        code_pos = full_text.find("Card #:" + code)
        if code_pos == -1:
            code_pos = full_text.find(code)

        if code_pos == -1:
            continue

        start = max(0, code_pos - 500)
        end = min(len(full_text), code_pos + 300)
        section = full_text[start:end]

        rarity = "Unknown"
        rarity_match = re.search(r"Rarity:\s*([A-Za-z\s]+?)(?:Card #|$)", section)
        if rarity_match:
            rarity = rarity_match.group(1).strip()

        price = "N/A"
        price_match = re.search(r"\$(\d+\.?\d*)", section[section.find(code) :])
        if price_match:
            price = f"${price_match.group(1)}"

        condition = "Unknown"
        condition_section = section[section.find(code) :]
        if "Near Mint" in condition_section[:100]:
            condition = "Near Mint"
        elif "Played" in condition_section[:100]:
            condition = "Played"

        if code and price != "N/A":
            listings.append(
                CardListing(
                    name=card_name,
                    code=code,
                    price=price,
                    rarity=rarity,
                    condition=condition,
                )
            )

    return listings


async def write_results_csv(listings: list[CardListing], output_path: str) -> None:
    fieldnames = ["name", "code", "price", "rarity", "condition"]
    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()

    for listing in listings:
        writer.writerow(
            {
                "name": listing.name,
                "code": listing.code,
                "price": listing.price,
                "rarity": listing.rarity,
                "condition": listing.condition,
            }
        )

    csv_content = buffer.getvalue()
    async with aiofiles.open(output_path, "w", encoding="utf-8", newline="") as file:
        await file.write(csv_content)


async def scrape_cards(cards: list[str]) -> list[CardListing]:
    all_listings: list[CardListing] = []
    total_cards = len(cards)

    async with AsyncClient(
        headers={"User-Agent": USER_AGENT},
        timeout=REQUEST_TIMEOUT_SECONDS,
        follow_redirects=True,
    ) as client:
        tasks: list[asyncio.Task] = []
        card_names: list[str] = []

        for index, card_name in enumerate(cards, start=1):
            print(f"[{index}/{total_cards}] fetching: {card_name}")
            encoded_name = quote(card_name, safe="").replace("%20", "+")
            url = f"{BASE_URL}{encoded_name}"
            task = asyncio.create_task(fetch_card_page(client, url))
            tasks.append(task)
            card_names.append(card_name)

            # rate limit for development purposes
            if index < total_cards:
                await asyncio.sleep(DELAY_BETWEEN_REQUESTS_SECONDS)

        htmls = await asyncio.gather(*tasks)

        for card_name, html in zip(card_names, htmls):
            if html:
                listings = parse_card_listings(html, card_name)
                all_listings.extend(listings)
                print(f"found {len(listings)} listings")
            else:
                print("failed to fetch page")

    return all_listings


async def main() -> None:
    try:
        cards = await parse_cards_file(INPUT_FILE)
    except FileNotFoundError as error:
        print(f"Error: {error}")
        return

    if not cards:
        return

    listings = await scrape_cards(cards)

    print(f"\ntotal listings found: {len(listings)}")

    if listings:
        await write_results_csv(listings, OUTPUT_FILE)
        print(f"results written to: {OUTPUT_FILE}")
    else:
        print("no listings found to write")

    print("\ndone")


if __name__ == "__main__":
    asyncio.run(main())
