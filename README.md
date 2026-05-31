# flipp-scraper

A Python web-scraping library for pulling deal data from [Flipp](https://flipp.com) flyers.

## Features

- Fetches current flyers from the Flipp API by Canadian postal code or US zip code
- Filters flyers by merchant name and category (e.g. "Groceries")
- Returns results as a [pandas](https://pandas.pydata.org/) `DataFrame` for easy analysis
- Saves results to CSV

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Command-line

```bash
python app.py
```

You will be prompted to enter a postal/zip code, and the results will be saved to `flyer_items_<postal_code>.csv`.

### Library

```python
from flipp_scraper import FlippScraper

scraper = FlippScraper()

# Fetch all matching grocery flyers and their items
df = scraper.scrape("M5V2H1")
print(df.head())
df.to_csv("flyer_items.csv", index=False)
```

#### Custom merchants / category filter

```python
from flipp_scraper import FlippScraper

scraper = FlippScraper(
    merchants={"Walmart", "No Frills"},
    category_filter="Groceries",  # pass None to disable
)
df = scraper.scrape("M5V2H1")
```

### Columns in the output DataFrame

| Column | Description |
|---|---|
| `merchant` | Store name |
| `flyer_id` | Flipp flyer ID |
| `name` | Item name |
| `description` | Item description |
| `price` | Numeric price (if available) |
| `pre_price_text` | Text preceding the price (e.g. "2 for") |
| `price_text` | Full formatted price string |
| `valid_from` | Flyer start date |
| `valid_to` | Flyer end date |

## Running tests

```bash
pip install pytest
pytest tests/
```

## Project structure

```
flipp-scraper/
├── app.py                  # CLI entry point
├── requirements.txt
├── flipp_scraper/
│   ├── __init__.py
│   ├── api.py              # Low-level Flipp API client
│   └── scraper.py          # High-level scraping logic
└── tests/
    ├── test_api.py
    └── test_scraper.py
```
