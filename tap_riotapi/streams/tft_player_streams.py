"""Stream type classes for tap-riotapi."""

from __future__ import annotations
import logging
import typing
import typing as t

from singer_sdk import typing as th  # JSON Schema typing helpers
from singer_sdk.helpers import types
from singer_sdk.helpers.types import Context

from tap_riotapi.client import RiotAPIStream
from singer_sdk.exceptions import FatalAPIError
from tap_riotapi.streams.mixins.tft_endpts import TFTMatchDetailMixin
from tap_riotapi.streams.mixins.match_history import TFTMatchListMixin
from tap_riotapi.utils import flatten_config, REGION_ROUTING_MAP

LOGGER = logging.getLogger(__name__)

if typing.TYPE_CHECKING:
    import requests

class TFTPlayerByNameStream(RiotAPIStream):

    name = "tft_player_by_name"
    path = "/riot/account/v1/accounts/by-riot-id/{gameName}/{tagLine}"
    schema = th.PropertiesList(
        th.Property(
            "puuid",
            th.StringType,
            required=True,
            title="Player UUID",
            description="Globally unique identifier for Riot Account.",
        )
    ).to_dict()

    @property
    def url_base(self) -> str:
        return "https://{region_routing_value}.api.riotgames.com"

    @property
    def partitions(self) -> list[dict] | None:

        player_list = []
        player_config, _, _ = flatten_config(self.config["following"])
        for player in player_config:
            if "#" not in player["name"]:
                LOGGER.info(f"MISSING TAGLINE - {player['name']}'")
                continue

            name, tagline = player["name"].split("#")

            platform = player["region"].lower()
            if platform not in REGION_ROUTING_MAP.keys():
                continue
            region = REGION_ROUTING_MAP[platform]

            player_list.append(
                {
                    "gameName": name,
                    "tagLine": tagline,
                    "platform_routing_value": platform,
                    "region_routing_value": region,
                }
            )
        return player_list

    def get_child_context(
        self,
        record: types.Record,
        context: types.Context | None,
    ) -> types.Context | None:
        return record | context

    def get_records(self, context: Context | None) -> t.Iterable[dict[str, t.Any]]:

        try:
            yield from super().request_records(context)
        except FatalAPIError as api_error:
            if "404 Client Error: Not Found for path" in str(api_error):
                self.logger.warning(
                    f"{api_error} - SKIPPING."
                )
                return
            raise api_error

class TFTPlayerMatchHistoryStream(TFTMatchListMixin, RiotAPIStream):

    name = "tft_player_match_history"
    parent_stream_type = TFTPlayerByNameStream


class TFTPlayerMatchDetailStream(TFTMatchDetailMixin, RiotAPIStream):

    name = "tft_player_match_detail"
    parent_stream_type = TFTPlayerMatchHistoryStream
