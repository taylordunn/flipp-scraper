"""Flipp API client module."""

import random
import requests

FLYERS_URL = "https://flyers-ng.flippback.com/api/flipp/data?locale=en&postal_code={}&sid={}"
FLYER_ITEMS_URL = (
    "https://flyers-ng.flippback.com/api/flipp/flyers/{}/flyer_items?locale=en&sid={}"
)


def generate_sid() -> str:
    """Generate a random 16-digit session ID for the Flipp API."""
    return "".join(str(random.randint(0, 9)) for _ in range(16))


class FlippClient:
    """Client for interacting with the Flipp API."""

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()

    def get_flyers(self, postal_code: str) -> dict:
        """
        Fetch flyer data for a given postal code.

        Args:
            postal_code: Canadian postal code (e.g. "M5V2H1") or US zip code
                         (e.g. "10001").

        Returns:
            Parsed JSON response from the Flipp API.

        Raises:
            requests.HTTPError: If the request fails.
        """
        sid = generate_sid()
        url = FLYERS_URL.format(postal_code, sid)
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def get_flyer_items(self, flyer_id: int) -> list:
        """
        Fetch all items for a given flyer ID.

        Args:
            flyer_id: Numeric flyer identifier from the Flipp API.

        Returns:
            List of flyer item dicts from the Flipp API.

        Raises:
            requests.HTTPError: If the request fails.
        """
        sid = generate_sid()
        url = FLYER_ITEMS_URL.format(flyer_id, sid)
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response.json()
