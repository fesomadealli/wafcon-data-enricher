from __future__ import annotations
from pathlib import Path
from typing import Union

import pandas as pd
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(filename)s:%(funcName)s:%(lineno)d - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class BaseDataLoader:
    """Small reusable reader/writer layer for CSV, JSON, and Parquet sources."""

    @staticmethod
    def read_csv(filepath: Union[str, Path], **kwargs) -> pd.DataFrame:

        path = Path(filepath)
        if not path.is_file():
            raise FileNotFoundError(f"File not found: {path}")
        df = pd.read_csv(path, **kwargs)
        logger.info(f"Read CSV {path} -> {len(df)} rows, {len(df.columns)} cols")
        return df

    @staticmethod
    def read_json(filepath: Union[str, Path], **kwargs) -> pd.DataFrame:

        path = Path(filepath)
        if not path.is_file():
            raise FileNotFoundError(f"File not found: {path}")
        df = pd.read_json(path, **kwargs)
        logger.info(f"Read JSON {path} -> {len(df)} rows, {len(df.columns)} cols")
        return df

    @staticmethod
    def read_parquet(filepath: Union[str, Path], **kwargs) -> pd.DataFrame:

        path = Path(filepath)
        if not path.is_file():
            raise FileNotFoundError(f"File not found: {path}")
        df = pd.read_parquet(path, engine="pyarrow", **kwargs)
        logger.info(f"Read Parquet {path} -> {len(df)} rows, {len(df.columns)} cols")
        return df

    @staticmethod
    def save_parquet(df: pd.DataFrame, output_path: Union[str, Path]) -> Path:

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            df.to_parquet(path, engine="pyarrow", index=False)
            logger.info(
                f"Wrote Parquet {path} -> {len(df)} rows, {len(df.columns)} cols"
            )
            return path
        except ImportError as e:
            # pyarrow not installed; fallback to CSV to avoid hard failure
            fallback = path.with_suffix(".csv")
            df.to_csv(fallback, index=False)
            logger.warning(
                "pyarrow not available; wrote CSV fallback %s instead of Parquet (%s)",
                fallback,
                e,
            )
            return fallback
        except Exception as e:
            logger.error(f"Error writing parquet file {path}: {e}")
            raise

    @staticmethod
    def write_json(
        df: pd.DataFrame, output_path: Union[str, Path], orient: str = "records"
    ) -> Path:

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_json(path, orient=orient, indent=4)  # type: ignore
        logger.info(f"Wrote JSON {path} -> {len(df)} rows, {len(df.columns)} cols")
        return path

    @staticmethod
    def convert_csv_to_json(
        csv_path: Union[str, Path], json_path: Union[str, Path]
    ) -> Path:

        c_path, j_path = Path(csv_path), Path(json_path)
        df = BaseDataLoader.read_csv(c_path)
        return BaseDataLoader.write_json(df, j_path)


def load_dataset_bundle(data_dir: Union[str, Path]) -> dict[str, pd.DataFrame]:

    base = Path(data_dir)
    raw_dir = base / "raw" if base.name != "raw" else base

    bundle: dict[str, pd.DataFrame] = {}

    aliases = {
        "cleaned_wafcon_match_events.csv": "match_events",
        "wafcon_squad_combined.csv": "wafcon_squads",
    }
    logger.info(f"Scanning for raw data in: {raw_dir}")

    if not raw_dir.exists():
        logger.warning(f"Raw data directory does not exist: {raw_dir}")

    for file_name, alias in aliases.items():
        path = raw_dir / file_name
        exists = path.exists()
        logger.info(f"Looking for {file_name}: {path} -> exists={exists}")
        if exists:
            try:
                bundle[alias] = BaseDataLoader.read_csv(path)
            except Exception as e:
                logger.error(f"Failed to read {path}: {e}")

    logger.info(f"Loaded dataset bundle keys: {list(bundle.keys())}")
    return bundle


def main():
    """
    Main extraction orchestrator:
    1. Loads and returns all raw tables as a dictionary bundle.
    """

    project_root = Path(__file__).resolve().parents[1]
    raw_dir = project_root / "data" / "raw"

    bundle = load_dataset_bundle(raw_dir)

    logger.info(f"Loaded raw dataset bundle with {len(bundle)} tables.")
    logger.info(sorted(bundle.keys()))


if __name__ == "__main__":
    main()
