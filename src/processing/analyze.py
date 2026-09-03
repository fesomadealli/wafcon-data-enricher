import pandas as pd
import numpy as np


def run_wafcon_analytics(wide_csv_path, event_csv_path):
    # ==========================================
    # STEP 1: DATA LOADING & PREPROCESSING
    # ==========================================
    wide_df = pd.read_csv(wide_csv_path)
    event_df = pd.read_csv(event_csv_path)

    # Standardize team naming and match primary keys
    wide_df["Team"] = wide_df["Team"].str.strip().str.upper()
    event_df["team"] = event_df["team"].str.strip().str.upper()

    # Split wide sheet by timeframes
    ft_df = wide_df[wide_df["Timeframe"] == "FT"].copy()
    h1_df = wide_df[wide_df["Timeframe"] == "1H"].copy()
    h2_df = wide_df[wide_df["Timeframe"] == "2H"].copy()

    results = {}

    # ==========================================
    # MODULE 1: TACTICAL STYLES & PLAYING IDENTITIES
    # ==========================================
    tactical_profile = (
        ft_df.groupby("Team")
        .agg(
            avg_pass_completion=("Pass completion", "mean"),
            avg_final_third_completion=("Passes in final third completion", "mean"),
            avg_long_pass_completion=("Long pass completion", "mean"),
            box_touches=("Touches in opposition box", "mean"),
            shots_inside_box=("Shots inside the box", "mean"),
            shots_outside_box=("Shots outside the box", "mean"),
        )
        .reset_index()
    )

    # Categorize play style based on short vs long pass ratio
    tactical_profile["playing_style"] = np.where(
        tactical_profile["avg_pass_completion"] > 0.70,
        "Possession-Based",
        np.where(
            tactical_profile["avg_long_pass_completion"] > 0.45,
            "Direct / Long Ball",
            "Balanced",
        ),
    )
    results["tactical_profile"] = tactical_profile

    # ==========================================
    # MODULE 2: IN-GAME DYNAMICS (1H vs 2H)
    # ==========================================
    h1_metrics = h1_df[
        ["Team", "Round", "Expected goals (xG)", "Fouls", "Pass completion"]
    ].rename(
        columns={
            "Expected goals (xG)": "xG_1H",
            "Fouls": "Fouls_1H",
            "Pass completion": "PassComp_1H",
        }
    )
    h2_metrics = h2_df[
        ["Team", "Round", "Expected goals (xG)", "Fouls", "Pass completion"]
    ].rename(
        columns={
            "Expected goals (xG)": "xG_2H",
            "Fouls": "Fouls_2H",
            "Pass completion": "PassComp_2H",
        }
    )

    ingame_shifts = pd.merge(h1_metrics, h2_metrics, on=["Team", "Round"])
    ingame_shifts["xG_delta"] = ingame_shifts["xG_2H"] - ingame_shifts["xG_1H"]
    ingame_shifts["pass_comp_delta"] = (
        ingame_shifts["PassComp_2H"] - ingame_shifts["PassComp_1H"]
    )

    results["ingame_shifts"] = (
        ingame_shifts.groupby("Team")[["xG_delta", "pass_comp_delta"]]
        .mean()
        .reset_index()
    )

    # ==========================================
    # MODULE 3: GOALKEEPING & FINISHING EFFICIENCY
    # ==========================================
    finishing_gk = (
        ft_df.groupby("Team")
        .agg(
            total_xG=("Expected goals (xG)", "sum"),
            total_xGOT=("xG on target (xGOT)", "sum"),
            total_goals_prevented=("Goals prevented", "sum"),
            total_saves=("Goalkeeper saves", "sum"),
        )
        .reset_index()
    )

    finishing_gk["shot_quality_index"] = (
        finishing_gk["total_xGOT"] - finishing_gk["total_xG"]
    )
    results["finishing_gk"] = finishing_gk

    return results


# Execute analysis execution pipeline
# outputs = run_wafcon_analytics('Wafcon_2026_Wide_Stat_Sheet.csv', 'Wafcon_2026_Event_Log.csv')
