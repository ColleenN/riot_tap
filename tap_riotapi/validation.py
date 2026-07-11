"""Player validation against the Riot account API."""

import requests

ACCOUNT_URL = "https://{region}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"


def validate_player(game_name: str, tag_line: str, platform: str, region: str, token: str) -> bool:
    """Return True if the player exists, False if 404.

    If the initial lookup returns 404 and the tagline differs from the platform
    routing value, retries once using the platform as the tagline.
    """
    def _get(tl: str) -> requests.Response:
        url = ACCOUNT_URL.format(region=region, game_name=game_name, tag_line=tl)
        return requests.get(url, headers={"X-Riot-Token": token})

    response = _get(tag_line)
    if response.status_code == 200:
        return True
    if response.status_code == 404 and tag_line.lower() != platform.lower():
        response = _get(platform)
        if response.status_code == 200:
            return True
        if response.status_code == 404:
            return False
    response.raise_for_status()
