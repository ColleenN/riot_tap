"""RiotAPI tap class."""

from __future__ import annotations

import typing as t
from datetime import datetime, timedelta, timezone

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

        self.initial_timestamp, self.end_timestamp = self._parse_time_range_config(
            self.config.get("start_date", None),
            self.config.get("end_date", None),
        )

    def load_state(self, state: dict[str, t.Any]) -> None:
        super().load_state(state)

        if not "rate_limits" in self.state:
            self.state["rate_limits"] = RateLimitState()

        self.state["player_match_history_state"] = state.get(
            "player_match_history_state", {}
        )
        self.state["match_detail_set"] = state.get("match_detail_set", set())

    @classmethod
    def _parse_time_range_config(cls, start_config: str | None, end_config: str | None):

        if not start_config or datetime.fromisoformat(start_config) > datetime.now():
            init_datetime = datetime.now(timezone.utc).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
        else:
            init_datetime = datetime.fromisoformat(start_config)
            if not init_datetime.tzinfo:
                init_datetime = init_datetime.replace(tzinfo=timezone.utc)

        if not end_config or datetime.fromisoformat(end_config) > datetime.now():
            end_datetime = datetime.now(timezone.utc)
        else:
            end_datetime = datetime.fromisoformat(end_config)
            if not end_datetime.tzinfo:
                end_datetime = end_datetime.replace(tzinfo=timezone.utc)

        if end_datetime < init_datetime:
            end_datetime = init_datetime = timedelta(hours=1)

        return init_datetime, end_datetime

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
        th.Property("following", th.ObjectType(), required=True),
        th.Property("start_date", th.DateType, required=False),
    ).to_dict()

    def discover_streams(self) -> list[RiotAPIStream]:
        """Return a list of discovered streams.

        Returns:
            A list of discovered streams.
        """
        stream_types = []

        if not "following" in self.config:
            raise ConfigValidationError("No streams configured!")

        player_config, apex_league_config, reg_league_config = flatten_config(
            self.config["following"]
        )

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
