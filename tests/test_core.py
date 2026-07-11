"""Tests standard tap features using the built-in SDK tests library."""

from singer_sdk.testing import get_tap_test_class

from tap_riotapi.tap import TapRiotAPI

PLAYER_CONFIG = {"players": ["SupremeKitteh#NA1"]}
"""
LEAGUE_CONFIG = {
    "leagues": [
        {"name": "challenger"}, 
        {"name": "diamond"}, 
        {"name": "iron", "division": 4}
    ]
}
"""
LEAGUE_CONFIG = {"leagues": [{"name": "diamond"}]}
SAMPLE_CONFIG = {
    "auth_token": "RGAPI-2baded1e-080b-4b19-af3c-73c5ae752d45",
    "following": {"NA1": LEAGUE_CONFIG},
    "start_date": "2025-08-01",
    "end_date": "2025-08-01",
}

SAMPLE_STATE = {
    "match_detail_set":
    ['NA1_5307758950', 'NA1_5307789920', 'NA1_5307809609', 'NA1_5307828117',
        'NA1_5308315615',
    ]
}
SAMPLE_STATE_NO_MATCHES = {}

def build_riot_tap_test_class():

    initial = get_tap_test_class(
        tap_class=TapRiotAPI,
        config=SAMPLE_CONFIG,
        state=SAMPLE_STATE_NO_MATCHES
    )
    to_keep_names = []
    to_keep_params = []
    for name, params in zip(
        initial.param_ids["test_tap_stream_returns_record"],
        initial.params["test_tap_stream_returns_record"],
    ):
        if not ("_match_detail" in name or "_match_history" in name):
            to_keep_names.append(name)
            to_keep_params.append(params)
    initial.param_ids["test_tap_stream_returns_record"] = to_keep_names
    initial.params["test_tap_stream_returns_record"] = to_keep_params

    return initial

TestTapRiotAPI = build_riot_tap_test_class()

# TODO: Create additional tests as appropriate for your tap.
# TODO: test for no streams configured
# TODO: test for invalid API key
