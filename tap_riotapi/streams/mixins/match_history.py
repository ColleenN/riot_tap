from datetime import datetime, timedelta
from math import floor
from typing import Iterable, Any

from _decimal import Decimal
from requests import Response

from singer_sdk import typing as th
from singer_sdk.helpers import types
from singer_sdk.pagination import BaseAPIPaginator, BaseOffsetPaginator
from singer_sdk.streams.core import REPLICATION_INCREMENTAL

from tap_riotapi.streams.mixins.rest_util import ResumablePaginationMixin


class TFTMatchListMixin(ResumablePaginationMixin):

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
        th.Property(
            "url_parms_used",
            th.PropertiesList(
                th.Property("count", th.NumberType),
                th.Property("start", th.NumberType),
                th.Property("startTime", th.NumberType),
                th.Property("endTime", th.NumberType),
            ),
        ),
    ).to_dict()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._page_size = kwargs.get("page_size", 500)

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
            "startTime": floor(self.get_start_timestamp(context).timestamp()),
            "endTime": floor(self.get_end_timestamp().timestamp()),
        }

    def build_paginator_from_state(self, state_partition: dict) -> BaseAPIPaginator:
        starting_index = 0
        if (
            state_partition
            and "last_used_query_params" in state_partition
            and "session_record_count"
        ):
            partial_page_finished = (
                state_partition["session_record_count"]
                % state_partition["last_used_query_params"]["count"]
            )
            starting_index = (
                state_partition["last_used_query_params"]["start"]
                + partial_page_finished
            )
        return MatchHistoryPaginator(
            start_value=starting_index, page_size=self._page_size
        )

    def get_start_timestamp(self, context: types.Context):

        state_dict = self.get_context_state(context)
        if "last_used_query_params" in state_dict:
            last_used_end_param = datetime.fromtimestamp(state_dict["last_used_query_params"]["endTime"])
            gap_period = self._tap.initial_timestamp - last_used_end_param
            if gap_period > timedelta(days=3):
                return self._tap.initial_timestamp
            else:
                return last_used_end_param

            return max(state_dict["last_used_query_params"][""], self._tap.initial_timestamp)

        if context["puuid"] in self.tap_state["player_match_history_state"]:
            my_history_state = self.tap_state["player_match_history_state"][context["puuid"]]
            if "last_processed" in my_history_state:
                return max(my_history_state["last_processed"], self._tap.initial_timestamp)
        return self._tap.initial_timestamp

    def get_end_timestamp(self):
        return self._tap.end_timestamp

    def post_process(
        self,
        row: dict,
        context: types.Context | None = None,  # noqa: ARG002
    ) -> dict | None:
        row = super().post_process(row, context)
        if row:
            return {
                "matchId": row["data"] if row["data"] is not None else "",
                "endTime": self.get_end_timestamp(),
                "url_parms_used": {
                    k: int(v[0]) for k, v in row["url_parms_used"].items()
                },
            }
        return None

    def generate_child_contexts(
        self,
        record: types.Record,
        context: types.Context | None,
    ) -> Iterable[types.Context | None]:
        if not record["matchId"] or record["matchId"] in self.tap_state["match_detail_set"]:
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
        if latest_record and self.replication_method == REPLICATION_INCREMENTAL:
            state_dict = self.get_context_state(context)
            state_dict.setdefault("session_record_count", 0)
            state_dict["session_record_count"] += 1
            state_dict["last_used_query_params"] = latest_record["url_parms_used"]

    def _finalize_state(self, state: dict | None = None) -> None:
        match_history_state = self.tap_state.setdefault(
            "player_match_history_state", {}
        )
        new_player_state = {
            "last_processed": datetime.fromtimestamp(state["last_used_query_params"]["endTime"])
        }
        if "matches_played" in state["context"]:
            new_player_state["matches_played"] = state["context"]["matches_played"]
        match_history_state.setdefault(state["context"]["puuid"], {}).update(
            new_player_state
        )

        context = state["context"]
        state.clear()
        state["context"] = context

        super()._finalize_state(state)


class MatchHistoryPaginator(BaseOffsetPaginator):

    def has_more(self, response: Response) -> bool:
        return len(response.json(parse_float=Decimal)) == self._page_size
