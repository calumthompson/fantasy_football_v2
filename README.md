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
immutable Python objects. Incorrect types and undocumented fields raise an
`FPLValidationError`.

```python
from fantasy_football.fpl_api import FPLClient

data = FPLClient().get_bootstrap_data()

for player in data.elements[:5]:
    print(player.web_name, player.price, player.total_points)
```
