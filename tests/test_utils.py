"""Offline tests for config flattening and other helpers in tap_riotapi.utils."""

import gzip
import json
from datetime import datetime

import pytest

from tap_riotapi.utils import default_encoding, flatten_config, load_player_file, load_player_json

PLAYERLIST = {
    "players": [
        {"pbe_id": "Ready#PBE", "registration_status": "READY"},
        {"pbe_id": "NoTag#PBE", "registration_status": "MISSING TAG"},
        {"pbe_id": None, "registration_status": "MISSING DISCORD ID AND PBE ACCOUNT"},
        {"pbe_id": " Padded #pbe ", "registration_status": "MISSING DISCORD ID"},
    ]
}
SELECT_TAGGED = ["$.players[?(@.registration_status != 'MISSING TAG')].pbe_id"]


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


def test_load_player_json_from_file(tmp_path):
    path = tmp_path / "playerlist.json"
    path.write_text(json.dumps(PLAYERLIST))

    assert load_player_json({"path": str(path), "select": SELECT_TAGGED}) == ["Ready#PBE", "Padded #pbe"]


def test_load_player_json_reads_last_file_in_folder(tmp_path):
    (tmp_path / "20261118T000000Z_playerlist.gz").write_bytes(
        gzip.compress(json.dumps({"players": [{"pbe_id": "Old#PBE"}]}).encode())
    )
    (tmp_path / "20261119T000000Z_playerlist.gz").write_bytes(gzip.compress(json.dumps(PLAYERLIST).encode()))

    assert load_player_json({"path": str(tmp_path), "select": ["$.players[*].pbe_id"]}) == [
        "Ready#PBE",
        "NoTag#PBE",
        "Padded #pbe",
    ]


def test_load_player_json_empty_folder(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_player_json({"path": str(tmp_path), "select": ["$.players[*].pbe_id"]})


def test_load_player_json_without_a_source():
    assert load_player_json(None) == []


def test_flatten_config_dedupes_players_across_sources(tmp_path):
    path = tmp_path / "playerlist.json"
    path.write_text(json.dumps(PLAYERLIST))

    players, _, _ = flatten_config(
        {"na1": {"players": ["ready#pbe"], "player_list_json": {"path": str(path), "select": SELECT_TAGGED}}}
    )

    assert players == [
        {"region": "na1", "name": "ready#pbe"},
        {"region": "na1", "name": "Padded #pbe"},
    ]


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
