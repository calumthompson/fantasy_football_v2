# API guide

## bootstrap-static
Up to date snapshot of the league

- events - List of gameweeks, past and future. Gets updated with info as it goes e.g. is_current, is_next, is_previous, which player was most selected
- teams - Breakdown of teams, number of games played etc
- elements - up to date data on players e.g. name, cost, selected percentage


## Fixtures 
List of each game in the season, past and present

- team_a - away team number 
- team_h - home team number
- event - gw number

## element-summary
Returns data for a given player id provided

- Fixtures - details on upcoming fixtures
- history - details of previous games in the season
- history_past - high level values for previous seasons