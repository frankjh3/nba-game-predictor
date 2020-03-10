import requests
import pandas as pd
from bs4 import BeautifulSoup


def referee_assignments():
    """
    Finds the referee assignments for today for each game from official.nba.com
    """
    response = requests.get("https://official.nba.com/referee-assignments/")
    page = response.content
    soup = BeautifulSoup(page, features="lxml")

    table = soup.find("div", {"class": "entry-content"})
    rows = table.find_all("tr")

    data_frame = pd.DataFrame(index=range(len(rows) - 1), columns=
    ["Home", "Crew Chief", "Referee", "Umpire"])

    del rows[0]  # Deletes header from table
    for i in range(len(rows)):
        cells = rows[i].find_all("td")
        for j in range(len(cells)):
            cells[j] = cells[j].get_text(strip="\n")
        del cells[4]  # Deletes alternate referee (usually not given)
        data_frame.loc[i] = cells

    # Game is represented as "away @ home"
    # Separates these and stores away team names as the index of the data_frame
    games = data_frame["Home"]

    away_teams = []
    home_teams = []
    for game in games:
        teams = game.split("@")
        for i in range(len(teams)):
            teams[i] = teams[i].strip()
        away_teams.append(teams[0])
        home_teams.append(teams[1])

    data_frame["Away"] = away_teams
    data_frame.set_index("Away", inplace=True)
    data_frame["Home"] = home_teams
    data_frame.columns.values[0] = "Home"

    return data_frame
