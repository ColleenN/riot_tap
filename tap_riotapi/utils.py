from __future__ import annotations


def flatten_config(config_dict: dict[str, list[dict]] | dict[str, list[str]]) -> list[dict]:

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
