import pandas as pd


def compute_game_states(timeline_df: pd.DataFrame) -> pd.DataFrame:
    """Calculates running score, handling own goals and tracking state before/after event."""
    processed_events = []

    # Process each match independently
    for match_id, match_group in timeline_df.groupby("match_id", sort=False):
        scores = {}

        for idx, row in match_group.iterrows():
            row_dict = row.to_dict()
            team = str(row["team"]).strip()
            opp = str(row["opp"]).strip()

            if team not in scores:
                scores[team] = 0
            if opp not in scores:
                scores[opp] = 0

            # State BEFORE event
            team_score_before = scores[team]
            opp_score_before = scores[opp]
            row_dict["score_before"] = f"{team_score_before}-{opp_score_before}"
            row_dict["team_game_state_before"] = _calc_state(
                team_score_before, opp_score_before
            )

            # Event score mutation
            event_type = str(row["event"]).strip().lower()
            pso = str(row["match_time"]).strip().lower()
            if event_type in ["goal", "penalty goal"] and pso != "pso":
                scores[team] += 1
            elif event_type == "own goal":
                scores[opp] += 1

            # State AFTER event
            team_score_after = scores[team]
            opp_score_after = scores[opp]
            row_dict["team_opp_score"] = f"{team_score_after}-{opp_score_after}"
            row_dict["team_game_state_after"] = _calc_state(
                team_score_after, opp_score_after
            )

            processed_events.append(row_dict)

    return pd.DataFrame(processed_events)


def _calc_state(team_score: int, opp_score: int) -> str:
    if team_score > opp_score:
        return "Ahead"
    elif team_score < opp_score:
        return "Behind"
    return "Draw"
