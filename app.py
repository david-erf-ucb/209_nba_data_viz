from flask import Flask
import json
import os
import pandas as pd
import numpy as np
import altair as alt
app = Flask(__name__)

@app.get("/")
def hello():
    return "Hello from Flask on EC2!"


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

def _load_shots_df() -> pd.DataFrame:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_dir, "data", "pbp_small.parquet")
    if os.path.exists(data_path):
        df_small = pd.read_parquet(data_path)
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
    df_small["timeActual"] = pd.to_datetime(df_small["timeActual"])  # ensure dtype
    return df_small

def _build_shot_chart_spec(df: pd.DataFrame) -> dict:
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
    max_games = int(df["game_number"].max()) if len(df) else 1
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

    return chart.to_dict()

@app.get("/shots")
def shots():
    df = _load_shots_df()
    chart_spec = _build_shot_chart_spec(df)
    return (
        """
        <!doctype html>
        <html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n<title>NBA Shot Chart</title>\n<style>\n  html, body { margin: 0; padding: 0; height: 100%; }\n  .frame-wrap { height: 100vh; width: 100%; display: flex; flex-direction: column; }\n  header { padding: 12px 16px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; border-bottom: 1px solid #eee; }\n  header h1 { font-size: 18px; margin: 0; }\n  #vis { flex: 1; display: flex; align-items: center; justify-content: center; padding: 16px; }\n</style>\n\n<script src=\"https://cdn.jsdelivr.net/npm/vega@5\"></script>\n<script src=\"https://cdn.jsdelivr.net/npm/vega-lite@5\"></script>\n<script src=\"https://cdn.jsdelivr.net/npm/vega-embed@6\"></script>\n</head>\n<body>\n  <div class=\"frame-wrap\">\n    <header>\n      <h1>NBA Shot Chart</h1>\n    </header>\n    <div id=\"vis\"></div>\n  </div>\n  <script>\n    const spec = REPLACE_SPEC;\n    vegaEmbed('#vis', spec, {actions: false});\n  </script>\n</body>\n</html>
        """
        .replace("REPLACE_SPEC", json.dumps(chart_spec))
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
