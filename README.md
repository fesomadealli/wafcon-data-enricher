# WAFCON Data Enricher

This project is currently in its data-enrichment and analysis stage for WAFCON competition data. It combines raw match event data, squad metadata, and aggregated performance statistics into a clean, analysis-ready data layer, with reusable processing modules and a modular analysis structure.

## Current project stage

The project is focused on:

- ingesting and validating raw WAFCON data files
- normalizing match and squad data into a consistent schema
- enriching match records with player and team metadata
- exporting processed outputs for downstream analysis
- separating reusable logic into module-based Python code instead of notebook-only logic

## Project structure

- `analysis/` — Nigeria-focused and exploratory analysis helpers
- `src/` — production pipeline code, data access, and processing modules
- `data/raw/` — original source data files
- `data/processed/` — generated analysis outputs
- `notebooks/` — notebook-based exploratory work
- `tests/` — validation and regression checks

## Data flow

The pipeline currently reads raw WAFCON files from `data/raw/`, normalizes them, and persists processed artifacts to `data/processed/`.

Typical flow:

1. Load match-event and squad input tables.
2. Normalize field names and date formats.
3. Enrich player/team resolution and match metadata.
4. Export processed outputs to CSV or Parquet for analysis.
5. Keep review-queue records separate for unresolved or uncertain matches.

## Raw data sources

The project currently uses the following raw files:

- `data/raw/cleaned_wafcon_match_events.csv` — event-level match timeline data
- `data/raw/wafcon_2026_wide_stat_sheet.csv` — team and match statistical sheet for the current edition
- `data/raw/wafcon_results_compiled.csv` — compiled WAFCON results set
- `data/raw/wafcon_squad_combined.csv` — player roster and squad metadata

## Processed outputs

- `data/processed/enriched.parquet` — enriched match/event output
- `data/processed/review_queue.parquet` — unresolved or low-confidence records flagged for review

## Data conventions and rules

### DOB handling

For the combined squad dataset, any missing or unknown date of birth is normalized to:

- 1900-01-01

This is a sentinel value used to preserve row integrity and avoid nulls in the roster dataset. It is considered a placeholder and should not be interpreted as a real birth date.

### Column standardization

During the normalization step:

- column names are lower-cased
- spaces are replaced with underscores
- date fields are interpreted consistently
- numeric columns are coerced where appropriate

### Review queue

Rows that cannot be confidently resolved during player or entity matching are written to the review queue rather than silently dropped.

## Intended usage

This project is designed to support:

- WAFCON match analysis
- squad and player profiling
- historical and current edition comparison
- data quality monitoring and review
- Google Sheets export and analysis workflows

## Notes

This stage is a working pipeline and is intentionally modular so that the logic can be reused outside notebook execution. The focus is on reproducible enrichment and clearer ownership between data access, processing, and analysis modules.
