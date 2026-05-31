#!/usr/bin/env python3
"""Command-line entry point for flipp-scraper."""

import sys

from flipp_scraper.scraper import FlippScraper, validate_postal_code


def prompt_postal_code() -> str:
    """Interactively prompt the user for a valid postal/zip code."""
    while True:
        code = input(
            "Enter your postal/zip code "
            "(Canadian: A1A1A1 or US: 10001): "
        ).strip()
        if validate_postal_code(code):
            return code.upper()
        print(
            "Invalid format. "
            "Please enter a Canadian postal code (e.g. M5V2H1) "
            "or a US zip code (e.g. 10001)."
        )


def main() -> None:
    """Run the Flipp scraper interactively."""
    postal_code = prompt_postal_code()
    print(f"\nFetching flyers for: {postal_code}")

    scraper = FlippScraper()

    print("Looking up matching flyers…")
    flyers = scraper.get_matching_flyers(postal_code)

    if not flyers:
        print("No matching flyers found for this postal/zip code.")
        sys.exit(0)

    print(f"Found {len(flyers)} matching flyer(s):")
    for f in flyers:
        print(f"  • {f['merchant']} (flyer ID {f['id']})")

    print("\nFetching flyer items…")
    df = scraper.scrape(postal_code)

    if df.empty:
        print("No items found.")
        sys.exit(0)

    filename = f"flyer_items_{postal_code}.csv"
    df.to_csv(filename, index=False)
    print(f"\nSaved {len(df)} item(s) to '{filename}'.")


if __name__ == "__main__":
    main()
