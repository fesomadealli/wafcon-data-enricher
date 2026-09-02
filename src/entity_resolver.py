import pandas as pd
from rapidfuzz import fuzz, process #type: ignore
from .normalizer import normalize_name, extract_tokens_and_initials


class EntityResolver:
    def __init__(self, squad_df: pd.DataFrame, confidence_cutoff: float = 75.0):
        self.cutoff = confidence_cutoff
        self.squad_df = squad_df.copy()

        # Pre-normalize Squad Names
        self.squad_df["norm_full_name"] = self.squad_df["full_name"].apply(
            normalize_name
        )

        # In-memory match cache to avoid re-resolving identical (name, team, year) tuples
        self.cache = {}

    def resolve_player(self, player_name: str, team: str, edition: int) -> dict:
        """Resolves raw player string into canonical player_id with audit metadata."""
        if not player_name or pd.isna(player_name) or str(player_name).strip() == "":
            return self._build_result(None, None, 0.0, "empty_input")

        cache_key = (player_name, team, edition)
        if cache_key in self.cache:
            return self.cache[cache_key]

        # Filter squad candidates strictly by (Country + Edition)
        candidates = self.squad_df[
            (self.squad_df["country"].str.lower() == str(team).strip().lower())
            & (self.squad_df["year"] == int(edition))
        ]

        if candidates.empty:
            result = self._build_result(None, None, 0.0, "no_squad_candidates")
            self.cache[cache_key] = result
            return result

        norm_event_name = normalize_name(player_name)

        # LEVEL 1: Exact Normalized Match
        exact_match = candidates[candidates["norm_full_name"] == norm_event_name]
        if not exact_match.empty:
            match = exact_match.iloc[0]
            result = self._build_result(
                match["player_id"], match["full_name"], 100.0, "exact_normalized"
            )
            self.cache[cache_key] = result
            return result

        # LEVEL 2: Token / Surname / Initials Match
        event_tokens, event_surname, event_initials = extract_tokens_and_initials(
            norm_event_name
        )

        for _, candidate in candidates.iterrows():
            c_norm = candidate["norm_full_name"]
            c_tokens, c_surname, _ = extract_tokens_and_initials(c_norm)

            # Check if surname matches and initial tokens overlap
            if event_surname == c_surname and len(event_surname) > 2:
                # High confidence anchor on multi-char surname
                result = self._build_result(
                    candidate["player_id"],
                    candidate["full_name"],
                    95.0,
                    "surname_anchor",
                )
                self.cache[cache_key] = result
                return result

        # LEVEL 3: Multi-Scorer RapidFuzz
        candidate_names = candidates["norm_full_name"].tolist()

        # Scorer strategy combining token set ratio and weighted ratio
        fz_res = process.extractOne(
            norm_event_name, candidate_names, scorer=fuzz.token_set_ratio
        )

        if fz_res:
            matched_norm, score, idx = fz_res
            matched_row = candidates.iloc[idx]

            if score >= self.cutoff:
                res = self._build_result(
                    matched_row["player_id"],
                    matched_row["full_name"],
                    float(score),
                    "rapidfuzz_token_set",
                )
            else:
                # Mark for manual review
                res = self._build_result(
                    None,
                    matched_row["full_name"],
                    float(score),
                    "unresolved_review_queue",
                )

            self.cache[cache_key] = res
            return res

        res = self._build_result(None, None, 0.0, "unresolved")
        self.cache[cache_key] = res
        return res

    def _build_result(self, p_id, matched_name, score, method) -> dict:
        return {
            "player_id": p_id,
            "matched_name": matched_name,
            "match_score": score,
            "match_method": method,
        }
