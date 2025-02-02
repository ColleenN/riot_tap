from __future__ import annotations

from singer_sdk import typing as th  # JSON Schema typing helpers
from singer_sdk.helpers import types

from tap_riotapi.client import RiotAPIStream
from tap_riotapi.utils import APEX_TIERS
from tap_riotapi.streams.mixins import TFTMatchListMixin, TFTMatchDetailMixin, TFTRankedLadderMixin


class ApexTierRankedLadderStream(TFTRankedLadderMixin, RiotAPIStream):
    name = "apex_ranked_ladder"
    path = "/tft/league/v1/{tier}"
    schema = th.PropertiesList(
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
        return [x for x in self.config.get("followed_leagues", []) if x in APEX_TIERS]

    def get_child_context(
        self,
        record: types.Record,
        context: types.Context | None,
    ) -> types.Context | None:
        return {"summonerId": record["summonerId"]}

    @property
    def records_jsonpath(self):
        return "$.entries[*]"


class RankedLadderSummonerIDStream(RiotAPIStream):

    name = "ranked_ladder_summoner_id"
    path = "/tft/summoner/v1/summoners/{summonerId}"


class RankedLadderMatchHistoryStream(TFTMatchListMixin, RiotAPIStream):

    name = "ranked_ladder_match_history"
    #parent_stream_type = RankedLadderSummonerIDStream


class RankedLadderMatchDetailStream(TFTMatchDetailMixin, RiotAPIStream):

    name = "ranked_ladder_match_detail"
    #parent_stream_type = RankedLadderMatchHistoryStream
