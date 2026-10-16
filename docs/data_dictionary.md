# Data Dictionary

## Project Scope

This repository assembles historical college football recruiting, player
production, NFL draft outcomes, and pre-draft rankings for a downstream
NIL return-or-declare research project.

The repository is a data-engineering deliverable. It does not contain a
decision model or claim that the assembled data alone identifies the causal
effect of NIL compensation.

## Core Processed Datasets

| File | Grain | Description |
|---|---|---|
| `draft_player_master.csv` | One row per NFL draft pick | Draft outcomes with recruiting-match information and coverage indicators |
| `draft_college_production_summary.csv` | One row per NFL draft pick | Aggregated college production for linked, observed seasons |
| `draft_college_season_history.csv` | One row per drafted player-season | Observed college statistics linked to a draft record |
| `draft_college_season_history_coverage.csv` | One row per NFL draft pick | Indicates whether linked college-season history was observed |
| `college_player_season_stats.csv` | One row per player-season-team combination | Aggregated regular-season college statistics from CFBD |
| `draft_results_2016_2025.csv` | One row per draft pick | Clean NFL draft outcomes for 2016–2025 |
| `consensus_big_board_historical.csv` | One row per historical ranking record | Historical consensus pre-draft rankings |
| `consensus_ranking_conflicts.csv` | One row per flagged conflict | Preserved conflicting consensus-ranking records |

## Source Coverage

- NFL draft outcomes: 2016–2025.
- College player statistics: regular seasons, 2016–2025.
- High-school recruiting records: 2000–2025.
- Historical consensus rankings: 2016–2025.

## Interpretation and Limitations

### Missing college statistics

The college-statistics source window begins in 2016. Players whose college
careers ended before 2016 may have no linked seasons even when they had
substantial college careers. Missing linked history must not be interpreted
as zero production or as evidence that the player did not play.

### Recruiting matches

Recruiting-to-draft links are based on the project's current matching rules.
A strong candidate is a high-confidence candidate under those rules, not
independent proof of identity. Review ambiguous matches before using them
for person-level conclusions.

### Production summaries

Production totals sum the linked, observed seasons available in the source
window. They are not guaranteed to represent complete college careers.
Rate statistics in the production summary use the latest observed season
where specified; they are not necessarily career-weighted rates.

### Rankings

Conflicting ranking records are retained in a separate audit output rather
than silently discarded. Check the ranking source's timing and definition
before interpreting a ranking as information available to a player at a
particular decision date.

### Scope

This repository does not contain verified NIL compensation valuations.
Recruiting ratings, draft outcomes, and college production are not substitutes
for actual NIL deal values. Downstream analysis should distinguish observed
data from inferred or missing information.

## Data Handling

Raw source downloads are kept separately from processed outputs. API keys
and other credentials must not be committed to the repository.

## Consolidated Recruiting Dataset

File: `data/processed/recruiting_players_2000_2025.csv`

- Grain: one source recruiting record per row.
- Coverage: high-school recruiting classes, 2000–2025.
- Rows: 77,275 in the current extraction.
- Source files: 26 annual CSVs, preserved locally.
- `source_file`: identifies the annual CSV from which each record originated.
- `athleteId`: source identifier when available; 40,124 records are missing it.
- `stars` and `rating`: preserve missing values; missing ratings do not mean zero-star recruits.
- `committedTo`: preserve missing values; missing commitments are not proof of no commitment.

This dataset contains high-school recruiting records only. It does not represent the full transfer-portal or junior-college recruiting population. Names and identifiers should be validated before joining recruiting records to college statistics or draft outcomes.

## NFL Financial Outcomes Dataset

File: `data/processed/draft_nfl_financial_outcomes.csv`

- Grain: one row per NFL draft pick, identified by `draft_year` and `pick`.
- Coverage: draft classes 2016–2025; 2,563 picks in the current extraction.
- Draft linkage: 2,433 picks have a verified link to a GSIS player identifier based on normalized player name, draft year, and overall pick agreement.
- Financial coverage: 2,423 picks have observed financial-season records; 140 picks have missing financial outcomes.
- `observed_career_cash_paid_millions`: sum of available player-season cash observations, expressed in millions of dollars. This is observed cash through the available source window, not verified lifetime earnings.
- `observed_career_base_salary_millions` and `observed_career_guaranteed_salary_millions`: sums of recorded season-level fields. These are distinct from contract-level total guarantees.
- `observed_financial_seasons`: number of seasons represented in the financial history. Coverage varies by player and draft class.
- `selected_contract_value_millions`, `selected_contract_apy_millions`, and `selected_contract_guaranteed_millions`: terms from one selected contract record, not cumulative career contract values. The selected record may not be the player's rookie contract.
- Contract monetary fields and season-history financial fields are represented in millions of dollars in the current extraction.
- Missing financial values are not converted to zero. A missing record does not establish that a player earned nothing.
- Cash outcomes are right-censored: newer draft classes have had less time to accumulate recorded earnings. Raw cumulative cash should not be compared across draft classes without accounting for the observation window.
- The underlying season history may not represent a complete career. Interpret these measures as observed financial outcomes, not guaranteed complete career earnings.

### Financial linkage and interpretation

The current financial linkage uses exact normalized player names, matching draft year, matching overall pick, and a nonmissing GSIS identifier. This is a deterministic matching rule, not independent proof of identity. Revalidate the linkage if source records or matching rules change.

Financial outcomes are retrospective. For any return-to-college versus declare-for-the-NFL analysis, post-draft earnings and later contract terms must not be used as predictors available at the player's original decision date.
