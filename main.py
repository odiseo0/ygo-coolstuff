import asyncio

from src.cli.console import console
from src.cli.output import display_results_table
from src.parsers.file_parser import parse_cards_file
from src.scraper.scraper import scrape_cards
from src.utils.constants import INPUT_FILE


async def main():
    console.print("[bold cyan]CoolStuffInc Yu-Gi-Oh! Card Price Scraper[/bold cyan]")
    console.print("=" * 60)

    try:
        cards = await parse_cards_file(INPUT_FILE)
    except FileNotFoundError as error:
        console.print(f"[red]Error: {error}[/red]")
        return

    if not cards:
        console.print("[yellow]No cards found in input file.[/yellow]")
        return

    console.print(f"[cyan]Found {len(cards)} unique cards to scrape[/cyan]\n")

    listings = await scrape_cards(cards)

    console.print()
    display_results_table(listings)
    console.print("\n[bold green]Done![/bold green]")


if __name__ == "__main__":
    asyncio.run(main())
