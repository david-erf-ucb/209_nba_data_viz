# ============================================
# Interactive NBA shot chart in Altair (Colab-friendly)
# - player dropdown
# - rolling 40-game slider
# - optional play() function (not auto-run)
# ============================================

import pandas as pd
import numpy as np
import altair as alt
from IPython.display import display, clear_output
import ipywidgets as widgets
import time

# --------------------------------------------------------
# 0) ASSUMPTION:
# You already have a dataframe called `pbp_only_coords_shots_half`
# from earlier steps, e.g.:
#   pbp_only_coords_shots = play_by_play_combined.dropna(subset=['x', 'y', 'shotResult'])
#   pbp_only_coords_shots_half = pbp_only_coords_shots[pbp_only_coords_shots['x'] <= 50]
# We'll start from that to stay light.
# --------------------------------------------------------

# 1) keep only columns we actually need
cols_needed = [
    'playerNameI', 'gameid', 'timeActual', 'x', 'y',
    'shotResult', 'Season'
]
df_small = pbp_only_coords_shots_half[cols_needed].copy()

# cast some to category to save RAM
for c in ['playerNameI', 'gameid', 'shotResult', 'Season']:
    df_small[c] = df_small[c].astype('category')

# ensure datetime
df_small['timeActual'] = pd.to_datetime(df_small['timeActual'])

# 2) compute per-player game_number
player_games = (
    df_small[['playerNameI', 'gameid', 'timeActual']]
    .dropna(subset=['timeActual'])
    .drop_duplicates(['playerNameI', 'gameid'])
    .sort_values(['playerNameI', 'timeActual', 'gameid'])
)

player_games['game_number'] = player_games.groupby('playerNameI').cumcount() + 1

df_small = df_small.merge(
    player_games[['playerNameI', 'gameid', 'game_number']],
    on=['playerNameI', 'gameid'],
    how='left'
)

# 3) Altair setup
alt.data_transformers.disable_max_rows()
alt.renderers.enable("html")

# list of players (you can limit this if too long)
player_options = sorted(df_small['playerNameI'].dropna().unique().tolist())
default_player = player_options[0]

# --- params: player dropdown + slider ---
player_dropdown = alt.binding_select(options=player_options, name='Player: ')
player_param = alt.param('player_sel', bind=player_dropdown, value=default_player)

window_size = 40
max_games_overall = int(df_small['game_number'].max())
slider_max = max(1, max_games_overall - window_size + 1)

window_slider = alt.binding_range(
    min=1, max=slider_max, step=1, name='Start game #: '
)
window_param = alt.param('gstart', bind=window_slider, value=1)

# 4) build the half-court directly in display coords (0..100, 4..50)
def make_court_df():
    # baseline
    baseline = pd.DataFrame({"x": [0, 100], "y": [4, 4], "group": ["baseline", "baseline"]})
    # sidelines
    left_sideline = pd.DataFrame({"x": [0, 0], "y": [4, 50], "group": ["left_sideline", "left_sideline"]})
    right_sideline = pd.DataFrame({"x": [100, 100], "y": [4, 50], "group": ["right_sideline", "right_sideline"]})
    # outer paint
    outer_paint = pd.DataFrame({
        "x": [34, 66, 66, 34, 34],
        "y": [4, 4, 25.3, 25.3, 4],
        "group": ["outer_paint"] * 5
    })
    # inner paint
    inner_paint = pd.DataFrame({
        "x": [38, 62, 62, 38, 38],
        "y": [4, 4, 25.3, 25.3, 4],
        "group": ["inner_paint"] * 5
    })
    # restricted arc
    t = np.linspace(0, np.pi, 80)
    restricted = pd.DataFrame({
        "x": 50 + 8 * np.cos(t),
        "y": 4 + 4.5 * np.sin(t),
        "group": ["restricted"] * len(t)
    })
    # free-throw top arc
    t2 = np.linspace(0, np.pi, 80)
    ft_top = pd.DataFrame({
        "x": 50 + 12 * np.cos(t2),
        "y": 20 + 6.7 * np.sin(t2),
        "group": ["ft_top"] * len(t2)
    })
    # corner threes
    corner_left = pd.DataFrame({"x": [6, 6], "y": [4, 14.4], "group": ["corner_left", "corner_left"]})
    corner_right = pd.DataFrame({"x": [94, 94], "y": [4, 14.4], "group": ["corner_right", "corner_right"]})
    # 3pt arc
    theta = np.linspace(np.deg2rad(22), np.deg2rad(158), 120)
    three_arc = pd.DataFrame({
        "x": 50 + 47.5 * np.cos(theta),
        "y": 4 + 26.65 * np.sin(theta),
        "group": ["three_arc"] * len(theta)
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
        three_arc
    ], ignore_index=True)
    return court_df

