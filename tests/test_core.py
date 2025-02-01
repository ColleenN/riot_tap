"""Tests standard tap features using the built-in SDK tests library."""


from singer_sdk.testing import get_tap_test_class

from tap_riotapi.tap import TapRiotAPI

SAMPLE_CONFIG = {
    "auth_token": "RGAPI-4c29620e-ddbe-4f84-9eb9-06413947a961",
    "followed_players": ["SupremeKitteh#NA1"],
}


# Run standard built-in tap tests from the SDK:
TestTapRiotAPI = get_tap_test_class(
    tap_class=TapRiotAPI,
    config=SAMPLE_CONFIG,
)


# TODO: Create additional tests as appropriate for your tap.
