"""Stream type classes for tap-riotapi."""

from __future__ import annotations

from setuptools.namespaces import flatten
from singer_sdk import typing as th  # JSON Schema typing helpers
from singer_sdk.helpers import types

from tap_riotapi.client import RiotAPIStream
from tap_riotapi.streams.mixins import TFTMatchDetailMixin, TFTMatchListMixin
from tap_riotapi.utils import flatten_config


class TFTPlayerByNameStream(RiotAPIStream):

    name = "tft_player_by_name"
    path = "/riot/account/v1/accounts/by-riot-id/{gameName}/{tagLine}"
    schema = th.PropertiesList(
        th.Property(
            "puuid",
            th.StringType,
            required=True,
            title="Player UUID",
            description="Globally unique identifier for Riot Account."
        )
    ).to_dict()

    @property
    def url_base(self) -> str:
        return "https://americas.api.riotgames.com"


    @property
    def partitions(self) -> list[dict] | None:

        player_list = []
        for player in flatten_config(self.config["followed_players"]):
            name, tagline = player["name"].split("#")
            player_list.append(
                {"gameName": name, "tagLine": tagline, "region": player["region"]})
        return player_list


    def get_child_context(
        self,
        record: types.Record,
        context: types.Context | None,
    ) -> types.Context | None:
        return record


class TFTPlayerMatchHistoryStream(TFTMatchListMixin, RiotAPIStream):

    name = "tft_player_match_history"
    parent_stream_type = TFTPlayerByNameStream


class TFTPlayerMatchDetailStream(TFTMatchDetailMixin, RiotAPIStream):

    name = "tft_player_match_detail"
    parent_stream_type = TFTPlayerMatchHistoryStream
