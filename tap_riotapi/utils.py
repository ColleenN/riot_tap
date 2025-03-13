from singer_sdk.pagination import BaseOffsetPaginator
from requests import Response


class RiotAPIPaginator(BaseOffsetPaginator):

    def has_more(self, response: Response) -> bool:

        if self._value > 200:
            return False
        return not len(response.content) == self._page_size


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
