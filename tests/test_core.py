"""Tests standard tap features using the built-in SDK tests library."""

from singer_sdk.testing import get_tap_test_class

from tap_riotapi.tap import TapRiotAPI

PLAYER_CONFIG = {"players": ["SupremeKitteh#NA1"]}
# LEAGUE_CONFIG = {"leagues": [{"name": "challenger"}, {"name": "diamond"}, {"name": "iron", "division": 4}]}

SAMPLE_CONFIG = {
    "auth_token": "",
    "following": {"NA1": PLAYER_CONFIG},
}
# Run standard built-in tap tests from the SDK:

def build_riot_tap_test_class():

    initial = get_tap_test_class(
        tap_class=TapRiotAPI,
        config=SAMPLE_CONFIG,
    )
    to_keep_names = []
    to_keep_params = []
    for name, params in zip(initial.param_ids['test_tap_stream_returns_record'], initial.params['test_tap_stream_returns_record']) :
        if not ('_match_detail' in name or '_match_history' in name):
            to_keep_names.append(name)
            to_keep_params.append(params)
    initial.param_ids['test_tap_stream_returns_record'] = to_keep_names
    initial.params['test_tap_stream_returns_record'] = to_keep_params

    return initial

TestTapRiotAPI = build_riot_tap_test_class()


# TODO: Create additional tests as appropriate for your tap.
# TODO: test for no streams configured
# TODO: test for invalid API key
