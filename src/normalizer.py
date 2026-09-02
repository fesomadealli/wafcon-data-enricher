import pandas as pd
import re
import unicodedata


def normalize_name(name: str) -> str:
    """Normalizes accents, removes punctuation, collapses whitespace."""
    if not name or pd.isna(name):
        return ""

    # Strip and lower
    name = str(name).strip().lower()

    # Remove accents/diacritics
    name = unicodedata.normalize("NFKD", name)
    name = "".join(c for c in name if not unicodedata.combining(c))

    # Remove non-alphanumeric except spaces
    name = re.sub(r"[^a-z0-9\s]", " ", name)

    # Collapse extra whitespace
    return re.sub(r"\s+", " ", name).strip()


def extract_tokens_and_initials(norm_name: str):
    """Splits normalized name into individual tokens and initials."""
    tokens = norm_name.split()
    if not tokens:
        return [], "", ""

    # Surname is typically last token(s)
    surname = tokens[-1]
    initials = "".join([t[0] for t in tokens if len(t) == 1 or t.endswith(".")])

    return tokens, surname, initials
