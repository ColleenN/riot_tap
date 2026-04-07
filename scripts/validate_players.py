"""Validate player name/tagline combinations against the Riot account API.

Reads players from a tap config JSON file (same format as tap-riotapi expects),
including any player_list_file CSVs specified per region. Hits the account
lookup endpoint for each player and reports which names cannot be found.

Usage:
    python scripts/validate_players.py --config path/to/config.json
    python scripts/validate_players.py --config path/to/config.json --token YOUR_TOKEN
"""

import argparse
import csv
import json
import os
import sys

import requests

# Allow running from the repo root without installing the package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tap_riotapi.utils import flatten_config, REGION_ROUTING_MAP

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


def main():
    parser = argparse.ArgumentParser(description="Validate Riot player names against the account API.")
    parser.add_argument("--config", required=True, help="Path to tap config JSON file.")
    parser.add_argument("--token", default=None, help="Riot API token. Defaults to TAP_RIOTAPI_AUTH_TOKEN env var.")
    parser.add_argument("--valid-out", default="valid_players.csv", help="Output CSV for valid players (default: valid_players.csv).")
    parser.add_argument("--invalid-out", default="invalid_players.csv", help="Output CSV for invalid players (default: invalid_players.csv).")
    args = parser.parse_args()

    token = args.token or os.environ.get("TAP_RIOTAPI_AUTH_TOKEN")
    if not token:
        sys.exit("Error: provide --token or set TAP_RIOTAPI_AUTH_TOKEN.")

    with open(args.config) as f:
        config = json.load(f)

    following = config.get("following")
    if not following:
        sys.exit("Error: config has no 'following' key.")

    players, _, _ = flatten_config(following)

    if not players:
        print("No players found in config.")
        return

    valid = []
    invalid = []
    errors = []

    for player in players:
        name_raw = player["name"]
        platform = player["region"].lower()  

        if platform not in REGION_ROUTING_MAP:
            errors.append(f"  {platform} | {name_raw!r} — unknown region, skipped")
            continue

        if "#" in name_raw:
            game_name, tag_line = name_raw.split("#", 1)
        else:
            game_name = name_raw
            tag_line = platform

        
        region = REGION_ROUTING_MAP[platform]

        try:
            found = validate_player(game_name, tag_line, platform, region, token)
        except requests.HTTPError as e:
            errors.append(f"  {platform} | {name_raw!r} — unexpected HTTP error: {e}")
            continue

        if found:
            valid.append((game_name, tag_line))
        else:
            invalid.append((game_name, tag_line))

    def write_csv(path: str, rows: list[tuple]) -> None:
        with open(path, "w", newline="") as f:
            csv.writer(f).writerows(rows)

    write_csv(args.valid_out, valid)
    write_csv(args.invalid_out, invalid)

    print(f"\n=== Results: {len(players)} players checked ===\n")

    if valid:
        print(f"VALID ({len(valid)}) -> {args.valid_out}")
    if invalid:
        print(f"INVALID - 404 ({len(invalid)}) -> {args.invalid_out}")
    if errors:
        print(f"\nSKIPPED ({len(errors)}):")
        print("\n".join(errors))

    if invalid:
        sys.exit(1)


if __name__ == "__main__":
    main()
