"""Tests standard tap features using the built-in SDK tests library."""


from singer_sdk.testing import get_tap_test_class

from tap_riotapi.tap import TapRiotAPI

SAMPLE_CONFIG_BASE = {
    "auth_token": "",
}
PLAYER_CONFIG = {
    "followed_players": {"NA": ["SupremeKitteh#NA1"]}
}
LEAGUE_CONFIG = {
    "followed_leagues":{
        "NA": [
            {"name": "challenger"},
            {"name": "diamond"},
            {"name": "iron", "division": 4},
        ]
    }
}


# Run standard built-in tap tests from the SDK:
TestTapRiotAPI = get_tap_test_class(
    tap_class=TapRiotAPI,
    config=(SAMPLE_CONFIG_BASE | PLAYER_CONFIG),
)


# TODO: Create additional tests as appropriate for your tap.

# TODO: test for no streams configured
# TODO: test for invalid API key
