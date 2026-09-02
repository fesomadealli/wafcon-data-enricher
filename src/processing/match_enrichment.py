from __future__ import annotations

import logging
from typing import Iterable

import pandas as pd

logger = logging.getLogger(__name__)


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize column names for downstream processing."""
    normalized = df.copy()
    normalized.columns = [
        str(col).strip().lower().replace(" ", "_") for col in normalized.columns
    ]
    logger.info("Normalized %s columns to %s", len(df.columns), len(normalized.columns))
    return normalized


def coerce_numeric_columns(
    df: pd.DataFrame,
    columns: Iterable[str] | None = None,
    *,
    errors: str = "coerce",
) -> pd.DataFrame:
    """Coerce the selected columns to numeric values without crashing on mixed strings."""
    result = df.copy()
    targets = list(columns) if columns is not None else list(result.columns)
    for column in targets:
        if column in result.columns:
            result[column] = pd.to_numeric(result[column], errors=errors)
    return result


def prepare_match_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Clean a raw match dataset into a usable WAFCON match table."""
    result = df.copy()
    result = normalize_columns(result)

    # Common schema variants
    for legacy, preferred in {
        "date_time": "date",
        "datetime": "date",
        "match_date": "date",
        "date_of_match": "date",
        "home_team": "home_team",
        "away_team": "away_team",
        "home_score": "home_score",
        "away_score": "away_score",
        "full_time_home_goals": "home_score",
        "full_time_away_goals": "away_score",
    }.items():
        if legacy in result.columns and preferred not in result.columns:
            result[preferred] = result[legacy]

    if "date" in result.columns:
        result["date"] = pd.to_datetime(result["date"], errors="coerce")

    for col in ["home_score", "away_score"]:
        if col in result.columns:
            result[col] = pd.to_numeric(result[col], errors="coerce")

    result = (
        result.sort_values(by=["date"], kind="mergesort")
        if "date" in result.columns
        else result
    )
    logger.info("Prepared match dataset with %s rows", len(result))
    return result


__all__ = ["normalize_columns", "coerce_numeric_columns", "prepare_match_dataset"]
