"""Tests standard tap features using the built-in SDK tests library."""


from singer_sdk.testing import get_tap_test_class

from tap_riotapi.tap import TapRiotAPI

SAMPLE_CONFIG = {
    "auth_token": "RGAPI-5297fb20-35a1-4212-b631-16cca440e317"
    # TODO: Initialize minimal tap config
}


# Run standard built-in tap tests from the SDK:
TestTapRiotAPI = get_tap_test_class(
    tap_class=TapRiotAPI,
    config=SAMPLE_CONFIG,
)


# TODO: Create additional tests as appropriate for your tap.
