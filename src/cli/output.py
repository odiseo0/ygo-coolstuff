from typing import TYPE_CHECKING

from rich.table import Table

from src.cli.console import console
from src.utils import sort_listings


if TYPE_CHECKING:
    from src.models.cards import CardListing


def display_results_table(listings: list["CardListing"]) -> None:
    if not listings:
        console.print("[yellow]No listings found to display.[/yellow]")
        return

    sorted_listings = sort_listings(listings)

    table = Table(
        title="[bold cyan]Yu-Gi-Oh! Card Prices - CoolStuffInc[/bold cyan]",
        show_header=True,
        header_style="bold magenta",
        border_style="blue",
        title_style="bold cyan",
    )

    table.add_column("Card Name", style="cyan", no_wrap=False, width=50)
    table.add_column("Code", style="green", width=15)
    table.add_column("Price", style="bold yellow", justify="right", width=12)
    table.add_column("Rarity", style="blue", width=25)
    table.add_column("Condition", style="white", width=12)

    for listing in sorted_listings:
        price_style = "bold yellow" if listing.price != "N/A" else "dim"
        table.add_row(
            listing.name,
            listing.code,
            f"[{price_style}]{listing.price}[/{price_style}]",
            listing.rarity,
            listing.condition,
        )

    console.print()
    console.print(table)
    console.print(f"\n[green]Total listings: {len(sorted_listings)}[/green]")
