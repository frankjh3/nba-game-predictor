"""
Combine scrapers for each website into one web scraper
Returns DataFrame (unless otherwise stated) containing results of scraping
"""
from basketball_stats_scraper.ats_trends_scraper.ats_scraper import *
from basketball_stats_scraper.basketball_reference_scraper.bbref_scraper import *
from basketball_stats_scraper.nba_com_scraper.nba_com_scraper import *


def ats_trends(team, year):
    return ats_trends(team, year)


def ats_results(team):
    return ats_results(team)


def season_spreads(team):
    return season_spreads(team)


def advanced_game_log(team, year, include_game_link=False, date=None):
    return game_log(team, year, advanced_stats=True,
                    include_game_link=include_game_link, date=date)


def standard_game_log(team, year, include_game_link=False, date=None):
    return game_log(team, year, advanced_stats=False,
                    include_game_link=include_game_link, date=date)


def per_game_team_stats(year, teams=None):
    return team_stats(year, teams=teams, stat_type="pergame")


def per_100_poss_team_stats(year, teams=None):
    return team_stats(year, teams=teams, stat_type="per100")


def advanced_team_stats(year, teams=None):
    return team_stats(year, teams=teams, stat_type="advanced")


def per_game_player_stats(player=None, player_url=None):
    return player_stats(player=player, player_url=player_url,
                        stat_type="pergame")


def per_36_mins_player_stats(player=None, player_url=None):
    return player_stats(player=player, player_url=player_url,
                        stat_type="per36")


def per_100_poss_player_stats(player=None, player_url=None):
    return player_stats(player=player, player_url=player_url,
                        stat_type="per100poss")


def advanced_player_stats(player=None, player_url=None):
    return player_stats(player=player, player_url=player_url,
                        stat_type="advanced")


def game_referee_stats(team):
    return game_referee_stats(team)


