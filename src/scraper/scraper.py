import asyncio
import re
from urllib.parse import quote

from bs4 import BeautifulSoup
from httpx import AsyncClient, HTTPStatusError, RequestError
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
)

from src.cli.console import console
from src.models.cards import CardListing
from src.utils.constants import BASE_URL, REQUEST_TIMEOUT_SECONDS, USER_AGENT
from src.utils.utils import deduplicate_listings


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

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task_id = progress.add_task("[cyan]Fetching cards...", total=total_cards)

            for _, card_name in enumerate(cards, start=1):
                encoded_name = quote(card_name, safe="").replace("%20", "+")
                url = f"{BASE_URL}{encoded_name}"
                task = asyncio.create_task(fetch_card_page(client, url))
                tasks.append(task)
                card_names.append(card_name)

            htmls = await asyncio.gather(*tasks)

            for card_name, html in zip(card_names, htmls):
                if html:
                    listings = parse_card_listings(html, card_name)
                    all_listings.extend(listings)
                    progress.update(
                        task_id,
                        description=f"[green]Found {len(listings)} listings for {card_name}",
                        advance=1,
                    )
                else:
                    progress.update(
                        task_id,
                        description=f"[red]Failed to fetch {card_name}",
                        advance=1,
                    )

    return all_listings


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


def extract_listing_from_row(row, card_name: str) -> CardListing | None:
    row_text = row.get_text()

    if "$" not in row_text:
        return None

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


def parse_card_listings(html: str, card_name: str) -> list[CardListing]:
    soup = BeautifulSoup(html, "html.parser")
    listings: list[CardListing] = []

    product_rows = soup.select("div.products-container div.row")

    if not product_rows:
        product_rows = soup.select("div.row.product-row")

    if not product_rows:
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


async def fetch_card_page(client: AsyncClient, url: str) -> str | None:
    try:
        response = await client.get(url)
        response.raise_for_status()
        return response.text
    except HTTPStatusError as error:
        if error.response.status_code == 404:
            return None
        return None
    except RequestError:
        return None
