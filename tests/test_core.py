"""Tests standard tap features using the built-in SDK tests library."""

from singer_sdk.testing import get_tap_test_class

from tap_riotapi.tap import TapRiotAPI

SAMPLE_CONFIG_BASE = {
    "auth_token": "RGAPI-704a63d0-704c-4ea0-bd65-092df415bda9",
}
PLAYER_CONFIG = {"followed_players": {"NA1": ["SupremeKitteh#NA1"]}}
LEAGUE_CONFIG = {
    "followed_leagues": {
        "NA1": [
            {"name": "challenger"},
            # {"name": "diamond"},
            # {"name": "iron", "division": 4},
        ]
    }
}


# Run standard built-in tap tests from the SDK:
TestTapRiotAPI = get_tap_test_class(
    tap_class=TapRiotAPI,
    config=(SAMPLE_CONFIG_BASE | PLAYER_CONFIG),
)


# get_tap_test_class(
#    tap_class=TapRiotAPI,
#    config=(SAMPLE_CONFIG_BASE | LEAGUE_CONFIG),
# )


# TODO: Create additional tests as appropriate for your tap.

# TODO: test for no streams configured
# TODO: test for invalid API key
