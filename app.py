from flask import Flask, request
import json
import os
import pandas as pd
import numpy as np
import altair as alt
from typing import Optional
try:
    import duckdb  # optional; used when partitioned dataset is available
except Exception:  # pragma: no cover
    duckdb = None
app = Flask(__name__)

@app.get("/")
def hello():
    return (
        """
        <!doctype html>
        <html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n<title>NBA Data Visualizations</title>\n<style>\n  :root { --bg:#0b1020; --card:#131a33; --text:#f2f4ff; --muted:#aab1d6; --accent:#5b8cff; }\n  html, body { margin:0; padding:0; height:100%; background:var(--bg); color:var(--text); }\n  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }\n  .wrap { min-height:100vh; display:flex; flex-direction:column; }\n  header { padding:24px 20px; border-bottom:1px solid rgba(255,255,255,0.08); }\n  header h1 { margin:0; font-size:22px; letter-spacing:0.2px; }\n  header p { margin:6px 0 0; color:var(--muted); font-size:14px; }\n  .grid { display:grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap:16px; padding:20px; max-width:1000px; width:100%; margin:0 auto; }\n  .card { background:var(--card); border:1px solid rgba(255,255,255,0.08); border-radius:12px; padding:20px; display:flex; flex-direction:column; gap:12px; box-shadow: 0 6px 18px rgba(0,0,0,0.25); }\n  .card h2 { margin:0; font-size:18px; }\n  .card p { margin:0; color:var(--muted); line-height:1.45; }\n  .actions { margin-top:auto; }\n  .btn { display:inline-block; background:var(--accent); color:white; text-decoration:none; padding:10px 14px; border-radius:8px; font-weight:600; }\n  .btn.secondary { background:transparent; border:1px solid rgba(255,255,255,0.18); color:var(--text); margin-left:8px; }\n  footer { padding:16px 20px; color:var(--muted); font-size:12px; text-align:center; border-top:1px solid rgba(255,255,255,0.08); margin-top:auto; }\n</style>\n</head>\n<body>\n  <div class=\"wrap\">\n    <header>\n      <h1>NBA Data Visualizations</h1>\n      <p>Select a tool below to explore player stats and shot charts.</p>\n    </header>\n    <main class=\"grid\">\n      <section class=\"card\">\n        <h2>Player Stats Explorer</h2>\n        <p>Interactive Streamlit app to explore relationships between player metrics across seasons and teams.</p>\n        <div class=\"actions\">\n          <a class=\"btn\" href=\"/explorer\">Open Explorer</a>\n        </div>\n      </section>\n      <section class=\"card\">\n        <h2>Rolling 40-game Shot Chart</h2>\n        <p>Altair-based half-court shot chart with player filter and animated rolling window.</p>\n        <div class=\"actions\">\n          <a class=\"btn\" href=\"/shots\">View Shot Chart</a>\n        </div>\n      </section>\n    </main>\n    <footer>\n      Served by Flask at /, Streamlit proxied at /nba/.\n    </footer>\n  </div>\n</body>\n</html>
        """
    )


@app.get("/explorer")
def explorer():
    return (
        """
        <!doctype html>
        <html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n<title>NBA Player Stats Explorer</title>\n<style>\n  html, body { margin: 0; padding: 0; height: 100%; }\n  .frame-wrap { height: 100vh; width: 100%; display: flex; flex-direction: column; }\n  header { padding: 12px 16px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; border-bottom: 1px solid #eee; }\n  header h1 { font-size: 18px; margin: 0; }\n  .frame { flex: 1; border: 0; width: 100%; }\n</style>\n</head>\n<body>\n  <div class=\"frame-wrap\">\n    <header>\n      <h1>NBA Player Stats Explorer</h1>\n    </header>\n    <iframe class=\"frame\" src=\"/nba/\" allow=\"fullscreen\" loading=\"lazy\"></iframe>\n  </div>\n</body>\n</html>
        """
    )

