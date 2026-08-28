import numpy as np
import requests 


class LivePlayerData():

    _STATIC_URL = "https://fantasy.premierleague.com/api/bootstrap-static/"

    def __init__(self):

        response = requests.get(self._STATIC_URL)
    
        if response.status_code == 200:
            self._raw_data = response.json()

            self.player_data = {}

            for element in self._raw_data['elements']:
                name = element['first_name'] + " " + element['second_name']
                self.player_data[name] = element


            self.element_types_map = {element['id']: element['singular_name_short'] for element in self._raw_data['element_types']}
            self.teams_map = {team['id']: team['name'] for team in self._raw_data['teams']}

        else:
            raise Exception(f"Failed to fetch data from FPL API. Status code: {response.status_code}")


    def get_player_id(self, name: str) -> str:
        """Return a player's FPL element ID, or NaN when the name is unknown."""
        try:
            return str(int(self.player_data[name]["id"]))
        except KeyError:
            return np.nan

    def get_player_web_name(self, name: str) -> str:
        """Return the player's short display name used by the FPL website."""
        try:
            return self.player_data[name]["web_name"]
        except KeyError:
            return np.nan

    def get_live_player_cost(self, name: str) -> int:
        """
        Get the live costs of players from the FPL API.
        Returns a dictionary with player IDs as keys and their live costs as values.
        """

        try: 
            return self.player_data[name]['now_cost']
        except:
            return np.nan

    def get_live_player_team(self, name: str) -> str:
        """
        Get the live team of players from the FPL API.
        Returns a dictionary with player IDs as keys and their live teams as values.
        """

        try: 
            return self.teams_map[self.player_data[name]['team']]
        except:
            return np.nan

    def get_live_player_position(self, name: str) -> str:
        """
        Get the live position of players from the FPL API.
        Returns a dictionary with player IDs as keys and their live positions as values.
        """

        try: 
            return self.element_types_map[self.player_data[name]['element_type']]
        except:
            return np.nan


    # TODO: ADD injury status, form, and other relevant live data as needed
