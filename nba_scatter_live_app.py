# --- nba_scatter_live_app.py ---
import pandas as pd
import altair as alt
import streamlit as st
from nba_api.stats.endpoints import LeagueDashPlayerStats
import numpy as np
import time
from pathlib import Path

# Headers to avoid Akamai blocking requests from cloud IPs
NBA_REQUEST_HEADERS = {
    "Host": "stats.nba.com",
    "Connection": "keep-alive",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.nba.com/",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://www.nba.com",
}
# --- 1️⃣ Function to load live NBA player data ---
@st.cache_data(ttl=3600)
def load_nba_data(season="2023-24"):
    """Load live NBA player statistics from NBA Stats API for the selected season.
    Retries a few times with a longer timeout to avoid transient failures on stats.nba.com.
    """
    last_err = None
    for attempt_idx in range(3):
        try:
            stats = LeagueDashPlayerStats(
                season=season,
                per_mode_detailed="PerGame",
                timeout=60,
                headers=NBA_REQUEST_HEADERS,
            )
            df = stats.get_data_frames()[0]
            return df
        except Exception as err:  # network flakiness / timeouts
            last_err = err
            time.sleep(2 * (attempt_idx + 1))
    raise last_err


def load_demo_data() -> pd.DataFrame:
    sample_csv = Path(__file__).parent / "sample_data" / "player_stats_2023_24_sample.csv"
    df_demo = pd.read_csv(sample_csv)
    return df_demo


# --- 2️⃣ Streamlit UI setup ---
st.title("🏀 NBA Player Stats Explorer")
st.markdown("""
Explore relationships between player performance metrics.  
Select a season, filter by team, and choose two variables to visualize their relationship.
""")

# --- 3️⃣ Season selection ---
seasons = [f"{yr}-{str(yr+1)[-2:]}" for yr in range(2019, 2024)][::-1]  # 2019–24
selected_season = st.selectbox("Select Season", seasons, index=0)

# --- 4️⃣ Load data ---
with st.spinner(f"Loading {selected_season} data..."):
    try:
        df = load_nba_data(season=selected_season)
    except Exception as load_err:
        try:
            df = load_demo_data()
            st.info("Using demo data because live NBA Stats API timed out.")
        except Exception:
            st.error(
                "Could not load NBA data right now (network timeout). Please refresh or try again in a moment."
            )
            st.caption(f"Details: {load_err}")
            st.stop()

st.success(f"✅ Loaded {len(df)} player records for {selected_season}.")

# --- 5️⃣ Filter numeric columns to meaningful stats only ---
numeric_cols = df.select_dtypes(include='number').columns.tolist()

excluded_keywords = [
    "RANK", "NBA_FANTASY", "WNBA_FANTASY", "_ID", "CF", "GROUP"
]
excluded_specific = [
    "W", "L", "W_PCT", "BLKA", "PFD", "DD2", "TD3", "TEAM_COUNT"
]

meaningful_cols = [
    c for c in numeric_cols
    if not any(keyword in c for keyword in excluded_keywords)
    and c not in excluded_specific
]

# --- 6️⃣ Create a friendly display name mapping ---
friendly_names = {
    "AGE": "Player Age",
    "GP": "Games Played",
    "MIN": "Minutes per Game",
    "FGM": "Field Goals Made per Game",
    "FGA": "Field Goals Attempted per Game",
    "FG_PCT": "Field Goal Percentage",
    "FG3M": "Three-Point Field Goals Made per Game",
    "FG3A": "Three-Point Field Goals Attempted per Game",
    "FG3_PCT": "Three-Point Percentage",
    "FTM": "Free Throws Made per Game",
    "FTA": "Free Throws Attempted per Game",
    "FT_PCT": "Free Throw Percentage",
    "OREB": "Offensive Rebounds per Game",
    "DREB": "Defensive Rebounds per Game",
    "REB": "Total Rebounds per Game",
    "AST": "Assists per Game",
    "STL": "Steals per Game",
    "BLK": "Blocks per Game",
    "TOV": "Turnovers per Game",
    "PF": "Personal Fouls per Game",
    "PTS": "Points per Game",
    "PLUS_MINUS": "Plus/Minus per Game",
}

