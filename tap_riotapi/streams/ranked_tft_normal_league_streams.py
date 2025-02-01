from __future__ import annotations

from tap_riotapi.client import RiotAPIStream

ROMAN_NUMERALS = {"1": "I", "2": "II", "3": "III", "4": "IV"}
NON_APEX_TIERS = {"diamond", "emerald", "platinum", "gold", "silver", "bronze", "iron"}


class NormalTierRankedLadderStream(TFTRankedLadderMixin, RiotAPIStream):
    name = "normal_ranked_ladder"
    path = "/tft/league/v1/entries/{tier}/{division}"

    @property
    def partitions(self) -> list[dict] | None:
        league_list = []
        for item in self.config.get("followed_leagues", []):
            division = None
            if item[-1].isdigit():
                tier = item[:-1]
                division = item[-1]
            else:
                tier = item
            tier = tier.lower()
            if tier in NON_APEX_TIERS:
                if division:
                    league_list.append(
                        {"division": ROMAN_NUMERALS[division], "tier": tier.upper()})
                else:
                    for n in range(1, 5):
                        league_list.append(
                            {"division": ROMAN_NUMERALS[n], "tier": tier.upper()})
        return league_list
