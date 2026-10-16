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