display_to_column = {
    friendly_names.get(c, c.replace("_", " ").title()): c for c in meaningful_cols
}
display_names = list(display_to_column.keys())

# --- 7️⃣ Variable selectors (friendly names shown to user) ---
x_display = st.selectbox(
    "Select X-axis variable",
    display_names,
    index=display_names.index("Three-Point Percentage") if "Three-Point Percentage" in display_names else 0
)
y_display = st.selectbox(
    "Select Y-axis variable",
    display_names,
    index=display_names.index("Field Goal Percentage") if "Field Goal Percentage" in display_names else 1
)

x_var = display_to_column[x_display]
y_var = display_to_column[y_display]

# --- 🆕 NEW: 7.5️⃣ Team Filter ---
teams = ["All Teams"] + sorted(df["TEAM_ABBREVIATION"].unique())
selected_team = st.selectbox("Filter by Team", teams, index=0)

if selected_team != "All Teams":
    df = df[df["TEAM_ABBREVIATION"] == selected_team]
    st.info(f"Showing data for **{selected_team}** ({len(df)} players).")

# --- 8️⃣ Clean data for plotting ---
df_clean = df[[x_var, y_var, 'PLAYER_NAME', 'TEAM_ABBREVIATION']].dropna()
df_clean = df_clean[
    (df_clean[x_var].apply(lambda x: isinstance(x, (int, float)))) &
    (df_clean[y_var].apply(lambda x: isinstance(x, (int, float))))
]

# --- 9️⃣ Build scatterplot ---
scatter = (
    alt.Chart(df_clean)
    .mark_circle(size=60, opacity=0.7, color='steelblue')
    .encode(
        x=alt.X(f"{x_var}:Q", title=x_display),
        y=alt.Y(f"{y_var}:Q", title=y_display),
        tooltip=["PLAYER_NAME", "TEAM_ABBREVIATION", x_var, y_var]
    )
    .interactive()
    .properties(
        width=700,
        height=450,
        title=f"{y_display} vs {x_display} ({selected_season}{'' if selected_team == 'All Teams' else ' - ' + selected_team})"
    )
)

# --- 🔟 Optional: Add regression trendline ---
if st.checkbox("Add regression trendline"):
    df_clean[x_var] = pd.to_numeric(df_clean[x_var], errors='coerce')
    df_clean[y_var] = pd.to_numeric(df_clean[y_var], errors='coerce')
    df_clean = df_clean.dropna(subset=[x_var, y_var])

    try:
        trend = (
            alt.Chart(df_clean)
            .transform_regression(x_var, y_var, as_=[x_var, y_var])
            .mark_line(color='red', size=2)
            .encode(
                x=alt.X(f"{x_var}:Q", title=x_display),
                y=alt.Y(f"{y_var}:Q", title=y_display)
            )
        )
        scatter = alt.layer(scatter, trend).resolve_scale(x='shared', y='shared')

        slope, intercept = np.polyfit(df_clean[x_var], df_clean[y_var], 1)
        st.write(f"**Regression equation:** {y_display} = {slope:.2f} × {x_display} + {intercept:.2f}")

    except Exception as e:
        st.warning(f"⚠️ Trendline could not be added: {e}")

# --- 11️⃣ Display chart ---
st.altair_chart(scatter, use_container_width=True)

# --- 12️⃣ Correlation coefficient ---
corr = df[x_var].corr(df[y_var])
st.write(f"**Correlation coefficient (r):** {corr:.2f}")

# --- 13️⃣ Footer ---
st.caption("Data Source: NBA.com Stats API (LeagueDashPlayerStats endpoint)")