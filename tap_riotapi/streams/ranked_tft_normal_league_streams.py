from __future__ import annotations

from singer_sdk import typing as th  # JSON Schema typing helpers

from tap_riotapi.client import RiotAPIStream
from tap_riotapi.streams.mixins import TFTRankedLadderMixin
from tap_riotapi.utils import ROMAN_NUMERALS, NON_APEX_TIERS, flatten_config


class NormalTierRankedLadderStream(TFTRankedLadderMixin, RiotAPIStream):
    name = "normal_ranked_ladder"
    path = "/tft/league/v1/entries/{tier}/{division}"
    schema = th.PropertiesList(
        th.Property(
            "puuid",
            th.StringType,
            required=True,
        ),
        th.Property(
            "summonerId",
            th.StringType,
            required=True,
            title="Summoner ID",
            description="Unique identifier for league player account"
        ),
    ).to_dict()

    @property
    def partitions(self) -> list[dict] | None:
        league_list = []
        for item in flatten_config(self.config["followed_leagues"]):
            if item["name"] in NON_APEX_TIERS:
                new_item = {
                    "tier": item["name"].upper(),
                    "region": item["region"]
                }
                if "division" in item:
                    league_list.append(new_item)
                else:
                    for n in range(1, 5):
                        league_list.append(new_item | {"division": n})
        return league_list
