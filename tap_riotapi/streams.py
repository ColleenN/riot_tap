"""Stream type classes for tap-riotapi."""

from __future__ import annotations

from typing import Any

from singer_sdk import typing as th  # JSON Schema typing helpers
from singer_sdk.helpers import types

from tap_riotapi.client import RiotAPIStream
from tap_riotapi.mixins import TFTMatchDetailMixin, TFTMatchListMixin

DIVIDED_LEAGUES = ["diamond", "emerald", "platinum", "gold", "silver", "bronze", "iron"]
ROMAN_NUMERALS = {"1": "I", "2": "II", "3": "III", "4": "IV"}

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

    @property
    def partitions(self) -> list[dict] | None:

        league_list = []
        for item in self.config.get("followed_leagues", []):
            division = None
            if item[-1].isdigit():
                tier = item[:-1]
                division = item[-1]
            else:
                tier = item
            tier = tier.lower()
            if tier in DIVIDED_LEAGUES:
                if division:
                    league_list.append(
                        {"division": ROMAN_NUMERALS[division], "tier": tier.upper()})
                else:
                    for n in range(1, 5):
                        league_list.append(
                            {"division": ROMAN_NUMERALS[n], "tier": tier.upper()})
            else:
                league_list.append({"tier": tier})
        return league_list


    def get_child_context(
        self,
        record: types.Record,
        context: types.Context | None,
    ) -> types.Context | None:
        return {"puuid": record["puuid"]}


    def get_url_params(
        self, *args, **kwargs
    ) -> dict[str, Any]:
        params = super().get_url_params(*args, **kwargs)
        params.update({"queue": "RANKED_TFT"})
        return params

    @property
    def url_base(self) -> str:
        return f"https://na1.api.riotgames.com"

    def get_url(self, context: types.Context | None) -> str:
        if context.get("division", None):
            return (
                f"{self.url_base}"
                f"/tft/league/v1/entries/"
                f"{context.get('tier')}/{context.get('division')}"
            )
        else:
            return f"{self.url_base}/tft/league/v1/{context.get('tier')}"


    @property
    def records_jsonpath(self):

        return "$.entries[*]"


class RankedLadderSummonerIDStream(RiotAPIStream):

    name = "ranked_ladder_summoner_id"
    path = "/tft/summoner/v1/summoners/{summonerId}"


class RankedLadderMatchHistoryStream(TFTMatchListMixin, RiotAPIStream):

    name = "ranked_ladder_match_history"
    parent_stream_type = RankedLadderStream


class RankedLadderMatchDetailStream(TFTMatchDetailMixin, RiotAPIStream):

    name = "ranked_ladder_match_detail"
    parent_stream_type = RankedLadderMatchHistoryStream


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
        for player in self.config.get("followed_players", []):
            name, tagline = player.split("#")
            player_list += [{"gameName": name, "tagLine": tagline}]
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