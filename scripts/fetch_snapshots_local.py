"""
Fetch snapshots for recent NBA seasons using nba_api and write CSVs into sample_data/.

Designed to run on your Mac without extra setup beyond nba_api + pandas.
Usage:
  python scripts/fetch_snapshots_local.py            # last 5 seasons
  python scripts/fetch_snapshots_local.py --seasons 2021-22 2022-23 2023-24
"""

from __future__ import annotations

import argparse
import datetime as _dt
from pathlib import Path
import subprocess
import json
import urllib.parse as _url
from typing import List

import pandas as pd
from nba_api.stats.endpoints import LeagueDashPlayerStats


NBA_REQUEST_HEADERS = {
    "Host": "stats.nba.com",
    "Connection": "keep-alive",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.nba.com/",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://www.nba.com",
    "x-nba-stats-origin": "stats",
    "x-nba-stats-token": "true",
}


def generate_last_n_seasons(n: int = 5) -> List[str]:
    """Return last n NBA seasons as strings like '2023-24'.

    We assume the current season spans current_year-1 to current_year if before July,
    else current_year to next_year.
    """
    today = _dt.date.today()
    if today.month < 7:
        end_year = today.year  # season like 2024-25 when in spring 2025
    else:
        end_year = today.year + 1
    seasons: List[str] = []
    for i in range(n):
        start = end_year - 1 - i
        end = (end_year - i) % 100
        seasons.append(f"{start}-{end:02d}")
    return list(reversed(seasons))


def fetch_season_csv(season: str, out_dir: Path) -> Path:
    """Fetch using curl (HTTP/2, compressed) first, fallback to nba_api if needed."""
    base = "https://stats.nba.com/stats/leaguedashplayerstats"
    params = {
        "College": "",
        "Conference": "",
        "Country": "",
        "DateFrom": "",
        "DateTo": "",
        "Division": "",
        "DraftPick": "",
        "DraftYear": "",
        "GameScope": "",
        "GameSegment": "",
        "Height": "",
        "LastNGames": 0,
        "LeagueID": "00",
        "Location": "",
        "MeasureType": "Base",
        "Month": 0,
        "OpponentTeamID": 0,
        "Outcome": "",
        "PORound": 0,
        "PaceAdjust": "N",
        "PerMode": "PerGame",
        "Period": 0,
        "PlayerExperience": "",
        "PlayerPosition": "",
        "PlusMinus": "N",
        "Rank": "N",
        "Season": season,
        "SeasonSegment": "",
        "SeasonType": "Regular Season",
        "ShotClockRange": "",
        "StarterBench": "",
        "TeamID": 0,
        "TwoWay": 0,
        "VsConference": "",
        "VsDivision": "",
        "Weight": "",
    }

    query = _url.urlencode(params, doseq=True)
    url = f"{base}?{query}"

    curl_cmd = [
        "curl", "--http2", "--compressed", "-m", "25", "-sS",
        "-H", f"User-Agent: {NBA_REQUEST_HEADERS['User-Agent']}",
        "-H", "Accept: application/json, text/plain, */*",
        "-H", "Referer: https://www.nba.com/",
        "-H", "Origin: https://www.nba.com",
        url,
    ]

    try:
        result = subprocess.run(curl_cmd, check=True, capture_output=True, text=True)
        data = json.loads(result.stdout)
        result_sets = data.get("resultSets") or [data.get("resultSet")]
        result_sets = [r for r in result_sets if r]
        cols = result_sets[0]["headers"]
        rows = result_sets[0]["rowSet"]
        df = pd.DataFrame(rows, columns=cols)
    except Exception:
        # Fallback to nba_api (may work on some networks)
        stats = LeagueDashPlayerStats(
            season=season,
            per_mode_detailed="PerGame",
            timeout=20,
            headers=NBA_REQUEST_HEADERS,
        )
        df = stats.get_data_frames()[0]

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"player_stats_{season.replace('/', '-').replace(' ', '_')}_snapshot.csv"
    df.to_csv(out_path, index=False)
    return out_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seasons", nargs="*", help="Explicit seasons like 2021-22 2022-23")
    args = parser.parse_args()

    seasons = args.seasons or generate_last_n_seasons(5)
    root = Path(__file__).resolve().parents[1]
    out_dir = root / "sample_data"

    written = []
    for s in seasons:
        p = fetch_season_csv(s, out_dir)
        print(f"Wrote {p}")
        written.append(p)

    print("Done:")
    for p in written:
        print(" -", p)


if __name__ == "__main__":
    main()


