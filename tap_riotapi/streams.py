"""Stream type classes for tap-riotapi."""

from __future__ import annotations

from typing import Any

from singer_sdk import typing as th  # JSON Schema typing helpers

from tap_riotapi.client import RiotAPIStream



class RankedLadderStream(RiotAPIStream):

    name = "ranked_ladder"
    path = ""
    schema = th.PropertiesList(
        th.Property(
            "summonerId",
            th.StringType,
            required=True,
            title="Summoner ID",
            description="Unique identifier for league player account"
        ),
        th.Property(
            "leaguePoints",
            th.NumberType,
            required=True,
            title="League Points",
            description="Current LP score for player"
        ),
    ).to_dict()
    # Take ranked tier & division as config args? Accept list & stand-alone

    def get_url_params(
        self, *args, **kwargs
    ) -> dict[str, Any]:
        params = super().get_url_params(*args, **kwargs)
        params.update({"queue": "RANKED_TFT"})
        return params

    @property
    def url_base(self) -> str:
        """Return the API URL root, configurable via tap settings."""
        # TODO: hardcode a value here, or retrieve it from self.config
        suffix = "challenger"
        return f"https://na1.api.riotgames.com/tft/league/v1/{suffix}"

    @property
    def records_jsonpath(self):

        return "$.entries[*]"
