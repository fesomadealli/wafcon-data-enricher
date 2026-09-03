from __future__ import annotations
from pathlib import Path
import pandas as pd
from typing import Any, Union, Dict

import logging

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.parent

from src.extract import BaseDataLoader

loader =  BaseDataLoader()

df_match = loader.read_csv(
    PROJECT_ROOT / "data" / "raw" / "wafcon_results_compiled.csv"
)

df_stats = loader.read_csv(
    PROJECT_ROOT / "data" / "raw" / "wafcon_2026_wide_stat_sheet.csv"
)

# ==========================================================
expected_cols = [
    "Date",
    "Season",
    "Competition",
    "Round",
    "Group",
    "Time",
    "Match Venue",
    "Home Team",
    "Away Team",
    "HTHG",
    "HTAG",
    "FTHG",
    "FTAG",
    "FTR",
    "Penalties",
    "Remarks",
    "HomeTeam Goals",
    "AwayTeam Goals",
    "Notes",
    "HomeTeam XI",
    "HomeTeam Reserves",
    "HomeTeam Subs",
    "AwayTeam XI",
    "AwayTeam Reserves",
    "AwayTeam Subs",
    "HomeTeam Coach",
    "AwayTeam Coach",
    "HomeTeam Formation",
    "AwayTeam Formation",
]

# ==========================================================

def prepare_match_results(df: pd.DataFrame |  Dict):

    if isinstance(df, dict):
        df = pd.DataFrame(df)

    df.columns = df.columns.str.strip()
    df_cleaned = df.copy()
    df_cleaned.columns = df_cleaned.columns.str.strip()

    # Convert specified columns to numeric, filling NaNs with 0, then to integer
    for col in ["HTHG", "HTAG", "FTHG", "FTAG"]:
        df_cleaned[col] = pd.to_numeric(df_cleaned[col], errors="coerce").fillna(0).astype(int)   #type: ignore

    df_cleaned["Round"] = df_cleaned["Round"].replace(
        ["Round 1", "Round 2", "Round 3"], "Group Stage"
    )

    group_stage_df = df_cleaned[df_cleaned['Round'] == 'Group Stage']
    quarterfinal_df = df_cleaned[df_cleaned['Round'] == 'Quarterfinal']
    semifinal_df = df_cleaned[df_cleaned['Round'] == 'Semifinal']
    final_df = df_cleaned[df_cleaned['Round'] == 'Final']

    df_bundle = {
        "wafcon_df": df_cleaned,   
        "group_stage": group_stage_df,  #type: ignore
        "quarterfinal": quarterfinal_df,
        "semifinal": semifinal_df,
        "final": final_df
    }
    return df_bundle


# Restructure the dataframe
def restructure_team_df(df, team=None):
    """
    Restructure dataframe for Nigeria matches

    If Nigeria is HOME:
    - HTTG (Half Time Team Goals) = HTHG
    - HTOG (Half Time Opponent Goals) = HTAG
    - FTTG (Full Time Team Goals) = FTHG
    - FTOG (Full Time Opponent Goals) = FTAG
    - team_goals_scorers = HomeTeam Goals
    - opponent_goals_scorers = AwayTeam Goals

    If Nigeria is AWAY:
    - HTTG = HTAG
    - HTOG = HTHG
    - FTTG = FTAG
    - FTOG = FTHG
    - team_goals_scorers = AwayTeam Goals
    - opponent_goals_scorers = HomeTeam Goals
    """

    if team is None:
      print('No <team> specified, please add a team information.')

    restructured_rows = []

    for idx, row in df.iterrows():
        if row['Home Team'].lower() == team.lower():
            # Team is HOME
            restructured_rows.append({
                'Date': row['Date'],
                'Season': row['Season'],
                'Competition': row['Competition'],
                'Round': row['Round'],
                'Group': row['Group'],
                'Venue': row['Match Venue'],
                'Team': team,
                'Opponent': row['Away Team'],
                'HTTG': row['HTHG'],  # Half Time Team Goals
                'HTOG': row['HTAG'],  # Half Time Opponent Goals
                'FTTG': row['FTHG'],  # Full Time Team Goals
                'FTOG': row['FTAG'],  # Full Time Opponent Goals
                'Result': f"{row['FTHG']}-{row['FTAG']}",
                'Clean_Sheet': row['FTAG'] == 0,  # True if opponent scored 0
                'Team_Goals_Scorers': row['HomeTeam Goals'] if pd.notna(row['HomeTeam Goals']) else '',
                'Opponent_Goals_Scorers': row['AwayTeam Goals'] if pd.notna(row['AwayTeam Goals']) else ''
            })
        else:
            # Team is AWAY
            restructured_rows.append({
                'Date': row['Date'],
                'Season': row['Season'],
                'Competition': row['Competition'],
                'Round': row['Round'],
                'Group': row['Group'],
                'Venue': row['Match Venue'],
                'Team': team,
                'Opponent': row['Home Team'],
                'HTTG': row['HTAG'],  # Half Time Team Goals (away team goals)
                'HTOG': row['HTHG'],  # Half Time Opponent Goals (home team goals)
                'FTTG': row['FTAG'],  # Full Time Team Goals (away team goals)
                'FTOG': row['FTHG'],  # Full Time Opponent Goals (home team goals)
                'Result': f"{row['FTAG']}-{row['FTHG']}",
                'Clean_Sheet': row['FTHG'] == 0,  # True if opponent scored 0
                'Team_Goals_Scorers': row['AwayTeam Goals'] if pd.notna(row['AwayTeam Goals']) else '',
                'Opponent_Goals_Scorers': row['HomeTeam Goals'] if pd.notna(row['HomeTeam Goals']) else ''
            })

    return pd.DataFrame(restructured_rows)






