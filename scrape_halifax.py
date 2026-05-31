import logging
from flipp_scraper.scraper import FlippScraper, validate_postal_code

logging.basicConfig(level=logging.DEBUG)

if __name__ == "__main__":
    postal_code = "B3M0L1"

    if not validate_postal_code(postal_code):
        logging.error(f"Invalid postal code: {postal_code}")
        exit(1)

    scraper = FlippScraper()
    flyers = scraper.get_matching_flyers(postal_code)

    logging.debug(f"Found {len(flyers)} matching flyers for postal code {postal_code}")

    if not flyers:
        logging.info("No matching flyers found.")
        exit(0)

    logging.debug("Fetching flyer items for each matching flyer:")

    

    for flyer in flyers:
        for key, value in flyer.items():
            logging.debug(f"  {key}: {value}")