court_df = make_court_df()

court_layer = (
    alt.Chart(court_df)
    .mark_line(color='black', strokeWidth=1)
    .encode(
        x=alt.X('x:Q', scale=alt.Scale(domain=[0, 100]), axis=None),
        y=alt.Y('y:Q', scale=alt.Scale(domain=[4, 50]), axis=None),
        detail='group:N'
    )
)

shots_layer = (
    alt.Chart(df_small)
    .mark_circle(size=60)
    .encode(
        x=alt.X('y:Q', scale=alt.Scale(domain=[0, 100]), axis=None),
        y=alt.Y('x:Q', scale=alt.Scale(domain=[4, 50]), axis=None),
        color=alt.Color(
            'shotResult:N',
            scale=alt.Scale(domain=['Made', 'Missed'], range=['green', 'red']),
            legend=alt.Legend(title='Result')
        ),
        tooltip=['playerNameI:N', 'gameid:N', 'shotResult:N', 'game_number:Q', 'timeActual:T']
    )
    .transform_filter('datum.playerNameI == player_sel')
    .transform_filter('datum.game_number >= gstart && datum.game_number < gstart + 40')
)

base_chart = (
    (court_layer + shots_layer)
    .add_params(player_param, window_param)
    .properties(
        width=700,
        height=400,
        title='Rolling 40-game Shot Chart'
    )
    .configure_view(stroke=None)
    .configure_axis(grid=False, domain=False, ticks=False, labels=False)
)

# show the interactive chart
display(base_chart)

# --------------------------------------------------------
# 5) Optional: Play / Stop widgets (safe version)
#    - DOES NOT auto-run
#    - call animate() when you actually want to play
# --------------------------------------------------------
play_button = widgets.Button(description="▶ Play")
stop_button = widgets.Button(description="■ Stop")
speed_slider = widgets.FloatSlider(
    value=0.4, min=0.1, max=1.5, step=0.1, description='Speed (s):'
)
display(widgets.HBox([play_button, stop_button, speed_slider]))

# mutable flag so buttons can change it
playing = {"value": False}

def on_play_clicked(b):
    playing["value"] = True

def on_stop_clicked(b):
    playing["value"] = False

play_button.on_click(on_play_clicked)
stop_button.on_click(on_stop_clicked)

def animate():
    """
    Safe, bounded animation:
    - loops over the valid slider range once
    - checks stop flag every step
    - re-renders the chart with updated gstart
    Run: animate()
    """
    for start in range(1, slider_max + 1):
        if not playing["value"]:
            break
        # rebuild chart with this start
        ch = (
            (court_layer + shots_layer)
            .add_params(
                player_param,
                alt.param('gstart', value=start)   # override slider
            )
            .properties(
                width=700,
                height=400,
                title='Rolling 40-game Shot Chart'
            )
            .configure_view(stroke=None)
            .configure_axis(grid=False, domain=False, ticks=False, labels=False)
        )
        clear_output(wait=True)
        display(ch)
        display(widgets.HBox([play_button, stop_button, speed_slider]))
        time.sleep(speed_slider.value)

