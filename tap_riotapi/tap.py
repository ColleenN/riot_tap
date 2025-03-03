"""RiotAPI tap class."""

from __future__ import annotations

from singer_sdk.exceptions import ConfigValidationError
from singer_sdk import Tap
from singer_sdk import typing as th  # JSON schema typing helpers

from tap_riotapi import streams
from tap_riotapi.client import RiotAPIStream
from tap_riotapi.rate_limiting import RateLimitState
from tap_riotapi.utils import *


class TapRiotAPI(Tap):
    """RiotAPI tap class."""

    def __init__(self, **kwargs) -> None:

        super().__init__(**kwargs)

        if not "rate_limits" in self.state.keys():
            self.state["rate_limits"] = RateLimitState()

    name = "tap-riotapi"

    config_jsonschema = th.PropertiesList(
        th.Property(
            "auth_token",
            th.StringType,
            required=True,
            secret=True,  # Flag config as protected.
            title="Auth Token",
            description="The token to authenticate against the API service",
        ),
        th.Property("following", th.ObjectType(), required=False),
    ).to_dict()

    def discover_streams(self) -> list[RiotAPIStream]:
        """Return a list of discovered streams.

        Returns:
            A list of discovered streams.
        """
        stream_types = []

        if not "following" in self.config:
            raise ConfigValidationError("No streams configured!")

        player_config, apex_league_config, reg_league_config = flatten_config(self.config["following"])

        if player_config:
            stream_types.extend(streams.TFT_PLAYER_STREAMS)

        if apex_league_config:
            stream_types.extend(streams.APEX_TIER_STREAMS)

        if reg_league_config:
            stream_types.extend(streams.NORMAL_TIER_STREAMS)

        if not stream_types:
            raise ConfigValidationError("No streams configured!")

        return [stream(tap=self) for stream in stream_types]


if __name__ == "__main__":
    TapRiotAPI.cli()
