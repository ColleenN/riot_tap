from typing import Any

from singer_sdk import typing as th  # JSON Schema typing helpers
from singer_sdk.helpers import types


class TFTRankedLadderMixin:

    routing_type = "platform"

    def get_url_params(self, *args, **kwargs) -> dict[str, Any]:
        params = super().get_url_params(*args, **kwargs)
        params.update({"queue": "RANKED_TFT"})
        return params


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
                # TODO: "participants" schema
            ),
            required=True,
            title="Info",
            description="Describes match end state.",
        ),
    ).to_dict()


class TFTMatchListMixin:

    path = "/tft/match/v1/matches/by-puuid/{puuid}/ids"
    schema = th.PropertiesList(
        th.Property(
            "",
            th.ArrayType(th.StringType),
            required=False,
            title="Match Identifier",
            description="Identifies a single game of TFT.",
        )
    ).to_dict()

    def get_child_context(
        self,
        record: types.Record,
        context: types.Context | None,
    ) -> types.Context | None:
        return record | context

    def post_process(
            self,
            row: dict,
            context: types.Context | None = None,  # noqa: ARG002
    ) -> dict | None:
        return {"matchId": super().post_process(row, context)}