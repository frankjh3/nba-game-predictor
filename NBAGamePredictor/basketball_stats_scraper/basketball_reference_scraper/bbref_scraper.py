import pandas as pd

from basketball_stats_scraper.basketball_reference_scraper.bbref_html_parser import bbref_table, bbref_player, bbref_referee_stats, splits_table
from util import team_name_conversion as conversion
from basketball_stats_scraper.nba_com_scraper.nba_com_scraper import ref_assignments


BASE_URL = "https://www.basketball-reference.com"


def game_log(team, year, stats=None, advanced_stats=False, include_game_link=False, date=None):
    """
    Return game log table of certain team for a given year. Can limit which stats are returned
    :param team: team to return gamelog of
    :param year: year of gamelog
    :param stats: [list of stats] used to narrow down which stats from the gamelog are returned
    :param advanced_stats: set to True to return advanced stats of the team
    :param include_game_link: whether to include gamelink for each game in the gamelog - as last column
    :param date:
    :return: DataFrame of gamelog for a team in a year
    """
    if advanced_stats:
        gamelog = "gamelog-advanced"
    else:
        gamelog = "gamelog"

    url = '{BASE_URL}/teams/{team}/{year}/{gamelog}'.format(BASE_URL = BASE_URL, team = conversion.team_to_abr(team), year = year, gamelog = gamelog)
    if advanced_stats:
        table = bbref_table("div_tgl_advanced", url=url, include_game_link=include_game_link)
        # Blank columns - removed
        table.drop(table.columns[17], axis="columns", inplace=True)
        table.drop(table.columns[21], axis="columns", inplace=True)
    else:
        table = bbref_table("div_tgl_basic", url=url, include_game_link=include_game_link)

    table.set_index("Date", inplace=True)

    if date:
        table.drop(table.index[:table.index.get_loc(date)], inplace=True)

    if stats:
        stat_table = pd.DataFrame(index= table.index.values)
        for stat in stats:
            stat_table[stat] = table[stat]
        return stat_table
    else:
        return table


def team_stats(year, teams=None, stat_type="pergame"):
    """
    Return team stats for every team in a specifc year, unless specified
    :param year: year to return stats of
    :param teams: [list of teams] to get stats for
    :param stat_type: Valid stat_type = "per_game", "per_100", "advanced"
    :return: Returned as data frame of team's statistics
    """
    url = '{BASE_URL}/leagues/NBA_{year}.html'.format(BASE_URL=BASE_URL, year = year)

    if stat_type == "pergame":
        table_id = "all_team-stats-per_game"
    elif stat_type == "per100":
        table_id = "all_team-stats-per_poss"
    elif stat_type == "advanced":
        table_id = "all_misc_stats"
    else:
        raise Exception('Invalid stat_type - stat_type must be pergame, per100, or advanced')

    table = bbref_table(table_id, url=url)

    for i in range(len(table["Team"])):  # Remove * From team names (it is placed to signify if team was in playoffs)
        table.at[i, "Team"] = table.at[i, "Team"].strip("*")

    table.set_index("Team", inplace=True)

    if teams:
        condensed_data = pd.DataFrame(columns=table.columns.values, index=teams)
        for team in teams:
            condensed_data.loc[team] = table.loc[team]
        return condensed_data
    else:
        return table


