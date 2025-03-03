from __future__ import annotations

from singer_sdk import typing as th  # JSON Schema typing helpers

from tap_riotapi.client import RiotAPIStream
from tap_riotapi.streams.mixins import (
    TFTMatchListMixin,
    TFTMatchDetailMixin,
    TFTRankedLadderMixin,
)
from tap_riotapi.utils import ROMAN_NUMERALS, NON_APEX_TIERS, REGION_ROUTING_MAP, flatten_config


class NormalTierRankedLadderStream(TFTRankedLadderMixin, RiotAPIStream):
    name = "normal_ranked_ladder"
    path = "/tft/league/v1/entries/{tier}/{division}"
    schema = th.PropertiesList(
        th.Property(
            "puuid",
            th.StringType,
            required=True,
        )
    ).to_dict()

    @property
    def partitions(self) -> list[dict] | None:

        _, _, reg_league_config = flatten_config(self.config["following"])
        league_list = []

        for item in reg_league_config:
            platform = item["region"].lower()
            if platform not in REGION_ROUTING_MAP.keys():
                continue
            region = REGION_ROUTING_MAP[platform]

            if item["name"] in NON_APEX_TIERS:
                new_item = {
                    "tier": item["name"].upper(),
                    "platform_routing_value": platform,
                    "region_routing_value": region,
                }
                if "division" in item.keys():
                    new_item["division"] = ROMAN_NUMERALS[item["division"]]
                    league_list.append(new_item)
                else:
                    for n in range(1, 5):
                        league_list.append(
                            new_item | {"division": ROMAN_NUMERALS[n]}
                        )
        return league_list


class NormalTierRankedLadderMatchHistoryStream(TFTMatchListMixin, RiotAPIStream):

    name = "ranked_ladder_match_history"
    parent_stream_type = NormalTierRankedLadderStream


class NormalTierRankedLadderMatchDetailStream(TFTMatchDetailMixin, RiotAPIStream):

    name = "ranked_ladder_match_detail"
    parent_stream_type = NormalTierRankedLadderMatchHistoryStream
