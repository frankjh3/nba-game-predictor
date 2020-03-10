import requests
import pandas as pd
from bs4 import BeautifulSoup

from util import team_name_conversion as conversion

# team id used by teamrankings.com
team_id = {
    "New Orleans": 355,
    "Golden State": 363,
    "LA Clippers": 368,
    "Milwaukee": 361,
    "Toronto": 360,
    "Brooklyn": 348,
    "Philadelphia": 350,
    "San Antonio": 370,
    "Oklahoma City": 366,
    "Washington": 352,
    "Boston": 349,
    "Sacramento": 369,
    "Portland": 364,
    "Houston": 375,
    "Atlanta": 359,
    "Minnesota": 371,
    "LA Lakers": 367,
    "Charlotte": 377,
    "Denver": 373,
    "Indiana": 362,
    "Dallas": 376,
    "Utah": 374,
    "Phoenix": 365,
    "Orlando": 351,
    "New York": 353,
    "Chicago": 357,
    "Detroit": 356,
    "Memphis": 372,
    "Miami": 354,
    "Cleveland": 358
}


def ats_trends_table(team, year):
    """
    Returns table of trends for a certain team's performance in a given year relative to the
    point spread.

    :param team: team to return trends for
    :param year: year of trends to return for
    :return: DataFrame of trends ats for a given team in a year
    """

    url = "https://www.teamrankings.com/ajax/league/v3/situations_controller.php"

    session = requests.Session()
    data = {
        "situation_id": 1,
        "type": "team-overview",
        "league": "nba",
        "team_id": team_id[conversion.team_to_city(team)],
        "stat_id": None,
        "season_id": 216,
        "cat_type": 4,
        "view": "ats_trends",
        "is_previous": 0,
        "tournament_id": None,
        "range-filter": "yearly_{prev}_{current}".format(prev= str(year-1), current=year)
    }

    response = session.post(url=url, data=data)
    page = response.content
    soup = BeautifulSoup(page, features="lxml")

    rows = soup.find_all("tr")

    data_frame = pd.DataFrame(columns= ["Trend", "ATS Record", "Cover%", "MOV", "ATS+-"], index=range(len(rows)))

    for i in range(len(rows)):
        cells = rows[i].find_all("td")
        for j in range(len(cells)):
            cells[j] = cells[j].get_text()
        data_frame.loc[i] = cells
    return data_frame


def ats_results_table(team):
    """
    Returns a DataFrame of a team's performance against the spread for each game in the current year
    :param team: team to return ATS results for
    :return: DataFrame of current season's spread results for a team
    """
    team = conversion.team_to_full(team).replace(" ", "-").lower()
    if team == "los-angeles-clippers":
        team = "la-clippers"

    url = "https://www.teamrankings.com/nba/team/{team}/ats-results".format(team=team)
    response = requests.get(url)

    page = response.content
    soup = BeautifulSoup(page, features="lxml")

    rows = soup.find_all("tr")
    data_frame = pd.DataFrame(columns=["Date", "H/A", "Opponent", "Opp Rank", "Line", "Result", "Diff"], index=range(len(rows) - 1))

    # Gets rid of header row
    for i in range(1, len(rows)):
        cells = rows[i].find_all("td")
        for j in range(len(cells)):
            cells[j] = cells[j].get_text()
        data_frame.loc[i - 1] = cells

    return data_frame


