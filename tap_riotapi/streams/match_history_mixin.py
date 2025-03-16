from math import floor
from typing import Iterable, Any

from _decimal import Decimal
from requests import Response

from singer_sdk import typing as th
from singer_sdk.helpers import types
from singer_sdk.pagination import BaseAPIPaginator, BaseOffsetPaginator
from singer_sdk.streams.core import REPLICATION_INCREMENTAL


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
        th.Property("endTime", th.DateTimeType),
        th.Property("query_params_used",
            th.PropertiesList(
                th.Property("count", th.NumberType),
                th.Property("start", th.NumberType),
                th.Property("startTime", th.NumberType),
                th.Property("endTime", th.NumberType),
            )
        ),
    ).to_dict()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._page_size = kwargs.get("page_size", 20)
        self._state_partitioning_keys = {"puuid"}

    @property
    def is_sorted(self) -> bool:
        return True

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

    def get_new_paginator(self) -> BaseAPIPaginator:
        return MatchHistoryPaginator(start_value=0, page_size=self._page_size)

    def get_start_timestamp(self):
        return self._tap.initial_timestamp

    def get_end_timestamp(self):
        return self._tap.end_timestamp

    def parse_response(self, response: Response) -> Iterable[dict]:
        yield from super().parse_response(response)

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



    def _increment_stream_state(
            self,
            latest_record: types.Record,
            *,
            context: types.Context | None = None,
    ):

        state_dict = self.get_context_state(context)
        if latest_record and self.replication_method == REPLICATION_INCREMENTAL:
            state_dict["last_used_query_params"] = self.get_url_params(context, next_page_token=None)


        super()._increment_stream_state(latest_record, context=context)


class MatchHistoryPaginator(BaseOffsetPaginator):

    def has_more(self, response: Response) -> bool:
        return len(response.json(parse_float=Decimal)) == self._page_size
