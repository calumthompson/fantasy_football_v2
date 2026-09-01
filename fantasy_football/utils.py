import pandas as pd
import pulp


def create_optimal_team(
    data: pd.DataFrame,
    target_column: str,
    excluded_player_names: list[str] | None = None,
) -> pd.DataFrame:
    """Return the highest-scoring valid FPL squad within a £100m budget.

    Args:
        data: Candidate players and their squad attributes.
        target_column: Column maximised by the optimiser.
        excluded_player_names: Player names that cannot be selected.
    """
    position_constraints = {
        "GKP": 2,
        "DEF": 5,
        "MID": 5,
        "FWD": 3,
    }

    budget = 1000  # Player values are stored in tenths of a million pounds.
    max_players_per_team = 3

    required_columns = {"name", "position", "team", "value", target_column}
    missing_columns = required_columns.difference(data.columns)
    if missing_columns:
        raise ValueError(f"Missing required columns: {sorted(missing_columns)}")

    excluded_player_names = excluded_player_names or []
    players = data.loc[~data["name"].isin(excluded_player_names)].reset_index(drop=True)
    if players[["position", "team", "value", target_column]].isna().any().any():
        raise ValueError("Position, team, value, and forecast columns cannot be null.")

    problem = pulp.LpProblem("the_draft", pulp.LpMaximize)
    selected = {
        index: pulp.LpVariable(f"select_{index}", cat="Binary")
        for index in players.index
    }

    problem += pulp.lpSum(
        selected[index] * players.at[index, target_column] for index in players.index
    )
    problem += (
        pulp.lpSum(
            selected[index] * players.at[index, "value"] for index in players.index
        )
        <= budget
    )

    for position, required_count in position_constraints.items():
        matching_players = players.index[players["position"] == position]
        problem += (
            pulp.lpSum(selected[index] for index in matching_players) == required_count
        )

    for team in players["team"].unique():
        matching_players = players.index[players["team"] == team]
        problem += (
            pulp.lpSum(selected[index] for index in matching_players)
            <= max_players_per_team
        )

    status = problem.solve(pulp.PULP_CBC_CMD(msg=False))
    if pulp.LpStatus[status] != "Optimal":
        raise ValueError(f"No valid team found: {pulp.LpStatus[status]}")

    selected_indices = [
        index for index in players.index if selected[index].value() > 0.5
    ]
    return players.loc[selected_indices].reset_index(drop=True)