def player_stats(player=None, player_url=None, stat_type="pergame"):
    """
    Returns the stats for a specific player in their career, year by year.
    The player's stats can be searched for by either the player name or the url
    of the player's page, if known
    :param player: Player is of form "Firstname Lastname (suffix)"
    :param player_url: link to player's page
    :param stat_type: Valid stat_type - "pergame", "per36", "per100poss", "advanced"
    :return: DataFrame of player's statistics year by year
    """

    if stat_type == "pergame":
        table_id = "div_per_game"
    elif stat_type == "per36":
        table_id = "all_per_minute"
    elif stat_type == "per100poss":
        table_id = "all_per_poss"
    elif stat_type == "advanced":
        table_id = "all_advanced"
    else:
        raise Exception('Invalid stat_type - stat_type must be pergame, per36, per100poss, advanced')

    if player_url:
        url = '{BASE_URL}{player_url}'.format(BASE_URL=BASE_URL, player_url=player_url)
        table = bbref_player(url=url, table_id=table_id)
    else:
        player_lower = player.lower()
        name_list = player_lower.split(" ")
        # Removes any suffixes from the name (they are not included in URL)
        if name_list[len(name_list) - 1] == "ii" or name_list[len(name_list) - 1] == "iii" \
            or name_list[len(name_list) - 1] == "iv" or name_list[len(name_list) - 1] == "v" \
                or name_list[len(name_list) - 1] == "jr." or name_list[len(name_list) - 1] == "sr.":
            name_list.pop()
        name_string = (name_list[len(name_list) - 1][:5] + name_list[0][:2])
        url = '{BASE_URL}/players/{last_initial}/{name}{num}.html'.format(BASE_URL=BASE_URL,
                                                                          last_initial=name_string[0],
                                                                          name=name_string,
                                                                          num="01")
        # Check if strong tag contains first, last, jr./sr./etc..
        table = bbref_player(url=url, table_id=table_id, player_name=player)

    table.set_index("Season", inplace=True)
    return table


# date - of the form year-month-day (all in numbers)
def inactives(box_url=None, home_team=None, date=None):
    if box_url is not None:
        url = '{BASE_URL}{box_url}'.format(BASE_URL=BASE_URL, box_url=box_url)
    else:
        date = date.split("-")
        url = '{BASE_URL}/boxscores/{year}{month}{day}0{team}.html'.format(BASE_URL=BASE_URL,
                                                                           year=date[0],
                                                                           month=date[1],
                                                                           day=date[2],
                                                                           team=conversion.team_to_abr(home_team))
    print(url)


def game_referee_stats(team):
    """
    Averages the relative stats for each referee in a given game (today) and returns
    their stats relative to average referees in terms of away and home team advantages/disadvantages
    :param team: team of tonight's game
    :return: DataFrame of averaged relative referee stats
    """
    team_name = conversion.team_to_city(team)
    if team_name == "LA Lakers":
        team_name = "L.A. Lakers"  #This is how it is represented on the nba officials website

    game_refs = ref_assignments(team=team_name)

    try:
        ref1 = game_refs.loc["Crew Chief"]
        ref2 = game_refs.loc["Referee"]
        ref3 = game_refs.loc["Umpire"]
    except KeyError:
        ref1 = game_refs["Crew Chief"][0]
        ref2 = game_refs["Referee"][0]
        ref3 = game_refs["Umpire"][0]
    ref_stats_table = bbref_referee_stats(ref1, ref2, ref3)

    return ref_stats_table


def referee_stats(referee):
    ()


def splits(away_team, home_team, year):
    """
    Uses the split stats of away_team and home_team in a given year to return the home court advantage
    that the home team has.
    :return:
    """
    away_url = "{BASE_URL}/teams/{team}/{year}/splits/".format(
        BASE_URL=BASE_URL, team=conversion.team_to_abr(away_team), year=year)
    home_url = "{BASE_URL}/teams/{team}/{year}/splits/".format(
        BASE_URL=BASE_URL, team=conversion.team_to_abr(home_team), year=year)
    away_splits = splits_table(away_url)
    home_splits = splits_table(home_url)

    away_diff = [float(away_splits[2][0]) - float(away_splits[0][0]), float(away_splits[2][1]) - float(away_splits[0][1])]
    home_diff = [float(home_splits[1][1]) - float(home_splits[0][1]), float(home_splits[1][0]) - float(home_splits[0][0])]

    # [adjust away, adjust home]
    avg_splits = [z / 2 for z in [x + y for x, y in zip(away_diff, home_diff)]]

    return avg_splits[0] - avg_splits[1]
