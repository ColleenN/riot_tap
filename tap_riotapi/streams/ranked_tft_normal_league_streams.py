from __future__ import annotations
from decimal import Decimal
from requests import Response
from typing import Any

from singer_sdk import typing as th  # JSON Schema typing helpers
from singer_sdk.pagination import BaseAPIPaginator, BasePageNumberPaginator
from singer_sdk.helpers import types

from tap_riotapi.client import RiotAPIStream
from tap_riotapi.streams.mixins import (
    TFTMatchListMixin,
    TFTMatchDetailMixin,
    TFTRankedLadderMixin,
)
from tap_riotapi.utils import (
    ROMAN_NUMERALS,
    NON_APEX_TIERS,
    REGION_ROUTING_MAP,
    flatten_config,
)


class NonApexLeaguePaginator(BasePageNumberPaginator):

    def __init__(
        self,
        start_value: int,
        page_size: int,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Create a new paginator.

        Args:
            start_value: Initial value.
            page_size: Constant page size.
            args: Paginator positional arguments.
            kwargs: Paginator keyword arguments.
        """
        super().__init__(start_value, *args, **kwargs)
        self._page_size = page_size

    def has_more(self, response: Response) -> bool:
        return len(response.json(parse_float=Decimal)) == self._page_size


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
                        league_list.append(new_item | {"division": ROMAN_NUMERALS[n]})
        return league_list

    def get_new_paginator(self) -> BaseAPIPaginator:
        return NonApexLeaguePaginator(start_value=1, page_size=205)

    def get_url_params(
        self,
        context: types.Context | None,  # noqa: ARG002
        next_page_token: Any | None,  # noqa: ANN401
    ) -> dict[str, Any]:
        params = super().get_url_params(context, next_page_token)
        params.update({"page": next_page_token})
        return params


class NormalTierRankedLadderMatchHistoryStream(TFTMatchListMixin, RiotAPIStream):

    name = "ranked_ladder_match_history"
    parent_stream_type = NormalTierRankedLadderStream


class NormalTierRankedLadderMatchDetailStream(TFTMatchDetailMixin, RiotAPIStream):

    name = "ranked_ladder_match_detail"
    parent_stream_type = NormalTierRankedLadderMatchHistoryStream
