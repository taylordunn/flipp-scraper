"""Flipp flyer scraper module."""

from __future__ import annotations

import re
from typing import Optional
import logging

import pandas as pd

from flipp_scraper.api import FlippClient

# Default set of grocery store merchants to include
DEFAULT_MERCHANTS = {
    "Sobeys",
    "Walmart",
    "Atlantic Superstore",
    "Loblaws",
    "No Frills",
    "Costco",
    "Lawtons Drugs",
    "Giant Tiger",
    "FreshCo",
    "Metro",
    "Food Basics",
    "Real Canadian Superstore",
    "T&T Supermarket",
}

CANADIAN_POSTAL_CODE_RE = re.compile(
    r"^[A-Za-z]\d[A-Za-z]\d[A-Za-z]\d$", re.IGNORECASE
)
US_ZIP_CODE_RE = re.compile(r"^\d{5}(-\d{4})?$")


def validate_postal_code(postal_code: str) -> bool:
    """Return True if *postal_code* is a valid Canadian or US postal code."""
    return bool(
        CANADIAN_POSTAL_CODE_RE.match(postal_code)
        or US_ZIP_CODE_RE.match(postal_code)
    )


class FlippScraper:
    """Scrapes flyer data from Flipp for a given postal code."""

    def __init__(
        self,
        merchants: Optional[set] = None,
        category_filter: Optional[str] = "Groceries",
        client: Optional[FlippClient] = None,
    ):
        """
        Args:
            merchants: Set of merchant names to include. Defaults to
                :data:`DEFAULT_MERCHANTS`.
            category_filter: Only include flyers whose ``categories`` list
                contains this string. Pass ``None`` to disable filtering by
                category.
            client: :class:`FlippClient` instance to use. A new one is created
                if not provided.
        """
        self.merchants = merchants if merchants is not None else DEFAULT_MERCHANTS
        logging.debug(f"Initialized FlippScraper with merchants: {self.merchants}")
        self.category_filter = category_filter
        logging.debug(f"Initialized FlippScraper with category filter: {self.category_filter}")
        self.client = client or FlippClient()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _flyer_matches(self, flyer: dict) -> bool:
        """Return True if a flyer dict passes the merchant/category filters."""
        merchant = flyer.get("merchant", "")
        if merchant not in self.merchants:
            logging.debug(f"Skipping flyer ID {flyer.get('id', '?')} for merchant '{merchant}'")
            return False

        if self.category_filter is not None:
            categories = flyer.get("categories", [])
            if isinstance(categories, str):
                categories = [c.strip() for c in categories.split(",")]
            if self.category_filter not in categories:
                logging.debug(f"Skipping flyer ID {flyer.get('id', '?')} for merchant '{merchant}' due to missing category '{self.category_filter}'")
                return False

        return True

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_matching_flyers(self, postal_code: str) -> list[dict]:
        """
        Return a list of ``{"id": …, "merchant": …}`` dicts for all flyers
        that match the configured merchant/category filters.

        Args:
            postal_code: Canadian postal code or US zip code.

        Returns:
            List of matching flyer metadata dicts, or an empty list if none.
        """
        data = self.client.get_flyers(postal_code)
        flyers = data.get("flyers", [])

        return [
            {"id": f["id"], "merchant": f.get("merchant", "")}
            for f in flyers
            if self._flyer_matches(f)
        ]

    def get_flyer_items_df(self, flyer_id: int, merchant: str) -> pd.DataFrame:
        """
        Fetch all items for *flyer_id* and return them as a
        :class:`pandas.DataFrame`.

        Args:
            flyer_id: Numeric flyer identifier.
            merchant: Merchant name, added as a column in the result.

        Returns:
            DataFrame with columns: merchant, flyer_id, name, description,
            price, pre_price_text, price_text, valid_from, valid_to.
        """
        items = self.client.get_flyer_items(flyer_id)
        rows = []
        for item in items:
            rows.append(
                {
                    "merchant": merchant,
                    "flyer_id": flyer_id,
                    "name": item.get("name", ""),
                    "description": item.get("description", ""),
                    "price": item.get("price", ""),
                    "pre_price_text": item.get("pre_price_text", ""),
                    "price_text": item.get("price_text", ""),
                    "valid_from": item.get("valid_from", ""),
                    "valid_to": item.get("valid_to", ""),
                }
            )
        return pd.DataFrame(rows)

    def scrape(self, postal_code: str) -> pd.DataFrame:
        """
        Fetch all matching flyer items for *postal_code* and return them as a
        single :class:`pandas.DataFrame`.

        Args:
            postal_code: Canadian postal code (e.g. ``"M5V2H1"``) or US zip
                         code (e.g. ``"10001"``).

        Returns:
            DataFrame of all items across every matching flyer, or an empty
            DataFrame if nothing was found.

        Raises:
            ValueError: If *postal_code* does not match the expected format.
        """
        postal_code = postal_code.strip().upper()
        if not validate_postal_code(postal_code):
            raise ValueError(
                f"Invalid postal/zip code: '{postal_code}'. "
                "Expected a Canadian postal code (e.g. 'M5V2H1') "
                "or a US zip code (e.g. '10001')."
            )

        flyers = self.get_matching_flyers(postal_code)
        if not flyers:
            return pd.DataFrame()

        frames = []
        for flyer in flyers:
            df = self.get_flyer_items_df(flyer["id"], flyer["merchant"])
            if not df.empty:
                frames.append(df)

        if not frames:
            return pd.DataFrame()

        return pd.concat(frames, ignore_index=True)