def _make_court_df():
    baseline = pd.DataFrame({"x": [0, 100], "y": [4, 4], "group": ["baseline", "baseline"]})
    left_sideline = pd.DataFrame({"x": [0, 0], "y": [4, 50], "group": ["left_sideline", "left_sideline"]})
    right_sideline = pd.DataFrame({"x": [100, 100], "y": [4, 50], "group": ["right_sideline", "right_sideline"]})
    outer_paint = pd.DataFrame({
        "x": [34, 66, 66, 34, 34],
        "y": [4, 4, 25.3, 25.3, 4],
        "group": ["outer_paint"] * 5,
    })
    inner_paint = pd.DataFrame({
        "x": [38, 62, 62, 38, 38],
        "y": [4, 4, 25.3, 25.3, 4],
        "group": ["inner_paint"] * 5,
    })
    t = np.linspace(0, np.pi, 80)
    restricted = pd.DataFrame({
        "x": 50 + 8 * np.cos(t),
        "y": 4 + 4.5 * np.sin(t),
        "group": ["restricted"] * len(t),
    })
    t2 = np.linspace(0, np.pi, 80)
    ft_top = pd.DataFrame({
        "x": 50 + 12 * np.cos(t2),
        "y": 20 + 6.7 * np.sin(t2),
        "group": ["ft_top"] * len(t2),
    })
    corner_left = pd.DataFrame({"x": [6, 6], "y": [4, 14.4], "group": ["corner_left", "corner_left"]})
    corner_right = pd.DataFrame({"x": [94, 94], "y": [4, 14.4], "group": ["corner_right", "corner_right"]})
    theta = np.linspace(np.deg2rad(22), np.deg2rad(158), 120)
    three_arc = pd.DataFrame({
        "x": 50 + 47.5 * np.cos(theta),
        "y": 4 + 26.65 * np.sin(theta),
        "group": ["three_arc"] * len(theta),
    })

    court_df = pd.concat([
        baseline,
        left_sideline,
        right_sideline,
        outer_paint,
        inner_paint,
        restricted,
        ft_top,
        corner_left,
        corner_right,
        three_arc,
    ], ignore_index=True)
    return court_df

