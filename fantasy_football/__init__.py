#%% 
"""Fantasy football analytics."""
from fantasy_football.model import predict_upcoming_fixtures_from_fpl
from fantasy_football.fpl_api import FPLAPIClient

__version__ = "0.1.0"


if __name__ == '__main__':


    snapshot = FPLAPIClient().load_full_snapshot()

    for player in snapshot.players[:5]:
        print(player.web_name, player.last_season_performance)

    predictions = predict_upcoming_fixtures_from_fpl()
    print(predictions.head(20))

#%%