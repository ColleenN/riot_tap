import json
from datetime import datetime
from singer_sdk.singerlib import Message
from singer_sdk.io_base import SingerWriter
import typing as t


def flatten_config(config_dict: dict[str, dict[str, list]]) -> tuple:

    players = []
    apex_leagues = []
    reg_leagues = []
    for region, region_config_dict in config_dict.items():
        base = {"region": region}
        players.extend(
            [base | {"name": p} for p in region_config_dict.get("players", [])]
        )
        for item in region_config_dict.get("leagues", []):
            if item["name"] in APEX_TIERS:
                apex_leagues.append(item | base)
            elif item["name"] in NON_APEX_TIERS:
                reg_leagues.append(item | base)

    return players, apex_leagues, reg_leagues


ROMAN_NUMERALS = {1: "I", 2: "II", 3: "III", 4: "IV"}
NON_APEX_TIERS = {"diamond", "emerald", "platinum", "gold", "silver", "bronze", "iron"}
APEX_TIERS = {"challenger", "grandmaster", "master"}

REGION_ROUTING_MAP = {
    "pbe": "americas",
    "na1": "americas",
    "br1": "americas",
    "la1": "americas",
    "la2": "americas",
    "jp1": "asia",
    "kr": "asia",
    "sg2": "sea",
    "tw2": "sea",
    "vn2": "sea",
    "oc1": "sea",
    "me1": "europe",
    "eun1": "europe",
    "euw1": "europe",
    "tr1": "europe",
    "ru": "europe",
}


def default_encoding(obj: t.Any) -> str:  # noqa: ANN401
    """Default JSON encoder.

    Args:
        obj: The object to encode.

    Returns:
        The encoded object.
    """
    if isinstance(obj, datetime):
        return obj.isoformat(sep="T")
    if isinstance(obj, set):
        return json.dumps(
            list(obj),
            default=default_encoding,
            separators=(",", ":")
        )
    return str(obj)


class MessageWriter(SingerWriter):


    def serialize_message(self, message: Message) -> str:  # noqa: PLR6301
        """Serialize a dictionary into a line of json.

        Args:
            message: A Singer message object.

        Returns:
            A string of serialized json.
        """
        value = json.dumps(
            message.to_dict(),
            default=default_encoding,
            separators=(",", ":")
        )
        return value