# NOTE:
# - This cell does NOT call animate() automatically, so it won't time out.
# - When you're ready, click ▶ Play, then run:
#       animate()
#   in a new cell, or call it from here manually.

# app.py
from flask import Flask, render_template
import pandas as pd
import numpy as np
import altair as alt
import json
import os

app = Flask(__name__)

# ------------------------------------------------
# figure out base dir (works in Flask AND Colab)
# ------------------------------------------------
if "__file__" in globals():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
else:
    # we're probably in a notebook / Colab
    BASE_DIR = os.getcwd()

# try to load a pre-saved file
DATA_PATH = os.path.join(BASE_DIR, "data", "pbp_small.parquet")

if os.path.exists(DATA_PATH):
    df_small = pd.read_parquet(DATA_PATH)
else:
    # fallback dummy data so the route still works
    df_small = pd.DataFrame({
        "playerNameI": ["V. Wembanyama"] * 5,
        "gameid": ["G1"] * 5,
        "timeActual": pd.date_range("2024-01-01", periods=5),
        "x": [10, 20, 30, 40, 45],
        "y": [20, 30, 50, 70, 10],
        "shotResult": ["Made", "Missed", "Made", "Missed", "Made"],
        "Season": ["2023-24"] * 5,
        "game_number": [1, 2, 3, 4, 5],
    })

df_small["timeActual"] = pd.to_datetime(df_small["timeActual"])

def make_court_df():
    baseline = pd.DataFrame({"x": [0, 100], "y": [4, 4], "group": ["baseline", "baseline"]})
    left_sideline = pd.DataFrame({"x": [0, 0], "y": [4, 50], "group": ["left_sideline", "left_sideline"]})
    right_sideline = pd.DataFrame({"x": [100, 100], "y": [4, 50], "group": ["right_sideline", "right_sideline"]})
    outer_paint = pd.DataFrame({
        "x": [34, 66, 66, 34, 34],
        "y": [4, 4, 25.3, 25.3, 4],
        "group": ["outer_paint"] * 5
    })
    inner_paint = pd.DataFrame({
        "x": [38, 62, 62, 38, 38],
        "y": [4, 4, 25.3, 25.3, 4],
        "group": ["inner_paint"] * 5
    })
    t = np.linspace(0, np.pi, 80)
    restricted = pd.DataFrame({
        "x": 50 + 8 * np.cos(t),
        "y": 4 + 4.5 * np.sin(t),
        "group": ["restricted"] * len(t)
    })
    t2 = np.linspace(0, np.pi, 80)
    ft_top = pd.DataFrame({
        "x": 50 + 12 * np.cos(t2),
        "y": 20 + 6.7 * np.sin(t2),
        "group": ["ft_top"] * len(t2)
    })
    corner_left = pd.DataFrame({"x": [6, 6], "y": [4, 14.4], "group": ["corner_left", "corner_left"]})
    corner_right = pd.DataFrame({"x": [94, 94], "y": [4, 14.4], "group": ["corner_right", "corner_right"]})
    theta = np.linspace(np.deg2rad(22), np.deg2rad(158), 120)
    three_arc = pd.DataFrame({
        "x": 50 + 47.5 * np.cos(theta),
        "y": 4 + 26.65 * np.sin(theta),
        "group": ["three_arc"] * len(theta)
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
        three_arc
    ], ignore_index=True)
    return court_df

def build_chart_spec(df):
    alt.data_transformers.disable_max_rows()

    court_df = make_court_df()

    players = sorted(df["playerNameI"].dropna().unique().tolist())
    player_dropdown = alt.binding_select(options=players, name="Player: ")
    player_param = alt.param("player_sel", bind=player_dropdown, value=players[0])

    window_size = 40
    max_games = int(df["game_number"].max())
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

@app.route("/")
def index():
    return "Hello from the NBA viz app! Go to /shots"

@app.route("/shots")
def shots():
    chart_spec = build_chart_spec(df_small)
    return render_template("shots.html", chart_spec=json.dumps(chart_spec))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8001, debug=True)



