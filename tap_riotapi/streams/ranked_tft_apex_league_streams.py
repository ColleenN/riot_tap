from __future__ import annotations

from singer_sdk import typing as th  # JSON Schema typing helpers
from singer_sdk.helpers import types

from tap_riotapi.client import RiotAPIStream
from tap_riotapi.utils import APEX_TIERS, REGION_ROUTING_MAP
from tap_riotapi.streams.mixins import (
    TFTMatchListMixin,
    TFTMatchDetailMixin,
    TFTRankedLadderMixin,
)


class ApexTierRankedLadderStream(TFTRankedLadderMixin, RiotAPIStream):
    name = "apex_ranked_ladder"
    path = "/tft/league/v1/{tier}"
    schema = th.PropertiesList(
        th.Property(
            "summonerId",
            th.StringType,
            required=True,
            title="Summoner ID",
            description="Unique identifier for league player account",
        ),
    ).to_dict()

    @property
    def partitions(self) -> list[dict] | None:
        partitions = []
        for server, leauge_list in self.config.get("followed_leagues", []).items():
            platform = server.lower()
            if platform not in REGION_ROUTING_MAP.keys():
                continue
            region = REGION_ROUTING_MAP[platform]
            for league in leauge_list:
                if league.get("name").lower() in APEX_TIERS:
                    partitions.append({
                        "tier": league.get("name"),
                        "platform_routing_value": platform,
                        "region_routing_value": region
                    })

        return partitions

    def get_child_context(
        self,
        record: types.Record,
        context: types.Context | None,
    ) -> types.Context | None:
        return {"summonerId": record["summonerId"]}

    @property
    def records_jsonpath(self):
        return "$.entries[*]"


class ApexTierRankedLadderSummonerIDStream(RiotAPIStream):

    name = "ranked_ladder_summoner_id"
    path = "/tft/summoner/v1/summoners/{summonerId}"
    parent_stream_type = ApexTierRankedLadderStream
    schema = th.PropertiesList(
        th.Property(
            "puuid",
            th.StringType,
            required=True,
            title="Player UUID",
            description="Globally unique identifier for Riot Account.",
        )
    )

    def get_child_context(
        self,
        record: types.Record,
        context: types.Context | None,
    ) -> types.Context | None:
        return record


class ApexTierRankedLadderMatchHistoryStream(TFTMatchListMixin, RiotAPIStream):

    name = "ranked_ladder_match_history"
    parent_stream_type = ApexTierRankedLadderSummonerIDStream


class ApexTierRankedLadderMatchDetailStream(TFTMatchDetailMixin, RiotAPIStream):

    name = "ranked_ladder_match_detail"
    parent_stream_type = ApexTierRankedLadderMatchHistoryStream
