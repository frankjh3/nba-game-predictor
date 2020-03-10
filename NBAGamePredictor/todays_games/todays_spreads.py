from bs4 import BeautifulSoup
import requests
from todays_games.game_data import GameData


def initialize_games():
    """
    Gets the games, spreads, and times for today's NBA Games.
    If all of the games are already playing, this has a chance to pull tomorrow's games instead
    :return:
    """
    odds_shark_site = requests.get("https://www.oddsshark.com/nba/odds")
    odds_shark_games = odds_shark_site.content

    soup = BeautifulSoup(odds_shark_games, features="lxml")

    away_team = []
    home_team = []
    spread = []
    time = []
    games_list = []

    outer_container = soup.find("div", {"class": "not-futures"})

    games = outer_container.findAll()

    odds_shark_date = games[0].text
    odds_shark_date_list = odds_shark_date.split(" ")
    odds_shark_date_list[2] = odds_shark_date_list[2].strip()
    odds_shark_date_list[1] = odds_shark_date_list[1].strip()

    for i in range(1, len(games)):
        game = games[i]
        if game["class"][0] == "op-separator-bar":
            break
        elif game["class"][0] == "op-matchup-wrapper":
            away_team.append(game.find("div", {"class": "op-matchup-team op-matchup-text op-team-top"}).text)
            home_team.append(game.find("div", {"class": "op-matchup-team op-matchup-text op-team-bottom"}).text)
            time.append(game.find("div", {"class": "op-matchup-time op-matchup-text"}).text)

    spread_container = soup.findAll("div", {"class": "op-item-row-wrapper not-futures"})
    for i in range(len(away_team)):
        if len(away_team) == 1:
            spread.append(spread_container[i].find("div", {"class": "op-item op-spread op-opening"}).text)
        else:
            spread.append(spread_container[i].find("div", {"class": "op-item op-spread border-bottom op-opening"}).text)
        games_list.append(GameData(away_team[i], home_team[i], spread[i], time[i],
                                   str("{}-{}".format(odds_shark_date_list[1], odds_shark_date_list[2]))))

    return games_list
