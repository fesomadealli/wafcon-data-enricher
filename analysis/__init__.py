"""Analysis helpers for the WAFCON enrichment project."""

from .nigeria import (
    common_scoreline,
    get_first_half_goals_by_team,
    goalscorers_df,
    nigeria_matches,
)

__all__ = [
    "nigeria_matches",
    "get_first_half_goals_by_team",
    "common_scoreline",
    "goalscorers_df",
]
