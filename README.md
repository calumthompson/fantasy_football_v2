# fantasy-football

Fantasy football analytics package.

## Setup

```bash
poetry install
```

## Usage

```python
import fantasy_football
```

### FPL API

The API client downloads the core FPL dataset and validates it before returning
Pydantic models.

```python
from fantasy_football.fpl_api import FPLAPIClient

snapshot = FPLAPIClient().load_full_snapshot()

for player in snapshot.players[:5]:
    print(player.web_name, player.last_season_performance)
```

### Live upcoming-fixture predictions

```python
from fantasy_football.model import predict_upcoming_fixtures_from_fpl

predictions = predict_upcoming_fixtures_from_fpl()
print(predictions.head(20))
```
