# --- nba_scatter_live_app.py ---
import pandas as pd
import altair as alt
import streamlit as st
from nba_api.stats.endpoints import LeagueDashPlayerStats
import numpy as np

# --- 1️⃣ Load NBA Data ---
@st.cache_data
def load_nba_data(season="2023-24"):
    """Load NBA player statistics (per game) for selected season."""
    stats = LeagueDashPlayerStats(season=season, per_mode_detailed="PerGame")
    df = stats.get_data_frames()[0]
    return df


# --- 2️⃣ Streamlit UI ---
st.title("🏀 NBA Player Stats Explorer (Interactive Dashboard)")
st.markdown("""
Explore player performance metrics interactively.  
You can brush the scatterplot to see linked team summaries,  
and use the dropdown below to inspect specific players’ stats.
""")

# --- 3️⃣ Season selection ---
seasons = [f"{yr}-{str(yr+1)[-2:]}" for yr in range(2019, 2025)][::-1]
selected_season = st.selectbox("Select Season", seasons, index=0)

# --- 4️⃣ Load data ---
with st.spinner(f"Loading {selected_season} data..."):
    df = load_nba_data(selected_season)
st.success(f"✅ Loaded {len(df)} player records for {selected_season}.")

# --- 5️⃣ Clean & filter numeric columns ---
numeric_cols = df.select_dtypes(include='number').columns.tolist()
excluded_keywords = ["RANK", "NBA_FANTASY", "WNBA_FANTASY", "_ID", "CF", "GROUP"]
excluded_specific = ["W", "L", "W_PCT", "BLKA", "PFD", "DD2", "TD3", "TEAM_COUNT"]
meaningful_cols = [
    c for c in numeric_cols
    if not any(k in c for k in excluded_keywords) and c not in excluded_specific
]

friendly_names = {
    "AGE": "Player Age", "GP": "Games Played", "MIN": "Minutes per Game",
    "FGM": "Field Goals Made per Game", "FGA": "Field Goals Attempted per Game",
    "FG_PCT": "Field Goal Percentage", "FG3M": "Three-Point Field Goals Made per Game",
    "FG3A": "Three-Point Field Goals Attempted per Game", "FG3_PCT": "Three-Point Percentage",
    "FTM": "Free Throws Made per Game", "FTA": "Free Throws Attempted per Game",
    "FT_PCT": "Free Throw Percentage", "OREB": "Offensive Rebounds per Game",
    "DREB": "Defensive Rebounds per Game", "REB": "Total Rebounds per Game",
    "AST": "Assists per Game", "STL": "Steals per Game", "BLK": "Blocks per Game",
    "TOV": "Turnovers per Game", "PF": "Personal Fouls per Game", "PTS": "Points per Game",
    "PLUS_MINUS": "Plus/Minus per Game",
}
display_to_column = {friendly_names.get(c, c.replace("_", " ").title()): c for c in meaningful_cols}
display_names = list(display_to_column.keys())

# --- 6️⃣ Team Filter ---
teams = ["All Teams"] + sorted(df["TEAM_ABBREVIATION"].unique())
selected_team = st.selectbox("Filter by Team", teams, index=0)
if selected_team != "All Teams":
    df = df[df["TEAM_ABBREVIATION"] == selected_team]
    st.info(f"Showing {len(df)} players from {selected_team}.")

# --- 7️⃣ Variable selectors ---
x_display = st.selectbox("Select X-axis variable", display_names,
                         index=display_names.index("Three-Point Percentage") if "Three-Point Percentage" in display_names else 0)
y_display = st.selectbox("Select Y-axis variable", display_names,
                         index=display_names.index("Field Goal Percentage") if "Field Goal Percentage" in display_names else 1)
x_var, y_var = display_to_column[x_display], display_to_column[y_display]

# --- 8️⃣ Prepare data ---
df_clean = df[[x_var, y_var, "PLAYER_NAME", "TEAM_ABBREVIATION", "PTS", "AST", "REB"]].dropna()
df_clean[x_var] = pd.to_numeric(df_clean[x_var], errors="coerce")
df_clean[y_var] = pd.to_numeric(df_clean[y_var], errors="coerce")
df_clean = df_clean.dropna(subset=[x_var, y_var])

# --- 9️⃣ Brushing & main scatterplot ---
brush = alt.selection_interval(encodings=['x', 'y'])

scatter = (
    alt.Chart(df_clean)
    .mark_circle(size=70, opacity=0.7)
    .encode(
        x=alt.X(f"{x_var}:Q", title=x_display),
        y=alt.Y(f"{y_var}:Q", title=y_display),
        tooltip=["PLAYER_NAME", "TEAM_ABBREVIATION", x_var, y_var],
        color=alt.condition(brush, alt.value("steelblue"), alt.value("lightgray")),
    )
    .add_params(brush)
    .properties(width=700, height=450,
                title=f"{y_display} vs {x_display} ({selected_season}{'' if selected_team == 'All Teams' else ' - ' + selected_team})")
)

# --- 🔟 Linked Views ---
# 1️⃣ Team Composition Bar Chart (# players per team)
team_bars = (
    alt.Chart(df_clean)
    .mark_bar(color='steelblue')
    .encode(
        y=alt.Y('TEAM_ABBREVIATION:N', sort='-x', title='Team'),
        x=alt.X('count():Q', title='Number of Selected Players'),
        tooltip=['TEAM_ABBREVIATION', alt.Tooltip('count():Q', title='Players Selected')]
    )
    .transform_filter(brush)
    .properties(width=700, height=250, title='Team Composition of Selected Players')
)

# 2️⃣ Adaptive Stat Histogram
if 'PTS' not in [x_var, y_var]:
    stat_var, stat_title = 'PTS', 'Points per Game'
elif 'AST' not in [x_var, y_var]:
    stat_var, stat_title = 'AST', 'Assists per Game'
else:
    stat_var, stat_title = 'REB', 'Rebounds per Game'

stat_hist = (
    alt.Chart(df_clean)
    .mark_bar(color='orange', opacity=0.8)
    .encode(
        x=alt.X(f'{stat_var}:Q', bin=alt.Bin(maxbins=20), title=stat_title),
        y=alt.Y('count():Q', title='Number of Players'),
        tooltip=[alt.Tooltip('count():Q', title='Players')]
    )
    .transform_filter(brush)
    .properties(width=700, height=250, title=f'{stat_title} Distribution of Selected Players')
)

# --- 11️⃣ Combine Charts ---
linked_charts = scatter & team_bars & stat_hist
st.altair_chart(linked_charts, use_container_width=True)

# --- 12️⃣ Table Section (Filtered Players Automatically Shown) ---
st.markdown("### 📋 Filtered Player Stats")

# Select relevant columns for display
display_cols = ["PLAYER_NAME", "TEAM_ABBREVIATION", "PTS", "AST", "REB", x_var, y_var]

# Sort players by Points per Game by default
table_df = df_clean[display_cols].sort_values(by="PTS", ascending=False).reset_index(drop=True)

# Display the table
st.dataframe(
    table_df.style.format(precision=2),
    use_container_width=True,
    height=400
)

st.caption(f"Showing {len(table_df)} players for {selected_team if selected_team != 'All Teams' else 'all teams'} ({selected_season}).")


# --- 13️⃣ Footer ---
st.caption("Data Source: NBA.com Stats API (LeagueDashPlayerStats endpoint)")