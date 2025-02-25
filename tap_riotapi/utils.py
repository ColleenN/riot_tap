from __future__ import annotations


def flatten_config(
    config_dict: dict[str, list[dict]] | dict[str, list[str]],
) -> list[dict]:

    flattened = []
    for region, region_config_value in config_dict.items():

        for item in region_config_value:
            if not isinstance(item, dict):
                item = {"name": item}
            flattened.append(item | {"region": region})

    return flattened


ROMAN_NUMERALS = {"1": "I", "2": "II", "3": "III", "4": "IV"}
NON_APEX_TIERS = {"diamond", "emerald", "platinum", "gold", "silver", "bronze", "iron"}
APEX_TIERS = {"challenger", "grandmaster", "master"}

REGION_ROUTING_MAP = {
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
