from app.components.app_data_inspector import render_app_data_inspector
from components.log_viewer import render_log_viewer

from app.services.app_data import AppData


def render_technical(app_data: AppData, force_refresh: bool) -> None:
    render_log_viewer(force_refresh)

    render_app_data_inspector(app_data)

