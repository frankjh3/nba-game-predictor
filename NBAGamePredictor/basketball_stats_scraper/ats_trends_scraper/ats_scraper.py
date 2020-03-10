import numpy as np
from basketball_stats_scraper.ats_trends_scraper.ats_html_parser import ats_trends_table, ats_results_table


def ats_trends(team, year):
    """
    trends include splits for a team, with ATS record, Cover%, MOV, and ATS+-
    """
    data_frame = ats_trends_table(team, year)
    data_frame.set_index("Trend", inplace=True)

    return data_frame


def ats_results(team):
    """
    ATS results for each game, with line and result
    """
    data_frame = ats_results_table(team)
    data_frame.set_index("Date", inplace=True)

    return data_frame


def season_spreads(team):
    """
    spreads for a team so far this season
    """
    data_frame = ats_results_table(team)

    spreads = np.array((data_frame["Line"]))
    spreads = np.reshape(spreads, (len(spreads), 1))

    for i in range(len(spreads)):
        if spreads[i][0] == "+":
            spreads[i] = spreads[i][1:]
        elif spreads[i] == "(Pick)":
            spreads[i] = 0
        spreads[i] = float(spreads[i])

    return spreads
