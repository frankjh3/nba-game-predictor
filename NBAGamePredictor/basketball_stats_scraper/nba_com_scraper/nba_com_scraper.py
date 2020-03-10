from basketball_stats_scraper.nba_com_scraper.nba_com_html_parser import referee_assignments


def ref_assignments(team=None):
    """
    Returns referee assignments today for each game, unless a game is specified.
    If a game is specified, only returns referees for that game.

    :param team: team to return referee assignments for
    :return: DataFrame of referee assignments for today's games
    """
    data_frame = referee_assignments()
    if team is not None:
        try:
            return data_frame.loc[team]
        except KeyError:
            # In the case the home team is entered, it will return games based on row with Home = to team passed
            return data_frame[data_frame["Home"] == team]
    else:
        return data_frame
