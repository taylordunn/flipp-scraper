import logging
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from flipp_scraper.scraper import FlippScraper, validate_postal_code

logging.basicConfig(level=logging.DEBUG)


def get_existing_flyer_ids_from_recent_files(
    data_dir: Path, postal_code: str, days: int = 14
) -> set[str]:
    today = datetime.now().date()
    cutoff_date = today - timedelta(days=days)
    candidate_files = sorted(data_dir.glob(f"flyer-items_{postal_code}_*.csv"))

    recent_files = []
    for file_path in candidate_files:
        try:
            file_date = datetime.strptime(
                file_path.stem.rsplit("_", 1)[-1], "%Y-%m-%d"
            ).date()
        except ValueError:
            continue

        if cutoff_date <= file_date <= today:
            recent_files.append(file_path)

    if recent_files:
        recent_file_names = "\n".join(f"  - {path.name}" for path in recent_files)
        logging.info(
            f"Using {len(recent_files)} historical file(s) from the past {days} days to de-duplicate by flyer_id:\n{recent_file_names}"
        )
    else:
        logging.info(
            f"No historical files found in the past {days} days for postal code {postal_code}."
        )
        return set()

    existing_flyer_ids = set()
    for recent_file in recent_files:
        existing_df = pd.read_csv(recent_file)
        if "flyer_id" in existing_df.columns:
            file_flyer_ids = set(existing_df["flyer_id"].dropna().astype(str))
            existing_flyer_ids.update(file_flyer_ids)
            logging.info(
                f"Loaded {len(file_flyer_ids)} unique flyer_id value(s) from '{recent_file.name}'."
            )
        else:
            logging.info(
                f"Skipped '{recent_file.name}' because it has no 'flyer_id' column."
            )

    return existing_flyer_ids


if __name__ == "__main__":
    postal_code = "B3M0L1"

    if not validate_postal_code(postal_code):
        logging.error(f"Invalid postal code: {postal_code}")
        exit(1)

    date_str = datetime.now().strftime("%Y-%m-%d")
    data_dir = Path("data")
    filename = data_dir / f"flyer-items_{postal_code}_{date_str}.csv"
    if filename.exists():
        logging.info(
            f"Today's data file already exists ('{filename}'). Skipping scrape to avoid overwrite."
        )
        exit(0)

    scraper = FlippScraper()
    flyers = scraper.get_matching_flyers(postal_code)

    if not flyers:
        logging.info("No matching flyers found.")
        exit(0)

    flyer_summary = "".join(
        f"  • {flyer['merchant']} (flyer ID {flyer['id']})\n" for flyer in flyers
    )
    logging.info(f"Found {len(flyers)} matching flyer(s):\n{flyer_summary}")

    df = scraper.scrape(postal_code)
    if df.empty:
        logging.info("No flyer items found.")

    existing_flyer_ids = get_existing_flyer_ids_from_recent_files(
        data_dir=data_dir,
        postal_code=postal_code,
        days=14,
    )

    if existing_flyer_ids and "flyer_id" in df.columns:
        original_count = len(df)
        df = df[~df["flyer_id"].astype(str).isin(existing_flyer_ids)]
        removed_count = original_count - len(df)
        if removed_count > 0:
            logging.info(
                f"Removed {removed_count} row(s) (out of {original_count}) with existing flyer_id found in the past 14 days."
            )

    if len(df) > 0:
        df.dropna(subset=["price"], inplace=True)
        df.to_csv(filename, index=False)
        logging.info(f"Saved {len(df)} flyer items to '{filename}'.")
