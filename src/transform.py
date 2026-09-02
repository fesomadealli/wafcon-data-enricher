from __future__ import annotations
import logging
import pandas as pd  # type: ignore
from .game_state import compute_game_states
from .entity_resolver import EntityResolver

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(filename)s:%(funcName)s:%(lineno)d - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def transform_timeline_data(
    match_events_df: pd.DataFrame,
    squads_df: pd.DataFrame,
    confidence_cutoff: float = 75.0,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Orchestrates transformation, score tracking, and entity resolution.
    Returns (enriched_events_df, review_queue_df).
    """
    logger.info("Computing game state transitions (Before vs After)...")
    events_df = compute_game_states(match_events_df)

    # Ensure there is a `date` column (some inputs use `datetime`)
    if "date" not in events_df.columns:
        if "datetime" in events_df.columns:
            # Parse datetimes robustly (mixed formats, missing seconds)
            parsed = pd.to_datetime(events_df["datetime"], errors="coerce")
            num_parsed = parsed.notna().sum()   #type: ignore
            num_total = len(parsed) #type: ignore
            events_df["date"] = parsed.dt.date  # type: ignore
            logger.info(
                "Created 'date' column from 'datetime' column (parsed %s/%s rows)",
                num_parsed,
                num_total,
            )
        elif "date_time" in events_df.columns:
            events_df["date"] = pd.to_datetime(events_df["date_time"]).dt.date  # type: ignore
            logger.info("Created 'date' column from 'date_time' column")

    # Derive edition year if missing: prefer explicit 'edition' or 'year', then 'date'
    if "edition_year" not in events_df.columns:
        if "edition" in events_df.columns:
            try:
                events_df["edition_year"] = events_df["edition"].astype(int)
                logger.info("Derived 'edition_year' from 'edition' column")
            except Exception:
                events_df["edition_year"] = (
                    pd.to_datetime(events_df.get("date", pd.NaT))
                    .dt.year.fillna(2026)  # type: ignore
                    .astype(int)
                )
                logger.info("Derived 'edition_year' from 'date' column with fallback")
        elif "year" in events_df.columns:
            events_df["edition_year"] = events_df["year"].astype(int)
            logger.info("Derived 'edition_year' from 'year' column")
        elif "date" in events_df.columns:
            events_df["edition_year"] = pd.to_datetime(events_df["date"]).dt.year #type: ignore
            logger.info("Derived 'edition_year' from 'date' column")
        else:
            events_df["edition_year"] = 2026  # Default fallback
            logger.info("No edition/date info found; defaulting 'edition_year' to 2026")

    # Initialize resolver
    logger.info("Initializing EntityResolver against squad database...")
    resolver = EntityResolver(squads_df, confidence_cutoff=confidence_cutoff)

    # Resolution storage lists
    p_ids, p_names, p_scores, p_methods = [], [], [], []
    s_ids, s_names, s_scores, s_methods = [], [], [], []

    logger.info(f"Resolving player names for {len(events_df)} event records...")
    for _, row in events_df.iterrows():
        year = row["edition_year"]
        team = row["team"]

        # Primary Player
        res_p = resolver.resolve_player(row.get("primary_player"), team, year)  # type: ignore
        p_ids.append(res_p["player_id"])
        p_names.append(res_p["matched_name"])
        p_scores.append(res_p["match_score"])
        p_methods.append(res_p["match_method"])

        # Secondary Player
        res_s = resolver.resolve_player(row.get("secondary_player"), team, year)  # type: ignore
        s_ids.append(res_s["player_id"])
        s_names.append(res_s["matched_name"])
        s_scores.append(res_s["match_score"])
        s_methods.append(res_s["match_method"])

    # Attach audit columns
    events_df["primary_player_id"] = p_ids
    events_df["primary_matched_name"] = p_names
    events_df["primary_match_score"] = p_scores
    events_df["primary_match_method"] = p_methods

    events_df["secondary_player_id"] = s_ids
    events_df["secondary_matched_name"] = s_names
    events_df["secondary_match_score"] = s_scores
    events_df["secondary_match_method"] = s_methods

    # Create a mapping dictionary from squad database: (player_id, year) -> position
    position_lookup = (
        squads_df.dropna(subset=["player_id"])
        .set_index(["player_id", "year"])["position"]
        .to_dict()
    )

    # Extract resolved positions in the transform loop:
    primary_positions = [
        position_lookup.get((p_id, year), None) if p_id else None
        for p_id, year in zip(p_ids, events_df["edition_year"])
    ]

    secondary_positions = [
        position_lookup.get((s_id, year), None) if s_id else None
        for s_id, year in zip(s_ids, events_df["edition_year"])
    ]

    # Attach to output DataFrame
    events_df["primary_player_pos"] = primary_positions
    events_df["secondary_player_pos"] = secondary_positions

    # Extract Review Queue (Unresolved or uncertain records)
    is_p_unresolved = events_df["primary_match_method"].str.startswith("unresolved")
    is_s_unresolved = events_df["secondary_match_method"].str.startswith("unresolved")

    review_queue = events_df[is_p_unresolved | is_s_unresolved][
        [
            "match_id",
            "date",
            "team",
            "event",
            "primary_player",
            "primary_matched_name",
            "primary_match_score",
            "primary_match_method",
            "secondary_player",
            "secondary_matched_name",
            "secondary_match_score",
            "secondary_match_method",
        ]
    ]

    logger.info(
        f"Transformation complete. {len(review_queue)} records sent to review queue."
    )
    return events_df, review_queue
