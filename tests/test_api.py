"""Tests for the Flipp API client module."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from flipp_scraper.api import FlippClient, generate_sid


# ---------------------------------------------------------------------------
# generate_sid
# ---------------------------------------------------------------------------


def test_generate_sid_length():
    sid = generate_sid()
    assert len(sid) == 16


def test_generate_sid_digits_only():
    sid = generate_sid()
    assert sid.isdigit()


def test_generate_sid_unique():
    """Two calls should (almost certainly) return different values."""
    sids = {generate_sid() for _ in range(20)}
    assert len(sids) > 1


# ---------------------------------------------------------------------------
# FlippClient.get_flyers
# ---------------------------------------------------------------------------


@patch("flipp_scraper.api.requests.Session.get")
def test_get_flyers_returns_parsed_json(mock_get):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"flyers": [{"id": 1, "merchant": "Walmart"}]}
    mock_get.return_value = mock_resp

    client = FlippClient()
    result = client.get_flyers("M5V2H1")

    assert result == {"flyers": [{"id": 1, "merchant": "Walmart"}]}
    mock_resp.raise_for_status.assert_called_once()


@patch("flipp_scraper.api.requests.Session.get")
def test_get_flyers_raises_on_http_error(mock_get):
    mock_resp = MagicMock()
    mock_resp.raise_for_status.side_effect = requests.HTTPError("404")
    mock_get.return_value = mock_resp

    client = FlippClient()
    with pytest.raises(requests.HTTPError):
        client.get_flyers("M5V2H1")


# ---------------------------------------------------------------------------
# FlippClient.get_flyer_items
# ---------------------------------------------------------------------------


@patch("flipp_scraper.api.requests.Session.get")
def test_get_flyer_items_returns_list(mock_get):
    mock_resp = MagicMock()
    mock_resp.json.return_value = [{"name": "Apples", "price": "1.99"}]
    mock_get.return_value = mock_resp

    client = FlippClient()
    items = client.get_flyer_items(42)

    assert items == [{"name": "Apples", "price": "1.99"}]
    mock_resp.raise_for_status.assert_called_once()


@patch("flipp_scraper.api.requests.Session.get")
def test_get_flyer_items_url_contains_flyer_id(mock_get):
    mock_resp = MagicMock()
    mock_resp.json.return_value = []
    mock_get.return_value = mock_resp

    client = FlippClient()
    client.get_flyer_items(99)

    call_url = mock_get.call_args[0][0]
    assert "/99/" in call_url
