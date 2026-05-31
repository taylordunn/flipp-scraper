"""Tests for the FlippScraper and validation helpers."""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from flipp_scraper.scraper import (
    DEFAULT_MERCHANTS,
    FlippScraper,
    validate_postal_code,
)


# ---------------------------------------------------------------------------
# validate_postal_code
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "code",
    [
        "M5V2H1",
        "m5v2h1",
        "A1A1A1",
        "V6B4A2",
        "10001",
        "90210",
        "10001-1234",
    ],
)
def test_validate_postal_code_valid(code):
    assert validate_postal_code(code) is True


@pytest.mark.parametrize(
    "code",
    [
        "",
        "12345-",
        "ABCDEF",
        "1234",
        "123456",
        "M5V 2H1",  # space not allowed
        "not-a-code",
    ],
)
def test_validate_postal_code_invalid(code):
    assert validate_postal_code(code) is False


# ---------------------------------------------------------------------------
# FlippScraper._flyer_matches
# ---------------------------------------------------------------------------


def _scraper():
    """Return a FlippScraper with a mocked client."""
    return FlippScraper(client=MagicMock())


def test_flyer_matches_known_merchant_and_category():
    scraper = _scraper()
    flyer = {"merchant": "Walmart", "categories": ["Groceries", "Electronics"]}
    assert scraper._flyer_matches(flyer) is True


def test_flyer_matches_unknown_merchant():
    scraper = _scraper()
    flyer = {"merchant": "Best Buy", "categories": ["Groceries"]}
    assert scraper._flyer_matches(flyer) is False


def test_flyer_matches_wrong_category():
    scraper = _scraper()
    flyer = {"merchant": "Walmart", "categories": ["Electronics"]}
    assert scraper._flyer_matches(flyer) is False


def test_flyer_matches_category_as_string():
    scraper = _scraper()
    flyer = {"merchant": "No Frills", "categories": "Groceries, Pharmacy"}
    assert scraper._flyer_matches(flyer) is True


def test_flyer_matches_no_category_filter():
    scraper = FlippScraper(category_filter=None, client=MagicMock())
    flyer = {"merchant": "Walmart", "categories": []}
    assert scraper._flyer_matches(flyer) is True


# ---------------------------------------------------------------------------
# FlippScraper.get_matching_flyers
# ---------------------------------------------------------------------------


def test_get_matching_flyers_returns_filtered_list():
    mock_client = MagicMock()
    mock_client.get_flyers.return_value = {
        "flyers": [
            {"id": 1, "merchant": "Walmart", "categories": ["Groceries"]},
            {"id": 2, "merchant": "Best Buy", "categories": ["Electronics"]},
            {"id": 3, "merchant": "No Frills", "categories": ["Groceries"]},
        ]
    }
    scraper = FlippScraper(client=mock_client)
    result = scraper.get_matching_flyers("M5V2H1")

    merchants = [r["merchant"] for r in result]
    assert "Walmart" in merchants
    assert "No Frills" in merchants
    assert "Best Buy" not in merchants


def test_get_matching_flyers_empty_response():
    mock_client = MagicMock()
    mock_client.get_flyers.return_value = {}
    scraper = FlippScraper(client=mock_client)
    assert scraper.get_matching_flyers("M5V2H1") == []


# ---------------------------------------------------------------------------
# FlippScraper.get_flyer_items_df
# ---------------------------------------------------------------------------


def test_get_flyer_items_df_columns():
    mock_client = MagicMock()
    mock_client.get_flyer_items.return_value = [
        {
            "name": "Apples",
            "description": "Gala apples",
            "price": "1.99",
            "pre_price_text": "",
            "price_text": "$1.99 /kg",
            "valid_from": "2024-01-01",
            "valid_to": "2024-01-07",
        }
    ]
    scraper = FlippScraper(client=mock_client)
    df = scraper.get_flyer_items_df(42, "Walmart")

    assert list(df.columns) == [
        "merchant",
        "flyer_id",
        "name",
        "description",
        "price",
        "pre_price_text",
        "price_text",
        "valid_from",
        "valid_to",
    ]
    assert df.iloc[0]["merchant"] == "Walmart"
    assert df.iloc[0]["flyer_id"] == 42
    assert df.iloc[0]["name"] == "Apples"


def test_get_flyer_items_df_empty_items():
    mock_client = MagicMock()
    mock_client.get_flyer_items.return_value = []
    scraper = FlippScraper(client=mock_client)
    df = scraper.get_flyer_items_df(42, "Walmart")
    assert df.empty


# ---------------------------------------------------------------------------
# FlippScraper.scrape
# ---------------------------------------------------------------------------


def test_scrape_invalid_postal_code_raises():
    scraper = FlippScraper(client=MagicMock())
    with pytest.raises(ValueError, match="Invalid postal/zip code"):
        scraper.scrape("INVALID")


def test_scrape_returns_combined_dataframe():
    mock_client = MagicMock()
    mock_client.get_flyers.return_value = {
        "flyers": [
            {"id": 1, "merchant": "Walmart", "categories": ["Groceries"]},
            {"id": 2, "merchant": "No Frills", "categories": ["Groceries"]},
        ]
    }
    mock_client.get_flyer_items.side_effect = [
        [{"name": "Milk", "price": "3.99", "description": "", "pre_price_text": "",
          "price_text": "", "valid_from": "", "valid_to": ""}],
        [{"name": "Bread", "price": "2.49", "description": "", "pre_price_text": "",
          "price_text": "", "valid_from": "", "valid_to": ""}],
    ]
    scraper = FlippScraper(client=mock_client)
    df = scraper.scrape("M5V2H1")

    assert len(df) == 2
    assert set(df["merchant"]) == {"Walmart", "No Frills"}


def test_scrape_no_matching_flyers_returns_empty_df():
    mock_client = MagicMock()
    mock_client.get_flyers.return_value = {"flyers": []}
    scraper = FlippScraper(client=mock_client)
    df = scraper.scrape("M5V2H1")
    assert isinstance(df, pd.DataFrame)
    assert df.empty
