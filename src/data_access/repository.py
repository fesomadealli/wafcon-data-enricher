from __future__ import annotations
from typing import Any

import logging

logger = logging.getLogger(__name__)


class DataAccessRepository:
    def __init__(self, config: dict[str, Any]):
        self.config = config

    # Task 2: Teams with most first half goals (per round and overall)

    def get_first_half_goals_by_team(self, df):
        """
        Calculate first half goals scored by each team
        When team is home, use HTHG; when away, use HTAG
        """
        # Create two dataframes: one for home goals, one for away goals
        home_goals = df[["Home Team", "Round", "HTHG"]].copy()
        home_goals.columns = ["Team", "Round", "First_Half_Goals"]

        away_goals = df[["Away Team", "Round", "HTAG"]].copy()
        away_goals.columns = ["Team", "Round", "First_Half_Goals"]

        # Combine home and away goals
        all_first_half_goals = pd.concat([home_goals, away_goals], ignore_index=True)

        # Convert 'First_Half_Goals' to numeric, coercing errors to NaN and filling with 0
        all_first_half_goals["First_Half_Goals"] = pd.to_numeric(
            all_first_half_goals["First_Half_Goals"], errors="coerce"
        ).fillna(0)

        # Remove any rows with NaN values (older matches might not have halftime data) - this step is now less critical for type but good for data quality
        all_first_half_goals = all_first_half_goals.dropna(subset=["First_Half_Goals"])

        return all_first_half_goals


    # Define off_white color for the function
    off_white = "#F5F5F5" #--add self off_white color for the function


    # Adjusted for Nigeris, edit to generalize
    def common_scoreline(self,
        df=None, season=None, cmap=None, period="FTR", viz_type="Probabilities"
    ):
        """
        df (Dataframe) : Dataframe to work with
        season (str) : Season in view as a string (.g: "2023/24", "2024/25" etc)
        period (str) : Match period as HTR | SHR | FTR
        viz_type (str) : Output values as Probabilities | Percentages
        """
        import matplotlib.patheffects as path_effects  # Import here to ensure it's available for the function

        # Filter for Nigeria matches
        nigeria_matches = df[
            (df["Home Team"] == "Nigeria") | (df["Away Team"] == "Nigeria")
        ].copy()  # ===edit here====

        # Convert FTHG and FTAG to numeric. Coerce errors to NaN and fill with 0.
        nigeria_matches["FTHG"] = pd.to_numeric(
            nigeria_matches["FTHG"], errors="coerce"
        ).fillna(0)
        nigeria_matches["FTAG"] = pd.to_numeric(
            nigeria_matches["FTAG"], errors="coerce"
        ).fillna(0)
        nigeria_matches["HTHG"] = pd.to_numeric(
            nigeria_matches["HTHG"], errors="coerce"
        ).fillna(0)
        nigeria_matches["HTAG"] = pd.to_numeric(
            nigeria_matches["HTAG"], errors="coerce"
        ).fillna(0)

        # Adjust columns based on which team is Nigeria
        nigeria_matches["Nigeria_Goals"] = nigeria_matches.apply(
            lambda row: row["FTHG"] if row["Home Team"] == "Nigeria" else row["FTAG"],
            axis=1,
        )
        nigeria_matches["Opponent_Goals"] = nigeria_matches.apply(
            lambda row: row["FTAG"] if row["Home Team"] == "Nigeria" else row["FTHG"],
            axis=1,
        )

        # Total Number of Games
        num_of_gms = len(nigeria_matches)

        # cols to fetch data based on period
        if period.upper() == "HTR":
            nigeria_matches["Nigeria_Goals"] = nigeria_matches.apply(
                lambda row: row["HTHG"] if row["Home Team"] == "Nigeria" else row["HTAG"],
                axis=1,
            )
            nigeria_matches["Opponent_Goals"] = nigeria_matches.apply(
                lambda row: row["HTAG"] if row["Home Team"] == "Nigeria" else row["HTHG"],
                axis=1,
            )
            match_period = "First Half"
        elif period.upper() == "SHR":
            # Note: SHR data not available in dataset
            print("Second half data not available in dataset")
            return
        else:
            match_period = "Full Time"

        h_teams = nigeria_matches["Nigeria_Goals"]
        a_teams = nigeria_matches["Opponent_Goals"]

        # Get the maximum values
        max_home_goals = int(max(nigeria_matches["Nigeria_Goals"]))
        max_away_goals = int(max(nigeria_matches["Opponent_Goals"]))

        # Get Threshold for Text Label Color
        threshold_df = (
            nigeria_matches[["Nigeria_Goals", "Opponent_Goals"]]
            .value_counts()
            .reset_index()
        )

        # Create the figure
        fig, ax = plt.subplots(1, 1, figsize=(10, 6), facecolor="white")
        ax.set_facecolor("white")

        # Create a 2D histogram
        heatmap, xedges, yedges = np.histogram2d(
            h_teams,
            a_teams,
            bins=(np.arange(max_home_goals + 2), np.arange(max_away_goals + 2)),
        )

        # Define a custom colormap
        if cmap:
            cmap = plt.get_cmap(cmap)
        else:
            cmap = plt.get_cmap("Greens")

        # ax tick text colors
        ax.tick_params(axis="both", colors="black")

        # Hide spines
        for spine in ax.spines.values():
            spine.set_visible(False)

        # Plot the heatmap
        plt.imshow(
            heatmap.T,
            cmap=cmap,
            vmin=0,
            vmax=np.max(heatmap),
            origin="lower",
            interpolation="none",
        )

        # Set xticks and yticks
        plt.xticks(np.arange(max_home_goals + 1))
        plt.yticks(np.arange(max_away_goals + 1))

        # Show the colorbar
        cbar = plt.colorbar(label="Frequency", orientation="vertical", extend="max")
        cbar.ax.set_ylabel(
            "Num of Matches", rotation=270, labelpad=20, fontsize=12, color="#588B8B"
        )
        cbar.ax.tick_params(axis="y", color="#588B8B")
        for spine in cbar.ax.spines.values():
            spine.set_visible(False)

        # Get the cbar ticks
        tick_values = cbar.get_ticks()
        threshold = int(max(tick_values) / 2) if len(tick_values) > 0 else 1

        # Print the frequency on top of each cell
        for i in range(len(xedges) - 1):
            for j in range(len(yedges) - 1):
                count = len(
                    nigeria_matches[
                        (nigeria_matches["Nigeria_Goals"] == i)
                        & (nigeria_matches["Opponent_Goals"] == j)
                    ]
                )
                if count > 0:
                    if count < threshold:
                        cnt_color = "black"
                    else:
                        cnt_color = off_white

                    # Expressing Results
                    if viz_type.lower() == "probabilities":
                        prob = count / num_of_gms
                        text = f"{prob:.2f}"
                    elif viz_type.lower() == "percentages":
                        pct = (count / num_of_gms) * 100
                        text = f"{pct:.1f}%"
                    else:
                        text = str(count)

                    match_cnt = ax.text(
                        i + 0.03,
                        j + 0.03,
                        text,
                        color=cnt_color,
                        ha="center",
                        va="center",
                        fontsize=11,
                        fontweight="bold",
                    )
                    match_cnt.set_path_effects(
                        [
                            path_effects.Stroke(linewidth=0.005, foreground=off_white),
                            path_effects.Normal(),
                        ]
                    )

        # Add labels
        plt.xlabel("Nigeria Goals")
        plt.ylabel("Opponent Goals")

        season_text = f" ({season})" if season else ""
        title_text = f"DISTRIBUTION OF NIGERIA {match_period} RESULTS{season_text}\nTotal Matches: {num_of_gms}\n\n"
        plt.title(title_text, fontweight="semibold", fontsize=12)

        plt.tight_layout()
        plt.show()

        # Also print the most common scoreline
        scoreline_counts = (
            nigeria_matches.groupby(["Nigeria_Goals", "Opponent_Goals"])
            .size()
            .reset_index(name="count")
        )
        scoreline_counts = scoreline_counts.sort_values("count", ascending=False)

        if not scoreline_counts.empty:
            most_common = scoreline_counts.iloc[0]
            print(
                f"\nMost common scoreline: Nigeria {int(most_common['Nigeria_Goals'])} - {int(most_common['Opponent_Goals'])} Opponent"
            )
            print(
                f"Occurred {most_common['count']} times ({most_common['count']/num_of_gms*100:.1f}% of matches)"
            )

            print("\nTop 5 most common scorelines:")
            for idx, row in scoreline_counts.head(5).iterrows():
                pct = (row["count"] / num_of_gms) * 100
                print(
                    f"  Nigeria {int(row['Nigeria_Goals'])}-{int(row['Opponent_Goals'])}: {row['count']} matches ({pct:.1f}%)"
                )

    # def fixed_goalscorers_df(df):
    def goalscorers_df(self, df):
        import re
        import pandas as pd
        import numpy as np

        data = []
        mismatch_log = []

        for idx, row in df.iterrows():
            # Get actual goals from match scores
            home_goals_actual = int(row["FTHG"]) if pd.notna(row["FTHG"]) else 0
            away_goals_actual = int(row["FTAG"]) if pd.notna(row["FTAG"]) else 0

            # Process Home Team Goals
            if pd.notna(row.get("HomeTeam Goals")) and str(row["HomeTeam Goals"]).strip():
                home_text = str(row["HomeTeam Goals"])
                home_scorers, home_recorded = process_team_scorers_improved(
                    home_text,
                    home_goals_actual,
                    row["Home Team"],
                    row["Away Team"],
                    row["Season"],
                    row["Date"],
                )
                data.extend(home_scorers)

                # Track mismatch if counts don't match
                if home_recorded != home_goals_actual:
                    mismatch_log.append(
                        {
                            "Date": row["Date"],
                            "Team": row["Home Team"],
                            "Opponent": row["Away Team"],
                            "Expected": home_goals_actual,
                            "Recorded": home_recorded,
                            "Difference": home_goals_actual - home_recorded,
                            "Scorer_Text": (
                                home_text[:100] + "..."
                                if len(home_text) > 100
                                else home_text
                            ),
                        }
                    )
            else:
                # No scorer data at all
                if home_goals_actual > 0:
                    mismatch_log.append(
                        {
                            "Date": row["Date"],
                            "Team": row["Home Team"],
                            "Opponent": row["Away Team"],
                            "Expected": home_goals_actual,
                            "Recorded": 0,
                            "Difference": home_goals_actual,
                            "Scorer_Text": "NO DATA",
                        }
                    )

            # Process Away Team Goals (similar)
            if pd.notna(row.get("AwayTeam Goals")) and str(row["AwayTeam Goals"]).strip():
                away_text = str(row["AwayTeam Goals"])
                away_scorers, away_recorded = process_team_scorers_improved(
                    away_text,
                    away_goals_actual,
                    row["Away Team"],
                    row["Home Team"],
                    row["Season"],
                    row["Date"],
                )
                data.extend(away_scorers)

                # Track mismatch if counts don't match
                if away_recorded != away_goals_actual:
                    mismatch_log.append(
                        {
                            "Date": row["Date"],
                            "Team": row["Away Team"],
                            "Opponent": row["Home Team"],
                            "Expected": away_goals_actual,
                            "Recorded": away_recorded,
                            "Difference": away_goals_actual - away_recorded,
                            "Scorer_Text": (
                                away_text[:100] + "..."
                                if len(away_text) > 100
                                else away_text
                            ),
                        }
                    )
            else:
                # No scorer data at all
                if away_goals_actual > 0:
                    mismatch_log.append(
                        {
                            "Date": row["Date"],
                            "Team": row["Away Team"],
                            "Opponent": row["Home Team"],
                            "Expected": away_goals_actual,
                            "Recorded": 0,
                            "Difference": away_goals_actual,
                            "Scorer_Text": "NO DATA",
                        }
                    )

        # Print detailed mismatch report
        if mismatch_log:
            print("\n" + "=" * 80)
            print("⚠️ GOAL COUNT MISMATCH REPORT")
            print("=" * 80)

            total_missing = 0
            for m in mismatch_log:
                total_missing += abs(m["Difference"])
                print(f"\n📅 {m['Date']} | {m['Team']} vs {m['Opponent']}")
                print(
                    f"   Expected: {m['Expected']} goals | Recorded: {m['Recorded']} goals"
                )
                print(
                    f"   Difference: {m['Difference']} goals {'❌' if m['Difference'] != 0 else '✅'}"
                )
                print(f"   Scorer data: {m['Scorer_Text']}")

            print(f"\n📊 TOTAL MISSING/EXTRA GOALS: {total_missing}")

        return pd.DataFrame(data)

    def process_team_scorers_improved(self,
        text, expected_goals, team_name, opponent, season, date
    ):
        """
        Process scorer text and VALIDATE that player-level counts make sense
        """
        import re

        scorers = []
        lines = str(text).split("\n")
        player_goal_counts = []  # Track goals per player for validation

        print(
            f"\n🔍 PROCESSING: {team_name} vs {opponent} (Expected: {expected_goals} goals)"
        )
        print(f"   Raw text: {text}")

        for line in lines:
            line = line.strip()
            if not line or "Team" in line and "Goals" in line:
                continue

            # Extract player and goal info
            match = re.search(r"([^(]+)\(([^)]*)\)", line)
            if match:
                player = match.group(1).strip()
                minutes_raw = match.group(2).replace(" ", "")

                # Handle empty parentheses
                if minutes_raw == "":
                    goal_count = 1
                    player_goal_counts.append(goal_count)
                    print(f"   ⏱️  {player}: 1 goal (time unknown)")

                    scorers.append(
                        {
                            "Season": season,
                            "Date": date,
                            "Player": player,
                            "Team": team_name,
                            "Opponent": opponent,
                            "Goal_Time": "Unknown",
                            "Is_Penalty": False,
                            "Is_OwnGoal": False,
                            "Is_Unknown": True,
                        }
                    )

                # Has minute data
                else:
                    goal_times = minutes_raw.split(",")
                    goal_count = len(goal_times)
                    player_goal_counts.append(goal_count)
                    print(f"   ⚽ {player}: {goal_count} goals ({minutes_raw})")

                    for gt in goal_times:
                        gt = gt.strip()
                        is_penalty = "[PK]" in gt or "PK" in gt
                        is_owngoal = "[OG]" in gt or "OG" in gt

                        clean_gt = (
                            gt.replace("[PK]", "")
                            .replace("PK", "")
                            .replace("[OG]", "")
                            .replace("OG", "")
                            .strip()
                        )

                        scorers.append(
                            {
                                "Season": season,
                                "Date": date,
                                "Player": player,
                                "Team": team_name,
                                "Opponent": opponent,
                                "Goal_Time": clean_gt,
                                "Is_Penalty": is_penalty,
                                "Is_OwnGoal": is_owngoal,
                                "Is_Unknown": False,
                            }
                        )

        # Calculate total recorded goals
        recorded_goals = len(scorers)

        # VALIDATION 1: Total count matches
        if recorded_goals != expected_goals:
            print(
                f"   ❌ COUNT MISMATCH: Total recorded {recorded_goals} vs expected {expected_goals}"
            )

            # VALIDATION 2: Check if any player has too many goals
            for i, count in enumerate(player_goal_counts):
                if count > expected_goals:
                    print(
                        f"      ⚠️  Player has {count} goals but team only scored {expected_goals} total!"
                    )

        else:
            print(f"   ✅ COUNT MATCH: {recorded_goals} goals match expected")

        return scorers, recorded_goals

    def time_dist_of_goals(self, df, dist='goals_for'):
        # Make a copy to avoid modifying the original DataFrame passed in
        df_processed = df.copy()

        # Function to determine the time group for a single goal_time string
        def get_time_group(goal_time_str):
            # Convert to string and handle Unknown
            goal_str = str(goal_time_str)
            if goal_str == 'Unknown':
                return 'Unknown'
            if '45+' in goal_str:
                return '45+'
            elif '90+' in goal_str:
                return '90+'
            else:
                # For numeric goal times
                try:
                    integer_value = int(re.findall(r'(\d+)', goal_str)[0])
                    if integer_value <= 15:
                        return '0-15'
                    elif 15 < integer_value <= 30:
                        return '16-30'
                    elif 30 < integer_value <= 45:
                        return '31-45'
                    elif 45 < integer_value <= 60:
                        return '46-60'
                    elif 60 < integer_value <= 75:
                        return '61-75'
                    elif 75 < integer_value <= 90:
                        return '76-90'
                    elif integer_value > 90:
                        return '90+'
                    else:
                        return 'Unknown'
                except (IndexError, ValueError):
                    return 'Unknown'

        # Define the order of columns for the output table
        ordered_groups = ['0-15', '16-30', '31-45', '45+', '46-60', '61-75', '76-90', '90+', 'Unknown']

        # Apply the function to create the 'group' column
        df_processed['group'] = pd.Categorical(
            df_processed['Goal_Time'].apply(get_time_group),  # Changed from 'Goal Info' to 'Goal_Time'
            categories=ordered_groups,
            ordered=True
        )

        # Choose which column to group by
        if dist == "goals_for":
            col_to_group_by = "Team"
        else:
            col_to_group_by = "Opponent"

        # Use pivot_table for aggregation
        grouped_df = df_processed.pivot_table(
            index=col_to_group_by,
            columns='group',
            aggfunc='size',
            fill_value=0
        )

        # Ensure all expected columns are present and in the correct order
        for group_col in ordered_groups:
            if group_col not in grouped_df.columns:
                grouped_df[group_col] = 0
        grouped_df = grouped_df[ordered_groups]

        grouped_df = grouped_df.reset_index()
        grouped_df = grouped_df.rename(columns={col_to_group_by: 'Team'})

        # Calculate total goals
        grouped_df['Goals'] = grouped_df[ordered_groups].sum(axis=1)
        grouped_df.insert(1, 'Goals', grouped_df.pop('Goals'))

        # Filter out Unknown if you don't want to show it
        # grouped_df = grouped_df.drop('Unknown', axis=1)

        # PLOT THE GOALS TABLE
        fig = plt.figure(figsize=(10, 7), dpi=100)  # Made slightly wider
        ax = plt.subplot()

        # Get columns for display (excluding Unknown if you want)
        display_cols = [col for col in grouped_df.columns if col != 'Unknown']
        ncols = len(display_cols)
        nrows = grouped_df.shape[0]

        ax.set_xlim(0, ncols + 2)
        ax.set_ylim(0, nrows + .5)

        # Dynamic positions based on number of columns
        positions = [0.5]  # Starting position for Team column
        for i in range(1, ncols):
            positions.append(positions[-1] + 1.2)  # Space out columns

        # Add table's main text
        for i in range(nrows):
            for j, column in enumerate(display_cols):
                if j == 0:
                    ha = 'left'
                else:
                    ha = 'center'
                if column == 'Goals':
                    weight = 'bold'
                else:
                    weight = 'normal'
                ax.annotate(
                    xy=(positions[j], nrows - (0.5 * (i + 0.5))),
                    text=grouped_df[column].iloc[i],
                    ha=ha,
                    va='center',
                    weight=weight
                )

        # Add column names
        column_names = [col if col != 'Team' else '' for col in display_cols]
        for index, c in enumerate(column_names):
            if index == 0:
                ha = 'left'
            else:
                ha = 'center'
            ax.annotate(
                xy=(positions[index], nrows + 0.15),
                text=column_names[index],
                ha=ha,
                va='bottom',
                weight='bold'
            )

        # Add dividing lines
        ax.plot([ax.get_xlim()[0], ax.get_xlim()[1]], [nrows, nrows], lw=1.5, color='black', marker='', zorder=4)
        ax.plot([ax.get_xlim()[0], ax.get_xlim()[1]], [0, 0], lw=1.5, color='black', marker='', zorder=4)
        for x in range(1, nrows):
            ax.plot([ax.get_xlim()[0], ax.get_xlim()[1]], [nrows - (x * 0.5), nrows - (x * 0.5)],
                    lw=1.25, color='gray', ls=':', zorder=3, marker='')

        ax.axis('off')
        plt.tight_layout()
        plt.show()

        return grouped_df


