from typing import Any, Iterable

from singer_sdk import typing as th  # JSON Schema typing helpers
from singer_sdk.helpers import types


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

    def post_process(
        self,
        row: dict,
        context: types.Context | None = None,  # noqa: ARG002
    ) -> dict | None:
        initial_row = super().post_process(row, context)
        if not initial_row:
            return context
        return context | {
            "puuid": initial_row["puuid"],
            "lp": initial_row["leaguePoints"],
            "matches_played": initial_row["wins"] + initial_row["losses"],
        }

    def generate_child_contexts(
        self,
        record: types.Record,
        context: types.Context | None,
    ) -> Iterable[types.Context | None]:
        # This occurs when there are no players in this rank tier.
        # Happens at the beginning of a new set, usually.
        if not "puuid" in record:
            return []
        if record["puuid"] in self.tap_state["player_match_history_state"]:
            my_history_state = self.tap_state["player_match_history_state"][
                record["puuid"]
            ]
            if my_history_state.get("matches_played", 0) == record["matches_played"]:
                return []
        yield self.get_child_context(record=record, context=context)

    def get_child_context(
        self,
        record: types.Record,
        context: types.Context | None,
    ) -> types.Context | None:
        return record | context if record else context


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
