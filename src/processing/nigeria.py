from .match_enrichment import df_match, prepare_data, prepare_match_results, restructure_team_df

_df = prepare_match_results(df_match)["wafcon_df"]

nigeria_df = _df[
    (_df["Home Team"] == "Nigeria") | (_df["Away Team"] == "Nigeria")
].copy()


# Apply the restructuring
nigeria_restructured = restructure_team_df(nigeria_df, team="Nigeria")


print("\n" + "=" * 80)
print("RESTRUCTURED NIGERIA DATAFRAME")
print("=" * 80)
print(
    nigeria_restructured[
        [
            "Date",
            "Round",
            "Opponent",
            "HTTG",
            "HTOG",
            "FTTG",
            "FTOG",
            "Result",
            "Clean_Sheet",
            "Team_Goals_Scorers",
            "Opponent_Goals_Scorers",
        ]
    ]
    .sample(2)
    .to_string(index=False)
)

# Now let's verify the clean sheets with the correct logic
print("\n" + "=" * 80)
print("VERIFYING CLEAN SHEETS (CORRECT LOGIC)")
print("=" * 80)

for idx, row in nigeria_restructured.iterrows():
    clean_sheet_status = "✅ CLEAN SHEET" if row["Clean_Sheet"] else "❌ Conceded"
    print(f"{row['Date']} vs {row['Opponent']}: {row['Result']} - {clean_sheet_status}")