def _dataset_dir() -> str:
    """
    Resolve the preferred dataset directory (partitioned parquet).
    Priority:
      1) NBA_PBP_DATASET_DIR env var (explicit override)
      2) repo sample_data/partitioned_shots (Option B symlink target)
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    explicit = os.environ.get("NBA_PBP_DATASET_DIR", "").strip()
    if explicit:
        return explicit
    return os.path.join(base_dir, "sample_data", "partitioned_shots")

def _query_shots_df(season: Optional[str] = None, player: Optional[str] = None, limit_points: int = 200_000) -> pd.DataFrame:
    """
    Query from partitioned parquet dataset using DuckDB with projection/predicate pushdown.
    Requires DuckDB and a valid dataset directory. If season is None, chooses the max Season.
    """
    if duckdb is None:
        raise RuntimeError("DuckDB not available")

    dataset = _dataset_dir()
    if not os.path.isdir(dataset):
        raise FileNotFoundError(f"Partitioned dataset directory not found: {dataset}")

    # Build a glob path for DuckDB to scan partitions
    glob_path = os.path.join(dataset, "**")

    # Determine default Season (latest) if not provided
    if season is None:
        season_df = duckdb.sql("""
            SELECT MAX(Season) AS Season
            FROM read_parquet(?, hive_partitioning=1)
        """, params=[glob_path]).df()
        season = season_df.iloc[0]["Season"]

    # Build parameterized SQL
    sql = """
      SELECT playerNameI, gameid, timeActual, x, y, shotResult, Season
      FROM read_parquet(?, hive_partitioning=1)
      WHERE Season = ?
        AND x IS NOT NULL AND y IS NOT NULL
        AND timeActual IS NOT NULL
        AND shotResult IS NOT NULL
        AND x BETWEEN 0 AND 100
        AND y BETWEEN 0 AND 100
      {player_filter}
      LIMIT ?
    """
    player_filter = "AND playerNameI = ?" if player else ""
    params = [glob_path, season] + ([player] if player else []) + [int(limit_points)]
    df_small = duckdb.sql(sql.format(player_filter=player_filter), params=params).df()

    # Ensure datetime
    if "timeActual" in df_small.columns:
        df_small["timeActual"] = pd.to_datetime(df_small["timeActual"])

    # Backfill game_number (per player chronological order)
    if {"playerNameI", "gameid", "timeActual"}.issubset(df_small.columns):
        player_games = (
            df_small[["playerNameI", "gameid", "timeActual"]]
            .dropna(subset=["timeActual"])
            .drop_duplicates(["playerNameI", "gameid"])
            .sort_values(["playerNameI", "timeActual", "gameid"])
        )
        player_games["game_number"] = player_games.groupby("playerNameI").cumcount() + 1
        df_small = df_small.merge(
            player_games[["playerNameI", "gameid", "game_number"]],
            on=["playerNameI", "gameid"],
            how="left",
        )
    return df_small

def _load_shots_df() -> pd.DataFrame:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # Prefer explicit path via env var; fallback to repo sample_data
    parquet_path = os.environ.get(
        "NBA_PBP_PARQUET_PATH",
        os.path.join(base_dir, "sample_data", "nba_pbp_combined.parquet"),
    )
    if os.path.exists(parquet_path):
        df_small = pd.read_parquet(parquet_path)
    else:
        df_small = pd.DataFrame({
            "playerNameI": ["V. Wembanyama"] * 5,
            "gameid": ["G1"] * 5,
            "timeActual": pd.date_range("2024-01-01", periods=5),
            "x": [10, 20, 30, 40, 45],
            "y": [20, 30, 50, 42, 18],
            "shotResult": ["Made", "Missed", "Made", "Missed", "Made"],
            "Season": ["2023-24"] * 5,
            "game_number": [1, 2, 3, 4, 5],
        })
    # Ensure datetime
    if "timeActual" in df_small.columns:
        df_small["timeActual"] = pd.to_datetime(df_small["timeActual"])  # ensure dtype
    # Backfill game_number if missing
    if "game_number" not in df_small.columns and {"playerNameI", "gameid", "timeActual"}.issubset(df_small.columns):
        player_games = (
            df_small[["playerNameI", "gameid", "timeActual"]]
            .dropna(subset=["timeActual"])  # only valid timestamps contribute
            .drop_duplicates(["playerNameI", "gameid"])  # one row per game
            .sort_values(["playerNameI", "timeActual", "gameid"])
        )
        player_games["game_number"] = player_games.groupby("playerNameI").cumcount() + 1
        df_small = df_small.merge(
            player_games[["playerNameI", "gameid", "game_number"]],
            on=["playerNameI", "gameid"],
            how="left",
        )
    return df_small

def _build_shot_chart_spec(df: pd.DataFrame):
    alt.data_transformers.disable_max_rows()

    court_df = _make_court_df()

    players = sorted(df["playerNameI"].dropna().unique().tolist())
    if not players:
        players = ["Player"]
        df = pd.DataFrame({
            "playerNameI": players * 1,
            "gameid": ["G1"],
            "timeActual": pd.date_range("2024-01-01", periods=1),
            "x": [30],
            "y": [25],
            "shotResult": ["Made"],
            "Season": ["2023-24"],
            "game_number": [1],
        })

    player_dropdown = alt.binding_select(options=players, name="Player: ")
    player_param = alt.param("player_sel", bind=player_dropdown, value=players[0])

    window_size = 40
    # Robust slider upper bound even if game_number has nulls
    max_game_val = pd.to_numeric(df.get("game_number"), errors="coerce").max() if len(df) else 1
    max_games = int(max_game_val) if pd.notna(max_game_val) else 1
    slider_max = max(1, max_games - window_size + 1)
    window_slider = alt.binding_range(min=1, max=slider_max, step=1, name="Start game #: ")
    window_param = alt.param("gstart", bind=window_slider, value=1)

    court_layer = (
        alt.Chart(court_df)
        .mark_line(color="black", strokeWidth=1)
        .encode(
            x=alt.X("x:Q", scale=alt.Scale(domain=[0, 100]), axis=None),
            y=alt.Y("y:Q", scale=alt.Scale(domain=[4, 50]), axis=None),
            detail="group:N",
        )
    )

    shots_layer = (
        alt.Chart(df)
        .mark_circle(size=60)
        .encode(
            x=alt.X("y:Q", scale=alt.Scale(domain=[0, 100]), axis=None),
            y=alt.Y("x:Q", scale=alt.Scale(domain=[4, 50]), axis=None),
            color=alt.Color(
                "shotResult:N",
                scale=alt.Scale(domain=["Made", "Missed"], range=["green", "red"]),
                legend=alt.Legend(title="Result"),
            ),
            tooltip=["playerNameI:N", "gameid:N", "shotResult:N", "game_number:Q", "timeActual:T"],
        )
        .transform_filter("datum.playerNameI == player_sel")
        .transform_filter("datum.game_number >= gstart && datum.game_number < gstart + 40")
    )

    chart = (
        (court_layer + shots_layer)
        .add_params(player_param, window_param)
        .properties(width=700, height=400, title="Rolling 40-game Shot Chart")
        .configure_view(stroke=None)
        .configure_axis(grid=False, domain=False, ticks=False, labels=False)
    )

    return chart.to_dict(), slider_max

@app.get("/shots")
def shots():
    # Read optional query params
    season_param = request.args.get("season") or None
    player_param = request.args.get("player") or None
    try:
        limit_param = int(request.args.get("limit", "50000"))
    except Exception:
        limit_param = 50000
    limit_param = max(1000, min(limit_param, 200_000))  # safety bounds

    # Prefer fast, memory-safe DuckDB path if available; otherwise fallback to legacy loader.
    try:
        df = _query_shots_df(season=season_param, player=player_param, limit_points=limit_param)
    except Exception:
        # Lightweight fallback: avoid loading full parquet to prevent OOM
        df = pd.DataFrame({
            "playerNameI": pd.Series(dtype="object"),
            "gameid": pd.Series(dtype="object"),
            "timeActual": pd.Series(dtype="datetime64[ns]"),
            "x": pd.Series(dtype="float"),
            "y": pd.Series(dtype="float"),
            "shotResult": pd.Series(dtype="object"),
            "Season": pd.Series(dtype="object"),
            "game_number": pd.Series(dtype="int"),
        })
    chart_spec, slider_max = _build_shot_chart_spec(df)
    return (
        """
        <!doctype html>
        <html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n<title>NBA Shot Chart</title>\n<style>\n  html, body { margin: 0; padding: 0; height: 100%; }\n  .frame-wrap { height: 100vh; width: 100%; display: flex; flex-direction: column; }\n  header { padding: 12px 16px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; border-bottom: 1px solid #eee; }\n  header h1 { font-size: 18px; margin: 0; }\n  .controls { padding: 8px 16px; }\n  #vis { flex: 1; display: flex; align-items: center; justify-content: center; padding: 16px; }\n</style>\n\n<script src=\"https://cdn.jsdelivr.net/npm/vega@5\"></script>\n<script src=\"https://cdn.jsdelivr.net/npm/vega-lite@5\"></script>\n<script src=\"https://cdn.jsdelivr.net/npm/vega-embed@6\"></script>\n</head>\n<body>\n  <div class=\"frame-wrap\">\n    <header>\n      <h1>NBA Shot Chart</h1>\n    </header>\n    <div class=\"controls\">\n      <button id=\"play\">▶ Play</button>\n      <button id=\"pause\">❚❚ Pause</button>\n    </div>\n    <div id=\"vis\"></div>\n  </div>\n  <script>\n    const spec = REPLACE_SPEC;\n    const SLIDER_MAX = REPLACE_MAX;\n    vegaEmbed('#vis', spec, {actions: false}).then((res) => {\n      const view = res.view;\n      let running = false;\n      let current = 1;\n      const stepMs = 400;\n      function tick(){\n        if(!running) return;\n        current = current >= SLIDER_MAX ? 1 : current + 1;\n        view.signal('gstart', current).run();\n        setTimeout(tick, stepMs);\n      }\n      document.getElementById('play').addEventListener('click', () => {\n        if(!running){ running = true; tick(); }\n      });\n      document.getElementById('pause').addEventListener('click', () => { running = false; });\n    });\n  </script>\n</body>\n</html>
        """
        .replace("REPLACE_SPEC", json.dumps(chart_spec))
        .replace("REPLACE_MAX", json.dumps(slider_max))
        )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
