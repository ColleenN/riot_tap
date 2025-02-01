"""RiotAPI tap class."""

from __future__ import annotations

from singer_sdk import Tap
from singer_sdk import typing as th  # JSON schema typing helpers

from tap_riotapi import streams


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
            th.ArrayType(th.StringType),
            required=False,
            title="Followed Players",
            description="Players for whom we would like to sync match data",
        ),
        th.Property(
            "following",
            th.PropertiesList()
        )

    ).to_dict()

    def discover_streams(self) -> list[streams.RiotAPIStream]:
        """Return a list of discovered streams.

        Returns:
            A list of discovered streams.
        """
        return [
            streams.TFTPlayerByNameStream(tap=self),
            streams.TFTPlayerMatchHistoryStream(tap=self),
            streams.TFTPlayerMatchDetailStream(tap=self)
        ]


if __name__ == "__main__":
    TapRiotAPI.cli()
