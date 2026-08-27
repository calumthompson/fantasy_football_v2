import numpy as np
import requests 


def get_most_recent_gw_points(player_id: int) -> int:

    _STATIC_URL = "https://fantasy.premierleague.com/api/element-summary/{element_id}/"

    response = requests.get(_STATIC_URL.format(element_id=player_id))

    if response.status_code == 200:
        response = response.json()
        history = response['history']
        last_week = max(history, key=lambda gw: gw['fixture'])

        return last_week['total_points']