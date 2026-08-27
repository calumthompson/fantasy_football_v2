"""Strict object models for responses from the FPL API."""

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, StrictBool, StrictFloat, StrictInt, StrictStr


StrictNumber = Union[StrictInt, StrictFloat]


class FPLModel(BaseModel):
    """Base model that rejects coercion and undocumented fields."""

    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)


class ChipPlay(FPLModel):
    chip_name: StrictStr
    num_played: StrictInt


class TopElementInfo(FPLModel):
    id: StrictInt
    points: StrictInt


class Gameweek(FPLModel):
    id: StrictInt
    name: StrictStr
    deadline_time: StrictStr
    release_time: Optional[StrictStr]
    average_entry_score: StrictInt
    finished: StrictBool
    data_checked: StrictBool
    highest_scoring_entry: Optional[StrictInt]
    deadline_time_epoch: StrictInt
    deadline_time_game_offset: StrictInt
    highest_score: Optional[StrictInt]
    is_previous: StrictBool
    is_current: StrictBool
    is_next: StrictBool
    cup_leagues_created: StrictBool
    h2h_ko_matches_created: StrictBool
    can_enter: StrictBool
    can_manage: StrictBool
    released: StrictBool
    ranked_count: StrictInt
    overrides: Dict[StrictStr, Any]
    chip_plays: List[ChipPlay]
    most_selected: Optional[StrictInt]
    most_transferred_in: Optional[StrictInt]
    top_element: Optional[StrictInt]
    top_element_info: Optional[TopElementInfo]
    transfers_made: StrictInt
    most_captained: Optional[StrictInt]
    most_vice_captained: Optional[StrictInt]


class Team(FPLModel):
    code: StrictInt
    draw: StrictInt
    form: None
    id: StrictInt
    loss: StrictInt
    name: StrictStr
    played: StrictInt
    points: StrictInt
    position: StrictInt
    short_name: StrictStr
    strength: None
    team_division: None
    unavailable: StrictBool
    win: StrictInt
    link_url: StrictStr
    strength_overall_home: StrictInt
    strength_overall_away: StrictInt
    strength_attack_home: StrictInt
    strength_attack_away: StrictInt
    strength_defence_home: StrictInt
    strength_defence_away: StrictInt
    pulse_id: StrictInt


class ElementType(FPLModel):
    id: StrictInt
    plural_name: StrictStr
    plural_name_short: StrictStr
    singular_name: StrictStr
    singular_name_short: StrictStr
    squad_select: StrictInt
    squad_min_select: None
    squad_max_select: None
    squad_min_play: StrictInt
    squad_max_play: StrictInt
    ui_shirt_specific: StrictBool
    sub_positions_locked: List[StrictInt]
    element_count: StrictInt


class ElementStat(FPLModel):
    label: StrictStr
    name: StrictStr


class Phase(FPLModel):
    id: StrictInt
    name: StrictStr
    start_event: StrictInt
    stop_event: StrictInt
    highest_score: Optional[StrictInt]


class Chip(FPLModel):
    id: StrictInt
    name: StrictStr
    number: StrictInt
    start_event: StrictInt
    stop_event: StrictInt
    chip_type: StrictStr
    overrides: Dict[StrictStr, Any]


class PriceChangeProjection(FPLModel):
    offset: StrictInt
    projected_percent: StrictStr
    likelihood: StrictInt


