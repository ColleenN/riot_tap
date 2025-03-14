"""RiotAPI tap class."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

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

        self.initial_timestamp, self.end_timestamp = self._parse_time_range_config(
            kwargs["config"].get("start_date", None),
            kwargs["config"].get("end_date", None),
        )

    @classmethod
    def _parse_time_range_config(cls, start_config: str, end_config: str):
        if start_config:
            init_date = datetime.strptime(start_config, "%Y-%m-%d")
        else:
            init_date = date.today() - timedelta(days=1)

        if init_date > date.today():
            init_date = date.today()

        initial_timestamp = datetime(
            init_date.year, init_date.month, init_date.day, 0, 0, 0, tzinfo=timezone.utc
        )

        if end_config:
            end_date = datetime.strptime(end_config, "%Y-%m-%d")
        else:
            end_date = date.today()

        if end_date < init_date:
            end_date = init_date

        if end_date >= date.today():
            end_timestamp = datetime.now(tz=timezone.utc)
        else:
            base = datetime(
                end_date.year,
                end_date.month,
                end_date.day + 1,
                0,
                0,
                0,
                tzinfo=timezone.utc,
            )
            end_timestamp = base - timedelta(microseconds=1)

        return initial_timestamp, end_timestamp

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
