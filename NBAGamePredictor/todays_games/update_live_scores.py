import datetime
import requests
from util import team_name_conversion as conversion
from todays_games.todays_spreads import initialize_games


def update_scores(games):
    """
    Update scores in games[] and then update away_scores[] and home_scores[] labels
    Data is pulled from NBA.com/scores
    """
    base_url = "https://data.nba.net/prod/v2/{year}{month}{day}/scoreboard.json"

    date = datetime.datetime.now()
    url = base_url.format(year=str(date.year), month=str(date.month).zfill(2), day=str(date.day).zfill(2))

    nba_data = requests.get(url).json()

    game_data = nba_data["games"]

    # For each game, match it with the data returned from game_data and update scores and time
    for game in games:
        for data in game_data:
            away_name = conversion.team_to_city(data["vTeam"]["triCode"])
            home_name = conversion.team_to_city(data["hTeam"]["triCode"])
            if game.away_team == away_name\
                    and game.home_team == home_name:
                game.away_score = data["vTeam"]["score"]
                game.home_score = data["hTeam"]["score"]

                # only update scores if the game has started and someone has scored
                if game.away_score and game.home_score and \
                        (game.away_score != "0" or game.home_score != "0"):
                    update_time(data, game)
                break


def update_time(game_json, game):
    period = game_json["period"]
    if period["isHalftime"]:
        game.time = "Halftime"
    elif period["isEndOfPeriod"]:
        game.time = "End of Q" + str(period["current"])
    elif game_json["statusNum"] == 3:
        game.time = "Final"
    else:
        game.time = "Q{quarter} {clock}".format(quarter=period["current"],
                                                clock=game_json["clock"])

