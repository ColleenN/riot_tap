"""Offline tests for config flattening and other helpers in tap_riotapi.utils."""

import json
from datetime import datetime

from tap_riotapi.utils import default_encoding, flatten_config, load_player_file


def test_load_player_file(tmp_path):
    path = tmp_path / "players.csv"
    path.write_text("SupremeKitteh,NA1\nSomeone Else,1234\n")

    assert load_player_file(str(path)) == ["SupremeKitteh#NA1", "Someone Else#1234"]


def test_load_player_file_without_a_path():
    assert load_player_file(None) == []
    assert load_player_file("") == []


def test_flatten_config_players_from_inline_and_file(tmp_path):
    path = tmp_path / "players.csv"
    path.write_text("FromFile,NA1\n")

    players, apex, regular = flatten_config(
        {"na1": {"players": ["Inline#NA1"], "player_list_file": str(path)}}
    )

    assert players == [
        {"region": "na1", "name": "Inline#NA1"},
        {"region": "na1", "name": "FromFile#NA1"},
    ]
    assert apex == [] and regular == []


def test_flatten_config_splits_apex_and_regular_leagues():
    players, apex, regular = flatten_config(
        {
            "na1": {"leagues": [{"name": "challenger"}, {"name": "diamond", "division": 2}]},
            "kr": {"leagues": [{"name": "master"}]},
        }
    )

    assert players == []
    assert apex == [
        {"name": "challenger", "region": "na1"},
        {"name": "master", "region": "kr"},
    ]
    assert regular == [{"name": "diamond", "division": 2, "region": "na1"}]


def test_flatten_config_ignores_unknown_tiers():
    _, apex, regular = flatten_config({"na1": {"leagues": [{"name": "unranked"}]}})

    assert apex == [] and regular == []


def test_default_encoding():
    assert default_encoding(datetime(2026, 11, 1, 12, 30)) == "2026-11-01T12:30:00"
    assert json.loads(default_encoding({"a"})) == ["a"]
    assert default_encoding(42) == "42"
