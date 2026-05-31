import logging
from datetime import datetime
from flipp_scraper.scraper import FlippScraper, validate_postal_code

logging.basicConfig(level=logging.DEBUG)

if __name__ == "__main__":
    postal_code = "B3M0L1"

    if not validate_postal_code(postal_code):
        logging.error(f"Invalid postal code: {postal_code}")
        exit(1)

    scraper = FlippScraper()
    flyers = scraper.get_matching_flyers(postal_code)

    if not flyers:
        logging.info("No matching flyers found.")
        exit(0)

    logging.info(
        f"Found {len(flyers)} matching flyer(s): {''.join(f'  • {f['merchant']} (flyer ID {f['id']})\n' for f in flyers)}"
    )

    df = scraper.scrape(postal_code)
    if df.empty:
        logging.info("No flyer items found.")

    filename = f"data/flyer-items_{postal_code}_{datetime.now().strftime("%Y-%m-%d")}.csv"
    df.dropna(subset=["price"], inplace=True)  # Remove items missing name or price
    df.to_csv(filename, index=False)
    logging.info(f"Saved {len(df)} flyer items to '{filename}'.")
