"""Streams whose endpoint returns a single object must emit it as one record."""

import pytest
from singer_sdk.helpers.jsonpath import extract_jsonpath

from tap_riotapi.streams import ranked_tft_apex_league_streams, ranked_tft_normal_league_streams, tft_player_streams
from tap_riotapi.streams.mixins.tft_endpts import TFTMatchDetailMixin

MATCH = {"metadata": {"match_id": "NA1_1"}, "info": {"game_version": "x"}}
ACCOUNT = {"puuid": "abc", "gameName": "Player", "tagLine": "NA1"}

MATCH_DETAIL_STREAMS = [
    cls
    for module in (tft_player_streams, ranked_tft_apex_league_streams, ranked_tft_normal_league_streams)
    for cls in vars(module).values()
    if isinstance(cls, type) and issubclass(cls, TFTMatchDetailMixin) and cls is not TFTMatchDetailMixin
]


def test_found_match_detail_streams():
    assert len(MATCH_DETAIL_STREAMS) == 3


@pytest.mark.parametrize("stream", MATCH_DETAIL_STREAMS, ids=lambda cls: cls.__name__)
def test_match_detail_is_one_record(stream):
    assert list(extract_jsonpath(stream.records_jsonpath, MATCH)) == [MATCH]


def test_player_by_name_is_one_record():
    assert list(extract_jsonpath(tft_player_streams.TFTPlayerByNameStream.records_jsonpath, ACCOUNT)) == [ACCOUNT]
