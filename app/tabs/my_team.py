from app.components.current_team import render_all_players, render_current_team
from app.components.transfer_recommendation import render_transfer_recommendation


def render_my_team(app_data) -> None:
    render_current_team(app_data)
    render_transfer_recommendation(app_data)
    render_all_players(app_data)
