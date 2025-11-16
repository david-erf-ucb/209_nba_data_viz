import argparse
from pathlib import Path
import httpx
import pandas as pd

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


def fetch_to_csv(season: str) -> Path:
    url = "https://stats.nba.com/stats/leaguedashplayerstats"
    params = {
        "LeagueID": "00",
        "Season": season,
        "PerMode": "PerGame",
        "SeasonType": "Regular Season",
        "MeasureType": "Base",
    }
    with httpx.Client(http2=True, headers=NBA_REQUEST_HEADERS, timeout=20) as client:
        resp = client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
        result = data.get("resultSets") or [data.get("resultSet")]
        result = [r for r in result if r]
        cols = result[0]["headers"]
        rows = result[0]["rowSet"]
        df = pd.DataFrame(rows, columns=cols)

    out_dir = Path(__file__).resolve().parents[1] / "sample_data"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"player_stats_{season.replace('/', '-').replace(' ', '_')}_snapshot.csv"
    df.to_csv(out_file, index=False)
    return out_file


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", default="2023-24")
    args = parser.parse_args()
    path = fetch_to_csv(args.season)
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()



