# Model layout

- `base_models/` contains reusable feature engineering and inference code used by
  the ensemble.
- `training/base_models/` contains the notebooks used to train and compare each
  base model.
- `artifacts/` is populated by the training notebooks with fitted model files.

Run `training/base_models/pre_season_model.ipynb` through its final cell to refit
the percentile-weighted model on all development data and write
`artifacts/pre_season_model.joblib`. It also exports player scores for the
2025/26 ensemble to `artifacts/pre_season_scores_2025_26.joblib`, keyed by the
stable cross-season FPL player code.

Run `training/base_models/in_season_model.ipynb` through its final cell to refit
the selected unweighted model on all development data and write
`artifacts/in_season_model.joblib`. It also builds deadline-safe fixture features
for 2025/26 and exports `artifacts/in_season_scores_2025_26.joblib` for the
ensemble.

Run `training/ensemble_model.ipynb` through its final cell to validate the
chronological folds, refit on every available 2025/26 fixture row, and write
`artifacts/ensemble_model.joblib` for later-season inference.

## Live upcoming-fixture predictions

The production pipeline downloads the FPL bootstrap, fixtures, and every
player's element summary. It combines previous-season aggregate scores with
current-season rolling fixture form, constructs every player-fixture in the
next gameweek, and passes those rows through the ensemble:

```python
from fantasy_football.model import predict_upcoming_fixtures_from_fpl

predictions = predict_upcoming_fixtures_from_fpl()
print(predictions.head(20))
```

It can also be run from the project root:

```bash
poetry run python -m fantasy_football.model.prediction_pipeline
```
