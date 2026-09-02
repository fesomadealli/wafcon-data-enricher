import pandas as pd    #type: ignore
from .transform import transform_timeline_data
from .extract import BaseDataLoader
from pathlib import Path

import logging

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(filename)s:%(funcName)s:%(lineno)d - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

ROOT_DIR = Path(__file__).resolve().parents[1]

loader = BaseDataLoader()


def run_enrichment_pipeline(
    timeline_df: pd.DataFrame, squad_df: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:  # type: ignore
    """Runs score derivation, entity resolution, player position matching and splits output into enriched data & review queue."""

    logger.info("Running Pipeline")
    enriched_df, review_df = transform_timeline_data(timeline_df, squad_df)
    processed_dir = ROOT_DIR / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Persist outputs with explicit filenames for clarity
    try:
        enriched_path = loader.save_parquet(
            enriched_df, processed_dir / "enriched.parquet"
        )
        logger.info(f"Saved enriched dataframe -> {enriched_path}")
    except Exception as e:
        logger.error(f"Failed to save enriched dataframe: {e}")
        raise

    try:
        review_path = loader.save_parquet(
            review_df, processed_dir / "review_queue.parquet"
        )
        logger.info(f"Saved review queue dataframe -> {review_path}")
    except Exception as e:
        logger.error(f"Failed to save review queue dataframe: {e}")
        raise

    return enriched_df, review_df


if __name__ == "__main__":
    # Entry point when run as a module: `python -m src.pipeline`
    # events_csv = ROOT_DIR / "raw" / "cleaned_wafcon_match_events.csv"
    # squad_csv = ROOT_DIR / "raw" / "wafcon_squad_combined.csv"

    data_dir = ROOT_DIR / "data" / "raw"

    from .extract import load_dataset_bundle

    bundle = load_dataset_bundle(data_dir)
    logger.info(f"Found bundle keys: {list(bundle.keys())}")

    required = ("match_events", "wafcon_squads")
    missing = [k for k in required if k not in bundle]
    if missing:
        logger.error(
            "Missing required input tables: %s. Expected files: cleaned_wafcon_match_events.csv, wafcon_squad_combined.csv",
            missing,
        )
        # List actual files in data_dir for debugging
        try:
            files = list(data_dir.iterdir())
            logger.info(f"Files present in {data_dir}: {[p.name for p in files]}")
        except Exception:
            logger.debug("Could not list raw directory contents")
        raise SystemExit(1)

    logger.info("All required inputs present — starting pipeline")
    run_enrichment_pipeline(bundle["match_events"], bundle["wafcon_squads"])