class Player(FPLModel):
    can_transact: StrictBool
    can_select: StrictBool
    chance_of_playing_next_round: Optional[StrictInt]
    chance_of_playing_this_round: Optional[StrictInt]
    code: StrictInt
    cost_change_event: StrictInt
    cost_change_event_fall: StrictInt
    cost_change_start: StrictInt
    cost_change_start_fall: StrictInt
    price_change_percent: StrictStr
    price_change_hourly_rate: StrictInt
    price_change_projections: List[PriceChangeProjection]
    price_change_locked_until: Optional[StrictStr]
    price_change_calibrating: StrictBool
    dreamteam_count: StrictInt
    element_type: StrictInt
    ep_next: StrictStr
    ep_this: StrictStr
    event_points: StrictInt
    first_name: StrictStr
    form: StrictStr
    id: StrictInt
    in_dreamteam: StrictBool
    news: StrictStr
    news_added: Optional[StrictStr]
    now_cost: StrictInt
    photo: StrictStr
    points_per_game: StrictStr
    removed: StrictBool
    second_name: StrictStr
    selected_by_percent: StrictStr
    special: StrictBool
    squad_number: None
    status: StrictStr
    team: StrictInt
    team_code: StrictInt
    total_points: StrictInt
    transfers_in: StrictInt
    transfers_in_event: StrictInt
    transfers_out: StrictInt
    transfers_out_event: StrictInt
    value_form: StrictStr
    value_season: StrictStr
    web_name: StrictStr
    known_name: StrictStr
    region: Optional[StrictInt]
    team_join_date: Optional[StrictStr]
    birth_date: Optional[StrictStr]
    has_temporary_code: StrictBool
    opta_code: StrictStr
    minutes: StrictInt
    goals_scored: StrictInt
    assists: StrictInt
    clean_sheets: StrictInt
    goals_conceded: StrictInt
    own_goals: StrictInt
    penalties_saved: StrictInt
    penalties_missed: StrictInt
    yellow_cards: StrictInt
    red_cards: StrictInt
    saves: StrictInt
    bonus: StrictInt
    bps: StrictInt
    influence: StrictStr
    creativity: StrictStr
    threat: StrictStr
    ict_index: StrictStr
    clearances_blocks_interceptions: StrictInt
    recoveries: StrictInt
    tackles: StrictInt
    defensive_contribution: StrictInt
    starts: StrictInt
    expected_goals: StrictStr
    expected_assists: StrictStr
    expected_goal_involvements: StrictStr
    expected_goals_conceded: StrictStr
    corners_and_indirect_freekicks_order: Optional[StrictInt]
    corners_and_indirect_freekicks_text: StrictStr
    direct_freekicks_order: Optional[StrictInt]
    direct_freekicks_text: StrictStr
    penalties_order: Optional[StrictInt]
    penalties_text: StrictStr
    scout_risks: List[Any]
    scout_news_link: StrictStr
    influence_rank: StrictInt
    influence_rank_type: StrictInt
    creativity_rank: StrictInt
    creativity_rank_type: StrictInt
    threat_rank: StrictInt
    threat_rank_type: StrictInt
    ict_index_rank: StrictInt
    ict_index_rank_type: StrictInt
    expected_goals_per_90: StrictNumber
    saves_per_90: StrictNumber
    expected_assists_per_90: StrictNumber
    expected_goal_involvements_per_90: StrictNumber
    expected_goals_conceded_per_90: StrictNumber
    goals_conceded_per_90: StrictNumber
    now_cost_rank: StrictInt
    now_cost_rank_type: StrictInt
    form_rank: StrictInt
    form_rank_type: StrictInt
    points_per_game_rank: StrictInt
    points_per_game_rank_type: StrictInt
    selected_rank: StrictInt
    selected_rank_type: StrictInt
    starts_per_90: StrictNumber
    clean_sheets_per_90: StrictNumber
    defensive_contribution_per_90: StrictNumber

    @property
    def price(self) -> float:
        """Return the displayed price in millions of pounds."""
        return self.now_cost / 10


class BootstrapData(FPLModel):
    """Validated contents of the bootstrap-static endpoint."""

    chips: List[Chip]
    events: List[Gameweek]
    game_settings: Dict[StrictStr, Any]
    game_config: Dict[StrictStr, Any]
    phases: List[Phase]
    teams: List[Team]
    total_players: StrictInt
    element_stats: List[ElementStat]
    element_types: List[ElementType]
    elements: List[Player]

    def player_by_id(self, player_id: int) -> Player:
        """Return a player by API id, raising ``KeyError`` if absent."""
        return next(player for player in self.elements if player.id == player_id)
