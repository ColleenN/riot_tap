"""RiotAPI tap class."""

from __future__ import annotations

from singer_sdk.exceptions import ConfigValidationError
from singer_sdk import Tap
from singer_sdk import typing as th  # JSON schema typing helpers

from tap_riotapi import streams
from tap_riotapi.client import RiotAPIStream
from tap_riotapi.utils import *


class TapRiotAPI(Tap):
    """RiotAPI tap class."""

    name = "tap-riotapi"

    # TODO: Update this section with the actual config values you expect:
    config_jsonschema = th.PropertiesList(
        th.Property(
            "auth_token",
            th.StringType,
            required=True,
            secret=True,  # Flag config as protected.
            title="Auth Token",
            description="The token to authenticate against the API service",
        ),
        th.Property(
            "followed_players",
            th.PropertiesList(),
            required=False,
            title="Followed Players",
            description="Players for whom we would like to sync match data",
        ),
        th.Property(
            "following",
            th.PropertiesList()
        )
    ).to_dict()

    def discover_streams(self) -> list[RiotAPIStream]:
        """Return a list of discovered streams.

        Returns:
            A list of discovered streams.
        """
        stream_list = []

        if "followed_players" in self.config:
            stream_list.extend(
                [
                    streams.TFTPlayerByNameStream(tap=self),
                    streams.TFTPlayerMatchHistoryStream(tap=self),
                    streams.TFTPlayerMatchDetailStream(tap=self)
                ]
            )
        if "followed_leagues" in self.config:
            config_items = flatten_config(self.config["followed_leagues"])
            leagues = set([x["name"] for x in config_items])
            if leagues & set(APEX_TIERS):
                stream_list.extend(
                    [
                        streams.ApexTierRankedLadderStream(tap=self)
                    ]
                )
            if leagues & set(NON_APEX_TIERS):
                stream_list.extend(
                    [
                        streams.NormalTierRankedLadderStream(tap=self)
                    ]
                )

        if not stream_list:
            raise ConfigValidationError("No streams configured!")

        return stream_list


if __name__ == "__main__":
    TapRiotAPI.cli()
