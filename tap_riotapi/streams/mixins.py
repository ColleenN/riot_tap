from decimal import Decimal
from typing import Any, Iterable
from math import floor

from requests import Response
from singer_sdk import typing as th  # JSON Schema typing helpers
from singer_sdk.helpers import types
from singer_sdk.pagination import BaseAPIPaginator, BaseOffsetPaginator


class TFTRankedLadderMixin:

    routing_type = "platform"

    def get_url_params(
        self,
        context: types.Context | None,  # noqa: ARG002
        next_page_token: Any | None,  # noqa: ANN401
    ) -> dict[str, Any]:
        params = super().get_url_params(context, next_page_token)
        params.update({"queue": "RANKED_TFT"})
        return params


class TFTMatchListMixin:

    replication_key = "endTime"

    path = "/tft/match/v1/matches/by-puuid/{puuid}/ids"
    schema = th.PropertiesList(
        th.Property(
            "matchId",
            th.StringType,
            required=True,
            title="Match Identifier",
            description="Identifies a single game of TFT.",
        ),
        th.Property("puuid", th.StringType, required=False, title="Player Identifier"),
        th.Property("endTime", th.DateTimeType)
    ).to_dict()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._page_size = kwargs.get("page_size", 20)
        self._state_partitioning_keys = {"puuid"}

    def generate_child_contexts(
            self,
            record: types.Record,
            context: types.Context | None,
    ) -> Iterable[types.Context | None]:
        if record["matchId"] in self.tap_state.setdefault("match_detail_set", set()):
            return []
        yield self.get_child_context(record=record, context=context)

    def get_child_context(
        self,
        record: types.Record,
        context: types.Context | None,
    ) -> types.Context | None:
        return context | {"matchId": record["matchId"]}

    def post_process(
        self,
        row: dict,
        context: types.Context | None = None,  # noqa: ARG002
    ) -> dict | None:
        data = super().post_process(row, context)
        if data:
            return {
                "matchId": data,
                "endTime": self.get_end_timestamp()
            }
        return None

    def get_new_paginator(self) -> BaseAPIPaginator:
        return MatchHistoryPaginator(start_value=0, page_size=self._page_size)

    def get_url_params(
        self,
        context: types.Context | None,  # noqa: ARG002
        next_page_token: Any | None,  # noqa: ANN401
    ) -> dict[str, Any]:
        return {
            "count": self._page_size,
            "start": next_page_token,
            "startTime": floor(self.get_start_timestamp().timestamp()),
            "endTime": floor(self.get_end_timestamp().timestamp()),
        }

    def get_start_timestamp(self):
        return self._tap.initial_timestamp

    def get_end_timestamp(self):
        return self._tap.end_timestamp

    @property
    def is_sorted(self) -> bool:
        return True

    def _increment_stream_state(
            self,
            latest_record: types.Record,
            *,
            context: types.Context | None = None,
    ):
        super()._increment_stream_state(latest_record, context=context)


class MatchHistoryPaginator(BaseOffsetPaginator):

    def has_more(self, response: Response) -> bool:
        return len(response.json(parse_float=Decimal)) == self._page_size


class TFTMatchDetailMixin:

    path = "/tft/match/v1/matches/{matchId}"
    schema = th.PropertiesList(
        th.Property(
            "metadata",
            th.PropertiesList(
                th.Property("data_version", th.StringType),
                th.Property("match_id", th.StringType),
                th.Property("participants", th.ArrayType(th.StringType)),
            ),
            required=True,
            title="Metadata",
            description="Match metadata.",
        ),
        th.Property(
            "info",
            th.PropertiesList(
                th.Property("endOfGameResult", th.StringType),
                th.Property("gameCreation", th.NumberType),
                th.Property("gameId", th.NumberType),
                th.Property("gameCreation", th.NumberType),
                th.Property("game_length", th.NumberType),
                th.Property("game_version", th.StringType),
                th.Property("mapId", th.NumberType),
                th.Property("queueId", th.NumberType),
                th.Property("queue_id", th.NumberType),
                th.Property("tft_game_type", th.StringType),
                th.Property("tft_set_core_name", th.StringType),
                th.Property("tft_set_number", th.NumberType),
                th.Property(
                    "participants",
                    th.ArrayType(
                        th.PropertiesList(
                            th.Property("gold_left", th.NumberType),
                            th.Property("last_round", th.NumberType),
                            th.Property("level", th.NumberType),
                            th.Property("placement", th.NumberType),
                            th.Property("players_eliminated", th.NumberType),
                            th.Property("puuid", th.StringType),
                            th.Property("riotIdGameName", th.StringType),
                            th.Property("riotIdTagline", th.StringType),
                            th.Property("time_eliminated", th.NumberType),
                            th.Property("total_damage_to_players", th.NumberType),
                            th.Property("win", th.BooleanType),
                            th.Property(
                                "traits",
                                th.ArrayType(
                                    th.PropertiesList(
                                        th.Property("name", th.StringType),
                                        th.Property("num_units", th.NumberType),
                                        th.Property("style", th.NumberType),
                                        th.Property("tier_current", th.NumberType),
                                        th.Property("tier_total", th.NumberType),
                                    )
                                ),
                            ),
                            th.Property(
                                "units",
                                th.ArrayType(
                                    th.PropertiesList(
                                        th.Property("character_id", th.StringType),
                                        th.Property("rarity", th.NumberType),
                                        th.Property("tier", th.NumberType),
                                        th.Property(
                                            "itemNames", th.ArrayType(th.StringType)
                                        ),
                                    )
                                ),
                            ),
                        )
                    ),
                ),
                # TODO: "participants" schema
            ),
            required=True,
            title="Info",
            description="Describes match end state.",
        ),
    ).to_dict()

    def _increment_stream_state(
            self,
            latest_record: types.Record,
            *,
            context: types.Context | None = None,
    ):
        super()._increment_stream_state(latest_record, context=context)
        self.tap_state.setdefault("match_detail_set", set()).add(context["matchId"])
