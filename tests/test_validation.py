"""Offline tests for player validation, with the Riot account API faked."""

import pytest
import requests

from tap_riotapi import validation


@pytest.fixture
def fake_api(monkeypatch):
    """Serve status codes by tag line; record the URLs requested."""
    responses: dict[str, int] = {}
    requested: list[str] = []

    def fake_get(url, headers):
        assert headers == {"X-Riot-Token": "token"}
        requested.append(url)
        response = requests.Response()
        response.status_code = responses[url.rsplit("/", 1)[-1]]
        response.url = url
        return response

    monkeypatch.setattr(validation.requests, "get", fake_get)
    return responses, requested


def validate(tag_line, platform="NA1"):
    return validation.validate_player("Player", tag_line, platform, "americas", "token")


def test_existing_player(fake_api):
    responses, requested = fake_api
    responses["1234"] = 200

    assert validate("1234") is True
    assert requested == [
        "https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/Player/1234"
    ]


def test_retries_with_platform_as_tag_line(fake_api):
    responses, requested = fake_api
    responses.update({"1234": 404, "NA1": 200})

    assert validate("1234") is True
    assert [url.rsplit("/", 1)[-1] for url in requested] == ["1234", "NA1"]


def test_missing_player_after_retry(fake_api):
    responses, _ = fake_api
    responses.update({"1234": 404, "NA1": 404})

    assert validate("1234") is False


def test_other_errors_raise(fake_api):
    responses, _ = fake_api
    responses["1234"] = 500

    with pytest.raises(requests.HTTPError):
        validate("1234")


def test_missing_player_whose_tag_line_is_the_platform(fake_api):
    responses, _ = fake_api
    responses["NA1"] = 404

    assert validate("NA1") is False