import re
import plottable
import matplotlib
import matplotlib.pyplot as plt
from plottable import ColumnDefinition, ColDef, Table
from plottable.plots import circled_image
from plottable.cmap import normed_cmap
import matplotlib.cm
import pandas as pd
import numpy as np

def pl_time_dist_of_goals(df, dist="goals_for",
                         list_of_teams=None, logos_fpath=None):
    """
    Plottable Time Distribution of Goals Scored/Conceded
    Updated to work with fixed_goalscorers_df output
    """
    # Function to determine the time group for a single goal_time string
    def get_time_group(goal_time_str):
        # Handle Unknown values
        if goal_time_str == 'Unknown':
            return 'Unknown'
        if '45+' in str(goal_time_str):
            return '45+'
        elif '90+' in str(goal_time_str):
            return '90+'
        else:
            # For numeric goal times
            try:
                integer_value = int(re.findall(r'(\d+)', str(goal_time_str))[0])
                if integer_value <= 15:
                    return '0-15'
                elif 15 < integer_value <= 30:
                    return '16-30'
                elif 30 < integer_value <= 45:
                    return '31-45'
                elif 45 < integer_value <= 60:
                    return '46-60'
                elif 60 < integer_value <= 75:
                    return '61-75'
                elif 75 < integer_value <= 90:
                    return '76-90'
                elif integer_value > 90:
                    return '90+'
                else:
                    return 'Unknown'
            except (IndexError, ValueError):
                return 'Unknown'

    # Choose column based on dist parameter
    if dist == "goals_for":
        col = 'Team'  # Your dataframe uses 'Team' column
        cmap = matplotlib.cm.YlGnBu_r
        group_title = "When are the Teams Scoring?"
        plottable_goals_col_title = 'GF'
    elif dist == "goals_against":  # Changed from "goals_against" for clarity
        col = 'Opponent'  # Your dataframe uses 'Opponent' column
        cmap = matplotlib.cm.YlOrRd_r
        group_title = "When are the Teams Conceding?"
        plottable_goals_col_title = 'GA'

    # Define the order of columns for the output table
    ordered_groups = ['0-15', '16-30', '31-45', '45+', '46-60', '61-75', '76-90', '90+']

    # Make a copy to avoid modifying the original DataFrame passed in
    df_copy = df.copy()

    # Apply the function to create the 'group' column
    df_copy['group'] = pd.Categorical(
        df_copy['Goal_Time'].apply(get_time_group),
        categories=ordered_groups,
        ordered=True
    )

    # Drop the 'Goal_Time' column as it's no longer needed
    df_cleaned = df_copy.drop('Goal_Time', axis=1)

    # IMPORTANT FIX: Filter out rows where the 'col' (Team or Opponent) is NaN
    df_cleaned = df_cleaned.dropna(subset=[col])

    # Instead of the manual loop, use pivot_table for aggregation.
    grouped_df = df_cleaned.pivot_table(
        index=col,
        columns='group',
        aggfunc='size',
        fill_value=0
    )

    # Ensure all ordered_groups columns are present, fill with 0 if not
    for group_col in ordered_groups:
        if group_col not in grouped_df.columns:
            grouped_df[group_col] = 0
    grouped_df = grouped_df[ordered_groups] # Ensure order

    grouped_df = grouped_df.reset_index()

    # Calculate total goals
    grouped_df['Goals'] = grouped_df[ordered_groups].sum(axis=1)

    # Reorder columns: Team, Goals, then time groups
    cols = [col, 'Goals'] + ordered_groups
    grouped_df = grouped_df[cols]

    # Conditional logic for populating logo paths
    columns_to_reorder = [col]
    if logos_fpath:
        grouped_df['logo'] = ""
        for index, team in enumerate(grouped_df[col]):
            grouped_df.loc[index, 'logo'] = "{}/{}.png".format(
                logos_fpath, str(team).replace(" ", "-").lower()
            )
        columns_to_reorder.append("logo")

    columns_to_reorder.extend(["Goals"] + ordered_groups)
    grouped_df = grouped_df[columns_to_reorder]

    # Set the team column as index
    grouped_df = grouped_df.set_index(col)

    # Plottable Section
    
    # Build column_definitions dynamically
    dynamic_column_definitions = []
    if logos_fpath:
        dynamic_column_definitions.append(
            ColumnDefinition(
                name="logo",
                width=0.8,
                title="",
                textprops={"ha": "right"},
                plot_fn=circled_image
            )
        )

    dynamic_column_definitions.extend([
        ColumnDefinition(
            name=col,
            width=1.85,
            title="",
            textprops={"ha": "left", "weight": "bold", "fontsize": 13}
        ),
        ColumnDefinition(
            name="Goals",
            width=0.85,
            title=plottable_goals_col_title,
            textprops={"ha": "center", "weight": "bold", "fontsize": 13}
        )
    ])

    # Add dynamic column definitions for the time groups
    for group_col in ordered_groups:
        dynamic_column_definitions.append(
            ColumnDefinition(
                name=group_col,
                width=0.75,
                group=group_title.upper(),
                cmap=normed_cmap(grouped_df[group_col], cmap=cmap, num_stds=2.5),
                textprops={"ha": "center", "fontsize": 13}
            )
        )

    fig, ax = plt.subplots(figsize=(12, 10))
    try:
        tab = Table(
            grouped_df,
            textprops={"fontsize": 16, "weight": "bold"},
            column_definitions=dynamic_column_definitions
        )
        plt.show()
    except ModuleNotFoundError as e:
        print("Plottable Not Installed")
        print(e)
    except Exception as e: # Catch other potential errors from Plottable
        print(f"Error creating Plottable table: {e}")

    return grouped_df




if "__name__" == "__main__":
    
    data_connector = DataAccessRepository()
    
    first_half_df = data_connector.get_first_half_goals_by_team(df)
    all_goals = data_connector.goalscorers_df(df_copy)
    pass
